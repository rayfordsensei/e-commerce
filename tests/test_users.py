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


@pytest.mark.asyncio
async def test_patch_user_updates_username_and_email(async_client: AsyncClient, auth_token: str, create_user):  # noqa: ANN001  # pyright:ignore[reportUnknownParameterType, reportMissingParameterType]
    creds = await create_user("patchuser", "patch@example.com", "initialPass1")  # pyright:ignore[reportUnknownVariableType]
    user_id = creds["id"]  # pyright:ignore[reportUnknownVariableType]

    new_username = "patched_name"
    resp1 = await async_client.patch(
        f"/users/{user_id}", json={"username": new_username}, headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert resp1.status_code == 204  # noqa: PLR2004

    get1 = await async_client.get(f"/users/{user_id}", headers={"Authorization": f"Bearer {auth_token}"})
    body1 = get1.json()  # pyright:ignore[reportAny]
    assert body1["username"] == new_username
    assert body1["email"] == "patch@example.com"

    new_email = "newpatch@example.com"
    resp2 = await async_client.patch(
        f"/users/{user_id}", json={"email": new_email}, headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert resp2.status_code == 204  # noqa: PLR2004

    get2 = await async_client.get(f"/users/{user_id}", headers={"Authorization": f"Bearer {auth_token}"})
    body2 = get2.json()  # pyright:ignore[reportAny]
    assert body2["username"] == new_username
    assert body2["email"] == new_email

    final_username = "final_user"
    final_email = "final@example.com"
    resp3 = await async_client.patch(
        f"/users/{user_id}",
        json={"username": final_username, "email": final_email},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp3.status_code == 204  # noqa: PLR2004

    get3 = await async_client.get(f"/users/{user_id}", headers={"Authorization": f"Bearer {auth_token}"})
    body3 = get3.json()  # pyright:ignore[reportAny]
    assert body3["username"] == final_username
    assert body3["email"] == final_email

    await asyncio.sleep(0)
