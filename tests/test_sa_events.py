import pytest
from loguru import logger

from infrastructure.databases.unit_of_work import UnitOfWork
from infrastructure.sqlalchemy.events import register_session_events


@pytest.mark.asyncio
async def test_after_rollback_logs(caplog):  # noqa: ANN001  # pyright:ignore[reportUnknownParameterType, reportMissingParameterType]
    register_session_events()
    caplog.set_level("WARNING", logger="loguru")  # pyright:ignore[reportUnknownMemberType]

    with pytest.raises(RuntimeError):  # noqa: PT012
        async with UnitOfWork() as uow:
            assert uow.users is not None
            _ = await uow.users.list_all()

            raise RuntimeError("force rollback")  # noqa: EM101, TRY003

    assert "issued an unexpected ROLLBACK" in caplog.text  # pyright:ignore[reportUnknownMemberType]
    _ = logger.complete()
