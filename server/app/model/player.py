from pydantic import BaseModel, Field
from typing import List
import datetime


from server.utils.enums import Position

class Player(BaseModel):

    # 이름  
    name: str = Field(default="")

    # 나이
    age: int = Field(default=0)

    # 팀
    team: str = Field(default="")

    # 포지션
    position: List[Position] = Field(default=[])

    # 번호
    shirt_number: int = Field(default=0)

    # 키
    height: int = Field(default=0)

    # 몸무게
    weight: int = Field(default=0)

    # 생년월일
    birth_date: datetime.datetime = Field(default=datetime.datetime.now())

    # 출생지
    birth_place: str = Field(default="")

    # 출생국
    birth_country: str = Field(default="")

    # 출생지역
    birth_state: str = Field(default="")

