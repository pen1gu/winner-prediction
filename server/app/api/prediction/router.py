from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.models.session import get_session
from server.app.schemas.prediction import MatchOutcomesRead
from server.app.services.prediction_service import (
    get_match_outcomes as get_match_outcomes_service,
)

router = APIRouter(prefix="/predictions", tags=["Prediction"])


@router.get(
    "/matches/{match_id}/outcomes",
    response_model=MatchOutcomesRead,
    status_code=status.HTTP_200_OK,
    summary="경기별 승·무·패 확률",
)
async def get_match_outcomes(
    match_id: int,
    session: AsyncSession = Depends(get_session),
) -> MatchOutcomesRead:
    return await get_match_outcomes_service(session, match_id=match_id)
