from typing import final

import falcon
from falcon import Request, Response

from application.use_cases.orders import (
    CreateOrder,
    DeleteOrder,
    GetOrder,
    ListOrders,
    UpdateOrderFields,
)
from schemas.order_schemas import OrderCreate, OrderOut


@final
class OrderResource:
    def __init__(
        self,
        create: CreateOrder,
        list_: ListOrders,
        get: GetOrder,
        delete: DeleteOrder,
        update: UpdateOrderFields,
    ) -> None:
        self._create = create
        self._list = list_
        self._get = get
        self._delete = delete
        self._update = update

    # POST /orders
    async def on_post(self, req: Request, resp: Response) -> None:
        cmd = OrderCreate(**await req.get_media())  # pyright:ignore[reportAny]
        order = await self._create(cmd.user_id, cmd.total_price)
        resp.status = falcon.HTTP_201
        resp.media = OrderOut.model_validate(order).model_dump()

    # GET /orders   or   /orders/{id}
    async def on_get(self, req: Request, resp: Response, order_id: int | None = None) -> None:
        user_id = req.get_param_as_int("user_id")  # optional filter ?user_id=...
        if order_id is None:
            orders = await self._list(user_id)
            resp.media = [OrderOut.model_validate(order).model_dump() for order in orders]
            return

        order = await self._get(order_id)
        if order is None:
            resp.status = falcon.HTTP_404
            resp.media = {"error": "Order not found"}
            return

        resp.media = OrderOut.model_validate(order).model_dump()

    # DELETE /orders/{id}
    async def on_delete(self, req: Request, resp: Response, order_id: int) -> None:
        _ = req

        await self._delete(order_id)
        resp.status = falcon.HTTP_204

    # PATCH /orders/{id}   body: {"total_price": 123.45}
    async def on_patch(self, req: Request, resp: Response, order_id: int) -> None:
        data = await req.get_media()  # pyright:ignore[reportAny]
        if "total_price" not in data:
            resp.status = falcon.HTTP_400
            resp.media = {"error": "total_price is required"}
            return
        await self._update(order_id, float(data["total_price"]))  # pyright:ignore[reportAny]
        resp.status = falcon.HTTP_204
