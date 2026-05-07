from pydantic import BaseModel, ConfigDict, Field


class MatchOutcomesRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    match_id: int = Field(description="경기 ID (match_logs.id)")
    home_team_name: str = Field(description="홈 팀 이름")
    away_team_name: str = Field(description="원정 팀 이름")
    home: float = Field(description="홈 승 확률 (0~1)")
    draw: float = Field(description="무승부 확률 (0~1)")
    away: float = Field(description="원정 승 확률 (0~1)")

