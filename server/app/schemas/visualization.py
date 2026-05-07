from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TeamMetricPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str = Field(description="차트 시리즈 식별자")
    label: str = Field(description="축·범례용 한글 라벨")
    home: Optional[float] = Field(default=None, description="홈 팀 값")
    away: Optional[float] = Field(default=None, description="원정 팀 값")


class TeamStatsComparisonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    match_id: int
    home_team_name: str
    away_team_name: str
    match_date: Optional[datetime] = Field(default=None, description="경기 일시(UTC)")
    league_name: Optional[str] = Field(default=None, description="리그명")
    metrics: list[TeamMetricPoint] = Field(description="홈/원정 비교용 수치 열")


class LineupRatingPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    player_id: int
    name: str
    is_home: bool
    model_rating: float = Field(description="모델 기반 산출 레이팅")
    match_rating: Optional[float] = Field(
        default=None, description="경기 데이터에 포함된 선수 평점(있을 때)"
    )


class LineupRatingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    match_id: int
    home_team_name: str
    away_team_name: str
    players: list[LineupRatingPoint] = Field(
        description="선발 기준, model_rating 내림차순"
    )

