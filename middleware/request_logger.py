import logging
import time

from falcon import Request, Response

logger = logging.getLogger(__name__)


class RequestLoggerMiddleware:
    """Middleware to log the method, path, and other relevant data for each request.

    Runs before and after each request to capture both inbound and outbound details.
    """

    async def process_request(self, req: Request, resp: Response) -> None:  # noqa: PLR6301
        """Process the incoming request.

        This is called before resource's on_* method is invoked.
        """
        _ = resp

        logger.info("Incoming request: %s %s from %s", req.method, req.path, req.remote_addr)
        req.context.start_time = time.time()

    async def process_response(self, req: Request, resp: Response, resource: object, req_succeeded: bool) -> None:  # noqa: FBT001, PLR6301
        """Process the response right before returning it to the client."""
        _ = resource, req_succeeded

        duration: float = time.time() - req.context.start_time  # pyright:ignore[reportAny]  # TODO: SimpleNamespace?

        logger.info("Response status: %s | %s %s (%.4fs)", resp.status, req.method, req.path, duration)
