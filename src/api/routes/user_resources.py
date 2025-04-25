from typing import final

import falcon
from spectree import Response

from api.schemas.user_schemas import UserCreate, UserError, UserOut
from app.spectree import api
from services.use_cases.users import DeleteUser, GetUser, ListUsers, RegisterUser


@final
class UserResource:
    def __init__(
        self,
        register_uc: RegisterUser,
        list_uc: ListUsers,
        get_uc: GetUser,
        delete_uc: DeleteUser,
    ):
        self._register = register_uc
        self._list = list_uc
        self._get = get_uc
        self._delete = delete_uc

    # POST /users
    @api.validate(  # pyright:ignore[reportUntypedFunctionDecorator, reportUnknownMemberType]
        json=UserCreate,
        resp=Response(
            HTTP_201=UserOut,
            HTTP_400=UserError,
        ),
        tags=["Users"],
    )
    async def on_post_collection(self, req: falcon.Request, resp: falcon.Response):
        """Register a new user."""
        data = req.context.json  # pyright:ignore[reportAny]
        try:
            user = await self._register(data.username, data.email, data.password)  # pyright:ignore[reportAny]
        except ValueError as exc:
            resp.status = falcon.HTTP_400
            resp.media = UserError(error=str(exc)).model_dump()
            return

        resp.status = falcon.HTTP_201
        resp.media = UserOut.model_validate(user).model_dump()

    # GET /users
    @api.validate(  # pyright:ignore[reportUntypedFunctionDecorator, reportUnknownMemberType]
        resp=Response(
            HTTP_200=list[UserOut],
        ),
        tags=["Users"],
        security={"bearerAuth": []},
    )
    async def on_get_collection(self, req: falcon.Request, resp: falcon.Response):
        """List all users."""
        _ = req

        users = await self._list()
        resp.media = [UserOut.model_validate(u).model_dump() for u in users]

    # GET /users/{user_id}
    @api.validate(  # pyright:ignore[reportUntypedFunctionDecorator, reportUnknownMemberType]
        resp=Response(
            HTTP_200=UserOut,
            HTTP_404=UserError,
        ),
        tags=["Users"],
        security={"bearerAuth": []},
        path_parameter_descriptions={"user_id": "User ID to retrieve"},
    )
    async def on_get_detail(self, req: falcon.Request, resp: falcon.Response, user_id: int):
        """Retrieve a specific user by ID."""
        _ = req

        user = await self._get(user_id)
        if user is None:
            resp.status = falcon.HTTP_404
            resp.media = UserError(error="User not found").model_dump()
            return

        resp.media = UserOut.model_validate(user).model_dump()

    # DELETE /users/{user_id}
    @api.validate(  # pyright:ignore[reportUntypedFunctionDecorator, reportUnknownMemberType]
        resp=Response(
            HTTP_204=None,
            HTTP_404=UserError,
            HTTP_409=UserError,
        ),
        tags=["Users"],
        security={"bearerAuth": []},
    )
    async def on_delete_detail(self, req: falcon.Request, resp: falcon.Response, user_id: int):
        """Delete a specific user by ID."""
        _ = req

        await self._delete(user_id)
        resp.status = falcon.HTTP_204
