from typing import final

from domain.auth import AbstractTokenIssuer
from domain.repositories import AbstractUserRepository
from shared.utils import verify_password


@final
class AuthenticateUser:
    """Check credentials and return a signed JWT."""

    def __init__(self, users: AbstractUserRepository, issuer: AbstractTokenIssuer) -> None:
        self._users = users
        self._issuer = issuer

    async def __call__(self, username: str, password: str) -> str:
        user = await self._users.get_by_username(username)
        if user is None or not verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")  # 401?  # noqa: EM101, TRY003

        if user.id is None:
            raise RuntimeError("Cannot issue token: user ID is missing.")  # noqa: EM101, TRY003

        return self._issuer.issue(user.id)
