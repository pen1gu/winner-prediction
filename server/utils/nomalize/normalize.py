from __future__ import annotations

from server.app.models import Team, Player, Manager


def normalize_team_data(team: Team) -> dict:
    """Team 데이터 정규화 (특수 변환 처리)"""
    data = team.model_dump(exclude_none=True)
    
    # founded: 문자열일 수 있으므로 변환
    if "founded" in data and data["founded"]:
        try:
            data["founded"] = int(data["founded"]) if isinstance(data["founded"], str) else data["founded"]
        except (ValueError, TypeError):
            data["founded"] = None
    
    # stadium_capacity: 쉼표 포함 문자열일 수 있으므로 변환
    if "stadium_capacity" in data and data["stadium_capacity"]:
        try:
            capacity_str = str(data["stadium_capacity"]).replace(",", "").replace(" ", "")
            data["stadium_capacity"] = int(capacity_str) if capacity_str.isdigit() else None
        except (ValueError, TypeError):
            data["stadium_capacity"] = None
    
    # stadium_location: List[float]를 문자열로 변환
    if "stadium_location" in data and isinstance(data.get("stadium_location"), list):
        data["stadium_location"] = str(data["stadium_location"])
    
    # 빈 문자열을 None으로 변환
    for key in ["country", "league", "stadium", "stadium_city"]:
        if key in data and data[key] == "":
            data[key] = None
    
    # league_id가 0이면 None으로
    if "league_id" in data and data["league_id"] == 0:
        data["league_id"] = None
    
    return data


def normalize_player_data(player: Player) -> dict:
    """Player 데이터 정규화"""
    data = player.model_dump(exclude_none=True)
    
    # position: List[Position]을 문자열 리스트로 변환 (이미 SQLModel에서 처리됨)
    # birth_date는 이미 문자열로 저장됨
    
    # 빈 문자열을 None으로 변환
    for key in ["birth_place", "birth_country", "birth_state"]:
        if key in data and data[key] == "":
            data[key] = None
    
    # age, shirt_number가 0이면 None으로
    for key in ["age", "shirt_number"]:
        if key in data and data[key] == 0:
            data[key] = None
    
    return data


def normalize_manager_data(manager: Manager) -> dict:
    """Manager 데이터 정규화"""
    data = manager.model_dump(exclude_none=True)
    
    # 빈 문자열을 None으로 변환
    if "country" in data and data["country"] == "":
        data["country"] = None
    
    # age가 0이면 None으로
    if "age" in data and data["age"] == 0:
        data["age"] = None
    
    return data

