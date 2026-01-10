from sqlmodel import select

from server.app.models.session import AsyncSessionLocal
from server.app.models.teams.team import Team
from server.app.models.players.player import Player

async def get_already_fetched_team_ids() -> list[int]:
    """
    이미 팀 정보를 가져온 팀 ID 목록을 가져오는 함수
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Team.id))
        return list(result.scalars().all())

async def get_already_fetched_player_ids() -> list[int]:
    """
    이미 선수 정보를 가져온 선수 ID 목록을 가져오는 함수
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Player.id))
        return list(result.scalars().all())