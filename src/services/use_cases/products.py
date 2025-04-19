from typing import final

from domain.products.entities import Product
from domain.products.repositories import AbstractProductRepository
from services.use_cases import BaseUseCase


@final
class CreateProduct(BaseUseCase[AbstractProductRepository]):
    async def __call__(self, name: str, description: str, price: float, stock: int) -> Product:
        # Business rules (field verification)
        if await self._repo.get_by_name(name):
            raise ValueError("Product name already exists")  # noqa: EM101, TRY003

        product = Product(id=None, name=name, description=description, price=price, stock=stock)
        return await self._repo.add(product)


@final
class ListProducts(BaseUseCase[AbstractProductRepository]):
    async def __call__(self) -> list[Product]:
        return list(await self._repo.list_all())


@final
class GetProduct(BaseUseCase[AbstractProductRepository]):
    async def __call__(self, product_id: int) -> Product | None:
        return await self._repo.get(product_id)


@final
class DeleteProduct(BaseUseCase[AbstractProductRepository]):
    async def __call__(self, product_id: int) -> None:
        await self._repo.delete(product_id)


@final
class UpdateProductFields(BaseUseCase[AbstractProductRepository]):
    async def __call__(self, product_id: int, price: float | None, stock: int | None) -> None:
        if price is None and stock is None:
            raise ValueError("No valid fields to update")  # noqa: EM101, TRY003

        if price is not None:
            await self._repo.update_price(product_id, price)

        if stock is not None:
            await self._repo.update_stock(product_id, stock)
