import logging
from typing import Any, final

import falcon
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

import utils
from db import get_db
from models import Product
from schemas.product_schemas import ProductCreate, ProductOut

logger = logging.getLogger("app." + __name__)


@final
class ProductResource:
    async def on_get(self, req: falcon.Request, resp: falcon.Response, product_id: int | None = None) -> None:  # noqa: PLR6301
        """Retrieve all products or a single product by ID."""
        _ = req

        try:
            async with get_db() as session:
                if product_id is None:
                    q = select(Product)
                    result = await session.execute(q)
                    products = result.scalars().all()

                    resp.media = [
                        ProductOut(
                            id=p.id,
                            name=p.name,
                            description=p.description,
                            price=p.price,
                            stock=p.stock,
                        ).model_dump()
                        for p in products
                    ]
                    return None

                q = select(Product).where(Product.id == product_id)
                result = await session.execute(q)
                product = result.scalar_one_or_none()

                if not product:
                    return utils.error_response(resp, falcon.HTTP_404, f"Product with id={product_id} does not exist.")

                resp.media = ProductOut(
                    id=product.id,
                    name=product.name,
                    description=product.description,
                    price=product.price,
                    stock=product.stock,
                ).model_dump()

        except SQLAlchemyError:
            logger.exception("Database error occurred while retrieving products.")
            utils.error_response(resp, falcon.HTTP_500, "Database error occured")
        except Exception:
            logger.exception("Unexpected error during product retrieval.")
            utils.error_response(resp, falcon.HTTP_500, "Internal server error")

    async def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:  # noqa: PLR6301
        """Create a new product."""
        try:
            data: dict[str, Any] = await req.get_media()  # pyright:ignore[reportExplicitAny, reportAny]
            product_in = ProductCreate(**data)  # pyright:ignore[reportAny]

        except ValidationError as e:
            logger.exception("Validation error while creating product.")
            msg = "; ".join(f"{' -> '.join(map(str, error['loc']))}: {error['msg']}" for error in e.errors())

            return utils.error_response(resp, falcon.HTTP_400, msg)

        try:
            async with get_db() as session:
                new_product = Product(
                    name=product_in.name,
                    description=product_in.description,
                    price=product_in.price,
                    stock=product_in.stock,
                )
                session.add(new_product)
                await session.commit()

                resp.status = falcon.HTTP_201
                resp.media = ProductOut(
                    id=new_product.id,
                    name=new_product.name,
                    description=new_product.description,
                    price=new_product.price,
                    stock=new_product.stock,
                ).model_dump()

        except IntegrityError:
            logger.exception("IntegrityError while creating product.")
            utils.error_response(resp, falcon.HTTP_409, "Product creation conflict (IntegrityError).")
        except SQLAlchemyError:
            logger.exception("Database error during product creation.")
            utils.error_response(resp, falcon.HTTP_500, "Database error occurred")
        except Exception:
            logger.exception("Unexpected error during product creation.")
            utils.error_response(resp, falcon.HTTP_500, "Internal server error")

    async def on_delete(self, req: falcon.Request, resp: falcon.Response, product_id: int) -> None:  # noqa: PLR6301
        """Delete an existing product by ID."""
        _ = req

        try:
            async with get_db() as session:
                q = select(Product).where(Product.id == product_id)
                result = await session.execute(q)
                product = result.scalar_one_or_none()

                if not product:
                    return utils.error_response(resp, falcon.HTTP_404, f"Product with id={product_id} not found.")

                await session.delete(product)
                await session.commit()
                resp.status = falcon.HTTP_204

        except SQLAlchemyError:
            logger.exception("Database error during product deletion.")
            utils.error_response(resp, falcon.HTTP_500, "Database error occurred during deletion")
        except Exception:
            logger.exception("Unexpected error during product deletion.")
            utils.error_response(resp, falcon.HTTP_500, "Internal server error")
