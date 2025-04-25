import asyncio
import datetime
import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from joserfc import jwt

from infrastructure.databases.unit_of_work import UnitOfWork
from infrastructure.jwt.service import JsonWebTokenService

_VALID_SECRET = "test-secret"  # noqa: S105
_BAD_SECRET = "bad-secret"  # noqa: S105


def _issue(user_id: int, *, secret: str = _VALID_SECRET, alg: str = "HS256", ttl: int = -3600) -> str:
    """Return a ready-to-use JWT; ttl<0 -> expired."""  # noqa: DOC201
    now = datetime.datetime.now(tz=datetime.UTC)
    claims = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + datetime.timedelta(seconds=ttl)).timestamp()),
    }
    return jwt.encode({"alg": alg}, claims, secret, algorithms=[alg])


jwt_service = JsonWebTokenService()

INVALID_TOKENS = [
    "",
    "invalid-token-string",
    "Bearer invalid",
    "a.b.c",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
]
EXPIRED = _issue(1, ttl=-60)
BAD_SECRET = _issue(1, secret="oops")  # noqa: S106
WRONG_ALG = _issue(1, alg="HS512")
MALFORMED_HEADERS: list[dict[str, str] | list[tuple[str, str]]] = [
    {"Authorization": "Token abc"},  # missing Bearer
    {"Authorization": "totally-invalid"},  # random bytes
    [("Authorization", "abc"), ("Authorization", "def")],  # duplicate hdrs
]


@pytest.mark.asyncio
async def test_login_with_valid_creds(async_client: AsyncClient, create_user):  # noqa: ANN001 #pyright:ignore[reportUnknownParameterType, reportMissingParameterType]
    creds = await create_user("alice", "alice@example.com", "validpassword")  # pyright:ignore[reportUnknownVariableType]

    resp = await async_client.post("/login", json={"username": "alice", "password": "validpassword"})

    rid = resp.headers["X-Request-ID"]
    assert resp.json()["request_id"] == rid
    assert uuid.UUID(rid)

    assert resp.status_code == 200  # noqa: PLR2004
    token = resp.json()["token"]  # pyright:ignore[reportAny]

    assert jwt_service.verify(token) == creds["id"]  # pyright:ignore[reportAny]

    async with UnitOfWork() as uow:
        assert uow.users is not None
        assert (await uow.users.get(creds["id"])) is not None  # pyright:ignore[reportUnknownArgumentType]

    await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_login_rejects_bad_password(async_client: AsyncClient, create_user):  # noqa: ANN001 #pyright:ignore[reportUnknownParameterType, reportMissingParameterType]
    await create_user("bob", "bob@example.com", "secret123")

    resp = await async_client.post("/login", json={"username": "bob", "password": "wrongpassword"})

    rid = resp.headers["X-Request-ID"]
    assert resp.json()["request_id"] == rid
    assert uuid.UUID(rid)

    assert resp.status_code == 401  # noqa: PLR2004
    assert resp.json()["error"] == "Invalid credentials"

    await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_access_protected_endpoint_without_token(async_client: AsyncClient):
    resp = await async_client.get("/users")

    rid = resp.headers["X-Request-ID"]
    assert resp.json()["request_id"] == rid
    assert uuid.UUID(rid)

    assert resp.status_code == 401  # noqa: PLR2004

    response_data = resp.json()  # pyright:ignore[reportAny]
    assert "description" in response_data
    assert response_data["description"] == "Missing or invalid Authorization header"


@pytest.mark.asyncio
@pytest.mark.parametrize("bad_token", INVALID_TOKENS)
async def test_access_protected_endpoint_with_invalid_token(async_client: AsyncClient, bad_token: str):
    headers = {"Authorization": f"Bearer {bad_token}"}
    resp = await async_client.get("/users", headers=headers)

    rid = resp.headers["X-Request-ID"]
    assert resp.json()["request_id"] == rid
    assert uuid.UUID(rid)

    assert resp.status_code == 401  # noqa: PLR2004

    response_data = resp.json()  # pyright:ignore[reportAny]
    assert "description" in response_data
    assert response_data["description"] == "Invalid token"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("token", "expected_msg"),
    [
        (EXPIRED, "Token has expired"),
        (BAD_SECRET, "Invalid token"),
        (WRONG_ALG, "Invalid token"),
    ],
)
async def test_protected_endpoint_rejects_bad_jwt(async_client: AsyncClient, token: str, expected_msg: str):
    resp = await async_client.get("/users", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 401  # noqa: PLR2004

    rid = resp.headers["X-Request-ID"]
    body = resp.json()  # pyright:ignore[reportAny]
    assert body["request_id"] == rid
    assert body["description"] == expected_msg


@pytest.mark.asyncio
@pytest.mark.parametrize("hdrs", MALFORMED_HEADERS)
async def test_malformed_authorization_header(async_client: AsyncClient, hdrs: list[Any]):  # pyright:ignore[reportExplicitAny]
    resp = await async_client.get("/users", headers=hdrs)

    assert resp.status_code == 401  # noqa: PLR2004
    body = resp.json()  # pyright:ignore[reportAny]
    assert body["description"] == "Missing or invalid Authorization header"
