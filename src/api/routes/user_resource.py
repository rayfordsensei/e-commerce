from typing import final

import falcon
import spectree

from api.schemas.user_schemas import UserCreate, UserError, UserOut
from app.spectree import api
from services.use_cases.users import DeleteUser, GetUser, ListUsers, RegisterUser


@final
class UserResource:
    def __init__(self, register_uc: RegisterUser, list_uc: ListUsers, get_uc: GetUser, delete_uc: DeleteUser):
        self._register = register_uc
        self._list = list_uc
        self._get = get_uc
        self._delete = delete_uc

    # POST /users
    @api.validate(  # pyright:ignore[reportUnknownMemberType, reportUntypedFunctionDecorator]  # write a stub?.. hell no
        json=UserCreate,
        resp=spectree.Response(
            HTTP_201=UserOut,
            HTTP_400=UserError,
        ),
        tags=["Users"],
    )
    async def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        """Register a new user.

        Accepts username, email, and password; returns the created user record.
        """
        data = req.context.json  # pyright:ignore[reportAny]
        try:
            user = await self._register(data.username, data.email, data.password)  # pyright:ignore[reportAny]

        except ValueError as exc:
            resp.status = falcon.HTTP_400
            resp.media = UserError(
                error=str(exc),
                request_id=req.context.request_id,  # pyright:ignore[reportAny]
            ).model_dump()
            return

        resp.status = falcon.HTTP_201
        resp.media = UserOut.model_validate(user).model_dump()

    # GET /users or GET /users/{user_id}

    @api.validate(  # pyright:ignore[reportUnknownMemberType, reportUntypedFunctionDecorator]
        resp=spectree.Response(
            HTTP_200=list[UserOut],
            HTTP_404=UserError,
        ),
        tags=["Users"],
        security={"bearerAuth": []},
        path_parameter_descriptions={"user_id": "User ID to retrieve (omit to list all users)"},
    )
    async def on_get(self, req: falcon.Request, resp: falcon.Response, user_id: int | None = None) -> None:
        """Retrieve one user or list all.

        If `user_id` is provided, returns that user; otherwise returns all users.
        """
        if user_id is None:
            users = await self._list()
            resp.media = [UserOut.model_validate(u).model_dump() for u in users]
            return

        user = await self._get(user_id)
        if user is None:
            resp.status = falcon.HTTP_404
            resp.media = UserError(error="User not found", request_id=req.context.request_id).model_dump()  # pyright:ignore[reportAny]
            return

        resp.media = UserOut.model_validate(user).model_dump()

    # DELETE /users/{id}
    @api.validate(  # pyright:ignore[reportUnknownMemberType, reportUntypedFunctionDecorator]
        resp=spectree.Response(
            HTTP_204=None,
            HTTP_404=UserError,
            HTTP_409=UserError,
        ),
        tags=["Users"],
        security={"bearerAuth": []},
        path_parameter_descriptions={"user_id": "User ID to delete (must be > 0)"},
    )
    async def on_delete(self, req: falcon.Request, resp: falcon.Response, user_id: int) -> None:
        """Delete a user.

        Permanently removes the user with the given ID if they have no orders.
        """
        try:
            await self._delete(user_id)
        except ValueError as exc:
            resp.status = falcon.HTTP_409 if "orders" in str(exc).lower() else falcon.HTTP_404
            resp.media = UserError(error=str(exc), request_id=req.context.request_id).model_dump()  # pyright:ignore[reportAny]
            return

        resp.status = falcon.HTTP_204
