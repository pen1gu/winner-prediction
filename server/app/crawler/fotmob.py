from typing import List, Dict, Optional, Any
from datetime import datetime, timezone

from server.app.models import (
    Player,
    Team,
    Manager,
    MatchDetails,
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

    async def get_players_info_by_team_id(self, team: Team, response: dict) -> List[Player]:
        squad = response.get("squad", {}).get("squad", [None, {}])[1:]

        players: list[Player] = []
        for players_info in squad:
            for player_info in players_info.get("members", []):
                position_str = player_info.get("positionIdsDesc", "")
                position_list = [p.strip() for p in position_str.split(",")] if position_str else None
                
                players.append(
                    Player(
                        id=player_info.get("id"), # fotmob_id -> id
                        name=player_info.get("name"),
                        age=player_info.get("age"),
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
                )

        return players

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
            country=manager_details.get("cname"),
        )
        return manager

    async def get_match_logs_info_by_team_id(self, team_id: int, response: dict) -> List[MatchLogs]:
        fixtures = response.get("fixtures", {})
        all_fixtures = fixtures.get("allFixtures", {})
        match_logs_data = all_fixtures.get("fixtures", [])
        next_match_data = all_fixtures.get("nextMatch")
        
        if not match_logs_data:
            return []
        
        match_logs = []
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
            
            match_log = MatchLogs(
                id=match_id, # fotmob_id -> id
                match_date=match_date,
                home_score=home_team.get("score", 0),
                away_score=away_team.get("score", 0),
                next_match=is_next_match,
                finished=finished,
                cancelled=cancelled,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
            )
            
            match_logs.append(match_log)
        
        return match_logs


    def _calculate_lineup_power_rating(self, starters: List[dict]) -> float:
        #TODO: 선수 details 데이터 추가되면 매일 업데이트해서 rating 변경할 수 있게 구현
        pass

    #TODO: 이건 db 조회해서 players id 추가하게 진행하자
    def _parse_lineup_players(self, players_list: List[dict]) -> List[dict]:
        """라인업의 선수 정보를 Player 모델 규격에 맞춰 변환"""
        parsed_players = []
        for p in players_list:
            # Player 모델 필드 및 분석용 추가 필드 매핑
            player_data = {
                "id": p.get("id"),
                "name": p.get("name", {}).get("fullName") if isinstance(p.get("name"), dict) else p.get("name"),
                "age": p.get("age"),
                "position": [str(p.get("positionId"))] if p.get("positionId") else [],
                "shirt_number": p.get("shirtNumber"),
                "role": p.get("role"),
                # 분석용 추가 데이터
                "market_value": p.get("marketValue"),
                "rating": p.get("performance", {}).get("rating"),
                "is_potm": p.get("performance", {}).get("playerOfTheMatch", False),
                "usual_position_id": p.get("usualPlayingPositionId")
            }
            parsed_players.append(player_data)
        return parsed_players

    async def get_match_details_info_by_match_id(self, match_id: int) -> MatchDetails:
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
        info_box = content.get("infoBox") or {}
        
        lineup = content.get("lineup") or {}
        home_lineup_raw = lineup.get("homeTeam") or {}
        away_lineup_raw = lineup.get("awayTeam") or {}
        
        # 1. 선수 데이터 파싱 (Player 모델 규격 참조)
        home_starters = self._parse_lineup_players(home_lineup_raw.get("starters", []))
        home_subs = self._parse_lineup_players(home_lineup_raw.get("subs", []))
        away_starters = self._parse_lineup_players(away_lineup_raw.get("starters", []))
        away_subs = self._parse_lineup_players(away_lineup_raw.get("subs", []))
        
        # 2. 라인업 파워 레이팅 계산
        home_power_rating = self._calculate_lineup_power_rating(home_lineup_raw.get("starters", []))
        away_power_rating = self._calculate_lineup_power_rating(away_lineup_raw.get("starters", []))
        
        # 3. 추가 정보 추출
        stadium = info_box.get("Stadium")
        referee = info_box.get("Referee", {}).get("text")
        halfs = status.get("halfs")
        
        # 4. 통계 추출 (데이터가 없는 경우 대비)
        stats_content = content.get("stats") or {}
        teams_stats = stats_content.get("teams") or {}
        home_team_stats = teams_stats.get("home") or {}
        away_team_stats = teams_stats.get("away") or {}

        return MatchDetails(
            id=match_id,
            match_name=general.get("matchName"),
            league_name=general.get("leagueName"),
            match_round=str(general.get("matchRound")) if general.get("matchRound") else None,
            match_time_utc=general.get("matchTimeUTC"),
            started=general.get("started"),
            finished=general.get("finished"),
            stadium=stadium,
            referee=referee,
            score_str=status.get("scoreStr"),
            halfs_info=halfs,
            penalty_shootout_reason=(status.get("reason") or {}).get("long"),
            penalties=(status.get("reason") or {}).get("penalties"),
            who_lost_on_penalties=status.get("whoLostOnPenalties"),
            attendance=home_team_stats.get("attendance") or info_box.get("Attendance"),
            events=(match_facts.get("events") or {}).get("events"),
            home_expected_goals=home_team_stats.get("expectedGoals"),
            away_expected_goals=away_team_stats.get("expectedGoals"),
            home_stats=home_team_stats,
            away_stats=away_team_stats,
            player_of_the_match=match_facts.get("playerOfTheMatch"),
            shotmap=content.get("shotmap"),
            home_starting_players=home_starters,
            home_substitute_players=home_subs,
            home_lineup_power_rating=home_power_rating,
            away_starting_players=away_starters,
            away_substitute_players=away_subs,
            away_lineup_power_rating=away_power_rating
        )
        

