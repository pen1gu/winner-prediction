from __future__ import annotations

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from server.app.models.team import Team
from server.app.models.player import Player
from server.app.models.manager import Manager
from server.app.db.session import get_session
from server.utils.logger import get_logger
from server.utils.nomalize.normalize import (
    normalize_team_data,
    normalize_player_data,
    normalize_manager_data,
)

logger = get_logger(__name__)


async def save_team_overview(
    team: Team,
    players: List[Player],
    manager: Manager,
    session: AsyncSession | None = None,
) -> dict:
    """
    팀 정보, 선수들, 감독을 DB에 저장합니다.
    
    Args:
        team: 팀 정보 (SQLModel)
        players: 선수 리스트 (SQLModel)
        manager: 감독 정보 (SQLModel)
        session: DB 세션 (None이면 자동으로 생성)
        
    Returns:
        저장된 데이터의 ID 딕셔너리
    """
    should_close_session = False
    if session is None:
        session_gen = get_session()
        session = await session_gen.__anext__()
        should_close_session = True
    
    try:
        # 1. Team 저장 또는 업데이트 (fotmob_id로 중복 체크)
        stmt = select(Team).where(Team.fotmob_id == team.fotmob_id)
        result = await session.execute(stmt)
        existing_team = result.scalar_one_or_none()
        
        if existing_team:
            # 기존 팀 업데이트
            team_data = normalize_team_data(team)
            for key, value in team_data.items():
                setattr(existing_team, key, value)
            team_db = existing_team
            logger.info(f"Updated existing team: {team.name} (fotmob_id: {team.fotmob_id})")
        else:
            # 새 팀 생성
            team_data = normalize_team_data(team)
            team_db = Team(**team_data)
            session.add(team_db)
            logger.info(f"Created new team: {team.name} (fotmob_id: {team.fotmob_id})")
        
        await session.flush()  # team_id를 얻기 위해 flush
        team_id = team_db.id
        
        # 2. Manager 저장 또는 업데이트
        stmt = select(Manager).where(Manager.fotmob_id == manager.fotmob_id)
        result = await session.execute(stmt)
        existing_manager = result.scalar_one_or_none()
        
        if existing_manager:
            manager_data = normalize_manager_data(manager)
            manager_data["team_id"] = team_id
            for key, value in manager_data.items():
                setattr(existing_manager, key, value)
            manager_db = existing_manager
            logger.info(f"Updated existing manager: {manager.name}")
        else:
            manager_data = normalize_manager_data(manager)
            manager_data["team_id"] = team_id
            manager_db = Manager(**manager_data)
            session.add(manager_db)
            logger.info(f"Created new manager: {manager.name}")
        
        await session.flush()
        
        # 3. Players 저장 또는 업데이트
        saved_player_ids = []
        for player in players:
            stmt = select(Player).where(Player.fotmob_id == player.fotmob_id)
            result = await session.execute(stmt)
            existing_player = result.scalar_one_or_none()
            
            if existing_player:
                player_data = normalize_player_data(player)
                player_data["team_id"] = team_id
                # position 변환 (Position enum을 문자열로)
                if hasattr(player, "position") and player.position:
                    if isinstance(player.position, list) and len(player.position) > 0:
                        # Position enum인 경우 문자열로 변환
                        player_data["position"] = [str(p) if hasattr(p, "value") else p for p in player.position]
                for key, value in player_data.items():
                    setattr(existing_player, key, value)
                player_db = existing_player
                logger.debug(f"Updated existing player: {player.name}")
            else:
                player_data = normalize_player_data(player)
                player_data["team_id"] = team_id
                # position 변환
                if hasattr(player, "position") and player.position:
                    if isinstance(player.position, list) and len(player.position) > 0:
                        player_data["position"] = [str(p) if hasattr(p, "value") else p for p in player.position]
                player_db = Player(**player_data)
                session.add(player_db)
                logger.debug(f"Created new player: {player.name}")
            
            await session.flush()
            saved_player_ids.append(player_db.id)
        
        # 4. 커밋
        await session.commit()
        
        logger.info(
            f"Successfully saved team overview: team_id={team_id}, "
            f"manager_id={manager_db.id}, players_count={len(saved_player_ids)}"
        )
        
        return {
            "team_id": team_id,
            "manager_id": manager_db.id,
            "player_ids": saved_player_ids,
        }
        
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to save team overview: {e}", exc_info=True)
        raise
    finally:
        if should_close_session:
            await session.close()
