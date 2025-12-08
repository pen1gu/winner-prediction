import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship

from server.app.models.teams.team import Team
from server.utils.model.db_model import TimestampMixin 

class MatchLogsBase(SQLModel):
    """MatchLogs 기본 정보 (공통 필드)"""
    fotmob_id: int = Field(nullable=False, index=True)
    
    match_date: datetime.datetime = Field(nullable=False)
    
    home_score: int = Field(nullable=False)

    away_score: int = Field(nullable=False)

    finished: bool = Field(nullable=False)

    cancelled: bool = Field(nullable=False)
    
class MatchLogs(MatchLogsBase, TimestampMixin, table=True):
    __tablename__ = "match_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)

    home_team_id: int = Field(foreign_key="teams.id")
    away_team_id: int = Field(foreign_key="teams.id")

    home_team: "Team" = Relationship(
        sa_relationship_kwargs={"primaryjoin": "MatchLogs.home_team_id==Team.id"}
    )
    away_team: "Team" = Relationship(
        sa_relationship_kwargs={"primaryjoin": "MatchLogs.away_team_id==Team.id"}
    )