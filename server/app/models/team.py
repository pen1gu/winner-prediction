from pydantic import BaseModel, Field, ConfigDict
from typing import List
from server.utils.model.pydantic_model import Model

"""
description: 기본 팀 정보
"""
class Team(Model):
    # FotMob ID
    fotmob_id: int = Field(default=0)
    
    # 팀 이름
    name: str = Field(default="")

    # 국가
    country: str = Field(default="")
    
    # 리그
    league: str = Field(default="")

    # 리그 ID
    league_id: int = Field(default=0)

    # 창단 연도
    founded: int = Field(default=0)

    # 경기장 이름
    stadium: str = Field(default="")

    # 경기장 수용 인원
    stadium_capacity: int = Field(default=0)

    # 경기장 위치
    stadium_location: List[float] = Field(default=[])

    # 경기장 도시
    stadium_city: str = Field(default="")