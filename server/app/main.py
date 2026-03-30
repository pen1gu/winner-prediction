from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from server.app.api import routers

API_V1_PREFIX = "/api/v1"

_WEB_DEMO_DIR = Path(__file__).resolve().parent.parent.parent / "client" / "web_demo"


def create_app() -> FastAPI:
    app = FastAPI(
        title="winner-prediction",
        version="0.1.0",
        description="fotmob 기반 축구 승부 예측 API",
    )
    for r in routers:
        app.include_router(r, prefix=API_V1_PREFIX)

    if _WEB_DEMO_DIR.is_dir():

        @app.get("/", include_in_schema=False)
        async def web_demo_index() -> FileResponse:
            return FileResponse(_WEB_DEMO_DIR / "index.html")

        app.mount(
            "/static",
            StaticFiles(directory=str(_WEB_DEMO_DIR)),
            name="web_demo_static",
        )

    return app


app = create_app()
