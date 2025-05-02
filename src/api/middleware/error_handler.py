import uuid
from typing import Any

import falcon
from falcon.asgi import WebSocket
from loguru import logger


async def generic_error_handler(  # noqa: RUF029
    req: falcon.Request,
    resp: falcon.Response | None,
    error: BaseException,
    params: dict[str, Any],
    *,
    ws: WebSocket | None = None,
) -> None:
    """One place to normalise *all* errors.

    * Adds/propagates `X-Request-ID`
    * Serialises body as `{"error": ..., "request_id": ...}`
    * Logs unexpected exceptions with stack-trace
    """
    _ = params, ws, req

    request_id = getattr(req.context, "request_id", str(uuid.uuid4()))

    if isinstance(error, falcon.HTTPError):
        status = error.status

        title = "Not Found" if status == falcon.HTTP_404 else error.title or "Error"

        body = {"error": title}

        if error.description:
            body["description"] = error.description

    else:
        status = falcon.HTTP_500
        body = {"error": "Internal Server Error"}
        logger.exception("Unhandled exception", exc_info=error)

    body["request_id"] = request_id

    if resp is not None:
        resp.set_header("X-Request-ID", request_id)
        resp.status = status
        resp.media = body
