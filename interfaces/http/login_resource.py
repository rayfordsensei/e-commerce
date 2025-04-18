from typing import final

import falcon

from application.use_cases.auth import AuthenticateUser
from schemas.login_schemas import LoginIn, TokenOut


@final
class LoginResource:
    def __init__(self, authenticate: AuthenticateUser):
        self._authenticate = authenticate

    async def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        cmd = LoginIn(**await req.get_media())  # pyright:ignore[reportAny]
        try:
            token = await self._authenticate(cmd.username, cmd.password)

        except ValueError:
            raise falcon.HTTPUnauthorized(description="Invalid credentials") from ValueError

        resp.status = falcon.HTTP_200
        resp.media = TokenOut(token=token).model_dump()
