from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


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
    matches: list[MatchSummaryRead]

