import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_404_uses_generic_error_handler(async_client: AsyncClient) -> None:
    resp = await async_client.get("/this-does-not-exist")

    assert resp.status_code == 404  # noqa: PLR2004

    rid = resp.headers["X-Request-ID"]
    assert resp.json()["request_id"] == rid
    assert uuid.UUID(rid)

    body = resp.json()  # pyright:ignore[reportAny]
    assert body["error"] == "Not Found"
    assert body["request_id"] == rid
