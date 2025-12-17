from typing import Optional
from sqlmodel import Relationship, SQLModel, Field

from server.app.models.matches.match_logs import MatchLogs
from server.utils.model.db_model import TimestampMixin

class MatchDetailsBase(SQLModel):
    """MatchDetails 기본 정보 (공통 필드)"""

    match_logs: int = Field(nullable=False, index=True)


class MatchDetails(MatchDetailsBase, TimestampMixin, table=True):
    __tablename__ = "match_details"
    
    id: Optional[int] = Field(default=None, primary_key=True)

    match_logs: MatchLogs = Relationship(
        back_populates="match_details",
        sa_relationship_kwargs={"lazy": "select"}
    )