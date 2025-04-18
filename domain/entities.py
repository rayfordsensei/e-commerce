from dataclasses import dataclass
from datetime import datetime


@dataclass
class Order:
    id: int | None
    user_id: int
    total_price: float
    created_at: datetime  # TODO: ...iso?


@dataclass
class Product:
    id: int | None
    name: str
    description: str
    price: float
    stock: int


@dataclass
class User:
    id: int | None
    username: str
    email: str
    password_hash: str
