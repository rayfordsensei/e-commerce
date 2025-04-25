from dataclasses import dataclass
from datetime import datetime


@dataclass
class Order:
    id: int | None
    user_id: int
    total_price: float
    created_at: datetime | None = None
