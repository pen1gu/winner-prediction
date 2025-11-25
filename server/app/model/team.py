from pydantic import BaseModel, Field

class Team(BaseModel):
    # 팀 이름
    name: str = Field(default="")

    # 국가
    country: str = Field(default="")
    
    # 리그
    league: str = Field(default="")

    # 로고 URL
    logo: str = Field(default="")

    # 창단 연도
    founded: int = Field(default=0)

    # 경기장 이름
    stadium: str = Field(default="")

    # 경기장 수용 인원
    stadium_capacity: int = Field(default=0)

    # 경기장 위치
    stadium_location: str = Field(default="")

    # 경기장 주소
    stadium_address: str = Field(default="")

    # 경기장 도시
    stadium_city: str = Field(default="")