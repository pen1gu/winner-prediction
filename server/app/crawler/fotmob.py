from typing import List
from datetime import datetime, timezone

from server.app.models import (
    Player,
    Team,
    Manager,
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
