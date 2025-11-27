from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional
from datetime import datetime

from server.app.models.player import Player
from server.app.models.team import Team
from server.app.models.player_details import PlayerDetails
from server.utils.model.pydantic_model import Model
"""
description: 선수 경기 영향 요소
"""

class PlayerMatchAffectFeatures(Model):
    model_config = ConfigDict(from_attributes=True)
    player: Player = Field(default=Player())

    team: Team = Field(default=Team())

    # 성적 추이 (최근 N경기)
    performance_trend: List[Dict] = Field(default=[])

    # 부상 이력
    injury_history: List[Dict] = Field(default=[])

    # 현재 폼 (Excellent, Good, Average, Poor)
    current_form: str = Field(default="")

    # 폼 점수 (0-10)
    form_rating: float = Field(default=0.0)

    # 최근 경기 기록
    recent_matches: List[Dict] = Field(default=[])

    # 출전 가능 여부
    availability_status: str = Field(default="")

    # 국가대표 출전 횟수
    national_team_caps: int = Field(default=0)

    # 최근 국가대표 경기를 다녀왔는지 
    recently_played_national_team: bool = Field(default=False)

    # 출전 시간 통계
    playing_time_stats: Dict = Field(default={})

    # 동료 선수 대비 통계
    comparison_with_peers: Dict = Field(default={})
