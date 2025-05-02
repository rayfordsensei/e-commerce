import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_list_and_delete_order(async_client: AsyncClient, create_user):  # noqa: ANN001  # pyright:ignore[reportUnknownParameterType, reportMissingParameterType]
    user = await create_user("orderuser", "order@example.com", "password123")  # pyright:ignore[reportUnknownVariableType]

    login = await async_client.post("/login", json={"username": user["username"], "password": user["password"]})  # pyright:ignore[reportUnknownArgumentType]
    token = login.json()["token"]

    resp = await async_client.post(
        "/orders", json={"user_id": user["id"], "total_price": 20.0}, headers={"Authorization": f"Bearer {token}"}  # pyright:ignore[reportUnknownArgumentType]
    )
    assert resp.status_code == 201
    order_id = resp.json()["id"]

    resp_list = await async_client.get(f"/orders?user_id={user['id']}", headers={"Authorization": f"Bearer {token}"})
    assert any(o["id"] == order_id for o in resp_list.json())

    resp_del = await async_client.delete(f"/orders/{order_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp_del.status_code == 204

    resp_get = await async_client.get(f"/orders/{order_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp_get.status_code == 404
