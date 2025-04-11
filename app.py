from falcon.asgi import App

from db import close_db, init_db
from middleware.lifespan import LifespanMiddleware
from resources.users import UserResource

# from resources.products import ProductResource
# from resources.orders import OrderResource

# logging middleware?

falcon_app = App()

user_resource = UserResource()
# product_resource = ProductResource()
# order_resource = OrderResource()

falcon_app.add_route("/users", user_resource)
falcon_app.add_route("/users/{user_id}", user_resource)
# app.add_route("/products", product_resource)
# app.add_route("/products/{product_id}", product_resource)
# app.add_route("/orders", order_resource)
# app.add_route("/orders/{order_id}", order_resource)

app = LifespanMiddleware(falcon_app, init_db, close_db)
