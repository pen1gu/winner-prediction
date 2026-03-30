from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from server.app.models.session import get_session
from server.app.schemas.visualization import LineupRatingsRead, TeamStatsComparisonRead
from server.app.services.visualization_service import (
    get_match_lineup_ratings_for_charts as get_match_lineup_ratings_for_charts_service,
    get_match_team_stats_for_charts as get_match_team_stats_for_charts_service,
)

router = APIRouter(prefix="/visualization", tags=["Visualization"])


@router.get(
    "/matches/{match_id}/team-stats",
    response_model=TeamStatsComparisonRead,
    status_code=status.HTTP_200_OK,
    summary="팀 스탯 비교(막대·레이더 차트용)",
)
async def get_match_team_stats_for_charts(
    match_id: int,
    session: AsyncSession = Depends(get_session),
) -> TeamStatsComparisonRead:
    return await get_match_team_stats_for_charts_service(session, match_id=match_id)

@router.get(
    "/matches/{match_id}/lineup-ratings",
    response_model=LineupRatingsRead,
    status_code=status.HTTP_200_OK,
    summary="선발 라인업 레이팅(막대·분포 차트용)",
)
async def get_match_lineup_ratings_for_charts(
    match_id: int,
    session: AsyncSession = Depends(get_session),
) -> LineupRatingsRead:
    return await get_match_lineup_ratings_for_charts_service(session, match_id=match_id)
