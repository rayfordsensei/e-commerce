from typing import final

import falcon
from joserfc.errors import ExpiredTokenError, JoseError

from auth import verify_jwt


@final
class JWTMiddleware:
    def __init__(self):
        self.unprotected = [
            ("/login", "POST"),
        ]

    async def process_request(self, req: falcon.Request, resp: falcon.Response):
        _ = resp

        route = req.path
        method = req.method.upper()

        if (route, method) in self.unprotected:
            return

        auth_header = req.get_header("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            raise falcon.HTTPUnauthorized(description="Missing or invalid Authorization header")

        token = auth_header.split(" ", 1)[1]

        try:
            claims = verify_jwt(token)
            req.context.user_id = int(claims["sub"])  # pyright:ignore[reportAny]

        except ExpiredTokenError:
            raise falcon.HTTPUnauthorized(description="Token has expired.") from ExpiredTokenError
        except JoseError:
            raise falcon.HTTPUnauthorized(description="Invalid token.") from JoseError
        except KeyError:
            raise falcon.HTTPUnauthorized(description="Token missing 'sub' claim.") from KeyError
