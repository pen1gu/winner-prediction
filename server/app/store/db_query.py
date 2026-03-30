from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import select

from server.app.models import MatchInfos, MatchLogs
from server.app.models.session import AsyncSessionLocal
from server.app.models.teams.team import Team
from server.app.models.players.player import Player
from server.app.models.players.player_rating import PlayerRating

async def get_already_fetched_team_ids() -> list[int]:
    """
    이미 팀 정보를 가져온 팀 ID 목록을 가져오는 함수
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Team.id))
        try:
            return list(result.scalars().all())
        finally:
            await result.close()

async def get_already_fetched_player_ids() -> list[int]:
    """
    이미 선수 정보를 가져온 선수 ID 목록을 가져오는 함수
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Player.id))
        try:
            return list(result.scalars().all())
        finally:
            await result.close()


async def get_player_by_id(player_id: int) -> Player | None:
    """
    Player를 관계 포함해서 조회.

    compute 로직이 `player.info`, `player.match_affect_features`, `player.match_details`를
    세션 외부에서도 접근할 수 있게 미리 로드한다.
    """
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Player)
            .where(Player.id == player_id)
            .options(
                selectinload(Player.info),
                selectinload(Player.match_affect_features),
                selectinload(Player.match_details),
            )
        )
        res = await session.execute(stmt)
        try:
            return res.scalar_one_or_none()
        finally:
            await res.close()


async def get_latest_player_rating(player_id: int) -> PlayerRating | None:
    """
    선수의 최신 rating 로그 1건 조회.
    """
    async with AsyncSessionLocal() as session:
        stmt = (
            select(PlayerRating)
            .where(PlayerRating.player_id == player_id)
            .order_by(PlayerRating.created_at.desc(), PlayerRating.id.desc())
            .limit(1)
        )
        res = await session.execute(stmt)
        try:
            return res.scalar_one_or_none()
        finally:
            await res.close()


def match_log_to_summary_dict(match: MatchLogs) -> dict:
    """MatchLogs(관계 로드됨) → 목록 API용 dict."""
    info = match.match_infos
    home_detail = next((d for d in match.match_details if d.is_home), None)
    away_detail = next((d for d in match.match_details if not d.is_home), None)

    match_date: datetime | None = info.match_date if info else None

    return {
        "match_id": match.id,
        "home_team": info.home_team.name if info and info.home_team else "Home",
        "away_team": info.away_team.name if info and info.away_team else "Away",
        "league_name": info.league_name if info else None,
        "match_round": info.match_round if info else None,
        "match_date": match_date,
        "finished": bool(info.finished) if info else False,
        "stadium": info.stadium if info else None,
        "score": {
            "home": home_detail.score if home_detail else None,
            "away": away_detail.score if away_detail else None,
        },
        "stats": {
            "home_xg": home_detail.expected_goals_value if home_detail else None,
            "away_xg": away_detail.expected_goals_value if away_detail else None,
            "home_possession": home_detail.possession if home_detail else None,
            "away_possession": away_detail.possession if away_detail else None,
            "home_shots": home_detail.shots_total if home_detail else None,
            "away_shots": away_detail.shots_total if away_detail else None,
            "home_shots_on_target": home_detail.shots_on_target
            if home_detail
            else None,
            "away_shots_on_target": away_detail.shots_on_target
            if away_detail
            else None,
        },
    }


async def fetch_recent_match_logs_for_list(
    session: AsyncSession, *, limit: int
) -> list[MatchLogs]:
    limit = max(1, min(30, limit))
    stmt = (
        select(MatchLogs)
        .options(
            joinedload(MatchLogs.match_infos).joinedload(MatchInfos.home_team),
            joinedload(MatchLogs.match_infos).joinedload(MatchInfos.away_team),
            joinedload(MatchLogs.match_details),
        )
        .order_by(MatchLogs.id.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    try:
        return list(result.scalars().unique().all())
    finally:
        await result.close()


async def fetch_recent_match_summaries(
    session: AsyncSession, *, limit: int
) -> list[dict]:
    """
    웹 데모·목록 API용 최근 경기 요약 (demo_server.fetch_recent_matches 와 동일 스키마).
    """
    matches = await fetch_recent_match_logs_for_list(session, limit=limit)
    return [match_log_to_summary_dict(m) for m in matches]