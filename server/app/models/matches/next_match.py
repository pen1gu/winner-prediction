import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship

from server.app.models.teams.team import Team
from server.utils.model.db_model import TimestampMixin 

class NextMatchBase(SQLModel):
    """MatchLogs 기본 정보 (공통 필드)"""
    fotmob_id: int = Field(nullable=False, index=True)
    
    match_date: datetime.datetime = Field(nullable=False)

    home_win_rate: float = Field(nullable=False)
    
    away_win_rate: float = Field(nullable=False)
    
    draw_rate: float = Field(nullable=False)

class NextMatch(NextMatchBase, TimestampMixin, table=True):
    __tablename__ = "next_match"
    
    id: Optional[int] = Field(default=None, primary_key=True)

    home_team_id: int = Field(foreign_key="teams.id")
    away_team_id: int = Field(foreign_key="teams.id")

    home_team: "Team" = Relationship(
        sa_relationship_kwargs={"primaryjoin": "NextMatch.home_team_id==Team.id"}
    )
    away_team: "Team" = Relationship(
        sa_relationship_kwargs={"primaryjoin": "NextMatch.away_team_id==Team.id"}
    )