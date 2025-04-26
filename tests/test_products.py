import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_product_crud(async_client: AsyncClient, auth_token: str):
    # Create
    payload = {"name": "Mouse", "description": "Wireless", "price": 15.0, "stock": 50}
    resp = await async_client.post("/products", json=payload, headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 201  # noqa: PLR2004
    product_id = resp.json()["id"]  # pyright:ignore[reportAny]

    # Read
    resp_get = await async_client.get(f"/products/{product_id}", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp_get.json()["name"] == "Mouse"

    # Update
    resp_patch = await async_client.patch(
        f"/products/{product_id}",
        json={"price": 12.0},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp_patch.status_code == 204  # noqa: PLR2004

    # Verify price updated
    resp_verify = await async_client.get(f"/products/{product_id}", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp_verify.json()["price"] == 12.0  # noqa: PLR2004

    # Delete
    resp_del = await async_client.delete(f"/products/{product_id}", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp_del.status_code == 204  # noqa: PLR2004


@pytest.mark.asyncio
async def test_duplicate_name_case_insensitive(async_client: AsyncClient, auth_token: str):
    payload = {"name": "Unique", "description": "", "price": 1.0, "stock": 1}
    _ = await async_client.post("/products", json=payload, headers={"Authorization": f"Bearer {auth_token}"})
    dup = await async_client.post(
        "/products", json={**payload, "name": "unique"}, headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert dup.status_code == 400  # noqa: PLR2004
    assert "duplicate" in dup.json()["error"].lower()  # pyright:ignore[reportAny]


@pytest.mark.asyncio
async def test_product_not_found_includes_request_id(async_client: AsyncClient, auth_token: str):
    resp = await async_client.get("/products/9999", headers={"Authorization": f"Bearer {auth_token}"})

    assert resp.status_code == 404  # noqa: PLR2004

    rid = resp.headers["X-Request-ID"]
    body = resp.json()  # pyright:ignore[reportAny]

    assert body["error"] == "Product not found"
    assert body["request_id"] == rid
