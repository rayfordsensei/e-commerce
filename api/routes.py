from falcon.asgi import App

from api.login import LoginResource
from api.orders import OrderResource
from api.products import ProductResource
from api.users import UserResource


def register_routes(app: App) -> None:
    login_resource = LoginResource()
    order_resource = OrderResource()
    product_resource = ProductResource()
    user_resource = UserResource()

    app.add_route("/login", login_resource)
    app.add_route("/orders", order_resource)
    app.add_route("/orders/{order_id}", order_resource)
    app.add_route("/products", product_resource)
    app.add_route("/products/{product_id}", product_resource)
    app.add_route("/users", user_resource)
    app.add_route("/users/{user_id}", user_resource)
