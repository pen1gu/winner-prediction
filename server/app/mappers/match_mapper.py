from __future__ import annotations

from datetime import datetime

from server.app.models import MatchLogs


def match_log_to_summary_dict(match: MatchLogs) -> dict:
    """MatchLogs(관계 로드됨) → 목록 API용 dict."""
    info = match.match_infos
    home_detail = next((d for d in match.match_details if d.is_home), None)
    away_detail = next((d for d in match.match_details if not d.is_home), None)

    match_date: datetime | None = info.match_date if info else None

    return {
        "match_id": match.id,
        "home_team": info.home_team.name if info and info.home_team else "Home",
        "away_team": info.away_team.name if info and info.away_team else "Away",
        "league_name": info.league_name if info else None,
        "match_round": info.match_round if info else None,
        "match_date": match_date,
        "finished": bool(info.finished) if info else False,
        "stadium": info.stadium if info else None,
        "score": {
            "home": home_detail.score if home_detail else None,
            "away": away_detail.score if away_detail else None,
        },
        "stats": {
            "home_xg": home_detail.expected_goals_value if home_detail else None,
            "away_xg": away_detail.expected_goals_value if away_detail else None,
            "home_possession": home_detail.possession if home_detail else None,
            "away_possession": away_detail.possession if away_detail else None,
            "home_shots": home_detail.shots_total if home_detail else None,
            "away_shots": away_detail.shots_total if away_detail else None,
            "home_shots_on_target": home_detail.shots_on_target
            if home_detail
            else None,
            "away_shots_on_target": away_detail.shots_on_target
            if away_detail
            else None,
        },
    }

