from collections.abc import Callable
from typing import final

import falcon

from domain.products.entities import Product
from domain.products.repositories import AbstractProductRepository
from infrastructure.databases.unit_of_work import UnitOfWork
from services.use_cases import BaseUseCase


@final
class CreateProduct:
    _uow_factory: Callable[[], UnitOfWork]

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def __call__(
        self, name: str, description: str, price: float, stock: int, owner_id: int | None = None
    ) -> Product:
        if not name or not name.strip():
            raise ValueError("name must be at least 1 character")  # noqa: EM101, TRY003

        if price < 0:
            raise ValueError("price must be ≥ 0")  # noqa: EM101, TRY003

        if stock < 0:
            raise ValueError("stock must be ≥ 0")  # noqa: EM101, TRY003

        async with self._uow_factory() as uow:
            assert uow.products is not None, "UnitOfWork.products not initialised"

            return await uow.products.add(
                Product(id=None, name=name, description=description, price=price, stock=stock, owner_id=owner_id)
            )


@final
class ListProducts(BaseUseCase[AbstractProductRepository]):
    async def __call__(self) -> list[Product]:
        return list(await self._repo.list_all())


@final
class GetProduct(BaseUseCase[AbstractProductRepository]):
    async def __call__(self, product_id: int) -> Product | None:
        return await self._repo.get(product_id)


@final
class DeleteProduct:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def __call__(self, product_id: int) -> None:
        async with self._uow_factory() as uow:
            assert uow.products is not None
            await uow.products.delete(product_id)


@final
class UpdateProductFields:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def __call__(self, product_id: int, price: float | None, stock: int | None) -> None:
        if price is None and stock is None:
            raise ValueError("At least one of 'price' or 'stock' must be provided")  # noqa: EM101, TRY003

        async with self._uow_factory() as uow:
            assert uow.products is not None

            existing = await uow.products.get(product_id)

            if existing is None:
                raise falcon.HTTPNotFound(description="Product not found")

            if price is not None:
                await uow.products.update_price(product_id, price)

            if stock is not None:
                await uow.products.update_stock(product_id, stock)
