from __future__ import annotations

from typing import List, Dict, Any, Union
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from server.app.models import Team, Player, Manager
from server.app.models.session import get_session
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

async def store(data: Union[Dict, List[SQLModel], SQLModel, None]):
    """
    어떤 데이터 형식이든 DB에 덮어씌워 저장할 수 있도록 처리하는 함수.
    
    지원 형식:
    1. Task 결과 Dict ({team_id: {team: Team, players: [Player], manager: Manager}})
    2. SQLModel 인스턴스 (단일)
    3. List[SQLModel] (리스트)
    """
    if not data:
        return

    # 1. Task 결과 Dict 처리
    if isinstance(data, dict):
        if not data:
            return
            
    # 2. SQLModel 처리 (단일 또는 리스트)
    session_gen = get_session()
    session = await session_gen.__anext__()
    
    try:
        if isinstance(data, SQLModel):
            await session.merge(data)
            
        elif isinstance(data, list) and data and isinstance(data[0], SQLModel):
            for item in data:
                await session.merge(item)
        
        await session.commit()
        
    except Exception as e:
        await session.rollback()
        logger.error(f"Store failed: {e}")
        raise e
    finally:
        await session.close()