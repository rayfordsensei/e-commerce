import logging
from typing import Any, final

import falcon
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from db import get_db
from models import Order, User

logger = logging.getLogger(__name__)


@final
class OrderResource:
    async def on_get(self, req: falcon.Request, resp: falcon.Response, order_id: int | None = None) -> None:  # noqa: PLR6301
        """Retrieve all orders or a single order by ID."""
        _ = req

        try:
            async with get_db() as session:
                if order_id is None:
                    q = select(Order)
                    result = await session.execute(q)
                    orders = result.scalars().all()
                    resp.media = [
                        {
                            "id": o.id,
                            "user_id": o.user_id,
                            "total_price": o.total_price,
                            "created_at": o.created_at_iso,
                        }
                        for o in orders
                    ]
                    return

                q = select(Order).where(Order.id == order_id)
                result = await session.execute(q)
                order = result.scalar_one_or_none()

                if not order:
                    resp.status = falcon.HTTP_404
                    resp.media = {"error": f"Order with id={order_id} not found."}
                    return

                resp.media = {
                    "id": order.id,
                    "user_id": order.user_id,
                    "total_price": order.total_price,
                    "created_at": order.created_at_iso,
                }

        except SQLAlchemyError:
            logger.exception("Database error occurred while retrieving orders.")
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Database error occurred"}
        except Exception:
            logger.exception("Unexpected error during order retrieval.")
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}

    async def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:  # noqa: PLR6301
        """Create a new order."""
        data: dict[str, Any] = await req.get_media()  # pyright:ignore[reportExplicitAny, reportAny]
        required_fields = ["user_id", "total_price"]
        missing = [field for field in required_fields if not data.get(field)]
        if missing:
            resp.status = falcon.HTTP_400
            resp.media = {"error": f"Missing required fields: {', '.join(missing)}"}
            return

        user_id = data["user_id"]  # pyright:ignore[reportAny]
        total_price = data["total_price"]  # pyright:ignore[reportAny]

        try:
            async with get_db() as session:
                user_q = select(User).where(User.id == user_id)  # pyright:ignore[reportAny]
                user_result = await session.execute(user_q)
                user = user_result.scalar_one_or_none()
                if not user:
                    resp.status = falcon.HTTP_400
                    resp.media = {"error": f"User with id={user_id} does not exist."}
                    return

                new_order = Order(
                    user_id=user_id,
                    total_price=total_price,
                )
                session.add(new_order)
                await session.commit()

                resp.status = falcon.HTTP_201
                resp.media = {
                    "id": new_order.id,
                    "user_id": new_order.user_id,
                    "total_price": new_order.total_price,
                    "created_at": new_order.created_at_iso,
                }

        except IntegrityError:
            logger.exception("IntegrityError while creating order.")
            resp.status = falcon.HTTP_409
            resp.media = {"error": "Order creation conflict (IntegrityError)."}
        except SQLAlchemyError:
            logger.exception("Database error during order creation.")
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Database error occurred"}
        except Exception:
            logger.exception("Unexpected error during order creation.")
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}

    async def on_delete(self, req: falcon.Request, resp: falcon.Response, order_id: int) -> None:  # noqa: PLR6301
        """Delete an existing order by ID."""
        _ = req

        try:
            async with get_db() as session:
                q = select(Order).where(Order.id == order_id)
                result = await session.execute(q)
                order = result.scalar_one_or_none()

                if not order:
                    resp.status = falcon.HTTP_404
                    resp.media = {"error": f"Order with id={order_id} not found."}
                    return

                await session.delete(order)
                await session.commit()
                resp.status = falcon.HTTP_204

        except SQLAlchemyError:
            logger.exception("Database error during order deletion.")
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Database error occurred during deletion"}
        except Exception:
            logger.exception("Unexpected error during order deletion.")
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}
