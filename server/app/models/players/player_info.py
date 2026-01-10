from typing import Optional, List, Dict, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from sqlalchemy import ForeignKey, Integer

from server.utils.model.db_model import TimestampMixin

if TYPE_CHECKING:
    from .player import Player
    from server.app.models.teams.team import Team

class PlayerInfosBase(SQLModel):
    """선수 기본 정보 및 일반 정보"""
    # --- 기본 정보 ---
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
    
    # 국적 코드 (ISO 코드, 예: 'NOR')
    nationality_code: Optional[str] = Field(default=None, max_length=16)
    
    # --- 통계 고도화 필드 ---
    # 팀 내 카테고리별 순위 및 통계 (Chances created, Assists 등)
    # 구조: [{"category_name": "total_att_assist", "rank": 1, "value": 25, "header": "Chances created"}]
    team_internal_rankings: Optional[List[Dict]] = Field(default=None, sa_column=Column(JSON))
    
    # 시즌 상세 카테고리 통계 (스키마의 stat 객체 정보 포함)
    # 구조: [{"stat_name": "total_att_assist", "stat_value": 25, "stat_format": "number"}]
    season_category_stats: Optional[List[Dict]] = Field(default=None, sa_column=Column(JSON))
    
    # --- 일반 정보 (시장 가치, 이적 이력 등) ---
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


class PlayerInfos(PlayerInfosBase, TimestampMixin, table=True):
    """선수 기본 정보 및 일반 정보 - SQLModel (DB + API)"""
    __tablename__ = "player_infos"
    
    # Player.id를 참조하는 FK이면서 PK
    id: int = Field(sa_column=Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), primary_key=True))
    
    # 팀 FK (teams.id 참조)
    team_id: Optional[int] = Field(default=None, sa_column=Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True))
    
    # Relationships
    player: "Player" = Relationship(
        back_populates="info",
        sa_relationship_kwargs={"lazy": "select"}
    )
    team: Optional["Team"] = Relationship(
        back_populates="player_infos",
        sa_relationship_kwargs={"lazy": "select"}
    )
