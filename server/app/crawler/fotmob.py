import httpx
import json
import asyncio
from playwright.async_api import async_playwright

from server.app.models.player import Player

from server.config.settings import settings
from server.utils.http.requests import FotMobHTTPClient

from server.utils.logger import get_logger

logger = get_logger(__name__)

class FotMobCrawler:
    def __init__(self):
        self.client = FotMobHTTPClient()


    """
    description: 특정 팀 내부 선수들이 기본 정보 반환
    """
    async def get_players_info_by_team_id(self, team_id: int):
        response = await self.client.get(
            "/data/teams",
            params={"id": team_id, "ccode3": "KOR"},
            raise_for_status=False
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get team info: {response.status_code} - {response.text}")

        squad = response.json().get("squad").get("squad")[1:]

        players = []
        for players_info in squad:
            for player_info in players_info.get("members"):
                players.append(
                    Player(
                        name=player_info.get("name"),
                        age=player_info.get("age"),
                        position=player_info.get("positionIdsDesc").split(","),
                        role=player_info.get("role"),
                        shirt_number=player_info.get("shirtNumber"),
                        height=player_info.get("height"),
                        weight=0,
                        birth_date=player_info.get("dateOfBirth"),
                        birth_place=player_info.get("cname"),
                        birth_country=player_info.get("ccode"),
                        birth_state=player_info.get("cname"),
                    )
            )

        return players

    """
    description: 특정 팀 내부 선수의 details 정보 반환
    """
    async def get_player_details_by_player_id(self, player_id: int):
        # TODO: 개발 필요
        response = await self.client.get(
            "/data/players",
            params={"id": player_id},
            raise_for_status=False
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get player details: {response.status_code} - {response.text}")

    async def get_team_info_by_team_id(self, team_id: int):
        # TODO: 개발 필요
        response = await self.client.get(
            "/data/teams",
            params={"id": team_id, "ccode3": "KOR"},
            raise_for_status=False
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get team info: {response.status_code} - {response.text}")
        
        team_details = response.json().get("details")
        
        return response.json()
    
player_info = FotMobCrawler()