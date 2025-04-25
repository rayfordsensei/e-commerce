import asyncio

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_list_and_delete_order(async_client: AsyncClient, auth_token: str, create_user):  # noqa: ANN001  # pyright:ignore[reportUnknownParameterType, reportMissingParameterType]
    user = await create_user("orderuser", "order@example.com", "pw123456")  # pyright:ignore[reportUnknownVariableType]

    # Create order
    resp = await async_client.post(
        "/orders",
        json={"user_id": user["id"], "total_price": 20.0},  # pyright:ignore[reportUnknownArgumentType]
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 201  # noqa: PLR2004
    order_id = resp.json()["id"]  # pyright:ignore[reportAny]

    # List orders for user
    resp_list = await async_client.get(
        f"/orders?user_id={user['id']}", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert any(o["id"] == order_id for o in resp_list.json())  # pyright:ignore[reportAny]

    # Delete
    resp_del = await async_client.delete(f"/orders/{order_id}", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp_del.status_code == 204  # noqa: PLR2004

    # Fetch again → 404
    resp_get = await async_client.get(f"/orders/{order_id}", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp_get.status_code == 404  # noqa: PLR2004

    await asyncio.sleep(0)
