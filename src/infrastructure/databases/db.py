from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.settings import settings

DEBUG = settings.DEBUG
SQLITE_URI = settings.SQLITE_URI

engine_args = {}
engine_args["echo"] = DEBUG
if SQLITE_URI.startswith("sqlite+aiosqlite") and ":memory:" in SQLITE_URI:
    SQLITE_URI = "sqlite+aiosqlite:///:memory:?cache=shared"  # pyright:ignore[reportConstantRedefinition]
    engine_args["poolclass"] = StaticPool
    engine_args["connect_args"] = {"check_same_thread": False, "uri": True}
    engine_args["pool_reset_on_return"] = "none"

engine = create_async_engine(SQLITE_URI, **engine_args)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():  # noqa: RUF029
    # TODO: make it... useful?
    print("[init_db] Relying on Alembic migrations to create/update tables.")


async def close_db():
    await engine.dispose()
    print("[close_db] Database engine disposed.")
