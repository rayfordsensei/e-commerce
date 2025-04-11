from contextlib import asynccontextmanager

from decouple import config
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from models import Base

# ASYNC_DATABASE_URI: str = config("ASYNC_DATABASE_URI")
# DATABASE_URI: str = config("DATABASE_URI")
SQLITE_URI = "sqlite+aiosqlite:///ecommerce.db"
DEBUG: bool = config("DEBUG", default=False, cast=bool)

engine = create_async_engine(SQLITE_URI, echo=DEBUG)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


@asynccontextmanager
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        # paranoia check
        def check_tables(sync_conn):
            inspector = inspect(sync_conn)
            return inspector.get_table_names()

        tables = await conn.run_sync(check_tables)

        if "users" not in tables:  # TODO: replace hardcoded value
            print("[init_db] Creating tables...")
            await conn.run_sync(Base.metadata.create_all)
        else:
            print("[init_db] Tables already exist — skipping creation.")


async def close_db():
    await engine.dispose()
    print("[close_db] Database engine disposed.")
