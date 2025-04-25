import asyncio

import pytest
from httpx import AsyncClient

from infrastructure.databases.unit_of_work import UnitOfWork


@pytest.mark.asyncio
async def test_register_and_retrieve_user(async_client: AsyncClient, auth_token: str):
    payload = {"username": "charlie", "email": "charlie@example.com", "password": "password123"}

    # Create through API
    resp = await async_client.post("/users", json=payload, headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 201  # noqa: PLR2004
    user_id = resp.json()["id"]  # pyright:ignore[reportAny]

    # Verify through UoW
    async with UnitOfWork() as uow:
        assert uow.users is not None
        user = await uow.users.get(user_id)  # pyright:ignore[reportAny]
        assert user is not None
        assert user.username == "charlie"
        assert user.email == "charlie@example.com"

    await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_delete_user_with_existing_orders_fails(async_client: AsyncClient, auth_token: str, create_user):  # noqa: ANN001, ARG001  # pyright:ignore[reportUnknownParameterType, reportUnusedParameter, reportMissingParameterType]
    # Create a second user and an order for them directly via API
    resp_u = await async_client.post(
        "/users",
        json={"username": "orderowner", "email": "oo@example.com", "password": "p@ssw0rd"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    user_id = resp_u.json()["id"]  # pyright:ignore[reportAny]

    resp_p = await async_client.post(
        "/products",
        json={"name": "item", "description": "x", "price": 5.0, "stock": 10},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    product_id = resp_p.json()["id"]  # noqa: F841  # pyright:ignore[reportAny, reportUnusedVariable]

    _ = await async_client.post(
        "/orders",
        json={"user_id": user_id, "total_price": 5.0},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    resp_del = await async_client.delete(f"/users/{user_id}", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp_del.status_code == 409  # noqa: PLR2004
    assert "orders still exist" in resp_del.json()["error"]

    async with UnitOfWork() as uow:
        assert uow.users is not None
        assert uow.orders is not None
        assert (await uow.users.get(user_id)) is not None  # pyright:ignore[reportAny]
        assert len(await uow.orders.list_for_user(user_id)) == 1  # pyright:ignore[reportAny]

    await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_delete_missing_user_returns_404(async_client: AsyncClient, auth_token: str):
    resp = await async_client.delete("/users/9999", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 404  # noqa: PLR2004
