"""Application factory for the Falcon-ASGI e-commerce API.

Exposes a single ``create_app`` entry point that wires together
infrastructure -> use-cases -> Falcon resources and wraps
the resulting app with :class:`api.middleware.lifespan.LifespanMiddleware`
so that DB startup/shutdown hooks fire automatically.
"""

from __future__ import annotations

import asyncio
from typing import TypedDict, final

import falcon.asgi
from swagger_ui_bundle import swagger_ui_path

from api.middleware.error_handler import generic_error_handler
from api.middleware.jwt import JWTMiddleware
from api.middleware.lifespan import LifespanMiddleware
from api.middleware.request_logger import RequestLoggerMiddleware
from api.middleware.role import RoleMiddleware
from api.routes.login_resource import LoginResource
from api.routes.order_resources import OrderDetail, OrdersCollection
from api.routes.product_resources import ProductResource
from api.routes.user_resources import UserResource
from app.settings import settings
from app.spectree import api
from common.logging import setup_logging
from infrastructure.databases.db import close_db, init_db
from infrastructure.databases.unit_of_work import UnitOfWork
from infrastructure.jwt.service import JsonWebTokenService
from infrastructure.sqlalchemy import events as sa_events
from infrastructure.sqlalchemy.repositories import (
    SQLAlchemyOrderRepository,
    SQLAlchemyProductRepository,
    SQLAlchemyUserRepository,
)
from services.use_cases.auth import AuthenticateUser
from services.use_cases.orders import (
    CreateOrder,
    DeleteOrder,
    GetOrder,
    ListOrders,
    UpdateOrderFields,
)
from services.use_cases.products import (
    CreateProduct,
    DeleteProduct,
    GetProduct,
    ListProducts,
    UpdateProductFields,
)
from services.use_cases.users import (
    DeleteUser,
    GetUser,
    ListUsers,
    RegisterUser,
    UpdateUserFields,
)


# Factory helpers
class _Repositories(TypedDict):
    orders: SQLAlchemyOrderRepository
    users: SQLAlchemyUserRepository
    products: SQLAlchemyProductRepository


class _Services(TypedDict):
    jwt: JsonWebTokenService


class _UseCases(TypedDict):
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
    update_user_fields: UpdateUserFields
    delete_user: DeleteUser


class _Resources(TypedDict):
    login: LoginResource
    orders_collection: OrdersCollection
    order_detail: OrderDetail
    products: ProductResource
    users: UserResource


# ------------------------ 1. Infrastructure ----------------------------------
def _create_repositories() -> _Repositories:
    """Instantiate concrete SQLAlchemy repository adapters.

    Returns
    -------
    _Repositories
        Mapping containing fully initialised repository instances for
        ``orders``, ``users`` and ``products`` aggregates.

    """
    return {
        "orders": SQLAlchemyOrderRepository(),
        "users": SQLAlchemyUserRepository(),
        "products": SQLAlchemyProductRepository(),
    }


def _create_services() -> _Services:
    """Create shared infrastructure services (e.g. JWT).

    Returns
    -------
    _Services
        Mapping with service singletons used across the application. At the
        moment this contains only ``jwt``.

    """
    return {"jwt": JsonWebTokenService()}


# ------------------------ 2. Use-cases ---------------------------------------
def _create_use_cases(repos: _Repositories, services: _Services) -> _UseCases:
    """Wire repositories and services into application business logic.

    Parameters
    ----------
    repos
        Infrastructure adapters responsible for data persistence.
    services
        Cross-cutting concerns (authentication, etc.).

    Returns
    -------
    _UseCases
        Mapping where each value is an invokable object encapsulating a single
        piece of business behaviour (e.g. ``CreateOrder``).

    """
    return {
        # Auth
        "auth": AuthenticateUser(repos["users"], services["jwt"]),
        # Orders
        "create_order": CreateOrder(UnitOfWork),
        "list_orders": ListOrders(repos["orders"]),
        "get_order": GetOrder(repos["orders"]),
        "delete_order": DeleteOrder(UnitOfWork),
        "update_order_fields": UpdateOrderFields(UnitOfWork),
        # Products
        "create_product": CreateProduct(UnitOfWork),
        "list_products": ListProducts(repos["products"]),
        "get_product": GetProduct(repos["products"]),
        "delete_product": DeleteProduct(UnitOfWork),
        "update_product_fields": UpdateProductFields(UnitOfWork),
        # Users
        "register_user": RegisterUser(UnitOfWork),
        "list_users": ListUsers(repos["users"]),
        "get_user": GetUser(repos["users"]),
        "update_user_fields": UpdateUserFields(UnitOfWork),
        "delete_user": DeleteUser(UnitOfWork),
    }


# ------------------------ 3. HTTP Resources ----------------------------------
def _create_resources(uc: _UseCases) -> _Resources:
    """Translate pure use-cases into Falcon controller resources.

    Parameters
    ----------
    uc
        Mapping of use-case objects created by :pyfunc:`_create_use_cases`.

    Returns
    -------
    _Resources
        Mapping of Falcon resources ready to be mounted on ``App`` routes.

    """
    return {
        "login": LoginResource(uc["auth"]),
        "orders_collection": OrdersCollection(uc["create_order"], uc["list_orders"]),
        "order_detail": OrderDetail(
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
            uc["update_user_fields"],
            uc["delete_user"],
        ),
    }


# ------------------------ 4. Auxiliary endpoints -----------------------------
@final
class _SwaggerUIIndex:
    """Serve Swagger-UI bundled with `swagger_ui_bundle`."""

    async def on_get(self, req: falcon.Request, resp: falcon.Response):  # noqa: PLR6301
        _ = req

        html = await asyncio.to_thread((swagger_ui_path / "index.html").read_text, encoding="utf-8")
        resp.content_type = "text/html"
        resp.text = html.replace("https://petstore.swagger.io/v2/swagger.json", "/openapi.json")


@final
class _FaviconResource:
    async def on_get(self, req: falcon.Request, resp: falcon.Response):  # noqa: PLR6301
        _ = req

        resp.content_type = "image/png"
        resp.data = await asyncio.to_thread((swagger_ui_path / "favicon-32x32.png").read_bytes)


@final
class CrashResource:  # Just blowing things up =)
    async def on_get(self, req: falcon.Request, resp: falcon.Response):  # noqa: PLR6301
        _ = req, resp

        if not settings.DEBUG:
            raise falcon.HTTPNotFound

        raise ValueError("something went terribly wrong... or did it?")  # noqa: EM101, TRY003


# ------------------------ 5. Public factory ----------------------------------
def create_app(*, log_level: str = "INFO") -> LifespanMiddleware:
    """Build and return an ASGI application wrapped in ``LifespanMiddleware``.

    The resulting callable is wrapped with :class:`api.middleware.lifespan.LifespanMiddleware`
    so that database startup/shutdown hooks are executed automatically when the
    hosting server emits the ASGI lifespan events.

    Parameters
    ----------
    log_level
        Root log level (e.g. "INFO", "DEBUG").

    Returns
    -------
    LifespanMiddleware
        ASGI-compatible callable ready to be served by Uvicorn or any other
        ASGI server.

    """
    setup_logging(log_level)
    sa_events.register_session_events()

    repos = _create_repositories()
    services = _create_services()
    use_cases = _create_use_cases(repos, services)
    resources = _create_resources(use_cases)

    app = falcon.asgi.App(
        middleware=[
            RequestLoggerMiddleware(),
            JWTMiddleware(services["jwt"]),
            # RoleMiddleware(),
        ]
    )

    # Authentication
    app.add_route("/login", resources["login"])

    # Orders
    app.add_route("/orders", resources["orders_collection"])
    app.add_route("/orders/{order_id:int}", resources["order_detail"])

    # Products
    app.add_route("/products", resources["products"], suffix="collection")
    app.add_route("/products/{product_id:int}", resources["products"], suffix="detail")

    # Users
    app.add_route("/users", resources["users"], suffix="collection")
    app.add_route("/users/{user_id:int}", resources["users"], suffix="detail")

    # Documentation & static
    app.add_route("/apidoc", _SwaggerUIIndex())
    app.add_route("/favicon.ico", _FaviconResource())

    # Auxiliary
    app.add_route("/__crash__", CrashResource())

    api.register(app)

    for exc in (Exception, falcon.HTTPError, falcon.HTTPStatus):
        app.add_error_handler(exc, generic_error_handler)

    # Wrap with lifespan management
    return LifespanMiddleware(app, init_db, close_db)
