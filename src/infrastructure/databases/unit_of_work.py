from types import TracebackType
from typing import final

from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.databases.db import AsyncSessionLocal
from infrastructure.sqlalchemy.repositories import (
    SQLAlchemyOrderRepository,
    SQLAlchemyProductRepository,
    SQLAlchemyUserRepository,
)


@final
class UnitOfWork:
    """Holds one session and all repos; commits or rolls back as a unit."""

    _session: AsyncSession | None
    users: SQLAlchemyUserRepository | None
    orders: SQLAlchemyOrderRepository | None
    products: SQLAlchemyProductRepository | None

    def __init__(self) -> None:
        self._session = None
        self.users = None
        self.orders = None
        self.products = None

    async def __aenter__(self) -> "UnitOfWork":
        self._session = AsyncSessionLocal()

        # inject the same session into each repo
        self.users = SQLAlchemyUserRepository(session=self._session)
        self.orders = SQLAlchemyOrderRepository(session=self._session)
        self.products = SQLAlchemyProductRepository(session=self._session)
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:
        _ = tb

        assert self._session is not None

        try:
            if exc_type:
                await self._session.rollback()
            else:
                try:
                    await self._session.commit()

                except Exception:
                    await self._session.rollback()
                    raise
        finally:
            await self._session.close()
