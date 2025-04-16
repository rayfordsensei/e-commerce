from falcon.asgi import App

from api.routes import register_routes
from db import close_db, init_db
from logging_conf import setup_logging
from middleware.jwt_auth import JWTMiddleware
from middleware.lifespan import LifespanMiddleware
from middleware.request_logger import RequestLoggerMiddleware

setup_logging("INFO")

falcon_app = App(
    middleware=[
        RequestLoggerMiddleware(),
        JWTMiddleware(),
    ],
)

register_routes(falcon_app)

app = LifespanMiddleware(falcon_app, init_db, close_db)

# TODO: context_types?
# TODO: pytest?
# TODO: pagination + filtering
# TODO: SimpleNamespace for req (esp. in request_logger)?
# TODO: Swagger/ReDoc? (falcon-apispec, falcon-oas)
# TODO: background tasks?
# TODO: rate-limiting + abuse protection?
# TODO: check whether joserfc is validating "exp"/claims
# TODO: implement different logging conf for dev/prod (structlog?)
