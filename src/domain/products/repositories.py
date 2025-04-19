import abc
from collections.abc import Sequence

from .entities import Product


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
