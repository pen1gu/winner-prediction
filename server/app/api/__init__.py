from fastapi import APIRouter

from server.app.api.health.router import router as health_router
from server.app.api.matches.router import router as matches_router
from server.app.api.prediction.router import router as prediction_router
from server.app.api.visualization.router import router as visualization_router

routers: list[APIRouter] = [
    health_router,
    matches_router,
    prediction_router,
    visualization_router,
]

__all__ = ["routers"]
