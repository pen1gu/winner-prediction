from server.utils.model.pydantic_model import Model
from pydantic import Field

from server.app.models.team import Team

"""
description: 기본 감독 정보
"""
class Manager(Model):
    # FotMob ID
    fotmob_id: int = Field(default=0)
    
    # 이름
    name: str = Field(default="")

    # 나이
    age: int = Field(default=0)

    # 국가
    country: str = Field(default="")

    # 소속 팀
    team: Team = Field(default=Team())