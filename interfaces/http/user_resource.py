from typing import final

import falcon
from falcon import Request, Response

from application.use_cases.users import DeleteUser, GetUser, ListUsers, RegisterUser
from schemas.user_schemas import UserCreate, UserOut


@final
class UserResource:
    def __init__(self, register: RegisterUser, list_: ListUsers, get: GetUser, delete: DeleteUser):
        self._register = register
        self._list = list_
        self._get = get
        self._delete = delete

    # POST /users
    async def on_post(self, req: Request, resp: Response) -> None:
        cmd = UserCreate(**await req.get_media())  # pyright:ignore[reportAny]
        user = await self._register(cmd.username, cmd.email, cmd.password)
        resp.status = falcon.HTTP_201
        resp.media = UserOut.model_validate(user).model_dump()

    # GET /users or /users/{id}
    async def on_get(self, req: Request, resp: Response, user_id: int | None = None) -> None:
        _ = req

        if user_id is None:
            users = await self._list()
            resp.media = [UserOut.model_validate(user).model_dump() for user in users]
            return

        user = await self._get(user_id)
        if user is None:
            resp.status = falcon.HTTP_404
            resp.media = {"error": "User not found"}
            return

        resp.media = UserOut.model_validate(user).model_dump()

    # DELETE /users/{id}
    async def on_delete(self, req: Request, resp: Response, user_id: int) -> None:
        _ = req

        try:
            await self._delete(user_id)

        except ValueError as exc:
            resp.status = falcon.HTTP_409
            resp.media = {"error": str(exc)}
            return

        resp.status = falcon.HTTP_204
