from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.models.session import get_session
from server.app.schemas.matches import LatestMatchesRead
from server.app.services.matches_service import get_latest_matches as get_latest_matches_service

router = APIRouter(prefix="/matches", tags=["Matches"])


@router.get(
    "/latest",
    response_model=LatestMatchesRead,
    status_code=status.HTTP_200_OK,
    summary="최근 경기 요약 목록",
)
async def get_latest_matches(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=10, ge=1, le=30, description="최대 30건"),
    include_outcomes: bool = Query(
        default=False,
        description="true면 경기별 승·무·패 확률(0~1)을 함께 계산(라인업 필요)",
    ),
) -> LatestMatchesRead:
    return await get_latest_matches_service(
        session,
        limit=limit,
        include_outcomes=include_outcomes,
    )
