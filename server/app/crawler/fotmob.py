from typing import List
import httpx
import json
import asyncio
from datetime import datetime, timezone
from playwright.async_api import async_playwright

from server.app.store.saveable import SaveableList
from server.app.models import (
    Player,
    PlayerMatchAffectFeatures,
    PlayerDetails,
    Team,
    Manager,
)

from server.app.models.matches.match_logs import MatchLogs
from server.config.settings import settings
from server.utils.http.requests import FotMobHTTPClient

from server.utils.logger import get_logger

logger = get_logger(__name__)

class FotMobCrawler:

    # 크롤링은 가능하면 매일 진행할 예정
    def __init__(self):
        self.client = FotMobHTTPClient()

    """
    description: 팀 데이터가 한 번에 나오기 때문에 response 호출 후 반환하여 사용
    """
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

        players: SaveableList[Player] = SaveableList()
        for players_info in squad:
            for player_info in players_info.get("members"):
                # position을 문자열 리스트로 변환
                position_str = player_info.get("positionIdsDesc", "")
                position_list = [p.strip() for p in position_str.split(",")] if position_str else None
                
                players.append(
                    Player(
                        fotmob_id=player_info.get("id"),
                        name=player_info.get("name"),
                        age=player_info.get("age"),
                        position=position_list,
                        role=player_info.get("role"),
                        shirt_number=player_info.get("shirtNumber"),
                        height=player_info.get("height"),
                        weight=0, # TODO: 관련 정보가 따로 없음, 체형 데이터를 넣는게 좋을까?
                        birth_date=str(player_info.get("dateOfBirth")) if player_info.get("dateOfBirth") else None,
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

        # stadium_location을 문자열로 변환 (List[float] -> str)
        stadium_location = team_overview.get("widget").get("location")
        if isinstance(stadium_location, list):
            stadium_location = str(stadium_location)
        
        team = Team(
            fotmob_id=team_id,
            name=team_details.get("name"),
            country=team_details.get("country"),
            league=team_details.get("primaryLeagueName"),
            league_id=team_details.get("primaryLeagueId"),
            founded=team_overview.get("statPairs")[2][1],
            stadium=team_overview.get("widget").get("name"),
            stadium_capacity=team_overview.get("statPairs")[1][1],
            stadium_location=stadium_location,
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
        )
        return manager

    async def get_next_match_info_by_match_id(self, match_id: int) -> MatchLogs:
        # TODO: 이건 나중에 특정 매치만 검색하는 기능이 필요하다 싶으면 개발

        response = await self.client.get(
            "/data/match",
            params={"id": match_id},
            raise_for_status=False
        )

        if response.status_code != 200:
            raise Exception(f"Failed to get next match info: {response.status_code} - {response.text}")

        logger.info(f"Next match info: {response.json()}")

        return

    async def get_match_logs_info_by_team_id(self, team_id: int, response: dict) -> List[MatchLogs]:
        # TODO: 이거 되는지 검증 필요
        fixtures = response.get("fixtures", {})
        all_fixtures = fixtures.get("allFixtures", {})
        match_logs_data = all_fixtures.get("fixtures", [])
        next_match_data = all_fixtures.get("nextMatch")
        
        if not match_logs_data:
            return SaveableList()
        
        match_logs: SaveableList[MatchLogs] = SaveableList()
        current_date = datetime.now(timezone.utc)
        
        # nextMatch의 id를 추출하여 next_match 판단에 사용
        next_match_id = next_match_data.get("id") if next_match_data else None
        
        for match_data in match_logs_data:
            # status 정보 추출
            status = match_data.get("status", {})
            if not status:
                logger.warning(f"Status is missing for match {match_data.get('id')}")
                continue
            
            # utcTime 파싱: ISO 형식 (예: '2025-07-23T11:30:00.000Z')
            utc_time_str = status.get("utcTime")
            if not utc_time_str:
                logger.warning(f"utcTime is missing for match {match_data.get('id')}")
                continue
            
            try:
                # ISO 형식 파싱 (Z는 UTC를 의미)
                if utc_time_str.endswith('Z'):
                    match_date = datetime.fromisoformat(utc_time_str.replace('Z', '+00:00'))
                else:
                    match_date = datetime.fromisoformat(utc_time_str)
            except ValueError as e:
                logger.warning(f"Failed to parse utcTime: {utc_time_str}, error: {e}")
                continue

            # naive/aware 혼재 방지: 항상 UTC timezone-aware로 정규화
            if match_date.tzinfo is None:
                match_date = match_date.replace(tzinfo=timezone.utc)
            else:
                match_date = match_date.astimezone(timezone.utc)
            
            # status 정보 추출
            finished = status.get("finished", False)
            cancelled = status.get("cancelled", False)
            not_started = match_data.get("notStarted", False)
            
            # next_match 판단: nextMatch의 id와 일치하거나, 아직 시작하지 않았고 현재 날짜보다 미래인 경우
            match_id = match_data.get("id")
            is_next_match = (next_match_id is not None and match_id == next_match_id) or (not_started and match_date > current_date)
            
            # home, away 팀 정보 추출
            home_team = match_data.get("home", {})
            away_team = match_data.get("away", {})
            
            home_team_id = home_team.get("id")
            away_team_id = away_team.get("id")
            
            if not home_team_id or not away_team_id:
                logger.warning(f"Team IDs are missing for match {match_id}")
                continue
            
            # 점수 추출 (home.score, away.score)
            home_score = home_team.get("score", 0)
            away_score = away_team.get("score", 0)
            
            match_log = MatchLogs(
                fotmob_id=match_id,
                match_date=match_date,
                home_score=home_score,
                away_score=away_score,
                next_match=is_next_match,
                finished=finished,
                cancelled=cancelled,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
            )
            
            match_logs.append(match_log)
        
        return match_logs
    

    async def get_previos_matchs_by_team_id(self, team_id: int) -> List[MatchLogs]:
        pass

player_info = FotMobCrawler()