from typing import final

from domain.entities import Product
from domain.repositories import AbstractProductRepository


@final
class CreateProduct:
    def __init__(self, products: AbstractProductRepository) -> None:
        self._products = products

    async def __call__(self, name: str, description: str, price: float, stock: int) -> Product:
        # Business rules (field verification)
        if await self._products.get_by_name(name):
            raise ValueError("Product name already exists")  # noqa: EM101, TRY003

        product = Product(id=None, name=name, description=description, price=price, stock=stock)
        return await self._products.add(product)


@final
class ListProducts:
    def __init__(self, products: AbstractProductRepository) -> None:
        self._products = products

    async def __call__(self) -> list[Product]:
        return list(await self._products.list_all())


@final
class GetProduct:
    def __init__(self, products: AbstractProductRepository) -> None:
        self._products = products

    async def __call__(self, product_id: int) -> Product | None:
        return await self._products.get(product_id)


@final
class DeleteProduct:
    def __init__(self, products: AbstractProductRepository) -> None:
        self._products = products

    async def __call__(self, product_id: int) -> None:
        await self._products.delete(product_id)


@final
class UpdateProductFields:
    def __init__(self, products: AbstractProductRepository):
        self._products = products

    async def __call__(self, product_id: int, price: float | None, stock: int | None) -> None:
        if price is None and stock is None:
            raise ValueError("No valid fields to update")  # noqa: EM101, TRY003

        if price is not None:
            await self._products.update_price(product_id, price)

        if stock is not None:
            await self._products.update_stock(product_id, stock)
