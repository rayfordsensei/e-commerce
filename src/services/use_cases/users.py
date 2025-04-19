from dataclasses import dataclass
from typing import final

from common.utils import hash_password
from domain.orders.repositories import AbstractOrderRepository
from domain.users.entities import User
from domain.users.repositories import AbstractUserRepository
from services.use_cases import BaseUseCase


@final
class RegisterUser(BaseUseCase[AbstractUserRepository]):
    async def __call__(self, username: str, email: str, password_plain: str) -> User:
        if await self._repo.get_by_username(username):
            raise ValueError("Username already exists")  # noqa: EM101, TRY003

        hashed = hash_password(password_plain)
        user = User(id=None, username=username, email=email, password_hash=hashed)
        return await self._repo.add(user)


@final
class ListUsers(BaseUseCase[AbstractUserRepository]):
    async def __call__(self) -> list[User]:
        return list(await self._repo.list_all())


@final
class GetUser(BaseUseCase[AbstractUserRepository]):
    async def __call__(self, user_id: int) -> User | None:
        return await self._repo.get(user_id)


@dataclass(slots=True)
class DeleteUser(BaseUseCase[AbstractUserRepository]):
    _orders: AbstractOrderRepository

    async def __call__(self, user_id: int) -> None:
        existing = await self._orders.list_for_user(user_id)
        if existing:
            raise ValueError("Cannot delete user - orders still exist.")  # noqa: EM101, TRY003

        await self._repo.delete(user_id)
