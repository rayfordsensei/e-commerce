from collections.abc import Callable, Sequence
from contextlib import asynccontextmanager, nullcontext
from inspect import isawaitable
from typing import Any, TypeVar, final, override

import falcon
from loguru import logger
from sqlalchemy import Select, delete, event, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from domain.orders.entities import Order
from domain.orders.repositories import AbstractOrderRepository
from domain.products.entities import Product
from domain.products.repositories import AbstractProductRepository
from domain.users.entities import User
from domain.users.repositories import AbstractUserRepository
from infrastructure.databases.db import AsyncSessionLocal
from infrastructure.sqlalchemy.models import Order as OrderORM
from infrastructure.sqlalchemy.models import Product as ProductORM
from infrastructure.sqlalchemy.models import User as UserORM

Entity = TypeVar("Entity")
Domain = TypeVar("Domain")

T = TypeVar("T")
type Scalar[T] = T | None
type Many[T] = list[T]


# Mappers
def _user_to_domain(row: UserORM) -> User:
    return User(id=row.id, username=row.username, email=row.email, password_hash=row.password)


def _product_to_domain(row: ProductORM) -> Product:
    return Product(id=row.id, name=row.name, description=row.description, price=row.price, stock=row.stock)


def _order_to_domain(row: OrderORM) -> Order:
    return Order(
        id=row.id,
        user_id=row.user_id,
        total_price=row.total_price,
        created_at=row.created_at,
    )


def _warn_unexpected_rollback(session: AsyncSession) -> None:
    logger.warning("Session {} issued an unexpected ROLLBACK", id(session))

    if session.in_transaction():
        logger.warning("Unexpected open transaction for session {}", id(session))


event.listen(Session, "after_rollback", _warn_unexpected_rollback)


class BaseSQLAlchemyRepo[Entity, Domain]:  # noqa: B903
    def __init__(self, session: AsyncSession | None, to_domain: Callable[[Entity], Domain]):
        self._session: AsyncSession | None = session
        self._to_domain: Callable[[Entity], Domain] = to_domain

    @staticmethod
    async def _maybe_await(value: Any) -> Any:  # pyright:ignore[reportAny, reportExplicitAny]  # noqa: ANN401
        if isawaitable(value):  # pyright:ignore[reportAny]
            return await value  # pyright:ignore[reportAny]
        return value  # pyright:ignore[reportAny]

    @asynccontextmanager
    async def _get_session(self):
        if self._session is not None:
            async with nullcontext(self._session):
                yield self._session
            return

        async with AsyncSessionLocal() as session:
            yield session

    async def _save(self, orm: Entity, work: Callable[[AsyncSession, Entity], Any]) -> Domain:  # pyright:ignore[reportExplicitAny]
        if self._session is not None:
            sess = self._session
            await self._maybe_await(work(sess, orm))

            await sess.flush()
            await sess.refresh(orm)

            return self._to_domain(orm)

        async with AsyncSessionLocal() as sess:
            await self._maybe_await(work(sess, orm))

            await sess.flush()
            await sess.refresh(orm)
            await sess.commit()

            return self._to_domain(orm)

    async def _exec(self, work: Callable[[AsyncSession], Any]):  # pyright:ignore[reportExplicitAny]
        if self._session is not None:
            sess = self._session
            result = await self._maybe_await(work(sess))

            rowcount = getattr(result, "rowcount", None)
            if rowcount is None or rowcount < 1:
                raise falcon.HTTPNotFound(description="Resource not found")
            return

        async with AsyncSessionLocal() as sess:
            result = await self._maybe_await(work(sess))

            rowcount = getattr(result, "rowcount", None)
            if rowcount is None or rowcount < 1:
                raise falcon.HTTPNotFound(description="Resource not found")

            await sess.commit()
            return

    async def _fetch_one(
        self,
        stmt: Select[Any],  # pyright:ignore[reportExplicitAny]
        *,
        mapper: Callable[[Entity], Domain] | None = None,
    ) -> Scalar[Domain]:
        mapper = mapper or self._to_domain
        async with self._get_session() as s:
            res = await s.execute(stmt)
            row: Entity | None = res.scalar_one_or_none()
            return mapper(row) if row else None

    async def _fetch_many(
        self,
        stmt: Select[Any],  # pyright:ignore[reportExplicitAny]
        *,
        mapper: Callable[[Entity], Domain] | None = None,
    ) -> Many[Domain]:
        mapper = mapper or self._to_domain
        async with self._get_session() as s:
            res = await s.execute(stmt)
            return [mapper(r) for r in res.scalars().all()]  # pyright:ignore[reportAny]


@final
class SQLAlchemyOrderRepository(BaseSQLAlchemyRepo[OrderORM, Order], AbstractOrderRepository):
    def __init__(self, session: AsyncSession | None = None) -> None:
        super().__init__(session, to_domain=_order_to_domain)

    #  Write ops
    @override
    async def add(self, order: Order) -> Order:
        orm = OrderORM(user_id=order.user_id, total_price=order.total_price)

        return await self._save(orm, lambda sess, o: sess.add(o))

    @override
    async def delete(self, order_id: int) -> None:
        await self._exec(lambda sess: sess.execute(delete(OrderORM).where(OrderORM.id == order_id)))

    @override
    async def update_total(self, order_id: int, new_total: float) -> None:
        await self._exec(
            lambda sess: sess.execute(update(OrderORM).where(OrderORM.id == order_id).values(total_price=new_total))
        )

    # Read ops
    @override
    async def get(self, order_id: int) -> Order | None:
        async with self._get_session() as session:
            res = await session.execute(select(OrderORM).where(OrderORM.id == order_id))
            row = res.scalar_one_or_none()
            return _order_to_domain(row) if row else None

    @override
    async def list_for_user(self, user_id: int) -> Sequence[Order]:
        async with self._get_session() as session:
            res = await session.execute(select(OrderORM).where(OrderORM.user_id == user_id))
            return [_order_to_domain(r) for r in res.scalars().all()]

    @override
    async def list_all(self) -> Sequence[Order]:
        async with self._get_session() as session:
            res = await session.execute(select(OrderORM))
            return [_order_to_domain(r) for r in res.scalars().all()]


@final
class SQLAlchemyUserRepository(BaseSQLAlchemyRepo[UserORM, User], AbstractUserRepository):
    def __init__(self, session: AsyncSession | None = None) -> None:
        super().__init__(session, to_domain=_user_to_domain)

    #  Write ops
    @override
    async def add(self, user: User) -> User:
        orm = UserORM(username=user.username, email=user.email, password=user.password_hash)

        async with self._get_session() as session:
            session.add(orm)

            try:
                if self._session is None:
                    await session.commit()
                else:
                    await session.flush()

                await session.refresh(orm)

            except IntegrityError:
                await session.rollback()
                raise

            return _user_to_domain(orm)

    @override
    async def delete(self, user_id: int) -> None:
        await self._exec(lambda sess: sess.execute(delete(UserORM).where(UserORM.id == user_id)))

    @override
    async def update_email(self, user_id: int, new_email: str) -> None:
        async with self._get_session() as session:
            _ = await session.execute(
                update(UserORM).where(UserORM.id == user_id).values(email=new_email),
            )

            await session.flush()
            if self._session is None:
                await session.commit()

            return

    # Read ops
    @override
    async def get(self, user_id: int) -> User | None:
        async with self._get_session() as session:
            res = await session.execute(select(UserORM).where(UserORM.id == user_id))
            row = res.scalar_one_or_none()

            return _user_to_domain(row) if row else None

    @override
    async def get_by_username(self, username: str) -> User | None:
        async with self._get_session() as session:
            res = await session.execute(select(UserORM).where(UserORM.username == username))
            row = res.scalar_one_or_none()

            return _user_to_domain(row) if row else None

    @override
    async def list_all(self) -> list[User]:
        async with self._get_session() as session:
            result = await session.execute(
                select(
                    UserORM.id,
                    UserORM.username,
                    UserORM.email,
                )
            )
            rows = result.all()

            return [User(id=row.id, username=row.username, email=row.email, password_hash="") for row in rows]  # pyright:ignore[reportAny]


@final
class SQLAlchemyProductRepository(BaseSQLAlchemyRepo[ProductORM, Product], AbstractProductRepository):
    def __init__(self, session: AsyncSession | None = None) -> None:
        super().__init__(session, to_domain=_product_to_domain)

    # Write ops
    @override
    async def add(self, product: Product) -> Product:
        orm = ProductORM(name=product.name, description=product.description, price=product.price, stock=product.stock)

        return await self._save(orm, lambda s, o: s.add(o))

    @override
    async def delete(self, product_id: int) -> None:
        await self._exec(lambda sess: sess.execute(delete(ProductORM).where(ProductORM.id == product_id)))

    @override
    async def update_stock(self, product_id: int, new_stock: int) -> None:
        await self._exec(
            lambda sess: sess.execute(update(ProductORM).where(ProductORM.id == product_id).values(stock=new_stock))
        )

    @override
    async def update_price(self, product_id: int, new_price: float) -> None:
        await self._exec(
            lambda sess: sess.execute(update(ProductORM).where(ProductORM.id == product_id).values(price=new_price))
        )

    # Read ops
    @override
    async def get(self, product_id: int) -> Product | None:
        async with self._get_session() as session:
            res = await session.execute(select(ProductORM).where(ProductORM.id == product_id))
            row = res.scalar_one_or_none()

            return _product_to_domain(row) if row else None

    @override
    async def get_by_name(self, name: str) -> Product | None:
        async with self._get_session() as session:
            res = await session.execute(select(ProductORM).where(ProductORM.name == name))
            row = res.scalar_one_or_none()

            return _product_to_domain(row) if row else None

    @override
    async def list_all(self) -> Sequence[Product]:
        async with self._get_session() as session:
            res = await session.execute(select(ProductORM))
            return [_product_to_domain(r) for r in res.scalars().all()]
