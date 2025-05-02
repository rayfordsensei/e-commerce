from typing import final

import falcon
from spectree import Response

from api.schemas.user_schemas import UserCreate, UserError, UserFilter, UserOut, UserUpdate
from app.spectree import api
from services.use_cases.users import DeleteUser, GetUser, ListUsers, RegisterUser, UpdateUserFields


@final
class UserResource:
    def __init__(
        self,
        register_uc: RegisterUser,
        list_uc: ListUsers,
        get_uc: GetUser,
        update_uc: UpdateUserFields,
        delete_uc: DeleteUser,
    ):
        self._register = register_uc
        self._list = list_uc
        self._get = get_uc
        self._update = update_uc
        self._delete = delete_uc

    # POST /users
    @api.validate(  # pyright:ignore[reportUntypedFunctionDecorator, reportUnknownMemberType]
        json=UserCreate,
        resp=Response(
            HTTP_201=UserOut,
            HTTP_400=UserError,
        ),
        tags=["Users"],
        security={"bearerAuth": []},
    )
    async def on_post_collection(self, req: falcon.Request, resp: falcon.Response):
        """Register a new user.

        Creates an account and returns its ID, username, and email.
        """
        data = req.context.json
        try:
            user = await self._register(data.username, data.email, data.password)
        except ValueError as exc:
            resp.status = falcon.HTTP_400
            resp.media = UserError(error=str(exc)).model_dump()
            return

        resp.status = falcon.HTTP_201
        resp.media = UserOut.model_validate(user).model_dump()

    # GET /users
    @api.validate(  # pyright:ignore[reportUntypedFunctionDecorator, reportUnknownMemberType]
        query=UserFilter,
        resp=Response(
            HTTP_200=list[UserOut],
        ),
        tags=["Users"],
        security={"bearerAuth": []},
    )
    async def on_get_collection(self, req: falcon.Request, resp: falcon.Response):
        """List all users.

        Returns a paginated list, optionally filtered by username or email substring.
        """
        f = req.context.query

        users, total = await self._list(
            page=f.page,
            per_page=f.per_page,
            username_contains=f.username_contains,
            email_contains=f.email_contains,
        )

        resp.media = [UserOut.model_validate(u).model_dump() for u in users]
        resp.set_header("X-Total-Count", str(total))

    # GET /users/{user_id}
    @api.validate(  # pyright:ignore[reportUntypedFunctionDecorator, reportUnknownMemberType]
        resp=Response(
            HTTP_200=UserOut,
            HTTP_400=UserError,
            HTTP_404=UserError,
        ),
        tags=["Users"],
        security={"bearerAuth": []},
        path_parameter_descriptions={"user_id": "User ID to retrieve"},
    )
    async def on_get_detail(self, req: falcon.Request, resp: falcon.Response, user_id: int):
        """Retrieve a specific user by ID.

        Returns the user's full profile or 404 if not found.
        """
        _ = req

        user = await self._get(user_id)
        if user is None:
            resp.status = falcon.HTTP_404
            resp.media = UserError(error="User not found").model_dump()
            return

        resp.media = UserOut.model_validate(user).model_dump()

    # PATCH /users/{user_id}
    @api.validate(  # pyright:ignore[reportUntypedFunctionDecorator, reportUnknownMemberType]
        json=UserUpdate,
        resp=Response(
            HTTP_204=None,
            HTTP_400=UserError,
            HTTP_404=UserError,
        ),
        tags=["Users"],
        security={"bearerAuth": []},
        path_parameter_descriptions={
            "user_id": "ID of the user to update",
        },
    )
    async def on_patch_detail(self, req: falcon.Request, resp: falcon.Response, user_id: int):
        """Update a user's username and/or email.

        Applies one or both of the `username` and `email` fields to the specified user account.
        Returns 204 No Content on success, or 400/404 if validation fails or the user doesn't exist.
        """
        data = req.context.json

        await self._update(user_id, data.username, data.email)
        resp.status = falcon.HTTP_204

    # DELETE /users/{user_id}
    @api.validate(  # pyright:ignore[reportUntypedFunctionDecorator, reportUnknownMemberType]
        resp=Response(
            HTTP_204=None,
            HTTP_400=UserError,
            HTTP_404=UserError,
            HTTP_409=UserError,
        ),
        tags=["Users"],
        security={"bearerAuth": []},
        path_parameter_descriptions={"user_id": "ID of the user to delete"},
    )
    async def on_delete_detail(self, req: falcon.Request, resp: falcon.Response, user_id: int):
        """Delete a specific user by ID.

        Fails with 409 if the user still has orders.
        """
        _ = req

        await self._delete(user_id)
        resp.status = falcon.HTTP_204
