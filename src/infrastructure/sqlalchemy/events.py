from typing import Any

from loguru import logger
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import Session


def _warn_unexpected_rollback(session: Session) -> None:
    logger.warning("Session {} issued an unexpected ROLLBACK", id(session))

    if session.in_transaction():
        logger.warning("Unexpected open transaction for session {}", id(session))


def register_session_events() -> None:
    event.listen(Session, "after_rollback", _warn_unexpected_rollback, propagate=True)


def register_engine_events(engine: AsyncEngine) -> None:
    def _on_checkout(dbapi_conn: Any, conn_record: Any, conn_proxy: Any):  # pyright:ignore[reportAny, reportExplicitAny]  # noqa: ANN401
        _ = dbapi_conn, conn_proxy

        conn_record.info["checked_out"] = "True"  # pyright:ignore[reportAny]

    def _on_checkin(dbapi_conn: Any, conn_record: Any) -> None:  # noqa: ANN401  # pyright:ignore[reportAny, reportExplicitAny]
        _ = dbapi_conn  # pyright:ignore[reportAny]

        conn_record.info.pop("checked_out", None)  # pyright:ignore[reportAny]

    sync_engine = engine.sync_engine
    event.listen(sync_engine, "checkout", _on_checkout)
    event.listen(sync_engine, "checkin", _on_checkin)
