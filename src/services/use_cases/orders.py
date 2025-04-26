from collections.abc import Callable
from typing import final

import falcon

from domain.orders.entities import Order
from domain.orders.repositories import AbstractOrderRepository
from infrastructure.databases.unit_of_work import UnitOfWork
from services.use_cases import BaseUseCase
from services.use_cases.access_control import assert_owner


class CreateOrder:
    _uow_factory: Callable[[], UnitOfWork]

    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self._uow_factory = uow_factory

    async def __call__(self, user_id: int, total: float) -> Order:
        async with self._uow_factory() as uow:
            assert uow.users is not None, "UnitOfWork.users not initialized"

            if await uow.users.get(user_id) is None:
                raise falcon.HTTPNotFound(description="User not found")

            order = Order(id=None, user_id=user_id, total_price=total)
            assert uow.orders is not None, "UnitOfWork.orders not initialized"

            return await uow.orders.add(order)


@final
class ListOrders(BaseUseCase[AbstractOrderRepository]):
    async def __call__(self, user_id: int | None = None) -> list[Order]:
        if user_id is None:
            return list(await self._repo.list_all())
        return list(await self._repo.list_for_user(user_id))


@final
class GetOrder(BaseUseCase[AbstractOrderRepository]):
    async def __call__(self, order_id: int) -> Order | None:
        return await self._repo.get(order_id)


@final
class DeleteOrder:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def __call__(self, order_id: int, acting_user: int) -> None:
        async with self._uow_factory() as uow:
            assert uow.orders is not None

            order = await uow.orders.get(order_id)
            if order is None:
                raise falcon.HTTPNotFound(description="Order not found")

            assert_owner(order.user_id, acting_user)
            await uow.orders.delete(order_id)


@final
class UpdateOrderFields:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def __call__(self, order_id: int, total_price: float | None) -> None:
        if total_price is None:
            raise ValueError("total_price is required.")  # noqa: EM101, TRY003

        async with self._uow_factory() as uow:
            assert uow.orders is not None

            order = await uow.orders.get(order_id)
            if order is None:
                raise falcon.HTTPNotFound(description="Order not found")

            await uow.orders.update_total(order_id, total_price)
