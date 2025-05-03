import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"

sys.path.insert(0, str(SRC_DIR))

from app.app import app as application  # pyright:ignore[reportUnusedImport]

# TODO: context_types?
# TODO: HATEOAS?
# TODO: SimpleNamespace for req (esp. in request_logger)?
# TODO: Improve Swagger/ReDoc?
# TODO: background tasks?
# TODO: rate-limiting + abuse protection?
# TODO: Check and fix "noqa" and "pyright:ignore"
# TODO: custom exceptions instead of generic ones (ValueError("...")) inside domain/exceptions.py
# TODO: shopping cart?..
# TODO: persistent db sessions / pooling?
# TODO: cache hot rows?
# TODO: intermediate tables?
# TODO: get rid of `assert`
# TODO: make cleaner engine_args
# TODO: nginx instead of py for static files?
