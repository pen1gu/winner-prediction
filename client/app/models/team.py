from typing import Optional
from pydantic import BaseModel


class Team(BaseModel):
    id: int
    name: str
    score: Optional[int] = None
    founded: Optional[int] = None
    stadium_capacity: Optional[int] = None
    stadium_location: Optional[str] = None
    stadium: Optional[str] = None
    stadium_city: Optional[str] = None
    country: Optional[str] = None
    league_id: Optional[int] = None
    league: Optional[str] = None

    class Config:
        from_attributes = True
