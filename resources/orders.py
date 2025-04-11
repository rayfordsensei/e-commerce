import json

import falcon

from db import get_db
from models import Order


class OrderResource:
    def on_get(self, req, resp, order_id=None) -> None:
        """Retrieve all orders or a single order."""
        db = next(get_db())

        if order_id:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                raise falcon.HTTPNotFound(description="Order not found")
            resp.media = {"id": order.id, "user_id": order.user_id, "total_price": order.total_price}
        else:
            orders = db.query(Order).all()
            resp.media = [{"id": o.id, "user_id": o.user_id, "total_price": o.total_price} for o in orders]

    def on_post(self, req, resp) -> None:
        """Create a new order."""
        db = next(get_db())
        data = json.load(req.bounded_stream)

        if not data.get("user_id") or not data.get("total_price"):
            raise falcon.HTTPBadRequest(description="Missing required fields")

        order = Order(user_id=data["user_id"], total_price=data["total_price"])
        db.add(instance=order)
        db.commit()

        resp.status = falcon.HTTP_201
        resp.media = {"message": "Order created", "id": order.id}
