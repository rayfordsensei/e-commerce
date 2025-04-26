"""Shared fixtures for the test-suite.

The database is switched to an **in-memory SQLite** engine
so every test-session starts with a pristine schema and no disk I/O.
"""

import os
from pathlib import Path

import pytest_asyncio
from asgi_lifespan import LifespanManager  # outdated pos
from httpx import ASGITransport, AsyncClient

# Point SQLAlchemy at an in-memory db **before** app modules import
BASE_DIR = Path(__file__).resolve().parent.parent
os.environ.update({
    "DEBUG": "False",
    "SECRET_KEY": "test-secret",
    "SQLITE_URI": "sqlite+aiosqlite:///:memory:",
    "ALEMBIC_URI": "sqlite:///:memory:",
    "TESTING": "True",
})

# Spin-up the ASGI application
from app.app import app as application  # noqa: E402
from infrastructure.databases.db import engine as _engine  # noqa: E402
from infrastructure.sqlalchemy.models import Base  # noqa: E402


#  Build the schema once per session — no Alembic required
@pytest_asyncio.fixture(scope="session", autouse=True)
async def _create_schema():  # pyright:ignore[reportUnusedFunction]
    """Build the schema once per session (no Alembic needed)."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # nothing to tear-down - the db lives only in RAM


#  HTTP client
@pytest_asyncio.fixture(scope="session")
async def async_client():
    """An httpx.AsyncClient that talks to the application **in-process** via ASGI.

    Lifespan events (startup/shutdown) are triggered by LifespanManager.
    """  # noqa: D401, DOC402
    transport = ASGITransport(app=application)  # pyright:ignore[reportArgumentType]

    async with LifespanManager(application), AsyncClient(transport=transport, base_url="http://testserver") as client:  # pyright:ignore[reportArgumentType]
        yield client


#  Helper fixtures
from sqlalchemy.exc import IntegrityError  # noqa: E402

from common.utils import hash_password  # noqa: E402
from domain.users.entities import User  # noqa: E402
from infrastructure.databases.unit_of_work import UnitOfWork  # noqa: E402


@pytest_asyncio.fixture
async def create_user():  # noqa: ANN201, RUF029
    """Factory fixture -> create a user inside a UnitOfWork and return its creds."""  # noqa: D401, DOC201

    async def _factory(username: str = "jane_doe", email: str = "jane_doe@example.com", password: str = "testpassword"):  # noqa: ANN202, S107
        async with UnitOfWork() as uow:
            assert uow.users is not None

            new_user = User(
                id=None,
                username=username,
                email=email,
                password_hash=hash_password(password),
            )

            try:
                created = await uow.users.add(new_user)

            except IntegrityError:
                # Already present -> fetch within the same UoW
                existing = await uow.users.get_by_username(username)
                assert existing is not None, "Expected user to exist after IntegrityError"

                return {"id": existing.id, "username": username, "password": password}
        return {"id": created.id, "username": username, "password": password}

    return _factory


@pytest_asyncio.fixture
async def auth_token(async_client: AsyncClient, create_user):  # noqa: ANN001, ANN201  # pyright:ignore[reportAny, reportUnknownParameterType, reportMissingParameterType]
    """JWT for the default test-user (register -> login)."""  # noqa: DOC201
    creds = await create_user()  # pyright:ignore[reportUnknownVariableType]
    resp = await async_client.post("/login", json={"username": creds["username"], "password": creds["password"]})  # pyright:ignore[reportUnknownArgumentType]

    return resp.json()["token"]  # pyright:ignore[reportAny]
