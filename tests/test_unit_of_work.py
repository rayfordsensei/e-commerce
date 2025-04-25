import asyncio

import pytest

from domain.users.entities import User
from infrastructure.databases.db import AsyncSessionLocal
from infrastructure.databases.unit_of_work import UnitOfWork
from infrastructure.sqlalchemy.repositories import SQLAlchemyUserRepository


@pytest.mark.asyncio
async def test_uow_commits_changes():
    async with UnitOfWork() as uow:
        assert uow.users is not None

        new_user = User(id=None, username="uow_user", email="uow@example.com", password_hash="x")  # noqa: S106
        created = await uow.users.add(new_user)
        assert created.id is not None
    await asyncio.sleep(0)

    async with AsyncSessionLocal() as verify_sess:
        repo = SQLAlchemyUserRepository(session=verify_sess)
        fetched = await repo.get(created.id)
        assert fetched is not None
        assert fetched.username == "uow_user"
    await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_uow_rolls_back_on_error():
    with pytest.raises(ValueError):  # noqa: PT011, PT012
        async with UnitOfWork() as uow:
            assert uow.users is not None

            _ = await uow.users.add(User(id=None, username="will_fail", email="fail@example.com", password_hash="x"))  # noqa: S106
            raise ValueError("Force rollback")  # noqa: EM101, TRY003

    async with AsyncSessionLocal() as verify_sess:
        repo = SQLAlchemyUserRepository(session=verify_sess)
        none_user = await repo.get_by_username("will_fail")
        assert none_user is None
    await asyncio.sleep(0)
