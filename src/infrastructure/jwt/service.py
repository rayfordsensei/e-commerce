import datetime
from typing import Final, override

from joserfc import jwt

from app.settings import settings
from domain.auth.auth import AbstractTokenIssuer, AbstractTokenVerifier

_SECRET: Final[bytes] = settings.SECRET_KEY.encode()
_ALG: Final[str] = "HS256"
_TTL_HOURS: Final[int] = 4


class JsonWebTokenService(AbstractTokenIssuer, AbstractTokenVerifier):
    @override
    def issue(self, user_id: int) -> str:
        now = datetime.datetime.now(datetime.UTC)
        header = {"alg": _ALG}
        claims = {
            "sub": str(user_id),
            "iat": int(now.timestamp()),
            "exp": int((now + datetime.timedelta(hours=_TTL_HOURS)).timestamp()),
        }

        return jwt.encode(header=header, claims=claims, key=_SECRET, algorithms=[_ALG])

    @override
    def verify(self, token: str) -> int:
        claims = jwt.decode(value=token, key=_SECRET, algorithms=[_ALG]).claims
        return int(claims["sub"])  # pyright:ignore[reportAny]
