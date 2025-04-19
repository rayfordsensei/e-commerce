import abc
from collections.abc import Sequence

from .entities import Order


class AbstractOrderRepository(abc.ABC):
    # Write ops
    @abc.abstractmethod
    async def add(self, order: Order) -> Order:
        pass

    @abc.abstractmethod
    async def delete(self, order_id: int) -> None:
        pass

    @abc.abstractmethod
    async def update_total(self, order_id: int, new_total: float) -> None:
        pass

    # Read ops
    @abc.abstractmethod
    async def get(self, order_id: int) -> Order | None:
        pass

    @abc.abstractmethod
    async def list_for_user(self, user_id: int) -> Sequence[Order]:
        pass

    @abc.abstractmethod
    async def list_all(self) -> Sequence[Order]:
        pass
