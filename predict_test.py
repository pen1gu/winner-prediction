import asyncio
from typing import List
from sqlmodel import select
from sqlalchemy.orm import joinedload
from server.app.models import Player, MatchLogs, MatchDetails, Team, MatchInfos
from server.app.models.session import AsyncSessionLocal
from server.app.compute.player_rating import predict_match_outcomes, compute_player_rating

async def get_players_by_ids(session, player_ids: List[int]) -> List[Player]:
    """ID 리스트로 선수 정보(info, match_affect_features 포함) 조회"""
    if not player_ids:
        return []
    
    statement = (
        select(Player)
        .where(Player.id.in_(player_ids))
        .options(
            joinedload(Player.info),
            joinedload(Player.match_affect_features)
        )
    )
    result = await session.execute(statement)
    return result.scalars().unique().all()

async def main():
    async with AsyncSessionLocal() as session:
        # 1. 특정 경기 가져오기 (팀 정보 포함)
        statement = (
            select(MatchLogs)
            .where(MatchLogs.id == 5103357)
            .options(
                joinedload(MatchLogs.match_details),
                joinedload(MatchLogs.match_infos).joinedload(MatchInfos.home_team),
                joinedload(MatchLogs.match_infos).joinedload(MatchInfos.away_team)
            )
        )
        result = await session.execute(statement)
        match = result.scalars().first()

        if not match:
            print("데이터베이스에 경기 정보가 없습니다. 먼저 크롤링을 진행해주세요.")
            return

        # 팀 이름 가져오기
        home_name = match.match_infos.home_team.name if match.match_infos and match.match_infos.home_team else "Home"
        away_name = match.match_infos.away_team.name if match.match_infos and match.match_infos.away_team else "Away"

        print(f"--- {home_name} vs {away_name} (ID: {match.id}) 승률 예측 테스트 ---")

        # 2. 홈/어웨이 팀 상세 정보 분리
        home_detail = next((d for d in match.match_details if d.is_home), None)
        away_detail = next((d for d in match.match_details if not d.is_home), None)

        if not home_detail or not away_detail:
            print("홈/어웨이 팀 상세 정보가 부족합니다.")
            return

        # 3. 선발 선수 ID 리스트로 선수 객체 조회
        home_players = await get_players_by_ids(session, home_detail.starting_players)
        away_players = await get_players_by_ids(session, away_detail.starting_players)

        if not home_players or not away_players:
            print("선수 라인업 정보가 없습니다 (starting_players가 비어있음).")
            return

        print(f"{home_name} 선수: {[p.info.name for p in home_players]}")
        print(f"{away_name} 선수: {[p.info.name for p in away_players]}")

        # 4. 승률 예측 실행
        outcomes = await predict_match_outcomes(
            session, 
            home_players, 
            away_players, 
            home_detail.team_id, 
            away_detail.team_id
        )
        
        print(f"\n[{home_name}] 승리 확률: {outcomes['home'] * 100:.2f}%")
        print(f"[무승부] 확률: {outcomes['draw'] * 100:.2f}%")
        print(f"[{away_name}] 승리 확률: {outcomes['away'] * 100:.2f}%")

if __name__ == "__main__":
    asyncio.run(main())
