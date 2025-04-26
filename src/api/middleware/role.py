from __future__ import annotations

from collections.abc import Iterable
from typing import final

import falcon
from falcon import Request, Response


@final
class RoleMiddleware:
    """Authorises requests after JWTMiddleware has set `req.context.user_roles`.

    Usage
    -----
    class OrdersCollection:
        required_roles = {"GET": {"admin", "sales"}, "POST": {"admin"}}
        ...

    If the method is not in the mapping the route is considered *public*.
    """

    async def process_resource(
        self,
        req: Request,
        resp: Response,  # unused but required
        resource: object,
        params: dict[str, str],  # unused
    ) -> None:
        _ = resp, params

        # 1. Skip completely public endpoints
        if not hasattr(resource, "required_roles"):
            return

        required: dict[str, Iterable[str]] = resource.required_roles
        allowed: set[str] = set(required.get(req.method, ()))

        # 2. No roles ⇒ open to everyone
        if not allowed:
            return

        user_roles: set[str] | None = getattr(req.context, "user_roles", None)
        if not user_roles:
            raise falcon.HTTPForbidden(
                title="Forbidden",
                description="Missing role assignment",
            )

        # 3. Intersect
        if allowed.isdisjoint(user_roles):
            raise falcon.HTTPForbidden(
                title="Forbidden",
                description="You do not have permission to access this resource.",
            )
