from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.api.prediction.lineup import try_predict_match_outcomes
from server.app.models.session import get_session
from server.app.store.db_query import (
    fetch_recent_match_logs_for_list,
    fetch_recent_match_summaries,
    match_log_to_summary_dict,
)

router = APIRouter(prefix="/matches", tags=["Matches"])


class MatchScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    home: Optional[int] = None
    away: Optional[int] = None


class MatchStatsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    home_xg: Optional[float] = None
    away_xg: Optional[float] = None
    home_possession: Optional[float] = None
    away_possession: Optional[float] = None
    home_shots: Optional[int] = None
    away_shots: Optional[int] = None
    home_shots_on_target: Optional[int] = None
    away_shots_on_target: Optional[int] = None


class MatchOutcomesBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    home: float = Field(description="홈 승 확률 (0~1)")
    draw: float = Field(description="무승부 확률 (0~1)")
    away: float = Field(description="원정 승 확률 (0~1)")


class MatchSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    match_id: int
    home_team: str
    away_team: str
    league_name: Optional[str] = None
    match_round: Optional[str] = None
    match_date: Optional[datetime] = None
    finished: bool
    stadium: Optional[str] = None
    score: MatchScoreRead
    stats: MatchStatsRead
    outcomes: Optional[MatchOutcomesBrief] = Field(
        default=None,
        description="include_outcomes=true 일 때만; 라인업 부족 시 null",
    )


class LatestMatchesRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ok: bool = True
    count: int
    matches: List[MatchSummaryRead]


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
    if include_outcomes:
        logs = await fetch_recent_match_logs_for_list(session, limit=limit)
        summaries: list[MatchSummaryRead] = []
        for m in logs:
            row = match_log_to_summary_dict(m)
            probs = await try_predict_match_outcomes(session, m)
            row["outcomes"] = (
                {"home": probs["home"], "draw": probs["draw"], "away": probs["away"]}
                if probs
                else None
            )
            summaries.append(MatchSummaryRead.model_validate(row))
    else:
        rows = await fetch_recent_match_summaries(session, limit=limit)
        summaries = [MatchSummaryRead.model_validate(row) for row in rows]

    return LatestMatchesRead(ok=True, count=len(summaries), matches=summaries)
