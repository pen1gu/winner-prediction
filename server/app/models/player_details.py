from __future__ import annotations

from typing import Optional, List, Dict, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, JSON, Column

if TYPE_CHECKING:
    from server.app.models.player import Player
    from server.app.models.team import Team
    from server.app.models.player_match_affect_features import PlayerMatchAffectFeatures


class PlayerDetailsBase(SQLModel):
    """선수 상세 정보 기본"""
    # 시장 가치 추이
    market_value_history: Optional[List[Dict]] = Field(default=None, sa_column=Column(JSON))
    
    # 현재 시장 가치
    current_market_value: Optional[int] = Field(default=None)
    
    # 최고 시장 가치
    peak_market_value: Optional[int] = Field(default=None)
    
    # 시장 가치 변동률
    market_value_change_percentage: Optional[float] = Field(default=None)
    
    # 이적료 이력
    transfer_fee_history: Optional[List[Dict]] = Field(default=None, sa_column=Column(JSON))
    
    # 시즌별 통계
    season_statistics: Optional[List[Dict]] = Field(default=None, sa_column=Column(JSON))
    
    # 커리어 통계
    career_statistics: Optional[Dict] = Field(default=None, sa_column=Column(JSON))
    
    # 이적 이력
    transfer_history: Optional[List[Dict]] = Field(default=None, sa_column=Column(JSON))
    
    # SNS 팔로워
    social_media_followers: Optional[Dict] = Field(default=None, sa_column=Column(JSON))
    
    # 뉴스 언급 횟수
    news_mentions_count: Optional[int] = Field(default=None)
    
    # 검색 트렌드 점수
    search_trend_score: Optional[float] = Field(default=None)
    
    # 팬 평점
    fan_rating: Optional[float] = Field(default=None)
    
    # 미디어 주목도
    media_attention_score: Optional[float] = Field(default=None)
    
    # 계약 정보
    contract_status: Optional[Dict] = Field(default=None, sa_column=Column(JSON))
    
    # 수상 기록
    awards: Optional[List[Dict]] = Field(default=None, sa_column=Column(JSON))


class PlayerDetails(PlayerDetailsBase, table=True):
    """선수 상세 정보 - SQLModel (DB + API)"""
    __tablename__ = "player_details"
    
    # Primary Key
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # 선수 FK
    player_id: int = Field(foreign_key="players.id", unique=True, sa_column_kwargs={"ondelete": "CASCADE"})
    
    # 팀 FK
    team_id: Optional[int] = Field(default=None, foreign_key="teams.id", sa_column_kwargs={"ondelete": "SET NULL", "nullable": True})
    
    # Timestamps
    created_at: Optional[datetime] = Field(default=None, sa_column_kwargs={"server_default": "now()"})
    updated_at: Optional[datetime] = Field(default=None, sa_column_kwargs={"server_default": "now()", "onupdate": "now()"})
    
    # Relationships
    player: "Player" = Relationship(back_populates="details")
    team: Optional["Team"] = Relationship(back_populates="details")
    match_affect_features: List["PlayerMatchAffectFeatures"] = Relationship(back_populates="details")
