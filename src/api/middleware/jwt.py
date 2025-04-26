from typing import final

from falcon import HTTPUnauthorized, Request, Response
from joserfc.errors import ExpiredTokenError, JoseError

from app.settings import settings
from domain.auth.auth import AbstractTokenVerifier


@final
class JWTMiddleware:
    def __init__(self, verifier: AbstractTokenVerifier):
        self._verifier = verifier
        self._public_endpoints = [
            ("/login", "POST"),
        ]

        if settings.TESTING:
            self._public_endpoints.append(("/products", "POST"))

    async def process_resource(self, req: Request, resp: Response, resource: object, params: dict[str, str]):
        _ = resp, resource, params

        route_method = (req.path, req.method.upper())
        if route_method in self._public_endpoints or req.path.startswith("/apidoc") or req.path == "/favicon.ico":
            return

        auth_header = req.get_header("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPUnauthorized(description="Missing or invalid Authorization header")

        token = auth_header.split(" ", 1)[1]
        try:
            user_id = self._verifier.verify(token)
            req.context.user_id = user_id

        except ExpiredTokenError:
            raise HTTPUnauthorized(description="Token has expired") from ExpiredTokenError
        except (JoseError, KeyError, ValueError):
            raise HTTPUnauthorized(description="Invalid token") from None  # B904
