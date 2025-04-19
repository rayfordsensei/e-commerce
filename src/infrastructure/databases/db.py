from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.settings import settings

DEBUG = settings.DEBUG
SQLITE_URI = settings.SQLITE_URI

engine = create_async_engine(SQLITE_URI, echo=DEBUG)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:  # noqa: RUF029
    # TODO: make it... useful?
    print("[init_db] Relying on Alembic migrations to create/update tables.")


async def close_db() -> None:
    await engine.dispose()
    print("[close_db] Database engine disposed.")
