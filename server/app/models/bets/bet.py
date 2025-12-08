from typing import Optional
from sqlmodel import SQLModel, Field

class BetsBase(SQLModel):
    """Bet 기본 정보"""
    # FotMob ID
    fotmob_id: int = Field(nullable=False, index=True)
    
    # 이름
    name: str = Field(max_length=255, nullable=False)
    
    # 나이
    age: Optional[int] = Field(default=None)


class Bets(BetsBase, table=True):
    __tablename__ = "bets"

