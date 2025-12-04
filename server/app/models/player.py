from __future__ import annotations

from typing import Optional, List, Dict, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from sqlalchemy import String

from server.utils.enums import Position

if TYPE_CHECKING:
    from server.app.models.team import Team
    from server.app.models.player_details import PlayerDetails
    from server.app.models.player_match_affect_features import PlayerMatchAffectFeatures


class PlayerBase(SQLModel):
    """선수 기본 정보"""
    # FotMob ID
    fotmob_id: int = Field(nullable=False, index=True)
    
    # 이름
    name: str = Field(max_length=255, nullable=False)
    
    # 나이
    age: Optional[int] = Field(default=None)
    
    # 포지션 정보 (JSON으로 저장)
    position: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    
    # 역할 상세 (JSON으로 저장)
    role: Optional[Dict[str, str]] = Field(default=None, sa_column=Column(JSON))
    
    # 등번호
    shirt_number: Optional[int] = Field(default=None)
    
    # 키
    height: Optional[int] = Field(default=None)
    
    # 몸무게
    weight: Optional[int] = Field(default=None)
    
    # 생년월일 (문자열로 저장)
    birth_date: Optional[str] = Field(default=None, max_length=32)
    
    # 출생지
    birth_place: Optional[str] = Field(default=None, max_length=255)
    
    # 출생국
    birth_country: Optional[str] = Field(default=None, max_length=128)
    
    # 출생 지역
    birth_state: Optional[str] = Field(default=None, max_length=128)


class Player(PlayerBase, table=True):
    """선수 정보 - SQLModel (DB + API)"""
    __tablename__ = "players"
    
    # Primary Key
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # 소속 팀 (Foreign Key)
    team_id: Optional[int] = Field(default=None, foreign_key="teams.id", sa_column_kwargs={"ondelete": "SET NULL"})
    
    # Timestamps
    created_at: Optional[datetime] = Field(default=None, sa_column_kwargs={"server_default": "now()"})
    updated_at: Optional[datetime] = Field(default=None, sa_column_kwargs={"server_default": "now()", "onupdate": "now()"})
    
    # Relationships
    team: Optional["Team"] = Relationship(back_populates="players")
    details: Optional["PlayerDetails"] = Relationship(
        back_populates="player",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"}
    )
    match_affect_features: List["PlayerMatchAffectFeatures"] = Relationship(
        back_populates="player",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
