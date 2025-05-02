from typing import final

import falcon
import spectree

from api.schemas.order_schemas import (
    OrderCreate,
    OrderError,
    OrderFilter,
    OrderOut,
    OrderUpdate,
)
from app.spectree import api
from services.use_cases.orders import (
    CreateOrder,
    DeleteOrder,
    GetOrder,
    ListOrders,
    UpdateOrderFields,
)


#  /orders — collection
@final
class OrdersCollection:
    def __init__(self, create_uc: CreateOrder, list_uc: ListOrders):
        self._create = create_uc
        self._list = list_uc

    # POST /orders
    @api.validate(  # pyright:ignore[reportUntypedFunctionDecorator, reportUnknownMemberType]
        json=OrderCreate,
        resp=spectree.Response(
            HTTP_201=OrderOut,
            HTTP_400=OrderError,
            HTTP_404=OrderError,
        ),
        tags=["Orders"],
        security={"bearerAuth": []},
    )
    async def on_post(self, req: falcon.Request, resp: falcon.Response):
        """Create a new order.

        Registers an order for the given user and returns the created order.
        """
        data = req.context.json

        order = await self._create(data.user_id, data.total_price)

        resp.status = falcon.HTTP_201
        resp.media = OrderOut.model_validate(order).model_dump()

    # GET /orders
    @api.validate(  # pyright:ignore[reportUntypedFunctionDecorator, reportUnknownMemberType]
        query=OrderFilter,
        resp=spectree.Response(
            HTTP_200=list[OrderOut],
        ),
        tags=["Orders"],
        security={"bearerAuth": []},
    )
    async def on_get(self, req: falcon.Request, resp: falcon.Response):
        """List orders.

        Returns a paginated list of all orders, or only those for a specific user if `user_id` is provided.
        """
        f = req.context.query

        orders, total = await self._list(
            f.user_id,
            page=f.page,
            per_page=f.per_page,
        )

        resp.media = [OrderOut.model_validate(o).model_dump() for o in orders]
        resp.set_header("X-Total-Count", str(total))


#  /orders/{order_id:int} — detail
@final
class OrderDetail:
    def __init__(
        self,
        get_uc: GetOrder,
        delete_uc: DeleteOrder,
        update_uc: UpdateOrderFields,
    ):
        self._get = get_uc
        self._delete = delete_uc
        self._update = update_uc

    # GET /orders/{order_id}
    @api.validate(  # pyright:ignore[reportUntypedFunctionDecorator, reportUnknownMemberType]
        resp=spectree.Response(
            HTTP_200=OrderOut,
            HTTP_400=OrderError,
            HTTP_404=OrderError,
        ),
        tags=["Orders"],
        security={"bearerAuth": []},
        path_parameter_descriptions={"order_id": "Order ID (must be > 0)"},
    )
    async def on_get(self, req: falcon.Request, resp: falcon.Response, order_id: int):
        """Retrieve an order by ID.

        Returns the order details for the specified order, or 404 if not found.
        """
        _ = req

        order = await self._get(order_id)
        if order is None:
            resp.status = falcon.HTTP_404
            resp.media = OrderError(error="Order not found").model_dump()
            return

        resp.media = OrderOut.model_validate(order).model_dump()

    # DELETE /orders/{order_id}
    @api.validate(  # pyright:ignore[reportUntypedFunctionDecorator, reportUnknownMemberType]
        resp=spectree.Response(
            HTTP_204=None,
            HTTP_400=OrderError,
            HTTP_403=OrderError,
            HTTP_404=OrderError,
        ),
        tags=["Orders"],
        security={"bearerAuth": []},
        validation_error_status=0,
        path_parameter_descriptions={"order_id": "Order ID (must be > 0)"},
    )
    async def on_delete(self, req: falcon.Request, resp: falcon.Response, order_id: int):
        """Delete an order by ID.

        Deletes the specified order if the caller owns it; returns 204 on success.
        """
        _ = req

        await self._delete(order_id, req.context.user_id)
        resp.status = falcon.HTTP_204

    # PATCH /orders/{order_id}
    @api.validate(  # pyright:ignore[reportUntypedFunctionDecorator, reportUnknownMemberType]
        json=OrderUpdate,
        resp=spectree.Response(
            HTTP_204=None,
            HTTP_400=OrderError,
            HTTP_404=OrderError,
        ),
        tags=["Orders"],
        security={"bearerAuth": []},
        path_parameter_descriptions={"order_id": "Order ID (must be > 0)"},
    )
    async def on_patch(self, req: falcon.Request, resp: falcon.Response, order_id: int):
        """Update an order's total price.

        Applies a new `total_price` to the specified order.
        """
        data = req.context.json

        await self._update(order_id, data.total_price)
        resp.status = falcon.HTTP_204
