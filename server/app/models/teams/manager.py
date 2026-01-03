from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import ForeignKey, Integer

from server.utils.model.db_model import TimestampMixin

if TYPE_CHECKING:
    from .team import Team

class ManagerBase(SQLModel):
    """감독 기본 정보"""
    # FotMob ID를 id(PK)로 사용
    id: int = Field(primary_key=True, index=True)
    
    # 이름
    name: str = Field(max_length=255, nullable=False)
    
    # 나이
    age: Optional[int] = Field(default=None)
    
    # 국가
    country: Optional[str] = Field(default=None, max_length=128)


class Manager(ManagerBase, TimestampMixin, table=True):
    """감독 정보 - SQLModel (DB + API)"""
    __tablename__ = "managers"
    
    # 소속 팀 FK (teams.id 참조)
    team_id: Optional[int] = Field(default=None, sa_column=Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True))
    
    # Relationships
    team: Optional["Team"] = Relationship(
        back_populates="managers",
        sa_relationship_kwargs={"lazy": "select"}
    )
