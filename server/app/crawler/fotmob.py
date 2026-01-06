from typing import List, Dict, Optional, Any
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
        general = data.get("general") or {}
        header = data.get("header") or {}
        status = header.get("status") or {}
        content = data.get("content") or {}
        match_facts = content.get("matchFacts") or {}
        info_box = match_facts.get("infoBox") or {}
        
        lineup = content.get("lineup") or {}
        home_lineup_raw = lineup.get("homeTeam") or {}
        away_lineup_raw = lineup.get("awayTeam") or {}
        
        home_team_id = general.get("homeTeam", {}).get("id")
        away_team_id = general.get("awayTeam", {}).get("id")

        # 1. 선수 데이터 파싱
        home_starters_data = self._parse_lineup_players(home_lineup_raw.get("starters", []), home_team_id)
        home_subs_data = self._parse_lineup_players(home_lineup_raw.get("subs", []), home_team_id)
        away_starters_data = self._parse_lineup_players(away_lineup_raw.get("starters", []), away_team_id)
        away_subs_data = self._parse_lineup_players(away_lineup_raw.get("subs", []), away_team_id)
        
        # 모든 Player 객체 (기본 정보 업데이트용)
        all_players = [d["player"] for d in (home_starters_data + home_subs_data + away_starters_data + away_subs_data)]
        
        # 명단 ID 리스트 및 평점 맵 구성
        home_starter_ids = [d["id"] for d in home_starters_data]
        home_sub_ids = [d["id"] for d in home_subs_data]
        away_starter_ids = [d["id"] for d in away_starters_data]
        away_sub_ids = [d["id"] for d in away_subs_data]
        
        player_ratings = {}
        for d in (home_starters_data + home_subs_data + away_starters_data + away_subs_data):
            if d["rating"]:
                player_ratings[str(d["id"])] = d["rating"]

        # 2. 라인업 파워 레이팅 계산
        home_power_rating = self._calculate_lineup_power_rating(home_lineup_raw.get("starters", []))
        away_power_rating = self._calculate_lineup_power_rating(away_lineup_raw.get("starters", []))
        
        # 3. 통계 추출
        stats_content = content.get("stats") or {}
        teams_stats = stats_content.get("teams") or {}
        home_team_stats_raw = teams_stats.get("home") or {}
        away_team_stats_raw = teams_stats.get("away") or {}

        def extract_stats(stats_list: List[Dict]) -> Dict[str, Any]:
            """FotMob stats 리스트에서 필요한 지표 추출"""
            extracted = {}
            for group in stats_list:
                for stat in group.get("stats", []):
                    title = stat.get("title")
                    val = stat.get("stat", {}).get("value")
                    if val is None:
                        continue
                        
                    try:
                        if title == "Ball possession": 
                            extracted["possession"] = float(val.replace("%", "")) if isinstance(val, str) else float(val)
                        elif title == "Total shots": 
                            extracted["shots_total"] = int(val)
                        elif title == "Shots on target": 
                            extracted["shots_on_target"] = int(val)
                        elif title == "Big chances": 
                            extracted["big_chances"] = int(val)
                        elif title == "Big chances missed": 
                            extracted["big_chances_missed"] = int(val)
                        elif title == "Accurate passes": 
                            if isinstance(val, str) and "/" in val:
                                extracted["accurate_passes"] = int(val.split("/")[0])
                            else:
                                extracted["accurate_passes"] = int(val)
                        elif title == "Total passes": 
                            if isinstance(val, str) and "/" in val:
                                # "345/412" 형태인 경우 분모 추출
                                extracted["total_passes"] = int(val.split("/")[1].split()[0])
                            else:
                                extracted["total_passes"] = int(val)
                        elif title == "Corners": 
                            extracted["corners"] = int(val)
                        elif title == "Offsides": 
                            extracted["offsides"] = int(val)
                        elif title == "Fouls committed": 
                            extracted["fouls"] = int(val)
                        elif title == "Yellow cards": 
                            extracted["yellow_cards"] = int(val)
                        elif title == "Red cards": 
                            extracted["red_cards"] = int(val)
                    except (ValueError, AttributeError, IndexError):
                        continue
            return extracted

        home_stats = extract_stats(home_team_stats_raw.get("stats", []))
        away_stats = extract_stats(away_team_stats_raw.get("stats", []))

        # 4. MatchInfos 생성
        match_date_str = general.get("matchTimeUTCDate")
        match_date = datetime.fromisoformat(match_date_str.replace('Z', '+00:00')) if match_date_str else datetime.now(timezone.utc)
        
        is_finished = general.get("finished", False)

        match_info = MatchInfos(
            id=match_id,
            match_date=match_date,
            match_name=general.get("matchName"),
            league_name=general.get("leagueName"),
            match_round=str(general.get("matchRound")) if general.get("matchRound") else None,
            match_time_utc=general.get("matchTimeUTC"),
            stadium=(info_box.get("Stadium") or {}).get("name"),
            referee=info_box.get("Referee", {}).get("text"),
            attendance=home_team_stats_raw.get("attendance") or info_box.get("Attendance"),
            weather=info_box.get("Weather"),
            next_match=not general.get("started") and not general.get("finished"),
            finished=is_finished,
            cancelled=status.get("cancelled", False),
            halfs_info=status.get("halfs"),
            events=(match_facts.get("events") or {}).get("events"),
            shotmap=content.get("shotmap"),
            home_team_id=home_team_id,
            away_team_id=away_team_id
        )

        # 5. MatchDetails 생성 (홈/어웨이)
        header_teams = header.get("teams", [{}, {}])
        home_header_score = header_teams[0].get("score")
        away_header_score = header_teams[1].get("score")
        
        reason = status.get("reason") or {}
        penalties = reason.get("penalties") # [home, away]
        
        # MOM 정보 추출
        potm_info = match_facts.get("playerOfTheMatch") or {}
        potm_player_id = potm_info.get("id")
        
        home_details = MatchDetails(
            id=match_id,
            team_id=home_team_id,
            is_home=True,
            score=home_header_score if home_header_score is not None else 0,
            penalty_score=penalties[0] if penalties else None,
            is_penalty_loser=status.get("whoLostOnPenalties") == header_teams[0].get("name"),
            score_str=status.get("scoreStr"),
            penalty_shootout_reason=reason.get("long"),
            expected_goals_value=home_team_stats_raw.get("expectedGoals"),
            **home_stats,
            starting_players=home_starter_ids,
            substitute_players=home_sub_ids,
            player_ratings=player_ratings,
            lineup_power_rating=home_power_rating,
            potm_player_id=potm_player_id if potm_info.get("teamId") == home_team_id else None
        )

        away_details = MatchDetails(
            id=match_id,
            team_id=away_team_id,
            is_home=False,
            score=away_header_score if away_header_score is not None else 0,
            penalty_score=penalties[1] if penalties else None,
            is_penalty_loser=status.get("whoLostOnPenalties") == header_teams[1].get("name"),
            score_str=status.get("scoreStr"),
            penalty_shootout_reason=reason.get("long"),
            expected_goals_value=away_team_stats_raw.get("expectedGoals"),
            **away_stats,
            starting_players=away_starter_ids,
            substitute_players=away_sub_ids,
            player_ratings=player_ratings,
            lineup_power_rating=away_power_rating,
            potm_player_id=potm_player_id if potm_info.get("teamId") == away_team_id else None
        )

        # 6. PlayerMatchDetails 생성 (선수별 경기 상세 스탯)
        player_match_details_list = []
        
        # 경기가 종료된 경우에만 선수별 상세 스탯 추출
        if is_finished:
            # shotmap 데이터 가져오기
            shotmap_data = content.get("shotmap") or {}
            
            # 선수별 상세 통계 추출 (FotMob API의 playerStats 섹션에서)
            player_stats_section = content.get("playerStats") or {}

            # 모든 선발/교체 ID 통합 (홈/어웨이 구분 없이 처리하기 위함)
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

        # 모든 모델 객체를 하나의 리스트로 합쳐서 반환
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

