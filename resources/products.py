import logging
from typing import Any, final

import falcon
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from db import get_db
from models import Product

logger = logging.getLogger(__name__)


@final
class ProductResource:
    async def on_get(self, req: falcon.Request, resp: falcon.Response, product_id: int | None = None) -> None:  # pyright:ignore[reportUnusedParameter]  # noqa: ARG002, PLR6301
        """Retrieve all products or a single product by ID."""
        try:  # TODO: pagination + filtering
            async with get_db() as session:
                if product_id is None:
                    q = select(Product)
                    result = await session.execute(q)
                    products = result.scalars().all()
                    resp.media = [
                        {
                            "id": p.id,
                            "name": p.name,
                            "description": p.description,
                            "price": p.price,
                            "stock": p.stock,
                        }
                        for p in products
                    ]
                    return

                q = select(Product).where(Product.id == product_id)
                result = await session.execute(q)
                product = result.scalar_one_or_none()

                if not product:
                    resp.status = falcon.HTTP_404
                    resp.media = {"error": f"Product with id={product_id} not found."}
                    return

                resp.media = {
                    "id": product.id,
                    "name": product.name,
                    "description": product.description,
                    "price": product.price,
                    "stock": product.stock,
                }

        except SQLAlchemyError:
            logger.exception("Database error occurred while retrieving products.")
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Database error occurred"}
        except Exception:
            logger.exception("Unexpected error during product retrieval.")
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}

    async def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:  # noqa: PLR6301
        """Create a new product."""
        data: dict[str, Any] = await req.get_media()  # pyright:ignore[reportExplicitAny, reportAny] # TODO: non-ideal
        required_fields = ["name", "price", "stock"]
        missing = [field for field in required_fields if not data.get(field)]
        if missing:
            resp.status = falcon.HTTP_400
            resp.media = {"error": f"Missing required fields: {', '.join(missing)}"}
            return

        name = data["name"]  # pyright:ignore[reportAny] # TODO: Comes from data being a dict with Any.
        description = data.get("description") or ""
        price = data["price"]  # pyright:ignore[reportAny] # TODO: Comes from data being a dict with Any.
        stock = data["stock"]  # pyright:ignore[reportAny] # TODO: Comes from data being a dict with Any.

        try:
            async with get_db() as session:
                new_product = Product(
                    name=name,
                    description=description,
                    price=price,
                    stock=stock,
                )
                session.add(new_product)
                await session.commit()

                resp.status = falcon.HTTP_201
                resp.media = {
                    "id": new_product.id,
                    "name": new_product.name,
                    "description": new_product.description,
                    "price": new_product.price,
                    "stock": new_product.stock,
                }

        except IntegrityError:
            logger.exception("IntegrityError while creating product.")
            resp.status = falcon.HTTP_409
            resp.media = {"error": "Product creation conflict (IntegrityError)."}
        except SQLAlchemyError:
            logger.exception("Database error during product creation.")
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Database error occurred"}
        except Exception:
            logger.exception("Unexpected error during product creation.")
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}

    async def on_delete(self, req: falcon.Request, resp: falcon.Response, product_id: int) -> None:  # pyright:ignore[reportUnusedParameter]  # noqa: ARG002, PLR6301
        """Delete an existing product by ID."""
        try:
            async with get_db() as session:
                q = select(Product).where(Product.id == product_id)
                result = await session.execute(q)
                product = result.scalar_one_or_none()

                if not product:
                    resp.status = falcon.HTTP_404
                    resp.media = {"error": f"Product with id={product_id} not found."}
                    return

                await session.delete(product)
                await session.commit()
                resp.status = falcon.HTTP_204

        except SQLAlchemyError:
            logger.exception("Database error during product deletion.")
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Database error occurred during deletion"}
        except Exception:
            logger.exception("Unexpected error during product deletion.")
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}
