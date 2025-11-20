"""
FotMob API를 사용하여 축구 선수 정보를 조회하는 모듈
httpx 기반으로 구현
"""

import httpx
from typing import Optional, Dict, Any, List
import json


class FotMobPlayerClient:
    """FotMob API를 사용하여 선수 정보를 조회하는 클라이언트"""
    
    BASE_URL = "https://www.fotmob.com/api"
    
    def __init__(self, timeout: float = 10.0):
        """
        Args:
            timeout: HTTP 요청 타임아웃 (초)
        """
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def close(self):
        """HTTP 클라이언트 종료"""
        self.client.close()
    
    def search_player(self, player_name: str) -> List[Dict[str, Any]]:
        """
        선수 이름으로 검색
        
        Args:
            player_name: 검색할 선수 이름
            
        Returns:
            검색된 선수 목록 (리스트)
        """
        url = f"{self.BASE_URL}/search"
        params = {"term": player_name}
        
        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # 검색 결과에서 선수 정보만 필터링
            players = []
            if isinstance(data, dict) and "players" in data:
                players = data["players"]
            elif isinstance(data, list):
                players = [item for item in data if item.get("type") == "player"]
            
            return players
        except httpx.HTTPError as e:
            print(f"HTTP 오류 발생: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {e}")
            return []
    
    def get_player_data(self, player_id: int) -> Optional[Dict[str, Any]]:
        """
        선수 ID로 상세 정보 조회
        
        Args:
            player_id: 선수 ID
            
        Returns:
            선수 상세 정보 (딕셔너리) 또는 None
        """
        url = f"{self.BASE_URL}/playerData"
        params = {"id": player_id}
        
        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"HTTP 오류 발생: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {e}")
            return None
    
    def get_player_by_name(self, player_name: str) -> Optional[Dict[str, Any]]:
        """
        선수 이름으로 검색 후 첫 번째 결과의 상세 정보 반환
        
        Args:
            player_name: 선수 이름
            
        Returns:
            선수 상세 정보 (딕셔너리) 또는 None
        """
        players = self.search_player(player_name)
        
        if not players:
            print(f"'{player_name}' 선수를 찾을 수 없습니다.")
            return None
        
        # 첫 번째 결과의 ID로 상세 정보 조회
        first_player = players[0]
        player_id = first_player.get("id")
        
        if not player_id:
            print("선수 ID를 찾을 수 없습니다.")
            return None
        
        return self.get_player_data(player_id)


def main():
    """사용 예제"""
    # 클라이언트 생성 및 사용
    with FotMobPlayerClient() as client:
        # 예제 1: 선수 이름으로 검색
        print("=== 선수 검색 예제 ===")
        search_results = client.search_player("Messi")
        print(f"검색 결과: {len(search_results)}명의 선수 발견")
        
        if search_results:
            for i, player in enumerate(search_results[:3], 1):  # 상위 3명만 출력
                print(f"\n{i}. {player.get('name', 'N/A')}")
                print(f"   ID: {player.get('id', 'N/A')}")
                print(f"   팀: {player.get('team', 'N/A')}")
        
        # 예제 2: 선수 이름으로 상세 정보 조회
        print("\n=== 선수 상세 정보 조회 예제 ===")
        player_data = client.get_player_by_name("Son Heung-min")
        
        if player_data:
            print(f"\n선수 이름: {player_data.get('name', 'N/A')}")
            print(f"선수 ID: {player_data.get('id', 'N/A')}")
            
            # 추가 정보가 있다면 출력
            if 'team' in player_data:
                print(f"소속 팀: {player_data['team']}")
            if 'position' in player_data:
                print(f"포지션: {player_data['position']}")
            
            # 전체 데이터 구조 확인용 (일부만 출력)
            print(f"\n전체 데이터 키: {list(player_data.keys())[:10]}")


if __name__ == "__main__":
    main()

