import asyncio
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(Path(__file__).parent / os.pardir).resolve()
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from infrastructure.databases.db import AsyncSessionLocal
from infrastructure.sqlalchemy.events import register_session_events

register_session_events()


async def trigger_rollback_via_exception():
    async with AsyncSessionLocal() as session, session.begin():
        print("About to raise!")
        raise RuntimeError("💥 force rollback!")  # noqa: EM101, TRY003


if __name__ == "__main__":
    asyncio.run(trigger_rollback_via_exception())
