import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy import StaticPool, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from alembic import command
from alembic.config import Config
from app.settings import settings
from common.utils import hash_password
from infrastructure.sqlalchemy import events as sa_events
from infrastructure.sqlalchemy.models import User as UserORM

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
sa_events.register_engine_events(engine)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
_ALEMBIC_INI = BASE_DIR / "alembic.ini"


async def _apply_migrations() -> None:
    cfg = Config(str(_ALEMBIC_INI))

    await asyncio.to_thread(command.upgrade, cfg, "head")


async def _ensure_demo_user() -> None:
    """Create `demo / demo1234` if the table is empty (dev only)."""
    if not settings.DEBUG:  # never in production
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(UserORM).limit(1))
        existing = result.scalars().first()
        if existing:
            return

        demo = UserORM(
            username="demo",
            email="demo@example.com",
            password=hash_password("demo1234"),
        )
        session.add(demo)
        await session.commit()

    print("[init_db] Seeded demo user → demo / demo1234")


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db(seed: bool = False):  # noqa: FBT001, FBT002  # Why not?
    if settings.TESTING:
        print("[init_db] TESTING mode detected - skipping migrations & demo-seeding.")
        return

    await _apply_migrations()

    if seed:
        await _ensure_demo_user()

    print("[init_db] Relying on Alembic migrations to create/update tables.")


async def close_db():
    await engine.dispose()
    print("[close_db] Database engine disposed.")
