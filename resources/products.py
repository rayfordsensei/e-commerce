import asyncio

import falcon
from sqlalchemy.orm.session import Session

from db import get_db
from models import Product


class ProductResource:
    async def on_get(self, req, resp, product_id=None) -> None:
        """Retrieve all products or a single product."""
        db = next(get_db())

        if product_id:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                raise falcon.HTTPNotFound(description="Product not found.")
            resp.media = {"id": product.id, "name": product.name, "price": product.price, "stock": product.stock}
        else:
            products = db.query(Product).all()
            resp.media = [{"id": p.id, "name": p.name, "price": p.price, "stock": p.stock} for p in products]

    async def on_post(self, req, resp) -> None:
        """Create a new product."""
        data = await req.media

        if not data.get("name") or not data.get("price") or not data.get("stock"):
            raise falcon.HTTPBadRequest(description="Missing required fields.")

        # Attempt at using thread pools for access to Db
        def create_product() -> Product:
            db = next(get_db())
            product = Product(name=data["name"], price=data["price"], stock=data["stock"])
            db.add(instance=product)
            db.commit()
            return product

        product = await asyncio.to_thread(create_product)

        resp.status = falcon.HTTP_201
        resp.media = {"message": "Product created", "id": product.id}

    async def on_delete(self, req, resp, product_id) -> None:
        """Delete a product."""

        if not product:
            raise falcon.HTTPNotFound(description="Product not found.")

        def delete_product():
            db = next(get_db())
            product = db.query(Product).filter(Product.id == product_id).first()
            db.delete(instance=product)
            db.commit()

        resp.status = falcon.HTTP_200
        resp.media = {"message": "Product deleted"}
