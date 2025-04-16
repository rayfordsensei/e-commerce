import logging
from typing import Any, final

import falcon
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

import utils
from db import get_db
from models import Order, User
from schemas.order_schemas import OrderCreate, OrderOut

logger = logging.getLogger("app." + __name__)


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
                        OrderOut(
                            id=o.id,
                            user_id=o.user_id,
                            total_price=o.total_price,
                            created_at=o.created_at_iso,
                        )
                        for o in orders
                    ]
                    return None

                q = select(Order).where(Order.id == order_id)
                result = await session.execute(q)
                order = result.scalar_one_or_none()

                if not order:
                    return utils.error_response(resp, falcon.HTTP_404, f"Order with id={order_id} not found.")

                resp.media = OrderOut(
                    id=order.id,
                    user_id=order.user_id,
                    total_price=order.total_price,
                    created_at=order.created_at_iso,
                )

        except SQLAlchemyError:
            logger.exception("Database error occurred while retrieving orders.")
            utils.error_response(resp, falcon.HTTP_500, "Database error occurred")
        except Exception:
            logger.exception("Unexpected error during order retrieval.")
            utils.error_response(resp, falcon.HTTP_500, "Internal server error")

    async def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:  # noqa: PLR6301
        """Create a new order."""
        try:
            data: dict[str, Any] = await req.get_media()  # pyright:ignore[reportExplicitAny, reportAny]
            order_in = OrderCreate(**data)  # pyright:ignore[reportAny]

        except ValidationError as e:
            logger.exception("Validation error while creating order.")
            msg = "; ".join(f"{' -> '.join(map(str, error['loc']))}: {error['msg']}" for error in e.errors())

            return utils.error_response(resp, falcon.HTTP_400, msg)

        try:
            async with get_db() as session:
                q = select(User).where(User.id == order_in.user_id)
                result = await session.execute(q)
                user = result.scalar_one_or_none()

                if not user:
                    return utils.error_response(
                        resp,
                        falcon.HTTP_400,
                        f"User with id={order_in.user_id} does not exist.",
                    )

                new_order = Order(
                    user_id=order_in.user_id,
                    total_price=order_in.total_price,
                )
                session.add(new_order)
                await session.commit()

                resp.status = falcon.HTTP_201
                resp.media = OrderOut(
                    id=new_order.id,
                    user_id=new_order.user_id,
                    total_price=new_order.total_price,
                    created_at=new_order.created_at_iso,
                ).model_dump()

        except IntegrityError:
            logger.exception("IntegrityError while creating order.")
            utils.error_response(resp, falcon.HTTP_409, "Order creation conflict (IntegrityError).")
        except SQLAlchemyError:
            logger.exception("Database error during order creation.")
            utils.error_response(resp, falcon.HTTP_500, "Database error occurred")
        except Exception:
            logger.exception("Unexpected error during order creation.")
            utils.error_response(resp, falcon.HTTP_500, "Internal server error")

    async def on_delete(self, req: falcon.Request, resp: falcon.Response, order_id: int) -> None:  # noqa: PLR6301
        """Delete an existing order by ID."""
        _ = req

        try:
            async with get_db() as session:
                q = select(Order).where(Order.id == order_id)
                result = await session.execute(q)
                order = result.scalar_one_or_none()

                if not order:
                    return utils.error_response(resp, falcon.HTTP_404, f"Order with id={order_id} not found.")

                await session.delete(order)
                await session.commit()
                resp.status = falcon.HTTP_204

        except SQLAlchemyError:
            logger.exception("Database error during order deletion.")
            utils.error_response(resp, falcon.HTTP_500, "Database error occurred during deletion")
        except Exception:
            logger.exception("Unexpected error during order deletion.")
            utils.error_response(resp, falcon.HTTP_500, "Internal server error")
