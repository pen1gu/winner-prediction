from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict, Field

router = APIRouter(prefix="/health", tags=["Health"])


class HealthRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str = Field(description="서비스 상태")


@router.get(
    "",
    response_model=HealthRead,
    status_code=status.HTTP_200_OK,
    summary="헬스 체크",
)
async def get_health() -> HealthRead:
    return HealthRead(status="ok")
