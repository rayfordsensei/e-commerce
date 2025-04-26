# pyright:basic

import pytest
from httpx import AsyncClient

from common.utils import hash_password
from domain.users.entities import User
from infrastructure.databases.unit_of_work import UnitOfWork
from infrastructure.jwt.service import JsonWebTokenService
from tests.helpers.boundaries import ENDPOINTS, boundary_matrix, dedup_for_success

rows = []
for method, url, schema_cls, happy, ok_code in ENDPOINTS:
    rows.extend(
        pytest.param(method, url, ok_code, case, id=f"{url} {case.note}") for case in boundary_matrix(schema_cls, happy)
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(("method", "url", "ok_code", "case"), rows)
async def test_schema_boundaries(async_client: AsyncClient, auth_token: str, method: str, url: str, ok_code: int, case):  # noqa: ANN001, PLR0913, PLR0917
    if "{id}" in url:
        create_row = next(r for r in ENDPOINTS if r[1] == url.replace("/{id}", ""))
        resp = await async_client.request(
            create_row[0], create_row[1], json=create_row[3], headers={"Authorization": f"Bearer {auth_token}"}
        )
        url = url.replace("{id}", str(resp.json()["id"]))

    headers = {} if url.startswith("/login") else {"Authorization": f"Bearer {auth_token}"}
    payload = case.payload

    if case.expected_status == "OK":
        payload = dedup_for_success(url, payload)

    if url == "/orders" and method == "POST" and case.expected_status == "OK":
        payload["user_id"] = JsonWebTokenService().verify(auth_token)

    if url == "/login" and case.expected_status == "OK":
        async with UnitOfWork() as uow:
            assert uow.users is not None
            _ = await uow.users.add(
                User(
                    id=None,
                    username=payload["username"],
                    email=f"{payload['username']}@example.com",
                    password_hash=hash_password(payload["password"]),
                )
            )

    resp = await async_client.request(method, url, json=payload, headers=headers)
    expected = ok_code if case.expected_status == "OK" else case.expected_status
    assert resp.status_code == expected, case.note
