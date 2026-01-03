from typing import Optional
from sqlmodel import SQLModel, Field

from server.utils.model.db_model import TimestampMixin

class BetsBase(SQLModel):
    """Bet 기본 정보"""
    # FotMob ID를 id(PK)로 사용
    id: int = Field(primary_key=True, index=True)
    
    # 이름
    name: str = Field(max_length=255, nullable=False)
    
    # 나이
    age: Optional[int] = Field(default=None)


class Bets(BetsBase, TimestampMixin, table=True):
    __tablename__ = "bets"
