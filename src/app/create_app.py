import asyncio
from typing import TypedDict, final

from falcon import Request, Response
from falcon.asgi import App
from swagger_ui_bundle import swagger_ui_path

from api.middleware.jwt import JWTMiddleware
from api.middleware.lifespan import LifespanMiddleware
from api.middleware.request_logger import RequestLoggerMiddleware
from api.routes.login_resource import LoginResource
from api.routes.order_resource import OrderResource
from api.routes.product_resource import ProductResource
from api.routes.user_resource import UserResource
from app.logging_conf import setup_logging
from app.spectree import api
from infrastructure.databases.db import close_db, init_db
from infrastructure.jwt.service import JsonWebTokenService
from infrastructure.sqlalchemy.repositories import (
    SQLAlchemyOrderRepository,
    SQLAlchemyProductRepository,
    SQLAlchemyUserRepository,
)
from services.use_cases.auth import AuthenticateUser
from services.use_cases.orders import CreateOrder, DeleteOrder, GetOrder, ListOrders, UpdateOrderFields
from services.use_cases.products import CreateProduct, DeleteProduct, GetProduct, ListProducts, UpdateProductFields
from services.use_cases.users import DeleteUser, GetUser, ListUsers, RegisterUser


@final
class SwaggerUIIndex:
    async def on_get(self, req: Request, resp: Response) -> None:  # noqa: PLR6301
        _ = req

        html_file = swagger_ui_path / "index.html"

        text = await asyncio.to_thread(html_file.read_text, encoding="utf-8")
        text = text.replace("https://petstore.swagger.io/v2/swagger.json", "/openapi.json")

        resp.content_type = "text/html"
        resp.text = text


class FaviconResource:  # Opting for a cutesy look!
    async def on_get(self, req: Request, resp: Response) -> None:  # noqa: PLR6301
        _ = req

        icon_path = swagger_ui_path / "favicon-32x32.png"
        icon_bytes = await asyncio.to_thread(icon_path.read_bytes)

        resp.content_type = "image/png"
        resp.data = icon_bytes


class Repositories(TypedDict):
    orders: SQLAlchemyOrderRepository
    users: SQLAlchemyUserRepository
    products: SQLAlchemyProductRepository


class Services(TypedDict):
    jwt: JsonWebTokenService


class UseCases(TypedDict):
    auth: AuthenticateUser
    create_order: CreateOrder
    list_orders: ListOrders
    get_order: GetOrder
    delete_order: DeleteOrder
    update_order_fields: UpdateOrderFields
    create_product: CreateProduct
    list_products: ListProducts
    get_product: GetProduct
    delete_product: DeleteProduct
    update_product_fields: UpdateProductFields
    register_user: RegisterUser
    list_users: ListUsers
    get_user: GetUser
    delete_user: DeleteUser


class Resources(TypedDict):
    login: LoginResource
    orders: OrderResource
    products: ProductResource
    users: UserResource


def create_repositories() -> Repositories:
    return {
        "orders": SQLAlchemyOrderRepository(),
        "users": SQLAlchemyUserRepository(),
        "products": SQLAlchemyProductRepository(),
    }


def create_services() -> Services:
    return {
        "jwt": JsonWebTokenService(),
    }


def create_use_cases(repos: Repositories, services: Services) -> UseCases:
    return {
        "auth": AuthenticateUser(repos["users"], services["jwt"]),
        "create_order": CreateOrder(repos["users"], repos["orders"]),
        "list_orders": ListOrders(repos["orders"]),
        "get_order": GetOrder(repos["orders"]),
        "delete_order": DeleteOrder(repos["orders"]),
        "update_order_fields": UpdateOrderFields(repos["orders"]),
        "create_product": CreateProduct(repos["products"]),
        "list_products": ListProducts(repos["products"]),
        "get_product": GetProduct(repos["products"]),
        "delete_product": DeleteProduct(repos["products"]),
        "update_product_fields": UpdateProductFields(repos["products"]),
        "register_user": RegisterUser(repos["users"]),
        "list_users": ListUsers(repos["users"]),
        "get_user": GetUser(repos["users"]),
        "delete_user": DeleteUser(repos["users"], repos["orders"]),
    }


def create_resources(uc: UseCases) -> Resources:
    return {
        "login": LoginResource(uc["auth"]),
        "orders": OrderResource(
            uc["create_order"],
            uc["list_orders"],
            uc["get_order"],
            uc["delete_order"],
            uc["update_order_fields"],
        ),
        "products": ProductResource(
            uc["create_product"],
            uc["list_products"],
            uc["get_product"],
            uc["delete_product"],
            uc["update_product_fields"],
        ),
        "users": UserResource(
            uc["register_user"],
            uc["list_users"],
            uc["get_user"],
            uc["delete_user"],
        ),
    }


def create_app() -> LifespanMiddleware:
    setup_logging("INFO")

    repos = create_repositories()
    services = create_services()
    use_cases = create_use_cases(repos, services)
    resources = create_resources(use_cases)

    app = App(
        middleware=[
            RequestLoggerMiddleware(),
            JWTMiddleware(services["jwt"]),
        ],
    )

    app.add_route("/login", resources["login"])
    app.add_route("/orders", resources["orders"])
    app.add_route("/orders/{order_id:int}", resources["orders"])
    app.add_route("/products", resources["products"])
    app.add_route("/products/{product_id:int}", resources["products"])
    app.add_route("/users", resources["users"])
    app.add_route("/users/{user_id:int}", resources["users"])
    app.add_route("/favicon.ico", FaviconResource())

    api.register(app)

    return LifespanMiddleware(app, init_db, close_db)
