import abc
from collections.abc import Sequence

from .entities import Order, Product, User


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


class AbstractProductRepository(abc.ABC):
    # Write ops
    @abc.abstractmethod
    async def add(self, product: Product) -> Product:
        pass

    @abc.abstractmethod
    async def delete(self, product_id: int) -> None:
        pass

    @abc.abstractmethod
    async def update_stock(self, product_id: int, new_stock: int) -> None:
        pass

    @abc.abstractmethod
    async def update_price(self, product_id: int, new_price: float) -> None:
        pass

    # Read ops
    @abc.abstractmethod
    async def get(self, product_id: int) -> Product | None:
        pass

    @abc.abstractmethod
    async def get_by_name(self, name: str) -> Product | None:
        pass

    @abc.abstractmethod
    async def list_all(self) -> Sequence[Product]:
        pass


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

    # Read ops
    @abc.abstractmethod
    async def get(self, user_id: int) -> User | None:
        pass

    @abc.abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        pass

    @abc.abstractmethod
    async def list_all(self) -> Sequence[User]:
        pass
