from typing import Any

import bcrypt
import falcon
from sqlalchemy import select

from auth import create_jwt
from db import get_db
from models import User
from utils import error_response


class LoginResource:
    async def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:  # noqa: PLR6301
        data: dict[str, Any] = await req.get_media()  # pyright:ignore[reportExplicitAny, reportAny]
        username = data.get("username")
        password = data.get("password")

        if not (username and password):
            return error_response(resp, falcon.HTTP_400, "Missing username or password")

        async with get_db() as session:
            q = select(User).where(User.username == username)  # pyright:ignore[reportAny]
            result = await session.execute(q)
            user = result.scalar_one_or_none()

            if user is None or not bcrypt.checkpw(password.encode(), user.password.encode()):  # pyright:ignore[reportAny]
                return error_response(resp, falcon.HTTP_401, "Invalid credentials")

            token = create_jwt(user.id)
            resp.status = falcon.HTTP_200
            resp.media = {"token": token}
            return None
