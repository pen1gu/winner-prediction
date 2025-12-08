from __future__ import annotations

from typing import Optional
from datetime import datetime
from sqlmodel import Field


class TimestampMixin:
    """Adds created_at / updated_at timestamp columns (SQLModel용 - 기본)."""

    created_at: Optional[datetime] = Field(
        default=None, 
        sa_column_kwargs={"server_default": "now()"}
    )
    updated_at: Optional[datetime] = Field(
        default=None, 
        sa_column_kwargs={"server_default": "now()", "onupdate": "now()"}
    )

