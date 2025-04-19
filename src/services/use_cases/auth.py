from dataclasses import dataclass

from common.utils import verify_password
from domain.auth.auth import AbstractTokenIssuer
from domain.users.repositories import AbstractUserRepository
from services.use_cases import BaseUseCase


@dataclass(slots=True)
class AuthenticateUser(BaseUseCase[AbstractUserRepository]):
    """Check credentials and return a signed JWT."""

    _issuer: AbstractTokenIssuer

    async def __call__(self, username: str, password: str) -> str:
        user = await self._repo.get_by_username(username)
        if user is None or not verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")  # 401?  # noqa: EM101, TRY003

        if user.id is None:
            raise RuntimeError("Cannot issue token: user ID is missing.")  # noqa: EM101, TRY003

        return self._issuer.issue(user.id)
