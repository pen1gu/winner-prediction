from typing import Optional, TYPE_CHECKING
from sqlmodel import Relationship, SQLModel, Field

from server.utils.model.db_model import TimestampMixin

if TYPE_CHECKING:
    from server.app.models.matches.match_logs import MatchLogs

class MatchDetailsBase(SQLModel):
    """MatchDetails 기본 정보 (공통 필드)"""
    pass

class MatchDetails(MatchDetailsBase, TimestampMixin, table=True):
    __tablename__ = "match_details"
    
    id: Optional[int] = Field(default=None, primary_key=True)

    # match_logs FK (match_logs.id 참조)
    match_logs_id: int = Field(foreign_key="match_logs.id", nullable=False, index=True)
    
    match_logs: "MatchLogs" = Relationship(
        back_populates="match_details",
        sa_relationship_kwargs={"lazy": "select"}
    )
