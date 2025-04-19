from typing import final

import falcon
from falcon import Request, Response

from api.schemas.product_schemas import ProductCreate, ProductOut
from services.use_cases.products import CreateProduct, DeleteProduct, GetProduct, ListProducts, UpdateProductFields


@final
class ProductResource:
    """Thin HTTP adapter: translate JSON == use-case DTOs."""

    # JSON <-> Pydantic <-> use_cases.
    def __init__(
        self,
        create: CreateProduct,
        list_: ListProducts,
        get: GetProduct,
        delete: DeleteProduct,
        update: UpdateProductFields,
    ) -> None:
        self._create = create
        self._list = list_
        self._get = get
        self._delete = delete
        self._update = update

    # ───────────────────────────
    # POST /products
    # ───────────────────────────
    async def on_post(self, req: Request, resp: Response) -> None:
        cmd = ProductCreate(**await req.get_media())  # pyright:ignore[reportAny]
        product = await self._create(cmd.name, cmd.description, cmd.price, cmd.stock)
        resp.status = falcon.HTTP_201
        resp.media = ProductOut.model_validate(product).model_dump()

    # ───────────────────────────
    # GET /products  or  /products/{id}
    # ───────────────────────────
    async def on_get(self, req: Request, resp: Response, product_id: int | None = None) -> None:
        _ = req

        if product_id is None:
            products = await self._list()
            resp.media = [ProductOut.model_validate(product).model_dump() for product in products]
            return

        product = await self._get(product_id)
        if product is None:
            resp.status = falcon.HTTP_404
            resp.media = {"error": "Product not found"}
            return

        resp.media = ProductOut.model_validate(product).model_dump()

    # ───────────────────────────
    # DELETE /products/{id}
    # ───────────────────────────
    async def on_delete(self, req: Request, resp: Response, product_id: int) -> None:
        _ = req

        await self._delete(product_id)
        resp.status = falcon.HTTP_204

    # ───────────────────────────
    # PATCH /products/{id}
    # Body: {"price": 8.99} or {"stock": 120}
    # ───────────────────────────
    async def on_patch(self, req: Request, resp: Response, product_id: int) -> None:
        data = await req.get_media()  # pyright:ignore[reportAny]

        try:
            await self._update(product_id, data.get("price"), data.get("stock"))  # pyright:ignore[reportAny]

        except ValueError as exc:
            resp.status = falcon.HTTP_400
            resp.media = {"error": str(exc)}
            return

        resp.status = falcon.HTTP_204
