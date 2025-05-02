from collections.abc import Callable
from typing import final

import falcon
from falcon import HTTPConflict
from sqlalchemy.exc import IntegrityError

from common.utils import hash_password
from domain.users.entities import User
from domain.users.repositories import AbstractUserRepository
from infrastructure.databases.unit_of_work import UnitOfWork
from services.use_cases import BaseUseCase


@final
class RegisterUser:
    _uow_factory: Callable[[], UnitOfWork]

    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self._uow_factory = uow_factory

    async def __call__(self, username: str, email: str, password_plain: str) -> User:
        async with self._uow_factory() as uow:
            assert uow.users is not None, "UnitOfWork.users not initialised"

            if await uow.users.get_by_username(username):
                raise ValueError("Username already exists")  # noqa: EM101, TRY003

            hashed = hash_password(password_plain)
            try:
                return await uow.users.add(User(id=None, username=username, email=email, password_hash=hashed))

            except IntegrityError:
                raise ValueError("Username or email already exists") from None  # noqa: EM101, TRY003


@final
class ListUsers(BaseUseCase[AbstractUserRepository]):
    async def __call__(
        self,
        page: int = 1,
        per_page: int = 20,
        username_contains: str | None = None,
        email_contains: str | None = None,
    ) -> tuple[list[User], int]:
        offset = (page - 1) * per_page

        items = list(
            await self._repo.list_all(
                offset=offset,
                limit=per_page,
                username_contains=username_contains,
                email_contains=email_contains,
            )
        )

        total = await self._repo.count_all(username_contains=username_contains, email_contains=email_contains)

        return items, total


@final
class GetUser(BaseUseCase[AbstractUserRepository]):
    async def __call__(self, user_id: int) -> User | None:
        return await self._repo.get(user_id)


@final
class UpdateUserFields:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def __call__(self, user_id: int, username: str | None = None, email: str | None = None) -> None:
        if username is None and email is None:
            raise ValueError("At least one of 'username' or 'email' must be provided")  # noqa: EM101, TRY003

        async with self._uow_factory() as uow:
            assert uow.users is not None

            existing = await uow.users.get(user_id)

            if existing is None:
                raise falcon.HTTPNotFound(description="User not found")

            if username is not None:
                await uow.users.update_username(user_id, username)

            if email is not None:
                await uow.users.update_email(user_id, email)


class DeleteUser:
    _uow_factory: Callable[[], UnitOfWork]

    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self._uow_factory = uow_factory

    async def __call__(self, user_id: int) -> None:
        async with self._uow_factory() as uow:
            assert uow.orders is not None, "UnitOfWork.orders not initialized"
            assert uow.users is not None, "UnitOfWork.users not initialized"

            existing = await uow.orders.list_for_user(user_id)
            if existing:
                raise HTTPConflict(title="Cannot delete user — orders still exist.")
            await uow.users.delete(user_id)
