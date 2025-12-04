from __future__ import annotations

from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from server.app.models.player import Player
    from server.app.models.manager import Manager
    from server.app.models.player_details import PlayerDetails
    from server.app.models.player_match_affect_features import PlayerMatchAffectFeatures


class TeamBase(SQLModel):
    """팀 기본 정보"""
    # FotMob ID
    fotmob_id: int = Field(nullable=False, index=True)
    
    # 팀 이름
    name: str = Field(max_length=255, unique=True, nullable=False)
    
    # 국가
    country: Optional[str] = Field(default=None, max_length=128)
    
    # 리그
    league: Optional[str] = Field(default=None, max_length=128)
    
    # 리그 ID
    league_id: Optional[int] = Field(default=None)
    
    # 창단 연도
    founded: Optional[int] = Field(default=None)
    
    # 경기장 이름
    stadium: Optional[str] = Field(default=None, max_length=255)
    
    # 경기장 수용 인원
    stadium_capacity: Optional[int] = Field(default=None)
    
    # 경기장 위치 (JSON으로 저장)
    stadium_location: Optional[str] = Field(default=None, max_length=255)
    
    # 경기장 도시
    stadium_city: Optional[str] = Field(default=None, max_length=128)


class Team(TeamBase, table=True):
    """팀 정보 - SQLModel (DB + API)"""
    __tablename__ = "teams"
    
    # Primary Key
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Timestamps
    created_at: Optional[datetime] = Field(default=None, sa_column_kwargs={"server_default": "now()"})
    updated_at: Optional[datetime] = Field(default=None, sa_column_kwargs={"server_default": "now()", "onupdate": "now()"})
    
    # Relationships
    players: List["Player"] = Relationship(back_populates="team", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    manager: Optional["Manager"] = Relationship(back_populates="team")
    details: List["PlayerDetails"] = Relationship(back_populates="team")
    match_affect_features: List["PlayerMatchAffectFeatures"] = Relationship(back_populates="team")
