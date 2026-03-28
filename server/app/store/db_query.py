from sqlmodel import select

from server.app.models.session import AsyncSessionLocal
from server.app.models.teams.team import Team
from server.app.models.players.player import Player
from server.app.models.players.player_rating import PlayerRating
from sqlalchemy.orm import selectinload

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
        return res.scalar_one_or_none()


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
        return res.scalar_one_or_none()