from collections.abc import Sequence
from typing import Any, NamedTuple
from uuid import uuid4

from pydantic import BaseModel

from api.schemas.login_schemas import LoginIn
from api.schemas.order_schemas import OrderCreate, OrderUpdate
from api.schemas.product_schemas import ProductCreate, ProductUpdate
from api.schemas.user_schemas import UserCreate

ENDPOINTS = [
    # Products
    ("POST", "/products", ProductCreate, {"name": "EdgeMouse", "description": "", "price": 1.0, "stock": 0}, 201),
    ("PATCH", "/products/{id}", ProductUpdate, {"price": 9.99}, 204),
    # Orders
    ("POST", "/orders", OrderCreate, {"user_id": 1, "total_price": 1.0}, 201),
    ("PATCH", "/orders/{id}", OrderUpdate, {"total_price": 2.0}, 204),
    # Users
    ("POST", "/users", UserCreate, {"username": "tester", "email": "t@example.com", "password": "secret123"}, 201),
    # Auth (public)
    ("POST", "/login", LoginIn, {"username": "tester", "password": "secret123"}, 200),
]

_seen_product_names: set[str] = set()
_seen_usernames: set[str] = set()


def dedup_for_success(url: str, payload: dict[str, Any]) -> dict[str, Any]:  # pyright:ignore[reportExplicitAny]
    p = payload.copy()

    if url == "/products":
        if p.get("name", "") in _seen_product_names:
            base = p["name"] or "item"
            p["name"] = f"{base}-{uuid4().hex[:6]}"
        _seen_product_names.add(p["name"])

    elif url == "/users":
        if p.get("username", "") in _seen_usernames:
            base = p["username"] or "user"
            p["username"] = f"{base}-{uuid4().hex[:6]}"
            p["email"] = f"{p['username']}@example.com"
        _seen_usernames.add(p["username"])

    return p


def dedup_payload(url: str, payload: dict[str, Any]) -> dict[str, Any]:  # pyright:ignore[reportExplicitAny]
    p = payload.copy()
    suffix = uuid4().hex[:6]

    if url == "/products":
        p["name"] = f"{p.get('name', 'item')}-{suffix}"

    elif url == "/users":
        base = p.get("username", "user")  # pyright:ignore[reportAny]

        p["username"] = f"{base}-{suffix}"
        p["email"] = f"{p['username']}@example.com"
    return p


class Case(NamedTuple):
    payload: dict[str, Any]  # pyright:ignore[reportExplicitAny]
    expected_status: str | int
    note: str


def boundary_matrix(model_cls: type[BaseModel], happy: dict[str, Any]) -> Sequence[Case]:  # pyright:ignore[reportExplicitAny]
    """Build boundary-value test cases by inspecting the JSON Schema that Pydantic v2 generates for the model."""  # noqa: DOC201
    cases: list[Case] = []

    schema = model_cls.model_json_schema(mode="validation")
    props = schema.get("properties", {})  # pyright:ignore[reportAny]

    for name, example in happy.items():  # pyright:ignore[reportAny]
        prop_schema = props.get(name)  # pyright:ignore[reportAny]
        if not prop_schema:
            continue

        if "exclusiveMinimum" in prop_schema:
            gt = prop_schema["exclusiveMinimum"]  # pyright:ignore[reportAny]
            bad = {**happy, name: gt}
            cases.append(Case(bad, 400, f"{name} == gt({gt}) should fail"))

            delta = 1 if isinstance(example, int) else 0.01
            cases.append(Case({**happy, name: gt + delta}, "OK", f"{name} just above gt({gt}) passes"))

        if "minimum" in prop_schema:
            ge = prop_schema["minimum"]  # pyright:ignore[reportAny]
            cases.append(Case({**happy, name: ge}, "OK", f"{name} == ge({ge}) passes"))

            delta = 1 if isinstance(example, int) else 0.01
            cases.append(Case({**happy, name: ge - delta}, 400, f"{name} just below ge({ge}) should fail"))

        if "minLength" in prop_schema:
            ml = prop_schema["minLength"]  # pyright:ignore[reportAny]

            cases.append(Case({**happy, name: "x" * ml}, "OK", f"{name} at min_length({ml}) passes"))
            if ml > 0:
                cases.append(Case({**happy, name: "x" * (ml - 1)}, 400, f"{name} below min_length({ml}) fails"))

    return cases
