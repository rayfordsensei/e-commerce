from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=255)
    price: float = Field(..., ge=0)
    stock: int = Field(..., ge=0)


class ProductOut(BaseModel):
    id: int
    name: str
    description: str
    price: float
    stock: int
