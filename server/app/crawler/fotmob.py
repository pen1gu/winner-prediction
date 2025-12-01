from typing import List
import httpx
import json
import asyncio
from playwright.async_api import async_playwright

from server.app.models.player import Player
from server.app.models.player_match_affect_features import PlayerMatchAffectFeatures
from server.app.models.player_details import PlayerDetails
from server.app.models.team import Team
from server.app.models.manager import Manager

from server.config.settings import settings
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


    """
    description: 특정 팀 내부 선수들이 기본 정보 반환
    """
    async def get_players_info_by_team_id(self, team: Team, response: dict) -> List[Player]:
        squad = response.get("squad").get("squad")[1:]

        players = []
        for players_info in squad:
            for player_info in players_info.get("members"):
                players.append(
                    Player(
                        fotmob_id=player_info.get("id"),
                        name=player_info.get("name"),
                        age=player_info.get("age"),
                        team=team,
                        position=player_info.get("positionIdsDesc").split(","),
                        role=player_info.get("role"),
                        shirt_number=player_info.get("shirtNumber"),
                        height=player_info.get("height"),
                        weight=0, # TODO: 관련 정보가 따로 없음, 체형 데이터를 넣는게 좋을까?
                        birth_date=player_info.get("dateOfBirth"),
                        birth_place=player_info.get("cname"),
                        birth_country=player_info.get("cname"),
                        birth_state=player_info.get("cname"),
                    )
            )

        return players

    """
    description: 특정 팀 내부 선수의 details 정보 반환
    """
    async def get_player_details_by_player_id(self, player_id: int) -> PlayerDetails:
        # TODO: 플레이어 디테일 개발 필요
        response = await self.client.get(
            "/data/players",
            params={"id": player_id},
            raise_for_status=False
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get player details: {response.status_code} - {response.text}")



    """
    description: ID 기반 특정 팀 정보 반환
    """
    async def get_team_info_by_team_id(self, team_id: int, response: dict) -> Team:
        team_details = response.get("details")
        team_overview = response.get("overview").get("venue")

        team = Team(
            fotmob_id=team_id,
            name=team_details.get("name"),
            country=team_details.get("country"),
            league=team_details.get("primaryLeagueName"),
            league_id=team_details.get("primaryLeagueId"),
            founded=team_overview.get("statPairs")[2][1],
            stadium=team_overview.get("widget").get("name"),
            stadium_capacity=team_overview.get("statPairs")[1][1],
            stadium_location=team_overview.get("widget").get("location"),
            stadium_city=team_overview.get("widget").get("city"),
        )

        return team

    async def get_manager_info_by_team_id(self, team: Team, response: dict) -> Manager:
        manager_details = response.get("squad").get("squad")[0].get("members")[0]

        manager = Manager(
            fotmob_id=manager_details.get("id"),
            name=manager_details.get("name"),
            age=manager_details.get("age"),
            country=manager_details.get("cname"),
            team=team,
        )
        return manager

        
    
player_info = FotMobCrawler()