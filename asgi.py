# pyright: basic
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"

sys.path.insert(0, str(SRC_DIR))

from app.app import app as application

# TODO: context_types?
# TODO: pytest?
# TODO: pagination + filtering
# TODO: HATEOAS?
# TODO: SimpleNamespace for req (esp. in request_logger)?
# TODO: Swagger/ReDoc? (falcon-apispec, falcon-oas)
# TODO: background tasks?
# TODO: rate-limiting + abuse protection?
# TODO: check whether joserfc is validating "exp"/claims
# TODO: implement different logging conf for dev/prod (structlog?)
# TODO: log request body for safe endpoints (logger.debug?)
# TODO: differ between log levels (only "INFO" for now)
# TODO: Make consistent hints for API endpoints in api/routes/, like:
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
# TODO: replace resp.status + resp.media errors with error_response(resp, ErrorCode, "desc", req.context.request_id)
# TODO: replace logging per loguru (shared/logging.py)
# from loguru import logger

# logger.info("Server started")
# logger.warning("User {user_id} not found", user_id=user.id)
# logger.debug("Request body: {}", body)
# logger.error("Oops", exc_info=True)

# import logging
# logger = logging.getLogger(...)  # is not needed anymore

# TODO: wrong token causes a ValueError("Invalid JSON Web Signature") with 500 Internal Server Error
# TODO: switch json encoder to a faster lib (orjson?)
# TODO: persistent db sessions / pooling?
# TODO: cache hot rows? (`functools.lru_cache`? redis?)
# TODO: simple frontend as a showcase
# TODO: intermediate tables?
