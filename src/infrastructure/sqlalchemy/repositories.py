from collections.abc import Callable, Sequence
from contextlib import asynccontextmanager, nullcontext
from inspect import isawaitable
from typing import Any, TypeVar, final, override

import falcon
from sqlalchemy import Select, delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

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
    return Product(
        id=row.id, name=row.name, description=row.description, price=row.price, stock=row.stock, owner_id=row.owner_id
    )


def _order_to_domain(row: OrderORM) -> Order:
    return Order(id=row.id, user_id=row.user_id, total_price=row.total_price, created_at=row.created_at)


class BaseSQLAlchemyRepo[Entity, Domain]:  # noqa: B903
    def __init__(self, session: AsyncSession | None, to_domain: Callable[[Entity], Domain]):
        self._session: AsyncSession | None = session
        self._to_domain: Callable[[Entity], Domain] = to_domain

    @staticmethod
    async def _maybe_await(value: Any) -> Any:  # noqa: ANN401
        if isawaitable(value):
            return await value
        return value

    @asynccontextmanager
    async def _get_session(self):
        if self._session is not None:
            async with nullcontext(self._session):
                yield self._session
            return

        async with AsyncSessionLocal() as session:
            yield session

    async def _save(self, orm: Entity, work: Callable[[AsyncSession, Entity], Any]) -> Domain:
        if self._session is not None:
            sess = self._session
            await self._maybe_await(work(sess, orm))

            try:
                await sess.flush()

            except IntegrityError:
                await sess.rollback()
                raise

            await sess.refresh(orm)
            return self._to_domain(orm)

        async with AsyncSessionLocal() as sess:
            await self._maybe_await(work(sess, orm))

            try:
                await sess.flush()
                await sess.commit()

            except IntegrityError:
                await sess.rollback()
                raise

            await sess.refresh(orm)
            return self._to_domain(orm)

    async def _exec(self, work: Callable[[AsyncSession], Any]):
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
        stmt: Select[Any],
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
        stmt: Select[Any],
        *,
        mapper: Callable[[Entity], Domain] | None = None,
    ) -> Many[Domain]:
        mapper = mapper or self._to_domain
        async with self._get_session() as s:
            res = await s.execute(stmt)
            return [mapper(r) for r in res.scalars().all()]


@final
class SQLAlchemyOrderRepository(BaseSQLAlchemyRepo[OrderORM, Order], AbstractOrderRepository):
    def __init__(self, session: AsyncSession | None = None) -> None:
        super().__init__(session, to_domain=_order_to_domain)

    @override
    async def count_all(self) -> int:
        async with AsyncSessionLocal() as s:
            stmt = select(func.count()).select_from(OrderORM)
            return (await s.execute(stmt)).scalar_one()

    @override
    async def count_for_user(self, user_id: int) -> int:
        async with AsyncSessionLocal() as s:
            stmt = select(func.count()).select_from(OrderORM).where(OrderORM.user_id == user_id)
            return (await s.execute(stmt)).scalar_one()

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
        stmt = select(OrderORM).where(OrderORM.id == order_id)
        return await self._fetch_one(stmt)

    @override
    async def list_for_user(self, user_id: int, *, offset: int = 0, limit: int | None = None) -> Sequence[Order]:
        stmt = select(OrderORM).where(OrderORM.user_id == user_id).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        return await self._fetch_many(stmt)

    @override
    async def list_all(self, *, offset: int = 0, limit: int | None = None) -> Sequence[Order]:
        stmt = select(OrderORM).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        return await self._fetch_many(stmt)


@final
class SQLAlchemyUserRepository(BaseSQLAlchemyRepo[UserORM, User], AbstractUserRepository):
    def __init__(self, session: AsyncSession | None = None) -> None:
        super().__init__(session, to_domain=_user_to_domain)

    @override
    async def count_all(self, *, username_contains: str | None = None, email_contains: str | None = None) -> int:
        stmt = select(func.count()).select_from(UserORM)

        if username_contains:
            stmt = stmt.where(UserORM.username.ilike(f"%{username_contains}%"))

        if email_contains:
            stmt = stmt.where(UserORM.email.ilike(f"%{email_contains}%"))

        async with AsyncSessionLocal() as sess:
            return (await sess.execute(stmt)).scalar_one()

    #  Write ops
    @override
    async def add(self, user: User) -> User:
        async with self._get_session() as sess:
            existing = await sess.execute(select(UserORM).where(UserORM.username == user.username))
            row: UserORM | None = existing.scalar_one_or_none()

            if row:
                return _user_to_domain(row)

        orm = UserORM(username=user.username, email=user.email, password=user.password_hash)
        return await self._save(orm, lambda sess, o: sess.add(o))

    @override
    async def delete(self, user_id: int) -> None:
        await self._exec(lambda sess: sess.execute(delete(UserORM).where(UserORM.id == user_id)))

    @override
    async def update_email(self, user_id: int, new_email: str) -> None:
        await self._exec(lambda s: s.execute(update(UserORM).where(UserORM.id == user_id).values(email=new_email)))

    @override
    async def update_username(self, user_id: int, new_username: str) -> None:
        await self._exec(
            lambda s: s.execute(update(UserORM).where(UserORM.id == user_id).values(username=new_username))
        )

    # Read ops
    @override
    async def get(self, user_id: int) -> User | None:
        stmt = select(UserORM).where(UserORM.id == user_id)
        return await self._fetch_one(stmt)

    @override
    async def get_by_username(self, username: str) -> User | None:
        stmt = select(UserORM).where(UserORM.username == username)
        return await self._fetch_one(stmt)

    @override
    async def list_all(
        self,
        *,
        offset: int = 0,
        limit: int | None = None,
        username_contains: str | None = None,
        email_contains: str | None = None,
    ) -> list[User]:
        stmt = select(UserORM).order_by(UserORM.id)

        if username_contains:
            stmt = stmt.where(UserORM.username.ilike(f"%{username_contains}%"))

        if email_contains:
            stmt = stmt.where(UserORM.email.ilike(f"%{email_contains}%"))

        stmt = stmt.offset(offset)

        if limit is not None:
            stmt = stmt.limit(limit)

        return await self._fetch_many(stmt)


@final
class SQLAlchemyProductRepository(BaseSQLAlchemyRepo[ProductORM, Product], AbstractProductRepository):
    def __init__(self, session: AsyncSession | None = None) -> None:
        super().__init__(session, to_domain=_product_to_domain)

    @override
    async def count_all(
        self, *, name_contains: str | None = None, min_price: float | None = None, max_price: float | None = None
    ) -> int:
        stmt = select(func.count()).select_from(ProductORM)

        if name_contains:
            stmt = stmt.where(ProductORM.name.ilike(f"%{name_contains}%"))

        if min_price is not None:
            stmt = stmt.where(ProductORM.price >= min_price)

        if max_price is not None:
            stmt = stmt.where(ProductORM.price <= max_price)

        async with AsyncSessionLocal() as sess:
            return (await sess.execute(stmt)).scalar_one()

    # Write ops
    @override
    async def add(self, product: Product) -> Product:
        async with self._get_session() as s:
            res = await s.execute(select(ProductORM).where(func.lower(ProductORM.name) == product.name.lower()))
            existing: ProductORM | None = res.scalar_one_or_none()

            if existing:
                if existing.name == product.name:
                    return _product_to_domain(existing)
                raise ValueError("Duplicate product name")  # noqa: EM101, TRY003

        orm = ProductORM(
            name=product.name,
            description=product.description,
            price=product.price,
            stock=product.stock,
        )
        return await self._save(orm, lambda sess, o: sess.add(o))

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
        stmt = select(ProductORM).where(ProductORM.id == product_id)
        return await self._fetch_one(stmt)

    @override
    async def get_by_name(self, name: str) -> Product | None:
        stmt = select(ProductORM).where(ProductORM.name == name)
        return await self._fetch_one(stmt)

    @override
    async def list_all(
        self,
        *,
        offset: int = 0,
        limit: int | None = None,
        name_contains: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
    ) -> Sequence[Product]:
        stmt = select(ProductORM)
        if name_contains:
            stmt = stmt.where(ProductORM.name.ilike(f"%{name_contains}%"))

        if min_price is not None:
            stmt = stmt.where(ProductORM.price >= min_price)

        if max_price is not None:
            stmt = stmt.where(ProductORM.price <= max_price)

        stmt = stmt.order_by(func.lower(ProductORM.name))
        stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        return await self._fetch_many(stmt)
