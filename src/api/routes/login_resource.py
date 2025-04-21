from typing import final

import falcon
from spectree import Response

from api.schemas.login_schemas import AuthError, LoginIn, TokenOut
from app.spectree import api
from services.use_cases.auth import AuthenticateUser


@final
class LoginResource:
    def __init__(self, authenticate_uc: AuthenticateUser) -> None:
        self._authenticate = authenticate_uc

    # POST /login
    @api.validate(  # pyright:ignore[reportUnknownMemberType, reportUntypedFunctionDecorator]  # write a stub?.. hell no
        json=LoginIn,
        resp=Response(
            HTTP_200=TokenOut,
            HTTP_401=AuthError,
        ),
        tags=["Auth"],
    )
    async def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        """Authenticate user and return a JWT.

        Accepts username & password, returns a signed token valid for 4 hours.
        """
        data = req.context.json  # pyright:ignore[reportAny]

        try:
            token = await self._authenticate(data.username, data.password)  # pyright:ignore[reportAny]

        except ValueError:
            resp.status = falcon.HTTP_401
            resp.media = AuthError(error="Invalid credentials").model_dump()
            return

        resp.media = TokenOut(token=token).model_dump()
