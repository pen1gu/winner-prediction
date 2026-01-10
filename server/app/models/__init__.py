from server.app.models.teams.team import Team, TeamBase
from server.app.models.players.player import Player, PlayerBase
from server.app.models.teams.manager import Manager, ManagerBase
from server.app.models.players.player_info import PlayerInfos, PlayerInfosBase
from server.app.models.players.player_match_details import PlayerMatchDetails, PlayerMatchDetailsBase
from server.app.models.players.player_match_affect_features import PlayerMatchAffectFeatures, PlayerMatchAffectFeaturesBase
from server.app.models.bets.bet import Bets, BetsBase
from server.app.models.matches.match_logs import MatchLogs, MatchLogsBase
from server.app.models.matches.match_details import MatchDetails, MatchDetailsBase
from server.app.models.matches.match_infos import MatchInfos, MatchInfosBase

# 하위 호환성을 위한 re-export (기존 import와의 호환성)
TeamModel = Team
PlayerModel = Player
PlayerInfosModel = PlayerInfos
PlayerMatchDetailsModel = PlayerMatchDetails
PlayerMatchAffectFeaturesModel = PlayerMatchAffectFeatures
ManagerModel = Manager

__all__ = [
    "Team",
    "TeamBase",
    "Player",
    "PlayerBase",
    "Manager",
    "ManagerBase",
    "PlayerInfos",
    "PlayerInfosBase",
    "PlayerMatchDetails",
    "PlayerMatchDetailsBase",
    "PlayerMatchAffectFeatures",
    "PlayerMatchAffectFeaturesBase",
    "Bets",
    "BetsBase",
    "MatchLogs",
    "MatchLogsBase",
    "MatchDetails",
    "MatchDetailsBase",
    "MatchInfos",
    "MatchInfosBase",
    # 하위 호환성
    "TeamModel",
    "PlayerModel",
    "PlayerInfosModel",
    "PlayerMatchDetailsModel",
    "PlayerMatchAffectFeaturesModel",
    "ManagerModel",
]
