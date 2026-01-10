from __future__ import annotations

from typing import Optional
from datetime import datetime
from sqlalchemy import DateTime, text
from sqlmodel import Field
from sqlalchemy.ext.asyncio import AsyncSession


class TimestampMixin:
    """Adds created_at / updated_at timestamp columns (SQLModel용 - 기본)."""

    created_at: Optional[datetime] = Field(
        default=None, 
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": text("now()")}
    )
    updated_at: Optional[datetime] = Field(
        default=None, 
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": text("now()"), "onupdate": text("now()")}
    )

