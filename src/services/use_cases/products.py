from collections.abc import Callable
from typing import final

from sqlalchemy.exc import IntegrityError

from domain.products.entities import Product
from domain.products.repositories import AbstractProductRepository
from infrastructure.databases.unit_of_work import UnitOfWork
from services.use_cases import BaseUseCase


@final
class CreateProduct:
    _uow_factory: Callable[[], UnitOfWork]

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def __call__(self, name: str, description: str, price: float, stock: int) -> Product:
        async with self._uow_factory() as uow:
            assert uow.products is not None, "UnitOfWork.products not initialised"

            if await uow.products.get_by_name(name):
                raise ValueError("Product name already exists")  # noqa: EM101, TRY003

            try:
                return await uow.products.add(
                    Product(id=None, name=name, description=description, price=price, stock=stock)
                )

            except IntegrityError:
                raise ValueError("Product name already exists") from None  # noqa: EM101, TRY003


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
            raise ValueError("No valid fields to update")  # noqa: EM101, TRY003

        async with self._uow_factory() as uow:
            assert uow.products is not None

            if price is not None:
                await uow.products.update_price(product_id, price)

            if stock is not None:
                await uow.products.update_stock(product_id, stock)
