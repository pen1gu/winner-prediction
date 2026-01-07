from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timezone

from server.app.models import (
    Player,
    Team,
    Manager,
    MatchDetails,
    MatchInfos,
    PlayerMatchDetails,
    PlayerInfos,
)
from server.app.models.matches.match_logs import MatchLogs
from server.utils.http.requests import FotMobHTTPClient
from server.utils.logger import get_logger

logger = get_logger(__name__)

class FotMobCrawler:
    def __init__(self):
        self.client = FotMobHTTPClient()

    async def fetch_team_overview(self, team_id: int):
        response = await self.client.get(
            "/data/teams",
            params={"id": team_id, "ccode3": "KOR"},
            raise_for_status=False
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get team info: {response.status_code} - {response.text}")

        return response.json()

    async def get_players_info_by_team_id(self, team: Team, response: dict) -> List[Any]:
        squad = response.get("squad", {}).get("squad", [None, {}])[1:]

        results = []
        for players_info in squad:
            for player_info in players_info.get("members", []):
                player_id = player_info.get("id")
                if not player_id:
                    continue
                
                position_str = player_info.get("positionIdsDesc", "")
                position_list = [p.strip() for p in position_str.split(",")] if position_str else None
                
                # Player (ID만)
                player = Player(id=player_id)
                
                # PlayerInfos (기본 정보)
                player_infos_obj = PlayerInfos(
                    id=player_id,
                        name=player_info.get("name"),
                        age=player_info.get("age"),
                        team_id=team.id,
                        position=position_list,
                        role=player_info.get("role"),
                        shirt_number=player_info.get("shirtNumber"),
                        height=player_info.get("height"),
                        weight=0,
                        birth_date=str(player_info.get("dateOfBirth")) if player_info.get("dateOfBirth") else None,
                        birth_place=player_info.get("cname"),
                        birth_country=player_info.get("cname"),
                        birth_state=player_info.get("cname"),
                    )
                
                results.extend([player, player_infos_obj])

        return results

    async def get_team_info_by_team_id(self, team_id: int, response: dict) -> Team:
        team_details = response.get("details", {})
        team_overview = response.get("overview", {}).get("venue", {})

        stadium_location = team_overview.get("widget", {}).get("location")
        if isinstance(stadium_location, list):
            stadium_location = str(stadium_location)
        
        team = Team(
            id=team_id, # fotmob_id -> id
            name=team_details.get("name"),
            country=team_details.get("country"),
            league=team_details.get("primaryLeagueName"),
            league_id=team_details.get("primaryLeagueId"),
            founded=team_overview.get("statPairs", [[], [], ["", 0]])[2][1] if team_overview.get("statPairs") else None,
            stadium=team_overview.get("widget", {}).get("name"),
            stadium_capacity=team_overview.get("statPairs", [[], ["", 0]])[1][1] if team_overview.get("statPairs") else None,
            stadium_location=stadium_location,
            stadium_city=team_overview.get("widget", {}).get("city"),
        )

        return team

    async def get_manager_info_by_team_id(self, team: Team, response: dict) -> Manager:
        manager_details = response.get("squad", {}).get("squad", [{}])[0].get("members", [{}])[0]

        manager = Manager(
            id=manager_details.get("id"), # fotmob_id -> id
            name=manager_details.get("name"),
            age=manager_details.get("age"),
            team_id=team.id,
            country=manager_details.get("cname"),
        )
        return manager

    async def get_match_logs_info_by_team_id(self, team_id: int, response: dict) -> List[Any]:
        fixtures = response.get("fixtures", {})
        all_fixtures = fixtures.get("allFixtures", {})
        match_logs_data = all_fixtures.get("fixtures", [])
        next_match_data = all_fixtures.get("nextMatch")
        
        if not match_logs_data:
            return []
        
        results = []
        current_date = datetime.now(timezone.utc)
        next_match_id = next_match_data.get("id") if next_match_data else None
        
        for match_data in match_logs_data:
            status = match_data.get("status", {})
            if not status: continue
            
            utc_time_str = status.get("utcTime")
            if not utc_time_str: continue
            
            try:
                if utc_time_str.endswith('Z'):
                    match_date = datetime.fromisoformat(utc_time_str.replace('Z', '+00:00'))
                else:
                    match_date = datetime.fromisoformat(utc_time_str)
            except ValueError: continue

            if match_date.tzinfo is None:
                match_date = match_date.replace(tzinfo=timezone.utc)
            else:
                match_date = match_date.astimezone(timezone.utc)
            
            finished = status.get("finished", False)
            cancelled = status.get("cancelled", False)
            not_started = match_data.get("notStarted", False)
            
            match_id = match_data.get("id")
            is_next_match = (next_match_id is not None and match_id == next_match_id) or (not_started and match_date > current_date)
            
            home_team = match_data.get("home", {})
            away_team = match_data.get("away", {})
            
            home_team_id = home_team.get("id")
            away_team_id = away_team.get("id")
            
            if not home_team_id or not away_team_id: continue
            
            # MatchLogs (ID만 포함)
            match_log = MatchLogs(id=match_id)
            
            # MatchInfos (공통 정보)
            match_info = MatchInfos(
                id=match_id,
                match_date=match_date,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                finished=finished,
                cancelled=cancelled,
                next_match=is_next_match
            )
            
            # MatchDetails (기초 점수 정보)
            home_details = MatchDetails(
                id=match_id,
                team_id=home_team_id,
                is_home=True,
                score=home_team.get("score", 0)
            )
            away_details = MatchDetails(
                id=match_id,
                team_id=away_team_id,
                is_home=False,
                score=away_team.get("score", 0)
            )
            
            results.extend([match_log, match_info, home_details, away_details])
        
        return results


    def _calculate_lineup_power_rating(self, starters: List[dict]) -> Optional[float]:
        """라인업 기반 전력 레이팅 계산 (사용자 직접 구현 예정)"""
        return None

    def _parse_lineup_players(self, players_list: List[dict], team_id: int) -> List[Dict[str, Any]]:
        """라인업의 선수 정보를 Player 모델 및 ID/평점 정보로 변환"""
        parsed_data = []
        for p in players_list:
            player_id = p.get("id")
            if not player_id:
                continue
                
            # 1. Player 모델 객체 생성 (ID만)
            player = Player(id=player_id)
            
            # 2. 경기별 메타 데이터 (ID와 평점)
            performance = p.get("performance") or {}
            rating = performance.get("rating")
            
            parsed_data.append({
                "player": player,
                "id": player_id,
                "rating": rating
            })
        return parsed_data

    async def get_match_details_info_by_match_id(self, match_id: int) -> List[Any]:
        response = await self.client.get(
            "/data/matchDetails",
            params={"matchId": match_id},
            raise_for_status=False
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get match details: {response.status_code} - {response.text}")
        
        data = response.json()

        # 1. 기본 매치 정보 (General)
        general = data.get("general") or {}
        home_team_id = general.get("homeTeam", {}).get("id")
        away_team_id = general.get("awayTeam", {}).get("id")
        match_date_str = general.get("matchTimeUTCDate")
        match_date = datetime.fromisoformat(match_date_str.replace('Z', '+00:00')) if match_date_str else datetime.now(timezone.utc)

        # 2. 상단 스코어보드 정보 (Header)
        header = data.get("header") or {}
        header_teams = header.get("teams", [{}, {}])
        status = header.get("status") or {}
        reason = status.get("reason") or {}
        penalties = reason.get("penalties") # [home, away]
        is_finished = status.get("finished", False)

        # 4. 핵심 상세 데이터 (Content)
        content = data.get("content") or {}
        match_facts = content.get("matchFacts") or {}
        info_box = match_facts.get("infoBox") or {}
        lineup = content.get("lineup") or {}
        
        # 4-3. 팀 통계 추출 (통합 구조 기반)
        stats_content = content.get("stats") or {}
        periods = stats_content.get("Periods") or {}
        all_stats_raw = periods.get("All", {}).get("stats", [])

        def parse_team_stats(stats_list: List[Dict]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
            """Periods.All.stats 리스트에서 그룹화 및 개별 지표를 한 번에 추출"""
            h_res, a_res = {}, {}
            # 결과 구조 초기화 (JSON 그룹 및 개별 필드)
            for d in [h_res, a_res]:
                d.update({
                    "attack_stats": {}, "passing_stats": {}, "defense_stats": {},
                    "duel_stats": {}, "discipline_stats": {}, "general_stats": {},
                    "expected_goals_value": 0.0, "expected_assists_value": 0.0, "expected_goals_on_target_value": 0.0,
                    "possession": None, "shots_total": 0, "shots_on_target": 0,
                    "big_chances": 0, "big_chances_missed": 0, "corners": 0,
                    "fouls": 0, "yellow_cards": 0, "red_cards": 0,
                    "accurate_passes": 0, "total_passes": 0, "offsides": 0,
                    "formation": None, "team_rating": None
                })

            # 지표별 그룹 매핑: (JSON그룹, 그룹내필드, 개별컬럼필드)
            category_map = {
                # 공격
                "total_shots": ("attack_stats", "shots_total", "shots_total"),
                "Shots": ("attack_stats", "shots_total", "shots_total"), # Fallback
                "ShotsOnTarget": ("attack_stats", "shots_on_target", "shots_on_target"),
                "ShotsOffTarget": ("attack_stats", "shots_off_target", None),
                "blocked_shots": ("attack_stats", "shots_blocked", None),
                "shots_inside_box": ("attack_stats", "shots_inside_box", None),
                "shots_outside_box": ("attack_stats", "shots_outside_box", None),
                "big_chance": ("attack_stats", "big_chances", "big_chances"),
                "big_chance_missed_title": ("attack_stats", "big_chances_missed", "big_chances_missed"),
                # 수비
                "matchstats.headers.tackles": ("defense_stats", "tackles", None),
                "interceptions": ("defense_stats", "interceptions", None),
                "clearances": ("defense_stats", "clearances", None),
                "shot_blocks": ("defense_stats", "blocks", None),
                "keeper_saves": ("defense_stats", "keeper_saves", None),
                # 듀얼
                "duel_won": ("duel_stats", "duels_won_total", None),
                "aerials_won": ("duel_stats", "duels_aerial_won", None),
                "ground_duels_won": ("duel_stats", "duels_ground_won", None),
                # 징계
                "fouls": ("discipline_stats", "fouls", "fouls"),
                "yellow_cards": ("discipline_stats", "yellow_cards", "yellow_cards"),
                "red_cards": ("discipline_stats", "red_cards", "red_cards"),
                # 일반
                "corners": ("general_stats", "corners", "corners"),
                "Offsides": ("general_stats", "offsides", "offsides")
            }

            for group in stats_list:
                for stat in group.get("stats", []):
                    key = stat.get("key")
                    # stats 리스트([h, a]) 혹은 stat 딕셔너리({"home": h, "away": a}) 모두 대응
                    vals = stat.get("stats")
                    if not vals and stat.get("stat"):
                        s = stat["stat"]
                        if isinstance(s, dict):
                            vals = [s.get("home"), s.get("away")]
                    
                    if not vals:
                        vals = [None, None]
                    if not key: continue

                    # A. 그룹 매핑 처리
                    if key in category_map:
                        cat, g_field, f_field = category_map[key]
                        h_res[cat][g_field], a_res[cat][g_field] = vals[0], vals[1]
                        if f_field:
                            try:
                                h_res[f_field] = int(vals[0]) if vals[0] is not None else 0
                                a_res[f_field] = int(vals[1]) if vals[1] is not None else 0
                            except (ValueError, TypeError):
                                h_res[f_field], a_res[f_field] = vals[0], vals[1]

                    # B. 특수 처리
                    elif key.lower() in ["ballpossession", "ballpossesion"]:
                        def parse_pos(v):
                            if v is None: return None
                            try: return float(str(v).replace("%", ""))
                            except: return None
                        h_res["possession"], a_res["possession"] = parse_pos(vals[0]), parse_pos(vals[1])
                        h_res["general_stats"]["possession"], a_res["general_stats"]["possession"] = h_res["possession"], a_res["possession"]
                    
                    elif key == "accurate_passes":
                        for i, (v, target_res) in enumerate(zip(vals, [h_res, a_res])):
                            if isinstance(v, str) and "(" in v:
                                try:
                                    acc = int(v.split("(")[0].strip())
                                    pct = float(v.split("(")[1].replace("%)", ""))
                                    target_res["passing_stats"]["accurate_passes"] = acc
                                    target_res["passing_stats"]["accuracy_percent"] = pct
                                    target_res["accurate_passes"] = acc
                                except: pass
                            elif isinstance(v, (int, float)):
                                target_res["passing_stats"]["accurate_passes"] = int(v)
                                target_res["accurate_passes"] = int(v)
                    
                    elif key == "passes":
                        try:
                            h_res["total_passes"] = int(vals[0]) if vals[0] is not None else 0
                            a_res["total_passes"] = int(vals[1]) if vals[1] is not None else 0
                            h_res["passing_stats"]["total_passes"] = h_res["total_passes"]
                            a_res["passing_stats"]["total_passes"] = a_res["total_passes"]
                        except: pass
                    
                    elif key == "long_balls_accurate":
                        h_res["passing_stats"]["long_balls_accuracy"], a_res["passing_stats"]["long_balls_accuracy"] = vals[0], vals[1]
                    
                    elif key == "accurate_crosses":
                        h_res["passing_stats"]["crosses_accuracy"], a_res["passing_stats"]["crosses_accuracy"] = vals[0], vals[1]

                    # C. 기대 지표 (유연한 키 대응 및 float 변환)
                    elif key.lower() in ["expected_goals", "expectedgoals", "xg", "expected_goals_all"]:
                        try:
                            h_xg = float(vals[0]) if vals[0] is not None else 0.0
                            a_xg = float(vals[1]) if vals[1] is not None else 0.0
                            h_res["attack_stats"]["xG"], a_res["attack_stats"]["xG"] = h_xg, a_xg
                            h_res["expected_goals_value"], a_res["expected_goals_value"] = h_xg, a_xg
                        except (ValueError, TypeError): pass
                    
                    elif key.lower() in ["expected_assists", "expectedassists", "xa"]:
                        try:
                            h_xa = float(vals[0]) if vals[0] is not None else 0.0
                            a_xa = float(vals[1]) if vals[1] is not None else 0.0
                            h_res["attack_stats"]["xA"], a_res["attack_stats"]["xA"] = h_xa, a_xa
                            h_res["expected_assists_value"], a_res["expected_assists_value"] = h_xa, a_xa
                        except (ValueError, TypeError): pass
                    
                    elif key.lower() in ["expected_goals_on_target", "expectedgoalsontarget", "xgot"]:
                        try:
                            h_xgot = float(vals[0]) if vals[0] is not None else 0.0
                            a_xgot = float(vals[1]) if vals[1] is not None else 0.0
                            h_res["attack_stats"]["xGOT"], a_res["attack_stats"]["xGOT"] = h_xgot, a_xgot
                            h_res["expected_goals_on_target_value"], a_res["expected_goals_on_target_value"] = h_xgot, a_xgot
                        except (ValueError, TypeError): pass
            
            return h_res, a_res
            
            return h_res, a_res

        home_stats, away_stats = parse_team_stats(all_stats_raw)

        # 4-4. 라인업 파싱
        home_lineup_raw = lineup.get("homeTeam") or {}
        away_lineup_raw = lineup.get("awayTeam") or {}

        # 포메이션 및 팀 평점 추가
        for stats_dict, lineup_raw in zip([home_stats, away_stats], [home_lineup_raw, away_lineup_raw]):
            stats_dict["general_stats"]["formation"] = lineup_raw.get("formation")
            stats_dict["general_stats"]["team_rating"] = lineup_raw.get("rating")
            stats_dict["formation"] = lineup_raw.get("formation")
            stats_dict["team_rating"] = lineup_raw.get("rating")
        
        home_starters_data = self._parse_lineup_players(home_lineup_raw.get("starters", []), home_team_id)
        home_subs_data = self._parse_lineup_players(home_lineup_raw.get("subs", []), home_team_id)
        away_starters_data = self._parse_lineup_players(away_lineup_raw.get("starters", []), away_team_id)
        away_subs_data = self._parse_lineup_players(away_lineup_raw.get("subs", []), away_team_id)

        all_players = [d["player"] for d in (home_starters_data + home_subs_data + away_starters_data + away_subs_data)]
        home_starter_ids = [d["id"] for d in home_starters_data]
        home_sub_ids = [d["id"] for d in home_subs_data]
        away_starter_ids = [d["id"] for d in away_starters_data]
        away_sub_ids = [d["id"] for d in away_subs_data]

        player_ratings = {str(d["id"]): d["rating"] for d in (home_starters_data + home_subs_data + away_starters_data + away_subs_data) if d["rating"]}

        # MOM 정보
        potm_info = match_facts.get("playerOfTheMatch") or {}
        potm_player_id = potm_info.get("id")

        # 모델 객체 생성 - MatchInfos
        match_info = MatchInfos(
            id=match_id,
            match_date=match_date,
            match_name=general.get("matchName"),
            league_name=general.get("leagueName"),
            match_round=str(general.get("matchRound")) if general.get("matchRound") else None,
            match_time_utc=general.get("matchTimeUTC"),
            stadium=(info_box.get("Stadium") or {}).get("name"),
            referee=info_box.get("Referee", {}).get("text"),
            attendance=info_box.get("Attendance"),
            weather=info_box.get("Weather"),
            next_match=not status.get("started") and not is_finished,
            finished=is_finished,
            cancelled=status.get("cancelled", False),
            halfs_info=status.get("halfs"),
            events=(content.get("events") or {}).get("events"),
            shotmap=content.get("shotmap"),
            home_team_id=home_team_id,
            away_team_id=away_team_id
        )

        # 모델 객체 생성 - MatchDetails (Home)
        home_details = MatchDetails(
            id=match_id,
            team_id=home_team_id,
            is_home=True,
            score=header_teams[0].get("score", 0),
            penalty_score=penalties[0] if penalties else None,
            is_penalty_loser=status.get("whoLostOnPenalties") == header_teams[0].get("name"),
            score_str=status.get("scoreStr"),
            penalty_shootout_reason=reason.get("long"),
            # 모든 스탯 데이터 (JSON 그룹 + 개별 컬럼) 언패킹
            **home_stats,
            starting_players=home_starter_ids,
            substitute_players=home_sub_ids,
            player_ratings=player_ratings,
            lineup_power_rating=self._calculate_lineup_power_rating(home_lineup_raw.get("starters", [])),
            potm_player_id=potm_player_id if potm_info.get("teamId") == home_team_id else None
        )

        # 모델 객체 생성 - MatchDetails (Away)
        away_details = MatchDetails(
            id=match_id,
            team_id=away_team_id,
            is_home=False,
            score=header_teams[1].get("score", 0),
            penalty_score=penalties[1] if penalties else None,
            is_penalty_loser=status.get("whoLostOnPenalties") == header_teams[1].get("name"),
            score_str=status.get("scoreStr"),
            penalty_shootout_reason=reason.get("long"),
            # 모든 스탯 데이터 (JSON 그룹 + 개별 컬럼) 언패킹
            **away_stats,
            starting_players=away_starter_ids,
            substitute_players=away_sub_ids,
            player_ratings=player_ratings,
            lineup_power_rating=self._calculate_lineup_power_rating(away_lineup_raw.get("starters", [])),
            potm_player_id=potm_player_id if potm_info.get("teamId") == away_team_id else None
        )

        # 4-5. 선수별 상세 스탯 (PlayerMatchDetails)
        player_match_details_list = []
        if is_finished:
            shotmap_data = content.get("shotmap") or {}
            player_stats_section = content.get("playerStats") or {}
            
            all_starters = set(home_starter_ids + away_starter_ids)
            all_subs = set(home_sub_ids + away_sub_ids)

            for player_stat in player_stats_section.values():
                player_match_detail = self._parse_player_match_details(
                    match_id=match_id,
                    player_stat=player_stat,
                    team_id=player_stat.get("teamId"),
                    starters_ids=all_starters,
                    subs_ids=all_subs,
                    potm_player_id=potm_player_id,
                    shotmap_data=shotmap_data
                )
                if player_match_detail:
                    player_match_details_list.append(player_match_detail)

        result = [match_info, home_details, away_details]
        result.extend(all_players)
        result.extend(player_match_details_list)
        return result

    def _parse_player_match_details(
        self,
        match_id: int,
        player_stat: Dict,
        team_id: int,
        starters_ids: List[int],
        subs_ids: List[int],
        potm_player_id: Optional[int],
        shotmap_data: Optional[Dict] = None
    ) -> Optional[PlayerMatchDetails]:
        """선수별 경기 상세 스탯을 PlayerMatchDetails 객체로 변환"""
        player_id = player_stat.get("id")
        if not player_id or not team_id:
            return None
        
        # 선발/교체 여부 판단
        is_starter = player_id in starters_ids
        
        # stats 리스트에서 데이터 추출을 위한 맵 구성
        raw_stats = {}
        for group in player_stat.get("stats", []):
            group_stats = group.get("stats", {})
            for stat_name, stat_info in group_stats.items():
                key = stat_info.get("key")
                if key:
                    raw_stats[key] = stat_info.get("stat")

        # 헬퍼 함수: 필드 값 추출
        def get_val(key, field="value"):
            stat = raw_stats.get(key)
            if stat:
                return stat.get(field)
            return None

        # 포지션 정보 (usualPosition 혹은 positionId)
        position = player_stat.get("positionId")
        if position is None:
            position = player_stat.get("usualPosition")
            
        if position is not None:
            position = str(position)
        
        # 기본 정보 및 성과
        performance = player_stat.get("performance", {})
        minutes_played = get_val("minutes_played")
        rating = get_val("rating_title")
        is_man_of_the_match = (potm_player_id is not None and player_id == potm_player_id)
        
        # 공격 스탯
        goals = get_val("goals") or 0
        assists = get_val("assists") or 0
        shots_total = get_val("total_shots")
        
        # xG, xA (있을 경우)
        expected_goals = get_val("expected_goals")
        expected_assists = get_val("expected_assists")
        expected_goals_on_target = get_val("expected_goals_on_target")
        
        # xG + xA 계산
        expected_goals_plus_assists = None
        if expected_goals is not None or expected_assists is not None:
            xg_val = expected_goals if expected_goals is not None else 0
            xa_val = expected_assists if expected_assists is not None else 0
            expected_goals_plus_assists = xg_val + xa_val
        
        # 패스 스탯
        passes_completed = get_val("accurate_passes")
        passes_attempted = get_val("accurate_passes", "total")
        
        # 패스 성공률 계산
        pass_accuracy = None
        if passes_completed is not None and passes_attempted is not None and passes_attempted > 0:
            pass_accuracy = (passes_completed / passes_attempted) * 100
        
        final_third_passes = get_val("passes_into_final_third") or get_val("key_passes")
        long_passes_completed = get_val("long_balls_won") or get_val("long_passes_completed")
        crosses_completed = get_val("accurate_crosses")
        
        # 수비 스탯
        tackles = get_val("matchstats.headers.tackles") or get_val("tackles_won")
        interceptions = get_val("interceptions")
        clearances = get_val("clearances")
        recoveries = get_val("recoveries")
        blocks = get_val("shot_blocks")
        dribbles_stopped = get_val("dribbles_stopped") or get_val("dribbled_past")
        
        # 듀얼 스탯
        ground_duels_won = get_val("ground_duels_won") or get_val("duel_won")
        ground_duels_total = get_val("ground_duels_won", "total")
        aerial_duels_won = get_val("aerials_won")
        aerial_duels_total = get_val("aerials_won", "total")
        
        # 듀얼 승률 계산
        ground_duels_win_rate = None
        if ground_duels_won is not None and ground_duels_total is not None and ground_duels_total > 0:
            ground_duels_win_rate = (ground_duels_won / ground_duels_total) * 100
        
        aerial_duels_win_rate = None
        if aerial_duels_won is not None and aerial_duels_total is not None and aerial_duels_total > 0:
            aerial_duels_win_rate = (aerial_duels_won / aerial_duels_total) * 100
        
        # 카드 및 파울
        yellow_cards = 1 if performance.get("yellowCard") else 0
        red_cards = 1 if performance.get("redCard") else 0
        fouls = get_val("fouls")
        
        # 슈팅 이벤트 (shotmap에서 추출)
        shot_events = self._extract_player_shot_events(player_id, shotmap_data)
        
        return PlayerMatchDetails(
            match_id=match_id,
            id=player_id,
            team_id=team_id,
            position=position,
            minutes_played=minutes_played,
            is_starter=is_starter,
            rating=rating,
            is_man_of_the_match=is_man_of_the_match,
            goals=goals,
            assists=assists,
            shots_total=shots_total,
            shots_on_target=get_val("shots_on_target"),
            expected_goals=expected_goals,
            expected_goals_on_target=expected_goals_on_target,
            expected_assists=expected_assists,
            expected_goals_plus_assists=expected_goals_plus_assists,
            passes_completed=passes_completed,
            passes_attempted=passes_attempted,
            pass_accuracy=pass_accuracy,
            final_third_passes=final_third_passes,
            long_passes_completed=long_passes_completed,
            crosses_completed=crosses_completed,
            tackles=tackles,
            interceptions=interceptions,
            clearances=clearances,
            recoveries=recoveries,
            blocks=blocks,
            dribbles_stopped=dribbles_stopped,
            ground_duels_won=ground_duels_won,
            ground_duels_total=ground_duels_total,
            ground_duels_win_rate=ground_duels_win_rate,
            aerial_duels_won=aerial_duels_won,
            aerial_duels_total=aerial_duels_total,
            aerial_duels_win_rate=aerial_duels_win_rate,
            shot_events=shot_events,
            yellow_cards=yellow_cards,
            red_cards=red_cards,
            fouls=fouls,
        )

    def _extract_player_shot_events(self, player_id: int, shotmap_data: Optional[Dict]) -> Optional[List[Dict]]:
        """shotmap 데이터에서 해당 선수의 슈팅 이벤트 추출"""
        if not shotmap_data:
            return None
        
        shot_events = []
        
        shots = []
        if isinstance(shotmap_data, dict):
            # home/away 구조인 경우
            if "home" in shotmap_data and "away" in shotmap_data:
                shots = (shotmap_data.get("home", {}).get("shots", []) + 
                        shotmap_data.get("away", {}).get("shots", []))
            # 직접 shots 배열인 경우
            elif "shots" in shotmap_data:
                shots = shotmap_data.get("shots", [])
            # events 배열인 경우
            elif "events" in shotmap_data:
                shots = [e for e in shotmap_data.get("events", []) if e.get("eventType") in ["Goal", "Shot", "ShotOnPost"]]
        
        # 해당 선수의 슈팅 이벤트 필터링
        for shot in shots:
            if shot.get("playerId") == player_id:
                shot_event = {
                    "minute": shot.get("min") or shot.get("minute"),
                    "x": shot.get("x"),
                    "y": shot.get("y"),
                    "eventType": shot.get("eventType") or shot.get("type"),
                    "xG": shot.get("expectedGoals") or shot.get("xG"),
                    "shotType": shot.get("shotType"),
                    "situation": shot.get("situation"),
                    "insideBox": shot.get("isFromInsideBox") or shot.get("insideBox", False)
                }
                # None 값 제거
                shot_event = {k: v for k, v in shot_event.items() if v is not None}
                shot_events.append(shot_event)
        
        return shot_events if shot_events else None

