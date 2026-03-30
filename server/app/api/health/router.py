from fastapi import APIRouter, status

from server.app.schemas.health import HealthRead

router = APIRouter(prefix="/health", tags=["Health"])

@router.get(
    "",
    response_model=HealthRead,
    status_code=status.HTTP_200_OK,
    summary="헬스 체크",
)
async def get_health() -> HealthRead:
    return HealthRead(status="ok")
