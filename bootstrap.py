from typing import TypedDict

from falcon.asgi import App

from application.use_cases.auth import AuthenticateUser
from application.use_cases.orders import CreateOrder, DeleteOrder, GetOrder, ListOrders, UpdateOrderFields
from application.use_cases.products import (
    CreateProduct,
    DeleteProduct,
    GetProduct,
    ListProducts,
    UpdateProductFields,
)
from application.use_cases.users import DeleteUser, GetUser, ListUsers, RegisterUser
from infrastructure.db import close_db, init_db
from infrastructure.jsonjwt import JsonWebTokenService
from infrastructure.sqlalchemy.repositories import (
    SQLAlchemyOrderRepository,
    SQLAlchemyProductRepository,
    SQLAlchemyUserRepository,
)
from interfaces.http.jwt_middleware import JWTMiddleware
from interfaces.http.lifespan import LifespanMiddleware
from interfaces.http.login_resource import LoginResource
from interfaces.http.order_resource import OrderResource
from interfaces.http.product_resource import ProductResource
from interfaces.http.request_logger_middleware import RequestLoggerMiddleware
from interfaces.http.user_resource import UserResource
from logging_conf import setup_logging


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
        "create_order": CreateOrder(repos["orders"], repos["users"]),
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


def create_falcon_app(resources: Resources, services: Services) -> App:
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

    return app


def build_app() -> LifespanMiddleware:
    setup_logging("INFO")

    repos = create_repositories()
    services = create_services()
    use_cases = create_use_cases(repos, services)
    resources = create_resources(use_cases)
    falcon_app = create_falcon_app(resources, services)

    return LifespanMiddleware(falcon_app, startup_task=init_db, shutdown_task=close_db)


app = build_app()

# TODO: context_types?
# TODO: pytest?
# TODO: pagination + filtering
# TODO: SimpleNamespace for req (esp. in request_logger)?
# TODO: Swagger/ReDoc? (falcon-apispec, falcon-oas)
# TODO: background tasks?
# TODO: rate-limiting + abuse protection?
# TODO: check whether joserfc is validating "exp"/claims
# TODO: implement different logging conf for dev/prod (structlog?)
# TODO: log request body for safe endpoints (logger.debug?)
# TODO: differ between log levels (only "INFO" for now)
# TODO: Make consistent hints for API endpoints in interfaces/http/, like:
# ───────────────────────────
# POST /products
# ───────────────────────────
# TODO: Check and fix "noqa" and "pyright:ignore"
# TODO: custom exceptions instead of generic ones (ValueError("...")) inside domain/exceptions.py
# TODO: shopping cart?..
# TODO: generic error handler like this:
# def generic_error_handler(ex, req, resp, params):
#     request_id = getattr(req.context, "request_id", None)
#     resp.set_header("X-Request-ID", request_id)
#     # Optionally log or attach `request_id` in the response body
# app = falcon.App(middleware=[...])
# app.add_error_handler(Exception, generic_error_handler)
# TODO: replace resp.status + resp.media errors with error_response(resp, falcon.ErrorCode, "desc", req.context.request_id)
# TODO: replace logging per loguru (shared/logging.py)
# from loguru import logger

# logger.info("Server started")
# logger.warning("User {user_id} not found", user_id=user.id)
# logger.debug("Request body: {}", body)
# logger.error("Oops", exc_info=True)

# import logging
# logger = logging.getLogger(...)  # is not needed anymore
