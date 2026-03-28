from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import ForeignKey, Integer, DateTime, text

if TYPE_CHECKING:
    from .player import Player


class PlayerRatingBase(SQLModel):
    """
    선수 rating 히스토리.

    - rating은 여러 번 계산/갱신될 수 있으므로 1:N 구조로 누적 저장한다.
    - append-only 로그 테이블로 운영하며 update는 사용하지 않는다.
    """

    player_id: int = Field(sa_column=Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), index=True, nullable=False))
    rating: float = Field(nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": text("now()")},
        nullable=False,
    )


class PlayerRating(PlayerRatingBase, table=True):
    __tablename__ = "player_ratings"

    id: Optional[int] = Field(default=None, primary_key=True)

    player: "Player" = Relationship(
        back_populates="ratings",
        sa_relationship_kwargs={"lazy": "select"},
    )

