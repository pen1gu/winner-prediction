from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Dict, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from sqlalchemy import ForeignKey, Integer

from server.utils.model.db_model import TimestampMixin

if TYPE_CHECKING:
    from .player import Player


class PlayerRatingBase(SQLModel):
    """
    선수 rating 히스토리.

    - rating은 여러 번 계산/갱신될 수 있으므로 1:N 구조로 누적 저장한다.
    - 알고리즘이 바뀌는 경우를 대비해 `algorithm_version`을 남길 수 있다(선택).
    """

    player_id: int = Field(sa_column=Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), index=True, nullable=False))
    rating: float = Field(nullable=False)

    algorithm_version: Optional[str] = Field(default=None, max_length=64)
    computed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # 디버깅/분석용 (선택)
    components: Optional[Dict] = Field(default=None, sa_column=Column(JSON))


class PlayerRating(PlayerRatingBase, TimestampMixin, table=True):
    __tablename__ = "player_ratings"

    id: Optional[int] = Field(default=None, primary_key=True)

    player: "Player" = Relationship(
        sa_relationship_kwargs={"lazy": "select"},
    )

