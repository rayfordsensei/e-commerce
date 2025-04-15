import logging

from falcon.asgi import App

from api.routes import register_routes
from db import close_db, init_db
from middleware.jwt_auth import JWTMiddleware
from middleware.lifespan import LifespanMiddleware
from middleware.request_logger import RequestLoggerMiddleware

logging.basicConfig(level=logging.INFO)  # TODO: configure all loggers

falcon_app = App(
    middleware=[
        RequestLoggerMiddleware(),
        JWTMiddleware(),
    ],
)

register_routes(falcon_app)

app = LifespanMiddleware(falcon_app, init_db, close_db)

# TODO: context_types?
# TODO: protected routes (JWTMw)?
# TODO: pytest?
# TODO: pagination + filtering
# TODO: SimpleNamespace for req (esp. in request_logger)?
# TODO: Swagger/ReDoc? (falcon-apispec, falcon-oas)
# TODO: background tasks?
# TODO: rate-limiting + abuse protection?
# TODO: check whether joserfc is validating "exp"/claims
