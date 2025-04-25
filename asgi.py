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
# TODO: Improve Swagger/ReDoc?
# TODO: background tasks?
# TODO: rate-limiting + abuse protection?
# TODO: check whether joserfc is validating "exp"/claims
# TODO: implement different logging conf for dev/prod (structlog?)
# TODO: log request body for safe endpoints (logger.debug?)
# TODO: differ between log levels (only "INFO" for now)
# TODO: Check and fix "noqa" and "pyright:ignore"
# TODO: custom exceptions instead of generic ones (ValueError("...")) inside domain/exceptions.py
# TODO: shopping cart?..
# TODO: generic error handler
# TODO: replace resp.status + resp.media errors with error_response(resp, ErrorCode, "desc", req.context.request_id)
# TODO: replace logging per loguru (shared/logging.py)
# TODO: switch json encoder to a faster lib (orjson?)
# TODO: persistent db sessions / pooling?
# TODO: cache hot rows? (`functools.lru_cache`? redis?)
# TODO: simple frontend as a showcase
# TODO: intermediate tables?
# tox r -e py312 <- for tests
# TODO: get rid of `assert`
# TODO: create an exception name handler that re-uses method's name (__name__)
# TODO: make cleaner engine_args
