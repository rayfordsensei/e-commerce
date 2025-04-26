from typing import final

import falcon
from spectree import Response

from api.schemas.product_schemas import (
    ProductCreate,
    ProductError,
    ProductOut,
    ProductUpdate,
)
from app.spectree import api
from services.use_cases.products import (
    CreateProduct,
    DeleteProduct,
    GetProduct,
    ListProducts,
    UpdateProductFields,
)


@final
class ProductResource:
    def __init__(
        self,
        create_uc: CreateProduct,
        list_uc: ListProducts,
        get_uc: GetProduct,
        delete_uc: DeleteProduct,
        update_uc: UpdateProductFields,
    ):
        self._create = create_uc
        self._list = list_uc
        self._get = get_uc
        self._delete = delete_uc
        self._update = update_uc

    # POST /products
    @api.validate(  # pyright:ignore[reportUntypedFunctionDecorator, reportUnknownMemberType]
        json=ProductCreate,
        resp=Response(
            HTTP_201=ProductOut,
            HTTP_400=ProductError,
        ),
        tags=["Products"],
        # security={"bearerAuth": []},
    )
    async def on_post_collection(self, req: falcon.Request, resp: falcon.Response):

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
            resp.media = ProductError(error=str(exc)).model_dump()
            return

        resp.status = falcon.HTTP_201
        resp.media = ProductOut.model_validate(product).model_dump()

    # GET /products
    @api.validate(  # pyright:ignore[reportUntypedFunctionDecorator, reportUnknownMemberType]
        resp=Response(
            HTTP_200=list[ProductOut],
        ),
        tags=["Products"],
        security={"bearerAuth": []},
    )
    async def on_get_collection(self, req: falcon.Request, resp: falcon.Response):
        _ = req

        products = await self._list()
        resp.media = [ProductOut.model_validate(p).model_dump() for p in products]

    # GET /products/{product_id}
    @api.validate(  # pyright:ignore[reportUntypedFunctionDecorator, reportUnknownMemberType]
        resp=Response(
            HTTP_200=ProductOut,
            HTTP_400=ProductError,
            HTTP_404=ProductError,
        ),
        tags=["Products"],
        security={"bearerAuth": []},
        path_parameter_descriptions={
            "product_id": "Product ID to retrieve",
        },
    )
    async def on_get_detail(self, req: falcon.Request, resp: falcon.Response, product_id: int):
        _ = req

        product = await self._get(product_id)
        if product is None:
            resp.status = falcon.HTTP_404
            resp.media = ProductError(error="Product not found").model_dump()
            return

        resp.media = ProductOut.model_validate(product).model_dump()

    # PATCH /products/{product_id}
    @api.validate(  # pyright:ignore[reportUntypedFunctionDecorator, reportUnknownMemberType]
        json=ProductUpdate,
        resp=Response(
            HTTP_204=None,
            HTTP_400=ProductError,
            HTTP_404=ProductError,
        ),
        tags=["Products"],
        security={"bearerAuth": []},
        path_parameter_descriptions={
            "product_id": "ID of the product to update",
        },
    )
    async def on_patch_detail(self, req: falcon.Request, resp: falcon.Response, product_id: int):
        data = req.context.json  # pyright:ignore[reportAny]

        await self._update(product_id, data.price, data.stock)  # pyright:ignore[reportAny]
        resp.status = falcon.HTTP_204

    # DELETE /products/{product_id}
    @api.validate(  # pyright:ignore[reportUntypedFunctionDecorator, reportUnknownMemberType]
        resp=Response(
            HTTP_204=None,
            HTTP_400=ProductError,
            HTTP_404=ProductError,
        ),
        tags=["Products"],
        security={"bearerAuth": []},
        path_parameter_descriptions={
            "product_id": "Product ID to delete",
        },
    )
    async def on_delete_detail(self, req: falcon.Request, resp: falcon.Response, product_id: int):
        _ = req

        await self._delete(product_id)
        resp.status = falcon.HTTP_204
