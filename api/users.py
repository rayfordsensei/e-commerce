import logging
from typing import Any, final

import bcrypt
import falcon
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

import utils
from db import get_db
from models import Order, User
from schemas.user_schemas import UserCreate, UserOut

logger = logging.getLogger("app." + __name__)


@final
class UserResource:
    async def on_get(self, req: falcon.Request, resp: falcon.Response, user_id: int | None = None) -> None:  # noqa: PLR6301
        """Retrieve all users or a single user by ID."""
        _ = req

        try:
            async with get_db() as session:
                if user_id is None:
                    q = select(User)
                    result = await session.execute(q)
                    users = result.scalars().all()

                    resp.media = [
                        UserOut(
                            id=u.id,
                            username=u.username,
                            email=u.email,
                        ).model_dump()
                        for u in users
                    ]
                    return None

                q = select(User).where(User.id == user_id)
                result = await session.execute(q)
                user = result.scalar_one_or_none()

                if not user:
                    return utils.error_response(resp, falcon.HTTP_400, f"User with id={user_id} does not exist.")

                resp.media = UserOut(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                ).model_dump()

        except SQLAlchemyError:
            logger.exception("Database error occurred while retrieving users.")
            utils.error_response(resp, falcon.HTTP_500, "Database error occurred")
        except Exception:
            logger.exception("Unexpected error during user retrieval")
            utils.error_response(resp, falcon.HTTP_500, "Internal server error")

    async def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:  # noqa: PLR6301
        """Create a new user."""
        try:
            data: dict[str, Any] = await req.get_media()  # pyright:ignore[reportAny, reportExplicitAny]
            user_in = UserCreate(**data)  # pyright:ignore[reportAny]

        except ValidationError as e:
            logger.exception("Validation error while creating user.")
            msg = "; ".join(f"{' -> '.join(map(str, error['loc']))}: {error['msg']}" for error in e.errors())

            return utils.error_response(resp, falcon.HTTP_400, msg)

        plain = user_in.password.encode("utf-8")
        hashed = bcrypt.hashpw(plain, bcrypt.gensalt())

        try:
            async with get_db() as session:
                new_user = User(
                    username=user_in.username,
                    email=user_in.email,
                    password=hashed.decode("utf-8"),
                )
                session.add(new_user)
                await session.commit()

                resp.status = falcon.HTTP_201
                resp.media = UserOut(
                    id=new_user.id,
                    username=new_user.username,
                    email=new_user.email,
                ).model_dump()

        except IntegrityError:
            logger.exception("IntegrityError while creating order.")
            utils.error_response(resp, falcon.HTTP_409, "User with this username or email already exists.")
        except SQLAlchemyError:
            logger.exception("Database error during user creation.")
            utils.error_response(resp, falcon.HTTP_500, "Database error occurred")
        except Exception:
            logger.exception("Unexpected error during user creation.")
            utils.error_response(resp, falcon.HTTP_500, "Internal server error")

    async def on_delete(self, req: falcon.Request, resp: falcon.Response, user_id: int) -> None:  # noqa: PLR6301
        """Delete an existing user by ID."""
        _ = req

        try:
            async with get_db() as session:
                q = select(User).where(User.id == user_id)
                result = await session.execute(q)
                user = result.scalar_one_or_none()

                if not user:
                    return utils.error_response(resp, falcon.HTTP_404, f"User with id={user_id} not found.")

                # Check whether the user has any order records.
                q = select(Order).where(Order.user_id == user_id)
                order_result = await session.execute(q)
                existing = order_result.scalars().first()

                if existing:
                    return utils.error_response(resp, falcon.HTTP_409, "Cannot delete user because orders still exist.")

                await session.delete(user)
                await session.commit()
                resp.status = falcon.HTTP_204

        except SQLAlchemyError:
            logger.exception("Database error during user deletion.")
            utils.error_response(resp, falcon.HTTP_500, "Database error occurred during deletion")
        except Exception:
            logger.exception("Unexpected error during user deletion.")
            utils.error_response(resp, falcon.HTTP_500, "Internal server error")
