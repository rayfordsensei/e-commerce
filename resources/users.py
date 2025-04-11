import logging
from typing import Any, final

import falcon
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from db import get_db
from models import User

logger = logging.getLogger(__name__)


@final
class UserResource:
    async def on_get(self, req: falcon.Request, resp: falcon.Response, user_id: int | None = None) -> None:  # pyright:ignore[reportUnusedParameter]  # noqa: ARG002, PLR6301
        """Retrieve all users or a single user by ID."""
        try:
            async with get_db() as session:
                if user_id:
                    q = select(User).where(User.id == user_id)
                    result = await session.execute(q)
                    user = result.scalar_one_or_none()
                    if user:
                        resp.media = {
                            "id": user.id,
                            "username": user.username,
                            "email": user.email,
                            # password is hidden
                        }
                    else:
                        resp.status = falcon.HTTP_404
                else:
                    # TODO: consider pagination?
                    q = select(User)
                    result = await session.execute(q)
                    users = result.scalars().all()
                    resp.media = [{"id": u.id, "username": u.username, "email": u.email} for u in users]
        except Exception:
            # TODO: improve this?..
            logger.exception("Unexpected error during user retrieval")
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}

    async def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:  # noqa: PLR6301
        """Create a new user."""
        try:
            async with get_db() as session:
                data: dict[str, Any] = await req.get_media()  # pyright:ignore[reportExplicitAny, reportAny]

                # Simple input validation
                required_fields = ["username", "email", "password"]  # TODO: pyJWT?.. Pydantic?..
                missing = [field for field in required_fields if field not in data or not data[field]]
                if missing:
                    resp.status = falcon.HTTP_400
                    resp.media = {"error": f"Missing required fields: {', '.join(missing)}"}
                    return

                # ...proceed?
                new_user = User(username=data["username"], email=data["email"], password=data["password"])
                session.add(new_user)

                try:
                    await session.commit()
                    resp.status = falcon.HTTP_201
                    resp.media = {
                        "id": new_user.id,
                        "username": new_user.username,
                        "email": new_user.email,
                        "password": new_user.password,  # TODO: field masking?..
                    }
                except IntegrityError:
                    resp.status = falcon.HTTP_CONFLICT
                    resp.media = {"error": "User with this username or email already exists"}
                except SQLAlchemyError:
                    resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
                    resp.media = {"error": "Database error occurred"}
        except Exception:
            # TODO: improve this?..
            logger.exception("Unexpected error during user creation")
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}

    async def on_delete(self, req: falcon.Request, resp: falcon.Response, user_id: int) -> None:  # pyright:ignore[reportUnusedParameter]  # noqa: ARG002, PLR6301
        """Delete a user by ID."""
        try:
            async with get_db() as session:
                try:
                    # TODO: handle invalid user_id (non-integer; <1)
                    q = select(User).where(User.id == user_id)
                    result = await session.execute(q)
                    user = result.scalar_one_or_none()
                    if user:
                        await session.delete(user)
                        await session.commit()
                        resp.status = falcon.HTTP_204
                    else:
                        resp.status = falcon.HTTP_404
                except SQLAlchemyError:
                    resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
                    resp.media = {"error": "Database error occurred during deletion"}
        except Exception:
            # TODO: improve this?..
            logger.exception("Unexpected error during user deletion")
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}
