from pydantic import BaseModel, ConfigDict, Field


class HealthRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str = Field(description="서비스 상태")

