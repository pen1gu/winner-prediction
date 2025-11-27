from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional
import datetime

from server.app.models.team import Team

from server.utils.enums import Position
from server.utils.model.pydantic_model import Model
"""
description: 기본 선수 정보
"""
class Player(Model):
    model_config = ConfigDict(from_attributes=True)

    # 이름  
    name: str = Field(default="")

    # 나이
    age: int = Field(default=0)

    # 팀
    team: str = Field(default="")

    # 포지션
    position: List[Position] = Field(default=[])

    # 상세 역할
    role: Dict[str, str] = Field(default={})

    # 번호
    shirt_number: int = Field(default=0)

    # 키
    height: Optional[int] = Field(default=None)

    # 몸무게
    weight: Optional[int] = Field(default=None)

    # 생년월일
    birth_date: Optional[datetime.datetime] = Field(default=None)

    # 출생지
    birth_place: Optional[str] = Field(default=None)

    # 출생국
    birth_country: Optional[str] = Field(default=None)

    # 출생지역
    birth_state: Optional[str] = Field(default=None)

    # 팀
    team: Team = Field(default=Team())
