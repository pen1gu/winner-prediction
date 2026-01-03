from sqlmodel import select

from server.app.models.session import AsyncSessionLocal
from server.app.models.teams.team import Team

async def get_already_fetched_team_ids() -> list[int]:
    """
    이미 팀 정보를 가져온 팀 ID 목록을 가져오는 함수
    """
    async with AsyncSessionLocal() as session:
        # fotmob_id -> id
        result = await session.execute(select(Team.id))
        return list(result.scalars().all())
