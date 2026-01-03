import datetime
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
import sqlalchemy as sa

from server.utils.model.db_model import TimestampMixin

if TYPE_CHECKING:
    from server.app.models.teams.team import Team
    from .match_details import MatchDetails

class MatchLogsBase(SQLModel):
    """MatchLogs 기본 정보 (공통 필드)"""
    # TODO: 나중에 fotmob id 날리고 그냥 이걸 id 로 사용할지 고려 필요
    fotmob_id: int = Field(nullable=False, index=True, unique=True)
    
    match_date: datetime.datetime = Field(
        sa_type=sa.DateTime(timezone=True), 
        nullable=False
    )
    
    home_score: int = Field(nullable=False)

    away_score: int = Field(nullable=False)

    # 다음 경기인지 아닌지
    next_match: bool = Field(nullable=False)

    # False 진행 중, True 종료
    finished: bool = Field(nullable=False)

    # False 취소, True 진행
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

    match_details: Optional["MatchDetails"] = Relationship(
        back_populates="match_logs",
        sa_relationship_kwargs={"uselist": False, "lazy": "select"},
    )
