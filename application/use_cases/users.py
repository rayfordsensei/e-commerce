from typing import final

from domain.entities import User
from domain.repositories import AbstractOrderRepository, AbstractUserRepository
from shared.utils import hash_password


@final
class RegisterUser:
    def __init__(self, users: AbstractUserRepository):
        self._users = users

    async def __call__(self, username: str, email: str, password_plain: str) -> User:
        if await self._users.get_by_username(username):
            raise ValueError("Username already exists")  # noqa: EM101, TRY003

        hashed = hash_password(password_plain)
        user = User(id=None, username=username, email=email, password_hash=hashed)
        return await self._users.add(user)


@final
class ListUsers:
    def __init__(self, users: AbstractUserRepository):
        self._users = users

    async def __call__(self) -> list[User]:
        return list(await self._users.list_all())


@final
class GetUser:
    def __init__(self, users: AbstractUserRepository):
        self._users = users

    async def __call__(self, user_id: int) -> User | None:
        return await self._users.get(user_id)


@final
class DeleteUser:
    def __init__(self, users: AbstractUserRepository, orders: AbstractOrderRepository):
        self._users = users
        self._orders = orders

    async def __call__(self, user_id: int) -> None:
        existing = await self._orders.list_for_user(user_id)
        if existing:
            raise ValueError("Cannot delete user - orders still exist.")  # noqa: EM101, TRY003

        await self._users.delete(user_id)
