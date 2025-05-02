import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_user_list_pagination_and_filter(async_client: AsyncClient, create_user, auth_token):  # noqa: ANN001  # pyright:ignore[reportUnknownParameterType, reportMissingParameterType]
    prefix = uuid.uuid4().hex[:6]
    headers = {"Authorization": f"Bearer {auth_token}"}

    seeded = []
    for base in ("alice", "bob", "carol", "dave", "eve"):
        uname = f"{prefix}_{base}"
        creds = await create_user(uname, f"{uname}@example.com", "secret123")  # pyright:ignore[reportUnknownVariableType]
        seeded.append(creds)  # pyright:ignore[reportUnknownMemberType, reportUnknownArgumentType]

    resp1 = await async_client.get(f"/users?username_contains={prefix}&page=1&per_page=2", headers=headers)
    assert resp1.status_code == 200
    assert [u["username"] for u in resp1.json()] == [seeded[0]["username"], seeded[1]["username"]]

    resp3 = await async_client.get(f"/users?username_contains={prefix}&page=3&per_page=2", headers=headers)
    assert resp3.status_code == 200
    assert [u["username"] for u in resp3.json()] == [seeded[4]["username"]]

    resp_f = await async_client.get(f"/users?username_contains={prefix}", headers=headers)
    got = sorted(u["username"] for u in resp_f.json())
    expect = sorted(u["username"] for u in seeded)  # pyright:ignore[reportUnknownArgumentType, reportUnknownVariableType]
    assert got == expect

    resp_fp = await async_client.get(f"/users?username_contains={prefix}&page=1&per_page=2", headers=headers)
    assert resp_fp.status_code == 200
    assert [u["username"] for u in resp_fp.json()] == expect[:2]
