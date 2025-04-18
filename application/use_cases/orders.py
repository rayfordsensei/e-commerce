import datetime
from typing import final

from application.use_cases import BaseUseCase
from domain.entities import Order
from domain.repositories import AbstractOrderRepository, AbstractUserRepository


@final
class CreateOrder:
    def __init__(self, orders: AbstractOrderRepository, users: AbstractUserRepository):
        self._orders = orders
        self._users = users

    async def __call__(self, user_id: int, total: float) -> Order:
        # business rules (field verification)
        if await self._users.get(user_id) is None:
            raise ValueError("User does not exist")  # noqa: EM101, TRY003

        order = Order(
            id=None,
            user_id=user_id,
            total_price=total,
            created_at=datetime.datetime.now(tz=datetime.UTC),  # TODO: isoformat?..
        )
        return await self._orders.add(order)


@final
class ListOrders:
    def __init__(self, orders: AbstractOrderRepository):
        self._orders = orders

    async def __call__(self, user_id: int | None = None) -> list[Order]:
        if user_id is None:
            return list(await self._orders.list_all())
        return list(await self._orders.list_for_user(user_id))


@final
class GetOrder:
    def __init__(self, orders: AbstractOrderRepository):
        self._orders = orders

    async def __call__(self, order_id: int) -> Order | None:
        return await self._orders.get(order_id)


@final
class DeleteOrder:
    def __init__(self, orders: AbstractOrderRepository):
        self._orders = orders

    async def __call__(self, order_id: int) -> None:
        await self._orders.delete(order_id)


@final
class UpdateOrderFields:
    def __init__(self, orders: AbstractOrderRepository):
        self._orders = orders

    async def __call__(self, order_id: int, total_price: float | None) -> None:
        if total_price is None:
            raise ValueError("total_price is required.")  # noqa: EM101, TRY003

        await self._orders.update_total(order_id, total_price)
