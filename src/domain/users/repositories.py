import abc

from .entities import User


class AbstractUserRepository(abc.ABC):
    # Write ops
    @abc.abstractmethod
    async def add(self, user: User) -> User:
        pass

    @abc.abstractmethod
    async def delete(self, user_id: int) -> None:
        pass

    @abc.abstractmethod
    async def update_email(self, user_id: int, new_email: str) -> None:
        pass

    @abc.abstractmethod
    async def update_username(self, user_id: int, new_username: str) -> None:
        pass

    # Read ops
    @abc.abstractmethod
    async def get(self, user_id: int) -> User | None:
        pass

    @abc.abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        pass

    @abc.abstractmethod
    async def list_all(
        self,
        *,
        offset: int = 0,
        limit: int | None = None,
        username_contains: str | None = None,
        email_contains: str | None = None,
    ) -> list[User]:
        pass

    @abc.abstractmethod
    async def count_all(self, *, username_contains: str | None = None, email_contains: str | None = None) -> int:
        pass
