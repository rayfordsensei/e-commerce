from typing import final

import falcon
from joserfc.errors import ExpiredTokenError, JoseError

from domain.auth import AbstractTokenVerifier


@final
class JWTMiddleware:
    def __init__(self, verifier: AbstractTokenVerifier):
        self._verifier = verifier
        self._public_endpoints = [("/login", "POST")]  # extend?..

    async def process_request(self, req: falcon.Request, resp: falcon.Response):
        _ = resp

        route_method = (req.path, req.method.upper())
        if route_method in self._public_endpoints:
            return

        auth_header = req.get_header("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise falcon.HTTPUnauthorized(description="Missing or invalid Authorization header")

        token = auth_header.split(" ", 1)[1]
        try:
            user_id = self._verifier.verify(token)
            req.context.user_id = user_id

        except ExpiredTokenError:
            raise falcon.HTTPUnauthorized(description="Token has expired") from ExpiredTokenError
        except (JoseError, KeyError):
            raise falcon.HTTPUnauthorized(description="Invalid token") from None  # B904
