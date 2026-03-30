import math
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from server.app.models import MatchDetails, Player


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _safe_float(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def _pos_bucket(player: Player) -> str:
    """
    포지션 문자열을 대략적인 버킷으로 정규화.
    - crawler에서 `positionIdsDesc`를 split해서 `PlayerInfos.position`에 저장함.
    - 값은 'Forward', 'Defender', 'Midfielder', 'Goalkeeper' 등으로 들어오는 케이스가 많지만
      'Striker', 'Left Winger' 같은 세부 포지션도 섞일 수 있어 보수적으로 처리한다.
    """
    raw: Optional[str] = None
    if player.info and player.info.position:
        raw = player.info.position[0]
    if not raw and player.match_details:
        for md in player.match_details:
            if md and md.position:
                raw = md.position
                break

    s = (raw or "").strip().lower()
    if not s:
        return "midfielder"

    # GK
    if "keeper" in s or s in {"gk", "goalkeeper"}:
        return "goalkeeper"

    # DEF
    if any(k in s for k in ("def", "back", "centre-back", "center-back", "cb", "lb", "rb", "lwb", "rwb")):
        return "defender"

    # MID
    if any(k in s for k in ("mid", "wing", "wm", "am", "dm", "cm")):
        return "midfielder"

    # FWD
    if any(k in s for k in ("for", "att", "striker", "forward", "st", "cf", "ss")):
        return "forward"

    # fallback: unknown을 미드로 처리
    return "midfielder"


def _recent_match_details(player: Player, n: int = 10) -> List:
    mds = list(player.match_details or [])
    # match_id가 복합 PK의 일부라서 대체로 최신경기가 큰 값일 가능성이 높음
    mds.sort(key=lambda x: getattr(x, "match_id", 0) or 0, reverse=True)
    return mds[:n]


def _per90(sum_value: float, minutes: float) -> float:
    if minutes <= 0:
        return 0.0
    return (sum_value / minutes) * 90.0


def _sum_minutes(mds: Iterable) -> int:
    total = 0
    for md in mds:
        mins = getattr(md, "minutes_played", None)
        if isinstance(mins, int) and mins > 0:
            total += mins
    return total


async def compute_player_rating(player: Player) -> float:
    """
    선수 개별 rating 계산.

    원칙:
    - API/DB에 저장된 `PlayerInfos`(프로필/가치), `PlayerMatchAffectFeatures`(폼/가용성),
      `PlayerMatchDetails`(경기별 성과)만으로 계산한다.
    - 포지션별로 중요 지표가 다르므로, 최근 N경기(per90)를 기반으로 가중치를 다르게 적용한다.
    """
    rating = 1500.0

    info = player.info
    maf = player.match_affect_features
    pos = _pos_bucket(player)

    # 1) 시장가치 (log-scale)
    # - value가 0~수억(EUR)까지 분포할 수 있어 로그로 스케일링
    if info and info.current_market_value and info.current_market_value > 0:
        mv = float(info.current_market_value)
        rating += _clamp(math.log10(mv + 1.0), 0.0, 9.0) * 35.0  # 대략 0~315

    # 2) 나이 (피크: 27, 완만한 감산)
    if info and isinstance(info.age, int) and info.age > 0:
        age = info.age
        # peak=27, 10년 차이나면 약 -40점 수준
        rating += -2.0 * abs(age - 27)

    # 3) 가용성/부상 패널티
    if maf and maf.availability_status:
        s = maf.availability_status.strip().lower()
        if any(k in s for k in ("injur", "unavail", "suspend", "doubt", "out")):
            rating -= 80.0
    if maf and maf.injury_history:
        # 최근에 부상 이력이 많으면 추가 감산 (데이터 구조 불명이라 길이로만 처리)
        rating -= _clamp(len(maf.injury_history) * 5.0, 0.0, 30.0)

    # 4) 최근 폼: 우선 form_rating(있으면) + 없으면 최근 경기 rating 가중 평균으로 대체
    form = _safe_float(getattr(maf, "form_rating", None)) if maf else None
    if form is None:
        mds = [md for md in _recent_match_details(player, n=8) if getattr(md, "minutes_played", 0) and (md.rating is not None)]
        if mds:
            weights = [1.0 + (i * 0.15) for i in range(len(mds))]  # 최신일수록 가중치↑ (sort가 최신 먼저라 i가 작음)
            weights = list(reversed(weights))  # 최신에 더 큰 weight
            vals = [float(md.rating) for md in mds]
            form = sum(w * v for w, v in zip(weights, vals)) / max(sum(weights), 1.0)

    if form is not None:
        # FotMob rating ~ 0~10, 기준 6.5
        rating += (form - 6.5) * 55.0

    # 5) 시즌/커리어 평점 (fan_rating 또는 match_details의 season_average_rating 보조)
    fan = _safe_float(info.fan_rating) if info else None
    if fan is not None:
        rating += (fan - 6.5) * 25.0
    else:
        # 최신 match_detail에 season_average_rating가 있으면 사용
        for md in _recent_match_details(player, n=12):
            sar = _safe_float(getattr(md, "season_average_rating", None))
            if sar is not None and sar > 0:
                rating += (sar - 6.5) * 18.0
                break

    # 6) 최근 N경기 per90 성과 (포지션별 가중치)
    mds_all = [md for md in _recent_match_details(player, n=10) if getattr(md, "minutes_played", 0) and (md.minutes_played or 0) > 0]
    mins = float(_sum_minutes(mds_all))
    if mins > 0:
        goals = sum(getattr(md, "goals", 0) or 0 for md in mds_all)
        assists = sum(getattr(md, "assists", 0) or 0 for md in mds_all)
        xg = sum((_safe_float(getattr(md, "expected_goals", None)) or 0.0) for md in mds_all)
        xgot = sum((_safe_float(getattr(md, "expected_goals_on_target", None)) or 0.0) for md in mds_all)
        xa = sum((_safe_float(getattr(md, "expected_assists", None)) or 0.0) for md in mds_all)
        sot = sum((getattr(md, "shots_on_target", None) or 0) for md in mds_all)

        tackles = sum((getattr(md, "tackles", None) or 0) for md in mds_all)
        interceptions = sum((getattr(md, "interceptions", None) or 0) for md in mds_all)
        clearances = sum((getattr(md, "clearances", None) or 0) for md in mds_all)
        blocks = sum((getattr(md, "blocks", None) or 0) for md in mds_all)
        recoveries = sum((getattr(md, "recoveries", None) or 0) for md in mds_all)

        pass_acc = [(_safe_float(getattr(md, "pass_accuracy", None)) or 0.0) for md in mds_all if _safe_float(getattr(md, "pass_accuracy", None)) is not None]
        pass_acc_avg = (sum(pass_acc) / len(pass_acc)) if pass_acc else 0.0

        yel = sum(getattr(md, "yellow_cards", 0) or 0 for md in mds_all)
        red = sum(getattr(md, "red_cards", 0) or 0 for md in mds_all)

        g90 = _per90(float(goals), mins)
        a90 = _per90(float(assists), mins)
        xg90 = _per90(float(xg), mins)
        xgot90 = _per90(float(xgot), mins)
        xa90 = _per90(float(xa), mins)
        sot90 = _per90(float(sot), mins)

        def90 = _per90(float(tackles + interceptions + clearances + blocks + recoveries), mins)
        y90 = _per90(float(yel), mins)
        r90 = _per90(float(red), mins)

        # 포지션별 “점수”를 만들고, 최종 레이팅에 더함 (스케일: 수십~수백)
        att_score = (g90 * 1.8) + (xg90 * 1.2) + (xgot90 * 0.6) + (xa90 * 0.8) + (a90 * 1.0) + (sot90 * 0.3)
        def_score = def90 * 0.35
        pass_score = _clamp((pass_acc_avg - 75.0) / 10.0, -3.0, 3.0)  # -3~3

        if pos == "forward":
            rating += att_score * 55.0
            rating += def_score * 10.0
            rating += pass_score * 8.0
        elif pos == "defender":
            rating += def_score * 80.0
            rating += att_score * 18.0
            rating += pass_score * 10.0
        elif pos == "goalkeeper":
            # GK 상세 스탯이 아직 모델에 없어서 수비/평점 위주로만 반영
            rating += def_score * 70.0
            rating += pass_score * 12.0
        else:  # midfielder
            rating += att_score * 30.0
            rating += def_score * 45.0
            rating += pass_score * 15.0

        # 징계 패널티 (레드는 강하게)
        rating -= (y90 * 18.0) + (r90 * 120.0)

        # MOTM 보너스
        motm = sum(1 for md in mds_all if getattr(md, "is_man_of_the_match", False))
        rating += _clamp(motm * 10.0, 0.0, 40.0)

    # 마지막 안전장치: 너무 튀는 값 제한
    rating = _clamp(rating, 900.0, 2300.0)
    return round(rating, 2)

async def compute_lineup_features(
    players: List[Player],
    match_context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    라인업 기반 feature 확장
    """
    ratings = []
    att_rating = 0.0
    def_rating = 0.0
    
    for p in players:
        p_rating = await compute_player_rating(p)
        ratings.append(p_rating)

        bucket = _pos_bucket(p)
        if bucket == "forward":
            att_rating += p_rating
        elif bucket in {"defender", "goalkeeper"}:
            def_rating += p_rating
        else:
            att_rating += p_rating * 0.5
            def_rating += p_rating * 0.5

    total_rating = sum(ratings) if ratings else 0.0
    if len(players) > 0 and len(players) < 11:
        avg_p_rating = total_rating / len(players)
        total_rating += avg_p_rating * (11 - len(players))
        
    avg_age = sum([p.info.age for p in players if p.info and p.info.age]) / len(players) if players else 26
    
    rest_days = int(match_context.get("rest_days", 3) or 3)
    fatigue_penalty = 0.95 if rest_days < 3 else 1.0
    
    is_home = 1 if match_context.get("is_home") else 0
    importance = match_context.get("importance", 1.0)
    
    return {
        "total_rating": total_rating * fatigue_penalty,
        "att_rating": att_rating,
        "def_rating": def_rating,
        "avg_age": avg_age,
        "is_home": is_home,
        "importance": importance,
        "rating_diff": total_rating
        - float(match_context.get("opponent_rating", total_rating) or total_rating),
    }

def softmax(logits: List[float]) -> List[float]:
    """Logits을 확률로 변환 (합계 1.0)"""
    max_l = max(logits)
    exps = [math.exp(l - max_l) for l in logits]
    sum_exps = sum(exps)
    return [e / sum_exps for e in exps]

async def get_historical_win_rate(
    session: AsyncSession,
    team_id: int,
    *,
    is_home: Optional[bool] = None,
    last_n: int = 50,
) -> float:
    """
    특정 팀의 과거 N경기 승률 계산.

    asyncpg + 단일 AsyncSession에서는 이전 Result를 닫기 전에 루프 안에서
    추가 execute를 호출하면 "another operation is in progress"가 날 수 있어,
    상대 팀 득점은 한 번의 조회로 묶는다.
    """
    statement = (
        select(MatchDetails)
        .where(MatchDetails.team_id == team_id)
    )
    if is_home is not None:
        statement = statement.where(MatchDetails.is_home == is_home)

    statement = statement.order_by(MatchDetails.id.desc()).limit(last_n)
    result = await session.execute(statement)
    try:
        details = list(result.scalars())
    finally:
        await result.close()

    if not details:
        return 0.5

    match_ids = list({d.id for d in details})
    opp_stmt = select(MatchDetails.id, MatchDetails.team_id, MatchDetails.score).where(
        MatchDetails.id.in_(match_ids)
    )
    opp_res = await session.execute(opp_stmt)
    try:
        opp_rows = opp_res.all()
    finally:
        await opp_res.close()

    by_match: Dict[int, Dict[int, int]] = {}
    for row in opp_rows:
        mid = row[0]
        tid = row[1]
        sc = row[2] or 0
        by_match.setdefault(mid, {})[tid] = int(sc)

    wins = 0
    for detail in details:
        scores = by_match.get(detail.id, {})
        opp_score = next(
            (s for tid, s in scores.items() if tid != team_id),
            0,
        )

        if detail.score > opp_score:
            wins += 1
        elif detail.score == opp_score:
            wins += 0.5

    return round(wins / len(details), 4)

async def predict_match_outcomes(
    session: AsyncSession,
    home_players: List[Player], 
    away_players: List[Player], 
    home_team_id: int,
    away_team_id: int
) -> Dict[str, float]:
    """
    홈 승 / 무승부 / 원정 승 확률 예측 (Softmax 적용)
    """
    home_feats = await compute_lineup_features(home_players, {"is_home": True})
    away_feats = await compute_lineup_features(away_players, {"is_home": False})
    
    home_hist_win_rate = await get_historical_win_rate(session, home_team_id, is_home=True)
    away_hist_win_rate = await get_historical_win_rate(session, away_team_id, is_home=False)

    # 1. 홈 승 Logit
    # Rating 차이가 크고, 과거 승률이 높고, 홈 어드밴티지가 있을수록 높음
    logit_home = (
        -0.1 + # Intercept
        (0.002 * (home_feats["total_rating"] - away_feats["total_rating"])) +
        (1.5 * (home_hist_win_rate - away_hist_win_rate)) +
        0.3 # Home Advantage
    )

    # 2. 무승부 Logit
    # 두 팀의 전력 차이가 적을수록(절대값이 작을수록) 무승부 확률이 높아짐
    rating_diff_abs = abs(home_feats["total_rating"] - away_feats["total_rating"])
    logit_draw = (
        0.5 - # 기본 무승부 성향
        (0.001 * rating_diff_abs) - # 전력 차이가 클수록 무승부 감소
        (0.5 * abs(home_hist_win_rate - away_hist_win_rate)) # 과거 승률 차이가 클수록 무승부 감소
    )

    # 3. 원정 승 Logit (기준점)
    logit_away = 0.0

    # Softmax 적용
    probs = softmax([logit_home, logit_draw, logit_away])

    return {
        "home": round(probs[0], 4),
        "draw": round(probs[1], 4),
        "away": round(probs[2], 4)
    }
