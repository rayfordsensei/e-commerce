from typing import Any

import bcrypt
import falcon


def error_response(resp: falcon.Response, status_code: str, message: str, request_id: str | None = None):
    resp.status = status_code
    resp.media = {"error": message}
    if request_id:
        resp.media["request_id"] = request_id


def get_missing_fields(data: dict[str, Any], required_fields: list[str]) -> list[str]:  # pyright:ignore[reportExplicitAny]
    return [field for field in required_fields if not data.get(field)]


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())
