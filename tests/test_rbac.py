import pytest
from httpx import AsyncClient

from infrastructure.jwt.service import JsonWebTokenService


@pytest.mark.asyncio
async def test_user_cannot_delete_others_order(async_client: AsyncClient, create_user, auth_token: str):  # pyright:ignore[reportUnknownParameterType, reportMissingParameterType]  # noqa: ANN001
    user_a = await create_user("alice", "a@ex.com", "password123")  # pyright:ignore[reportUnknownVariableType]
    user_b = await create_user("bob", "b@ex.com", "password123")  # pyright:ignore[reportUnknownVariableType]

    resp = await async_client.post(
        "/orders",
        json={"user_id": user_a["id"], "total_price": 9.99},  # pyright:ignore[reportUnknownArgumentType]
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    order_id = resp.json()["id"]  # pyright:ignore[reportAny]

    jwt_svc = JsonWebTokenService()
    token_b = jwt_svc.issue(user_b["id"])  # pyright:ignore[reportUnknownArgumentType]

    resp_del = await async_client.delete(f"/orders/{order_id}", headers={"Authorization": f"Bearer {token_b}"})

    assert resp_del.status_code == 403  # noqa: PLR2004
    assert resp_del.json()["error"] == "Forbidden"


@pytest.mark.asyncio
async def test_owner_can_delete_their_order(async_client: AsyncClient, auth_token: str):
    jwt_svc = JsonWebTokenService()
    user_id = jwt_svc.verify(auth_token)

    resp = await async_client.post(
        "/orders", json={"user_id": user_id, "total_price": 1.0}, headers={"Authorization": f"Bearer {auth_token}"}
    )
    oid = resp.json()["id"]  # pyright:ignore[reportAny]

    resp_del = await async_client.delete(f"/orders/{oid}", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp_del.status_code == 204  # noqa: PLR2004
