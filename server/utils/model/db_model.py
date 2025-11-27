from __future__ import annotations

from sqlalchemy import DateTime, func, Integer
from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column


class DBModel(DeclarativeBase):
    """Common SQLAlchemy declarative base."""

    # 고유 ID
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


class TimestampMixin:
    """Adds created_at / updated_at timestamp columns."""

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

