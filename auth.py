import datetime

from joserfc import jwt

from config import settings

SECRET_KEY = settings.SECRET_KEY.encode("utf-8")
ALGORITHM = "HS256"
EXPIRY_HOURS = 4


def create_jwt(user_id: int) -> str:
    header = {
        "alg": ALGORITHM,
    }

    claims = {
        # Cast per JWT standard
        "sub": str(user_id),
        "iat": int(datetime.datetime.now(datetime.UTC).timestamp()),
        "exp": int((datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=EXPIRY_HOURS)).timestamp()),
    }

    return jwt.encode(header=header, claims=claims, key=SECRET_KEY, algorithms=[ALGORITHM])


def verify_jwt(token: str) -> jwt.Claims:
    return jwt.decode(value=token, key=SECRET_KEY, algorithms=[ALGORITHM]).claims
