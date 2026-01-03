from typing import Optional, List, Dict, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from sqlalchemy import ForeignKey, Integer

from server.utils.model.db_model import TimestampMixin

if TYPE_CHECKING:
    from .player import Player
    from server.app.models.teams.team import Team

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


class PlayerMatchAffectFeatures(PlayerMatchAffectFeaturesBase, TimestampMixin, table=True):
    """선수 경기 영향 요소 - SQLModel (DB + API)"""
    __tablename__ = "player_match_affect_features"
    
    # Primary Key
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # 선수 FK
    player_id: int = Field(sa_column=Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False))
    
    # 팀 FK
    team_id: Optional[int] = Field(default=None, sa_column=Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True))
    
    # Relationships
    player: "Player" = Relationship(
        back_populates="match_affect_features",
        sa_relationship_kwargs={"lazy": "select"}
    )
    team: Optional["Team"] = Relationship(
        back_populates="match_affect_features",
        sa_relationship_kwargs={"lazy": "select"}
    )
