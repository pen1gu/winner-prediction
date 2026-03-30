from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import select

from server.app.compute.player_rating import predict_match_outcomes
from server.app.models import MatchLogs, Player


async def load_players_for_prediction(
    session: AsyncSession, player_ids: List[int]
) -> List[Player]:
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
        await result.close()


async def try_predict_match_outcomes(
    session: AsyncSession, match: MatchLogs
) -> Optional[Dict[str, float]]:
    """
    라인업·상세가 갖춰진 경우에만 홈/무/원정 확률 dict를 반환하고, 아니면 None.
    """
    details = match.match_details or []
    home_detail = next((d for d in details if d.is_home), None)
    away_detail = next((d for d in details if not d.is_home), None)
    if not home_detail or not away_detail:
        return None

    home_players = await load_players_for_prediction(
        session, home_detail.starting_players
    )
    away_players = await load_players_for_prediction(
        session, away_detail.starting_players
    )
    if not home_players or not away_players:
        return None

    outcomes = await predict_match_outcomes(
        session,
        home_players,
        away_players,
        home_detail.team_id,
        away_detail.team_id,
    )
    return outcomes
