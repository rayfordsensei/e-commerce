import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any, Literal, TypedDict, final

logger = logging.getLogger(__name__)


# ASGI lifespan message types
class LifespanStartupMessage(TypedDict):
    type: Literal["lifespan.startup"]


class LifespanShutdownMessage(TypedDict):
    type: Literal["lifespan.shutdown"]


class LifespanStartupComplete(TypedDict):
    type: Literal["lifespan.startup.complete"]


class LifespanStartupFailed(TypedDict):
    type: Literal["lifespan.startup.failed"]
    message: str


class LifespanShutdownComplete(TypedDict):
    type: Literal["lifespan.shutdown.complete"]


class LifespanShutdownFailed(TypedDict):
    type: Literal["lifespan.shutdown.failed"]
    message: str


LifespanReceiveMessage = LifespanStartupMessage | LifespanShutdownMessage
LifespanSendMessage = (
    LifespanStartupComplete | LifespanStartupFailed | LifespanShutdownComplete | LifespanShutdownFailed
)

# lifespan only?..
ASGIScope = dict[str, Any]  # pyright:ignore[reportExplicitAny]  # broad scope to avoid errors in falcon.asgi.App
ASGIReceive = Callable[[], Awaitable[dict[str, Any]]]  # pyright:ignore[reportExplicitAny]
ASGISend = Callable[[dict[str, Any]], Awaitable[None]]  # pyright:ignore[reportExplicitAny]


@final
class LifespanMiddleware:
    def __init__(
        self,
        app: Callable[[ASGIScope, ASGIReceive, ASGISend], Awaitable[None]],
        startup_task: Callable[[], Awaitable[None]] | None = None,
        shutdown_task: Callable[[], Awaitable[None]] | None = None,
    ) -> None:
        self.app = app
        self.startup_task = startup_task
        self.shutdown_task = shutdown_task
        self.started = False
        self._lock = asyncio.Lock()

    async def _ensure_started(self) -> None:
        """Ensure that the startup task is run only once."""
        if not self.started and self.startup_task:
            async with self._lock:
                if not self.started:
                    await self.startup_task()
                    self.started = True

    async def _handle_startup(self, send: ASGISend) -> None:
        """Handle the lifespan startup message."""
        try:
            await self._ensure_started()
            await send({"type": "lifespan.startup.complete"})

        except Exception as e:
            logger.exception("Startup failed")
            await send({"type": "lifespan.startup.failed", "message": str(e)})

    async def _handle_shutdown(self, send: ASGISend) -> None:
        """Handle the lifespan shutdown message."""
        try:
            if self.shutdown_task:
                await self.shutdown_task()
            logger.info("Lifespan shutdown complete")
            await send({"type": "lifespan.shutdown.complete"})

        except Exception as e:
            logger.exception("Lifespan shutdown failed")
            await send({"type": "lifespan.shutdown.failed", "message": str(e)})

    async def __call__(self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend) -> None:
        if scope["type"] != "lifespan":
            # For HTTP and other non-lifespan scopes make sure the app is started.
            await self._ensure_started()
            await self.app(scope, receive, send)
            return

        while True:
            message = await receive()
            message_type = message.get("type")
            if message_type == "lifespan.startup":
                await self._handle_startup(send)
            elif message_type == "lifespan.shutdown":
                await self._handle_shutdown(send)
                return
