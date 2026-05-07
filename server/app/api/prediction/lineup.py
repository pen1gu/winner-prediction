from typing import Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from server.app.compute.player_rating import predict_match_outcomes
from server.app.models import MatchLogs
from server.app.repositories.prediction_repository import load_players_for_prediction


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
        session,
        player_ids=home_detail.starting_players,
    )
    away_players = await load_players_for_prediction(
        session,
        player_ids=away_detail.starting_players,
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
