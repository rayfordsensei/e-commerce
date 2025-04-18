from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    total_price: float = Field(..., ge=0)


class OrderOut(BaseModel):
    id: int
    user_id: int
    total_price: float
    created_at: str  # isoformat?..
