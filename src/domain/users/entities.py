from dataclasses import dataclass


@dataclass
class User:
    id: int | None
    username: str
    email: str
    password_hash: str
