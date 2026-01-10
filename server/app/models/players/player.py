from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

from server.utils.model.db_model import TimestampMixin

if TYPE_CHECKING:
    from .player_info import PlayerInfos
    from .player_match_affect_features import PlayerMatchAffectFeatures
    from .player_match_details import PlayerMatchDetails

class PlayerBase(SQLModel):
    """Player 선수 식별자 (마스터 테이블)"""
    # FotMob ID를 id(PK)로 사용
    id: int = Field(primary_key=True, index=True)


class Player(PlayerBase, TimestampMixin, table=True):
    """선수 식별자 - SQLModel (DB + API)"""
    __tablename__ = "players"
    
    # 선수 기본 정보 (1:1)
    info: Optional["PlayerInfos"] = Relationship(
        back_populates="player",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan", "lazy": "select"}
    )
    
    # 경기 영향 요소 (1:1)
    match_affect_features: Optional["PlayerMatchAffectFeatures"] = Relationship(
        back_populates="player",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan", "lazy": "select"}
    )
    
    # 경기별 상세 성과 (1:N)
    match_details: List["PlayerMatchDetails"] = Relationship(
        back_populates="player",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "select"}
    )
