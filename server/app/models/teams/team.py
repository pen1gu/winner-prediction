from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

from server.utils.model.db_model import TimestampMixin

if TYPE_CHECKING:
    from server.app.models.players.player import Player
    from .manager import Manager
    from server.app.models.players.player_info import PlayerInfos
    from server.app.models.players.player_match_affect_features import PlayerMatchAffectFeatures
    from server.app.models.players.player_match_details import PlayerMatchDetails
    from server.app.models.matches.match_details import MatchDetails

class TeamBase(SQLModel):
    """팀 기본 정보"""
    # FotMob ID를 id(PK)로 사용
    id: int = Field(primary_key=True, index=True)
    
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


class Team(TeamBase, TimestampMixin, table=True):
    """팀 정보 - SQLModel (DB + API)"""
    __tablename__ = "teams"
    
    # Relationships
    # 감독 정보 (1:1 관계)
    manager: Optional["Manager"] = Relationship(
        back_populates="team",
        sa_relationship_kwargs={"lazy": "select", "uselist": False}
    )

    # 팀 소속 선수 정보 리스트
    player_infos: List["PlayerInfos"] = Relationship(
        back_populates="team",
        sa_relationship_kwargs={"lazy": "select"}
    )

    # 팀의 경기 참여 기록 (MatchDetails를 통해 연결)
    match_details: List["MatchDetails"] = Relationship(
        back_populates="team",
        sa_relationship_kwargs={"lazy": "select"}
    )

    match_affect_features: List["PlayerMatchAffectFeatures"] = Relationship(
        back_populates="team",
        sa_relationship_kwargs={"lazy": "select"}
    )
    player_match_details: List["PlayerMatchDetails"] = Relationship(
        sa_relationship_kwargs={"lazy": "select"}
    )