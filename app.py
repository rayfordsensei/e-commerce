import logging

from falcon.asgi import App

from db import close_db, init_db
from middleware.lifespan import LifespanMiddleware
from middleware.request_logger import RequestLoggerMiddleware
from resources.login import LoginResource
from resources.orders import OrderResource
from resources.products import ProductResource
from resources.users import UserResource

logging.basicConfig(level=logging.INFO)  # TODO: configure all loggers

falcon_app = App(
    middleware=[
        RequestLoggerMiddleware(),
    ],
)

login_resource = LoginResource()
order_resource = OrderResource()
product_resource = ProductResource()
user_resource = UserResource()

falcon_app.add_route("/login", login_resource)
falcon_app.add_route("/orders", order_resource)
falcon_app.add_route("/orders/{order_id}", order_resource)
falcon_app.add_route("/products", product_resource)
falcon_app.add_route("/products/{product_id}", product_resource)
falcon_app.add_route("/users", user_resource)
falcon_app.add_route("/users/{user_id}", user_resource)

app = LifespanMiddleware(falcon_app, init_db, close_db)

# TODO: context_types?
# TODO: protected routes (JWTMw)?
# TODO: pytest?
# TODO: pagination + filtering
# TODO: SimpleNamespace for req (esp. in request_logger)?
