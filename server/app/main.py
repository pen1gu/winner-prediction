from fastapi import FastAPI

from server.app.api import routers

API_V1_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    app = FastAPI(
        title="winner-prediction",
        version="0.1.0",
        description="fotmob 기반 축구 승부 예측 API",
    )
    for r in routers:
        app.include_router(r, prefix=API_V1_PREFIX)
    return app


app = create_app()
