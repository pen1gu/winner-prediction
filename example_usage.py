"""
FotMob 선수 정보 조회 모듈 사용 예제
"""

from fotmob_player import FotMobPlayerClient
import json


def example_search_players():
    """선수 검색 예제"""
    print("=" * 50)
    print("예제 1: 선수 검색")
    print("=" * 50)
    
    with FotMobPlayerClient() as client:
        # 여러 선수 검색
        search_terms = ["Messi", "Ronaldo", "Son Heung-min"]
        
        for term in search_terms:
            print(f"\n'{term}' 검색 중...")
            players = client.search_player(term)
            
            if players:
                print(f"  → {len(players)}명의 선수 발견")
                # 첫 번째 결과만 간단히 출력
                first = players[0]
                print(f"  → 첫 번째 결과: {first.get('name', 'N/A')} (ID: {first.get('id', 'N/A')})")
            else:
                print(f"  → 검색 결과 없음")


def example_get_player_details():
    """선수 상세 정보 조회 예제"""
    print("\n" + "=" * 50)
    print("예제 2: 선수 상세 정보 조회")
    print("=" * 50)
    
    with FotMobPlayerClient() as client:
        player_name = "Son Heung-min"
        print(f"\n'{player_name}' 선수 정보 조회 중...")
        
        player_data = client.get_player_by_name(player_name)
        
        if player_data:
            print(f"\n✓ 선수 정보 조회 성공!")
            print(f"\n기본 정보:")
            print(f"  - 이름: {player_data.get('name', 'N/A')}")
            print(f"  - ID: {player_data.get('id', 'N/A')}")
            
            # 데이터 구조 확인
            print(f"\n데이터 구조:")
            print(f"  - 전체 키 개수: {len(player_data)}")
            print(f"  - 주요 키: {', '.join(list(player_data.keys())[:10])}")
            
            # JSON으로 저장하고 싶다면
            # with open(f"{player_name.replace(' ', '_')}_data.json", "w", encoding="utf-8") as f:
            #     json.dump(player_data, f, ensure_ascii=False, indent=2)
        else:
            print(f"✗ 선수 정보를 찾을 수 없습니다.")


def example_get_multiple_players():
    """여러 선수 정보를 한 번에 조회하는 예제"""
    print("\n" + "=" * 50)
    print("예제 3: 여러 선수 정보 일괄 조회")
    print("=" * 50)
    
    player_names = ["Messi", "Ronaldo", "Mbappé"]
    
    with FotMobPlayerClient() as client:
        results = {}
        
        for name in player_names:
            print(f"\n'{name}' 조회 중...")
            player_data = client.get_player_by_name(name)
            
            if player_data:
                results[name] = {
                    "id": player_data.get("id"),
                    "name": player_data.get("name"),
                    "found": True
                }
                print(f"  ✓ 조회 완료 (ID: {player_data.get('id')})")
            else:
                results[name] = {"found": False}
                print(f"  ✗ 조회 실패")
        
        print(f"\n=== 조회 결과 요약 ===")
        for name, info in results.items():
            status = "✓" if info.get("found") else "✗"
            print(f"{status} {name}: {info.get('id', 'N/A') if info.get('found') else '없음'}")


def example_interactive_search():
    """대화형 선수 검색 예제"""
    print("\n" + "=" * 50)
    print("예제 4: 대화형 선수 검색")
    print("=" * 50)
    
    with FotMobPlayerClient() as client:
        while True:
            player_name = input("\n검색할 선수 이름을 입력하세요 (종료: 'q'): ").strip()
            
            if player_name.lower() == 'q':
                print("검색을 종료합니다.")
                break
            
            if not player_name:
                print("선수 이름을 입력해주세요.")
                continue
            
            print(f"\n'{player_name}' 검색 중...")
            players = client.search_player(player_name)
            
            if players:
                print(f"\n{len(players)}명의 선수 발견:")
                for i, player in enumerate(players[:5], 1):  # 최대 5명만 표시
                    print(f"  {i}. {player.get('name', 'N/A')} (ID: {player.get('id', 'N/A')})")
                
                # 상세 정보 조회 여부
                if len(players) > 0:
                    choice = input(f"\n첫 번째 선수 상세 정보를 조회하시겠습니까? (y/n): ").strip().lower()
                    if choice == 'y':
                        player_data = client.get_player_data(players[0].get('id'))
                        if player_data:
                            print(f"\n상세 정보:")
                            print(f"  - 이름: {player_data.get('name', 'N/A')}")
                            print(f"  - ID: {player_data.get('id', 'N/A')}")
            else:
                print(f"'{player_name}'에 대한 검색 결과가 없습니다.")


def main():
    """메인 함수 - 모든 예제 실행"""
    print("\n" + "=" * 50)
    print("FotMob 선수 정보 조회 예제 프로그램")
    print("=" * 50)
    
    # 예제 1: 선수 검색
    example_search_players()
    
    # 예제 2: 선수 상세 정보 조회
    example_get_player_details()
    
    # 예제 3: 여러 선수 정보 일괄 조회
    example_get_multiple_players()
    
    # 예제 4: 대화형 검색 (주석 해제하면 사용 가능)
    # example_interactive_search()
    
    print("\n" + "=" * 50)
    print("모든 예제 실행 완료!")
    print("=" * 50)


if __name__ == "__main__":
    main()

