import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from server.config.settings import settings
from server.utils.model.db_model import DBModel

from server.app.db import (  # noqa: F401
    TeamModel,
    PlayerModel,
    PlayerDetailsModel,
    PlayerMatchAffectFeaturesModel,
)


async def init_database() -> None:
    engine = create_async_engine(
        settings.database_url,
        echo=settings.database_echo,
        future=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(DBModel.metadata.create_all)
    await engine.dispose()
    print(f"✅ Database initialized at {settings.database_url}")


if __name__ == "__main__":
    asyncio.run(init_database())

