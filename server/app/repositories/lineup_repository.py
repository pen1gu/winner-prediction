from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import select

from server.app.models import Player


async def load_players_for_prediction(
    session: AsyncSession,
    *,
    player_ids: list[int],
) -> list[Player]:
    if not player_ids:
        return []

    statement = (
        select(Player)
        .where(Player.id.in_(player_ids))
        .options(
            joinedload(Player.info),
            joinedload(Player.match_affect_features),
            joinedload(Player.match_details),
        )
    )
    result = await session.execute(statement)
    try:
        return list(result.scalars().unique().all())
    finally:
        result.close()

