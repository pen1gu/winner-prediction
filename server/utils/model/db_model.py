from __future__ import annotations

from typing import Optional
from datetime import datetime
import sqlalchemy as sa
from sqlmodel import Field
from sqlalchemy.ext.asyncio import AsyncSession


class TimestampMixin:
    """Adds created_at / updated_at timestamp columns (SQLModel용 - 기본)."""

    created_at: Optional[datetime] = Field(
        default=None, 
        sa_type=sa.DateTime(timezone=True),
        sa_column_kwargs={"server_default": sa.text("now()")}
    )
    updated_at: Optional[datetime] = Field(
        default=None, 
        sa_type=sa.DateTime(timezone=True),
        sa_column_kwargs={"server_default": sa.text("now()"), "onupdate": sa.text("now()")}
    )

