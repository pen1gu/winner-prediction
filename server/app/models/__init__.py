from server.app.models.teams.team import Team, TeamBase
from server.app.models.players.player import Player, PlayerBase
from server.app.models.teams.manager import Manager, ManagerBase
from server.app.models.players.player_details import PlayerDetails, PlayerDetailsBase
from server.app.models.players.player_match_affect_features import PlayerMatchAffectFeatures, PlayerMatchAffectFeaturesBase
from server.app.models.bets.bet import Bets, BetsBase
from server.app.models.matches.match_logs import MatchLogs, MatchLogsBase
from server.app.models.matches.match_details import MatchDetails, MatchDetailsBase

# 하위 호환성을 위한 re-export (기존 import와의 호환성)
TeamModel = Team
PlayerModel = Player
PlayerDetailsModel = PlayerDetails
PlayerMatchAffectFeaturesModel = PlayerMatchAffectFeatures
ManagerModel = Manager

__all__ = [
    "Team",
    "TeamBase",
    "Player",
    "PlayerBase",
    "Manager",
    "ManagerBase",
    "PlayerDetails",
    "PlayerDetailsBase",
    "PlayerMatchAffectFeatures",
    "PlayerMatchAffectFeaturesBase",
    "Bets",
    "BetsBase",
    "MatchLogs",
    "MatchLogsBase",
    "MatchDetails",
    "MatchDetailsBase",
    # 하위 호환성
    "TeamModel",
    "PlayerModel",
    "PlayerDetailsModel",
    "PlayerMatchAffectFeaturesModel",
    "ManagerModel",
]
