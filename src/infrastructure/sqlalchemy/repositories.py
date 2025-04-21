from collections.abc import Sequence
from typing import override

from sqlalchemy import delete, select, update

from domain.orders.entities import Order
from domain.orders.repositories import AbstractOrderRepository
from domain.products.entities import Product
from domain.products.repositories import AbstractProductRepository
from domain.users.entities import User
from domain.users.repositories import AbstractUserRepository
from infrastructure.databases.db import get_db
from infrastructure.sqlalchemy.models import Order as OrderORM
from infrastructure.sqlalchemy.models import Product as ProductORM
from infrastructure.sqlalchemy.models import User as UserORM


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


class SQLAlchemyOrderRepository(AbstractOrderRepository):
    """Infrastructure adapter that fulfils the domain contract."""

    #  Write ops
    @override
    async def add(self, order: Order) -> Order:
        async with get_db() as session:
            orm = OrderORM(
                user_id=order.user_id,
                total_price=order.total_price,
                created_at=order.created_at,
            )
            session.add(orm)
            await session.commit()
            await session.refresh(orm)  # get generated id
            return _order_to_domain(orm)

    @override
    async def delete(self, order_id: int) -> None:
        async with get_db() as session:
            _ = await session.execute(delete(OrderORM).where(OrderORM.id == order_id))
            await session.commit()

    @override
    async def update_total(self, order_id: int, new_total: float) -> None:
        async with get_db() as session:
            _ = await session.execute(
                update(OrderORM).where(OrderORM.id == order_id).values(total_price=new_total),
            )
            await session.commit()

    # Read ops
    @override
    async def get(self, order_id: int) -> Order | None:
        async with get_db() as session:
            res = await session.execute(select(OrderORM).where(OrderORM.id == order_id))
            row = res.scalar_one_or_none()
            return _order_to_domain(row) if row else None

    @override
    async def list_for_user(self, user_id: int) -> Sequence[Order]:
        async with get_db() as session:
            res = await session.execute(select(OrderORM).where(OrderORM.user_id == user_id))
            return [_order_to_domain(r) for r in res.scalars().all()]

    @override
    async def list_all(self) -> Sequence[Order]:
        async with get_db() as session:
            res = await session.execute(select(OrderORM))
            return [_order_to_domain(r) for r in res.scalars().all()]


class SQLAlchemyUserRepository(AbstractUserRepository):
    #  Write ops
    @override
    async def add(self, user: User) -> User:
        async with get_db() as session:
            orm = UserORM(username=user.username, email=user.email, password=user.password_hash)
            session.add(orm)
            await session.commit()
            await session.refresh(orm)
            return _user_to_domain(orm)

    @override
    async def delete(self, user_id: int) -> None:
        async with get_db() as session:
            _ = await session.execute(delete(UserORM).where(UserORM.id == user_id))
            await session.commit()

    @override
    async def update_email(self, user_id: int, new_email: str) -> None:
        async with get_db() as session:
            _ = await session.execute(
                update(UserORM).where(UserORM.id == user_id).values(email=new_email),
            )
            await session.commit()

    # Read ops
    @override
    async def get(self, user_id: int) -> User | None:
        async with get_db() as session:
            res = await session.execute(select(UserORM).where(UserORM.id == user_id))
            row = res.scalar_one_or_none()
            return _user_to_domain(row) if row else None

    @override
    async def get_by_username(self, username: str) -> User | None:
        async with get_db() as session:
            res = await session.execute(select(UserORM).where(UserORM.username == username))
            row = res.scalar_one_or_none()
            return _user_to_domain(row) if row else None

    @override
    async def list_all(self) -> list[User]:
        async with get_db() as session:
            result = await session.execute(
                select(
                    UserORM.id,
                    UserORM.username,
                    UserORM.email,
                )
            )
            rows = result.all()

        return [User(id=row.id, username=row.username, email=row.email, password_hash="") for row in rows]  # pyright:ignore[reportAny]


class SQLAlchemyProductRepository(AbstractProductRepository):
    # Write ops
    @override
    async def add(self, product: Product) -> Product:
        async with get_db() as session:
            orm = ProductORM(
                name=product.name,
                description=product.description,
                price=product.price,
                stock=product.stock,
            )
            session.add(orm)
            await session.commit()
            await session.refresh(orm)
            return _product_to_domain(orm)

    @override
    async def delete(self, product_id: int) -> None:
        async with get_db() as session:
            _ = await session.execute(delete(ProductORM).where(ProductORM.id == product_id))
            await session.commit()

    @override
    async def update_stock(self, product_id: int, new_stock: int) -> None:
        async with get_db() as session:
            _ = await session.execute(
                update(ProductORM).where(ProductORM.id == product_id).values(stock=new_stock),
            )
            await session.commit()

    @override
    async def update_price(self, product_id: int, new_price: float) -> None:
        async with get_db() as session:
            _ = await session.execute(
                update(ProductORM).where(ProductORM.id == product_id).values(price=new_price),
            )
            await session.commit()

    # Read ops
    @override
    async def get(self, product_id: int) -> Product | None:
        async with get_db() as session:
            res = await session.execute(select(ProductORM).where(ProductORM.id == product_id))
            row = res.scalar_one_or_none()
            return _product_to_domain(row) if row else None

    @override
    async def get_by_name(self, name: str) -> Product | None:
        async with get_db() as session:
            res = await session.execute(select(ProductORM).where(ProductORM.name == name))
            row = res.scalar_one_or_none()
            return _product_to_domain(row) if row else None

    @override
    async def list_all(self) -> Sequence[Product]:
        async with get_db() as session:
            res = await session.execute(select(ProductORM))
            return [_product_to_domain(r) for r in res.scalars().all()]
