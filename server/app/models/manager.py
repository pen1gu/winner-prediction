from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from server.app.models.team import Team


class ManagerBase(SQLModel):
    """감독 기본 정보"""
    # FotMob ID
    fotmob_id: int = Field(nullable=False, index=True)
    
    # 이름
    name: str = Field(max_length=255, nullable=False)
    
    # 나이
    age: Optional[int] = Field(default=None)
    
    # 국가
    country: Optional[str] = Field(default=None, max_length=128)


class Manager(ManagerBase, table=True):
    """감독 정보 - SQLModel (DB + API)"""
    __tablename__ = "manager"
    
    # Primary Key
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # 소속 팀 (Foreign Key)
    team_id: Optional[int] = Field(default=None, foreign_key="teams.id", sa_column_kwargs={"ondelete": "SET NULL", "nullable": True})
    
    # Timestamps
    created_at: Optional[datetime] = Field(default=None, sa_column_kwargs={"server_default": "now()"})
    updated_at: Optional[datetime] = Field(default=None, sa_column_kwargs={"server_default": "now()", "onupdate": "now()"})
    
    # Relationships
    team: Optional["Team"] = Relationship(back_populates="manager")
