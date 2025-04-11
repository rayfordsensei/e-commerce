from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from decouple import config
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# from models import Base # Might need this for referencing (or not).

SQLITE_URI = "sqlite+aiosqlite:///ecommerce.db"
DEBUG = config("DEBUG", default=False, cast=bool)  # pyright:ignore[reportAny]

engine = create_async_engine(SQLITE_URI, echo=DEBUG)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:  # noqa: RUF029
    # Just a placeholder now, might add some test queries.
    print("[init_db] Relying on Alembic migrations to create/update tables.")


async def close_db() -> None:
    await engine.dispose()
    print("[close_db] Database engine disposed.")
