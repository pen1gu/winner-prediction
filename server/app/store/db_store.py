from __future__ import annotations
from contextlib import asynccontextmanager
from typing import Type, AsyncIterator, Iterable
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from server.app.models.session import get_session

async def upsert_model(
    session: AsyncSession,
    obj: SQLModel,
    *,
    conflict_cols: list[str] | None = None,
) -> SQLModel:
    """어떤 SQLModel이든 upsert (Postgres ON CONFLICT 우선, 아니면 merge fallback)."""
    model: Type[SQLModel] = type(obj)
    table = model.__table__  # type: ignore[attr-defined]

    data = obj.model_dump(exclude_none=True)
    
    # 기본 충돌 컬럼을 id로 설정 (이제 fotmob_id가 id로 바뀌었으므로)
    if conflict_cols is None:
        conflict_cols = ["id"] if "id" in data else []

    if conflict_cols:
        stmt = pg_insert(table).values(**data)
        excluded = stmt.excluded  # type: ignore[attr-defined]
        
        # PK(id)를 제외한 나머지 컬럼 업데이트
        update_cols = {k: getattr(excluded, k) for k in data.keys() if k not in conflict_cols}

        if update_cols:
            stmt = stmt.on_conflict_do_update(  # type: ignore[attr-defined]
                index_elements=conflict_cols,
                set_=update_cols,
            )
        else:
            # 업데이트할 컬럼이 없으면 아무것도 안 함
            stmt = stmt.on_conflict_do_nothing(index_elements=conflict_cols) # type: ignore[attr-defined]
            
        await session.execute(stmt)
        return obj

    return await session.merge(obj)

async def save(
    data: SQLModel | Iterable[SQLModel],
    *,
    session: AsyncSession | None = None,
    conflict_cols: list[str] | None = None,
) -> None:
    """SQLModel(또는 iterable)을 upsert하고 commit."""
    async with _ensure_session(session) as session:
        try:
            if isinstance(data, SQLModel):
                await upsert_model(session, data, conflict_cols=conflict_cols)
            else:
                for item in data:
                    await upsert_model(session, item, conflict_cols=conflict_cols)
            await session.commit()
        except Exception:
            await session.rollback()
            raise

@asynccontextmanager
async def _ensure_session(
    session: AsyncSession | None,
) -> AsyncIterator[AsyncSession]:
    """session 없으면 내부에서 생성/정리."""
    if session is not None:
        yield session
        return

    session_gen = get_session()
    created_session = await session_gen.__anext__()
    try:
        yield created_session
    finally:
        await created_session.close()
        await session_gen.aclose()
