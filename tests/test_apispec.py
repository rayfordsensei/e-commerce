import pytest
from httpx import AsyncClient

EXPECTED = {
    ("/orders", "get"): {"200", "400"},
    ("/orders", "post"): {"201", "400", "404"},
    ("/orders/{order_id}", "get"): {"200", "400", "404"},
    ("/orders/{order_id}", "patch"): {"204", "400", "404"},
    ("/orders/{order_id}", "delete"): {"204", "400", "404", "403"},
    ("/products", "get"): {"200", "400"},
    ("/products", "post"): {"201", "400"},
    ("/products/{product_id}", "get"): {"200", "400", "404"},
    ("/products/{product_id}", "patch"): {"204", "400", "404"},
    ("/products/{product_id}", "delete"): {"204", "400", "404"},
    ("/users", "get"): {"200", "400"},
    ("/users", "post"): {"201", "400"},
    ("/users/{user_id}", "get"): {"200", "400", "404"},
    ("/users/{user_id}", "delete"): {"204", "400", "404", "409"},
}


@pytest.mark.asyncio
async def test_spec_includes_all_expected_statuses(async_client: AsyncClient):
    resp = await async_client.get("/apidoc/openapi.json")
    assert resp.status_code == 200  # noqa: PLR2004
    spec = resp.json()  # pyright:ignore[reportAny]

    for (path, method), expected_codes in EXPECTED.items():
        operation = spec["paths"][path].get(method)  # pyright:ignore[reportAny]
        assert operation is not None, f"Spec missing operation {method.upper()} {path}"

        actual_codes = set(operation["responses"].keys())  # pyright:ignore[reportAny]
        assert actual_codes == expected_codes, (
            f"{method.upper()} {path}: spec has {sorted(actual_codes)}, but expected {sorted(expected_codes)}"
        )
