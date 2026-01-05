from typing import List, TYPE_CHECKING, Optional
from sqlmodel import SQLModel, Field, Relationship

from server.utils.model.db_model import TimestampMixin

if TYPE_CHECKING:
    from .match_details import MatchDetails
    from .match_infos import MatchInfos

class MatchLogsBase(SQLModel):
    """MatchLogs 경기 식별자 (마스터 테이블)"""
    id: int = Field(primary_key=True, index=True)

class MatchLogs(MatchLogsBase, TimestampMixin, table=True):
    __tablename__ = "match_logs"

    # 경기 기본 정보 (1:1)
    match_infos: Optional["MatchInfos"] = Relationship(
        back_populates="match_logs",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"}
    )
    
    # 팀별 경기 상세 통계 및 결과 (1:N - 홈/어웨이 2개 레코드)
    match_details: List["MatchDetails"] = Relationship(
        back_populates="match_logs",
        sa_relationship_kwargs={"lazy": "select", "cascade": "all, delete-orphan"}
    )
