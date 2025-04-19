import datetime
from dataclasses import dataclass
from typing import final

from domain.orders.entities import Order
from domain.orders.repositories import AbstractOrderRepository
from domain.users.repositories import AbstractUserRepository
from services.use_cases import BaseUseCase


@dataclass(slots=True)
class CreateOrder(BaseUseCase[AbstractUserRepository]):
    _orders: AbstractOrderRepository

    async def __call__(self, user_id: int, total: float) -> Order:
        # business rules (field verification)
        if await self._repo.get(user_id) is None:
            raise ValueError("User does not exist")  # noqa: EM101, TRY003

        order = Order(
            id=None,
            user_id=user_id,
            total_price=total,
            created_at=datetime.datetime.now(tz=datetime.UTC),  # TODO: isoformat?..
        )
        return await self._orders.add(order)


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
class DeleteOrder(BaseUseCase[AbstractOrderRepository]):
    async def __call__(self, order_id: int) -> None:
        await self._repo.delete(order_id)


@final
class UpdateOrderFields(BaseUseCase[AbstractOrderRepository]):
    async def __call__(self, order_id: int, total_price: float | None) -> None:
        if total_price is None:
            raise ValueError("total_price is required.")  # noqa: EM101, TRY003

        await self._repo.update_total(order_id, total_price)
