from __future__ import annotations

from typing import Optional, List, Dict, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, JSON, Column

if TYPE_CHECKING:
    from server.app.models.player import Player
    from server.app.models.team import Team
    from server.app.models.player_details import PlayerDetails


class PlayerMatchAffectFeaturesBase(SQLModel):
    """선수 경기 영향 요소 기본"""
    # 성적 추이
    performance_trend: Optional[List[Dict]] = Field(default=None, sa_column=Column(JSON))
    
    # 부상 이력
    injury_history: Optional[List[Dict]] = Field(default=None, sa_column=Column(JSON))
    
    # 현재 폼
    current_form: Optional[str] = Field(default=None, max_length=32)
    
    # 폼 점수
    form_rating: Optional[float] = Field(default=None)
    
    # 최근 경기 기록
    recent_matches: Optional[List[Dict]] = Field(default=None, sa_column=Column(JSON))
    
    # 출전 가능 여부
    availability_status: Optional[str] = Field(default=None, max_length=64)
    
    # 국가대표 출전 횟수
    national_team_caps: Optional[int] = Field(default=None)
    
    # 최근 국가대표 출장 여부
    recently_played_national_team: Optional[bool] = Field(default=None)
    
    # 출전 시간 통계
    playing_time_stats: Optional[Dict] = Field(default=None, sa_column=Column(JSON))
    
    # 동료 대비 비교 지표
    comparison_with_peers: Optional[Dict] = Field(default=None, sa_column=Column(JSON))


class PlayerMatchAffectFeatures(PlayerMatchAffectFeaturesBase, table=True):
    """선수 경기 영향 요소 - SQLModel (DB + API)"""
    __tablename__ = "player_match_affect_features"
    
    # Primary Key
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # 선수 FK
    player_id: int = Field(foreign_key="players.id", nullable=False, sa_column_kwargs={"ondelete": "CASCADE"})
    
    # 팀 FK
    team_id: Optional[int] = Field(default=None, foreign_key="teams.id", sa_column_kwargs={"ondelete": "SET NULL", "nullable": True})
    
    # Timestamps
    created_at: Optional[datetime] = Field(default=None, sa_column_kwargs={"server_default": "now()"})
    updated_at: Optional[datetime] = Field(default=None, sa_column_kwargs={"server_default": "now()", "onupdate": "now()"})
    
    # Relationships
    player: "Player" = Relationship(back_populates="match_affect_features")
    team: Optional["Team"] = Relationship(back_populates="match_affect_features")
    details: Optional["PlayerDetails"] = Relationship(back_populates="match_affect_features")
