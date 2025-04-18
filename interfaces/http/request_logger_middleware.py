import logging
import time
import uuid
from typing import final

from falcon import Request, Response

logger = logging.getLogger("app." + __name__)


@final
class RequestLoggerMiddleware:
    """Middleware to log the method, path, and other relevant data for each request.

    Runs before and after each request to capture both inbound and outbound details.
    """

    async def process_request(self, req: Request, resp: Response) -> None:  # noqa: PLR6301
        """Process the incoming request.

        This is called before resource's on_* method is invoked.
        """
        _ = resp

        request_id = req.get_header("X-Request-ID") or str(uuid.uuid4())
        req.context.request_id = request_id
        user_id: int | None = getattr(req.context, "user_id", None)
        query = req.query_string or ""

        if user_id:
            logger.info(
                "Request %s by user %s: %s %s?%s from %s",
                request_id,
                user_id,
                req.method,
                req.path,
                query,
                req.remote_addr,
            )
        else:
            logger.info(
                "Request %s: %s %s?%s from %s",
                request_id,
                req.method,
                req.path,
                query,
                req.remote_addr,
            )

        req.context.start_time = time.time()

    async def process_response(self, req: Request, resp: Response, resource: object, req_succeeded: bool) -> None:  # noqa: FBT001, PLR6301
        """Process the response right before returning it to the client."""
        _ = resource, req_succeeded

        duration: float = time.time() - req.context.start_time  # pyright:ignore[reportAny]  # TODO: SimpleNamespace?
        request_id = getattr(req.context, "request_id", "unknown")
        if not request_id:
            request_id = str(uuid.uuid4())
            req.context.request_id = request_id

        resp.set_header("X-Request-ID", request_id)

        logger.info("Response %s: %s | %s %s (Took %.3fs)", request_id, resp.status, req.method, req.path, duration)
