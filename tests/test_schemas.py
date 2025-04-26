# pyright:basic

from uuid import uuid4

import pytest
from httpx import AsyncClient

from api.schemas.product_schemas import ProductCreate
from tests.helpers.boundaries import boundary_matrix

VALID_PRODUCT = {
    "name": "Edge Mouse",
    "description": "Wireless",
    "price": 1.0,
    "stock": 0,
}


@pytest.mark.asyncio
@pytest.mark.parametrize("case", boundary_matrix(ProductCreate, VALID_PRODUCT))
async def test_product_boundaries(async_client: AsyncClient, case):  # noqa: ANN001
    req_json = case.payload
    if case.expected_status == "OK":
        req_json = {"name": f"{req_json['name']}-{uuid4().hex[:6]}", **req_json}

    headers = {"Content-Type": "application/json"}
    resp = await async_client.post("/products", json=req_json, headers=headers)

    expected = 201 if case.expected_status == "OK" else case.expected_status
    assert resp.status_code == expected
