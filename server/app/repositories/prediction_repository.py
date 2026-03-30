from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from server.app.models import MatchLogs
from server.app.repositories.lineup_repository import load_players_for_prediction
from server.app.repositories.match_repository import (
    fetch_match_log_by_id_with_teams_and_details,
)


# TODO: 추후 변경 필요
async def fetch_match_for_prediction(
    session: AsyncSession,
    *,
    match_id: int,
) -> MatchLogs | None:
    """
    승부 예측용 경기 로드: 팀명·홈/어웨이 상세·선발 id에 필요한 관계까지 eager load.
    """
    return await fetch_match_log_by_id_with_teams_and_details(
        session,
        match_id=match_id,
    )


__all__ = [
    "fetch_match_for_prediction",
    "load_players_for_prediction",
]
