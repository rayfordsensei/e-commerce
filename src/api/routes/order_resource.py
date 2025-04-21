from typing import final

import falcon
import spectree

from api.schemas.order_schemas import OrderCreate, OrderError, OrderFilter, OrderOut, OrderUpdate
from app.spectree import api
from services.use_cases.orders import (
    CreateOrder,
    DeleteOrder,
    GetOrder,
    ListOrders,
    UpdateOrderFields,
)


@final
class OrderResource:
    def __init__(
        self,
        create_uc: CreateOrder,
        list_uc: ListOrders,
        get_uc: GetOrder,
        delete_uc: DeleteOrder,
        update_uc: UpdateOrderFields,
    ) -> None:
        self._create = create_uc
        self._list = list_uc
        self._get = get_uc
        self._delete = delete_uc
        self._update = update_uc

    # POST /orders
    @api.validate(  # pyright:ignore[reportUnknownMemberType, reportUntypedFunctionDecorator]  # write a stub?.. hell no
        json=OrderCreate,
        resp=spectree.Response(
            HTTP_201=OrderOut,
            HTTP_400=OrderError,
        ),
        tags=["Orders"],
        security={"bearerAuth": []},
    )
    async def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        """Create a new order.

        Accepts a user_id and total_price, returns the created order record.
        """
        data = req.context.json  # pyright:ignore[reportAny]
        try:
            order = await self._create(data.user_id, data.total_price)  # pyright:ignore[reportAny]

        except ValueError as exc:
            resp.status = falcon.HTTP_400
            resp.media = OrderError(error=str(exc), request_id=req.context.request_id).model_dump()  # pyright:ignore[reportAny]
            return

        resp.status = falcon.HTTP_201
        resp.media = OrderOut.model_validate(order).model_dump()

    # GET /orders or GET /orders/{id}
    @api.validate(  # pyright:ignore[reportUnknownMemberType, reportUntypedFunctionDecorator]
        query=OrderFilter,
        resp=spectree.Response(
            HTTP_200=list[OrderOut],
            HTTP_404=OrderError,
        ),
        tags=["Orders"],
        security={"bearerAuth": []},
        path_parameter_descriptions={
            "order_id": "Order ID to retrieve (omit to list all orders, must be > 0)",
        },
    )
    async def on_get(self, req: falcon.Request, resp: falcon.Response, order_id: int | None = None) -> None:
        """Retrieve one order or list orders.

        If `order_id` is provided, returns that order; otherwise returns all orders,
        optionally filtered by `?user_id=`.
        """
        filter_ = req.context.query  # pyright:ignore[reportAny]
        if order_id is None:
            orders = await self._list(filter_.user_id)  # pyright:ignore[reportAny]
            resp.media = [OrderOut.model_validate(o).model_dump() for o in orders]
            return

        order = await self._get(order_id)
        if order is None:
            resp.status = falcon.HTTP_404
            resp.media = OrderError(
                error="Order not found",
                request_id=req.context.request_id,  # pyright:ignore[reportAny]
            ).model_dump()
            return

        resp.media = OrderOut.model_validate(order).model_dump()

    # DELETE /orders/{order_id}
    @api.validate(  # pyright:ignore[reportUnknownMemberType, reportUntypedFunctionDecorator]
        resp=spectree.Response(
            HTTP_204=None,
            HTTP_404=OrderError,
        ),
        tags=["Orders"],
        security={"bearerAuth": []},
        path_parameter_descriptions={
            "order_id": "Order ID to delete (must be > 0)",
        },
    )
    async def on_delete(self, req: falcon.Request, resp: falcon.Response, order_id: int) -> None:
        """Delete an order.

        Permanently removes the order with the given ID.
        """
        try:
            await self._delete(order_id)

        except ValueError as exc:
            resp.status = falcon.HTTP_404
            resp.media = OrderError(
                error=str(exc),
                request_id=req.context.request_id,  # pyright:ignore[reportAny]
            ).model_dump()
            return

        resp.media = falcon.HTTP_204

    # PATCH /orders/{id}
    @api.validate(  # pyright:ignore[reportUnknownMemberType, reportUntypedFunctionDecorator]
        json=OrderUpdate,
        resp=spectree.Response(
            HTTP_204=None,
            HTTP_400=OrderError,
            HTTP_404=OrderError,
        ),
        tags=["Orders"],
        security={"bearerAuth": []},
        path_parameter_descriptions={
            "order_id": "Order ID to update (must be > 0)",
        },
    )
    async def on_patch(self, req: falcon.Request, resp: falcon.Response, order_id: int) -> None:
        """Update an existing order's total_price.

        Requires `{"total_price": ...}` in the request body.
        """
        data = req.context.json  # pyright:ignore[reportAny]
        try:
            await self._update(order_id, data.total_price)  # pyright:ignore[reportAny]

        except ValueError as exc:
            resp.status = falcon.HTTP_400
            resp.media = OrderError(
                error=str(exc),
                request_id=req.context.request_id,  # pyright:ignore[reportAny]
            ).model_dump()
            return

        resp.status = falcon.HTTP_204
