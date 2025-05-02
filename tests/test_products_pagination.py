import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_products_pagination_and_filter(async_client: AsyncClient, auth_token: str):
    prefix = uuid.uuid4().hex[:6]
    headers = {"Authorization": f"Bearer {auth_token}"}

    seeded = []
    for i in range(5):
        payload = {
            "name": f"{prefix}_prod{i}",
            "description": "",
            "price": i * 10 + 5,
            "stock": 1,
        }
        resp = await async_client.post("/products", json=payload, headers=headers)
        assert resp.status_code == 201
        seeded.append(payload)  # pyright:ignore[reportUnknownMemberType]

    resp_f = await async_client.get("/products?min_price=15&max_price=35", headers=headers)
    assert resp_f.status_code == 200
    for item in resp_f.json():
        assert 15 <= item["price"] <= 35

    resp_p = await async_client.get("/products?page=2&per_page=2", headers=headers)
    assert resp_p.status_code == 200
    names_page2 = [p["name"] for p in resp_p.json()]
    assert names_page2 == [seeded[2]["name"], seeded[3]["name"]]
