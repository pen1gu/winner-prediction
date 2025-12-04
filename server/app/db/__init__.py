# SQLModel로 통합되어 models 폴더로 이동
# 하위 호환성을 위해 re-export
from server.app.models import (
    Team,
    Player,
    PlayerDetails,
    PlayerMatchAffectFeatures,
    Manager,
)

# 기존 import와의 호환성
TeamModel = Team
PlayerModel = Player
PlayerDetailsModel = PlayerDetails
PlayerMatchAffectFeaturesModel = PlayerMatchAffectFeatures
ManagerModel = Manager

__all__ = [
    "Team",
    "Player",
    "PlayerDetails",
    "PlayerMatchAffectFeatures",
    "Manager",
    # 하위 호환성
    "TeamModel",
    "PlayerModel",
    "PlayerDetailsModel",
    "PlayerMatchAffectFeaturesModel",
    "ManagerModel",
]
