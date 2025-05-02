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
    async def list_all(
        self,
        *,
        offset: int = 0,
        limit: int | None = None,
        name_contains: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
    ) -> Sequence[Product]:
        pass

    @abc.abstractmethod
    async def count_all(
        self, *, name_contains: str | None = None, min_price: float | None = None, max_price: float | None = None
    ) -> int:
        pass
