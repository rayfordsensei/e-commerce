from typing import final

import falcon
import spectree

from api.schemas.product_schemas import ProductCreate, ProductError, ProductOut, ProductUpdate
from app.spectree import api
from services.use_cases.products import CreateProduct, DeleteProduct, GetProduct, ListProducts, UpdateProductFields


@final
class ProductResource:
    def __init__(
        self,
        create_uc: CreateProduct,
        list_uc: ListProducts,
        get_uc: GetProduct,
        delete_uc: DeleteProduct,
        update_uc: UpdateProductFields,
    ) -> None:
        self._create = create_uc
        self._list = list_uc
        self._get = get_uc
        self._delete = delete_uc
        self._update = update_uc

    @api.validate(  # pyright:ignore[reportUnknownMemberType, reportUntypedFunctionDecorator]  # write a stub?.. hell no
        json=ProductCreate,
        resp=spectree.Response(
            HTTP_201=ProductOut,
            HTTP_400=ProductError,
        ),
        tags=["Products"],
        security={"bearerAuth": []},
    )
    async def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        """Create a new product.

        Accepts name, description, price and stock; returns the created product.
        """
        data = req.context.json  # pyright:ignore[reportAny]
        try:
            product = await self._create(
                data.name,  # pyright:ignore[reportAny]
                data.description,  # pyright:ignore[reportAny]
                data.price,  # pyright:ignore[reportAny]
                data.stock,  # pyright:ignore[reportAny]
            )

        except ValueError as exc:
            resp.status = falcon.HTTP_400
            resp.media = ProductError(
                error=str(exc),
                request_id=req.context.request_id,  # pyright:ignore[reportAny]
            ).model_dump()
            return

        resp.status = falcon.HTTP_201
        resp.media = ProductOut.model_validate(product).model_dump()

    # GET /products  or  /products/{id}
    @api.validate(  # pyright:ignore[reportUnknownMemberType, reportUntypedFunctionDecorator]
        resp=spectree.Response(
            HTTP_200=list[ProductOut],
            HTTP_404=ProductError,
        ),
        tags=["Products"],
        security={"bearerAuth": []},
        path_parameter_descriptions={"product_id": "Product ID to retrieve; omit to list all"},
    )
    async def on_get(self, req: falcon.Request, resp: falcon.Response, product_id: int | None = None) -> None:
        """Retrieve one product or list all.

        If `product_id` is provided, returns that product; otherwise returns all products.
        """
        if product_id is None:
            products = await self._list()
            resp.media = [ProductOut.model_validate(product).model_dump() for product in products]
            return

        product = await self._get(product_id)
        if product is None:
            resp.status = falcon.HTTP_404
            resp.media = ProductError(
                error="Product not found",
                request_id=req.context.request_id,  # pyright:ignore[reportAny]
            ).model_dump()
            return

        resp.media = ProductOut.model_validate(product).model_dump()

    # DELETE /products/{id}
    @api.validate(  # pyright:ignore[reportUnknownMemberType, reportUntypedFunctionDecorator]
        resp=spectree.Response(
            HTTP_204=None,
            HTTP_404=ProductError,
        ),
        tags=["Products"],
        security={"bearerAuth": []},
        path_parameter_descriptions={"product_id": "Product ID to delete"},
    )
    async def on_delete(self, req: falcon.Request, resp: falcon.Response, product_id: int) -> None:
        """Delete a product.

        Permanently removes the product with the given ID.
        """
        try:
            await self._delete(product_id)

        except ValueError as exc:
            resp.status = falcon.HTTP_404
            resp.media = ProductError(
                error=str(exc),
                request_id=req.context.request_id,  # pyright:ignore[reportAny]
            ).model_dump()
            return

        resp.status = falcon.HTTP_204

    # PATCH /products/{id}
    @api.validate(  # pyright:ignore[reportUnknownMemberType, reportUntypedFunctionDecorator]
        json=ProductUpdate,
        resp=spectree.Response(
            HTTP_204=None,
            HTTP_400=ProductError,
            HTTP_404=ProductError,
        ),
        tags=["Products"],
        security={"bearerAuth": []},
        path_parameter_descriptions={"product_id": "ID of the product to update"},
    )
    async def on_patch(self, req: falcon.Request, resp: falcon.Response, product_id: int) -> None:
        """Update a product.

        Accepts `price` and/or `stock` in the JSON body.
        """
        data = req.context.json  # pyright:ignore[reportAny]
        try:
            await self._update(product_id, data.price, data.stock)  # pyright:ignore[reportAny]

        except ValueError as exc:
            resp.status = falcon.HTTP_400
            resp.media = ProductError(
                error=str(exc),
                request_id=req.context.request_id,  # pyright:ignore[reportAny]
            ).model_dump()
            return

        resp.status = falcon.HTTP_204
