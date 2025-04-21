from pydantic import BaseModel, ConfigDict, Field


class OrderCreate(BaseModel):
    user_id: int = Field(
        ...,
        gt=0,
        description="ID of the user placing the order",
        examples=[1, 15, 25],
    )
    total_price: float = Field(
        ...,
        ge=0,
        description="Total price of the order",
        examples=[1.99, 9.99],
    )


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # pyright:ignore[reportUnannotatedClassAttribute]

    id: int = Field(
        ...,
        description="Unique order ID",
        examples=[123, 15, 3],
    )
    user_id: int = Field(
        ...,
        description="ID of the user who placed the order",
        examples=[42, 5, 15],
    )
    total_price: float = Field(
        ...,
        description="Order total price",
        examples=[99.95, 19.99],
    )
    created_at: str = Field(
        ...,
        description="Timestamp when the order was created",
        examples=[],  # TODO: add examples? isoformat (ISO 8601?)?..
    )


class OrderFilter(BaseModel):
    user_id: int | None = Field(
        None,
        gt=0,
        description="Only return orders for this user ID (optional)",
        examples=[1, 15, 25],
    )


class OrderUpdate(BaseModel):
    total_price: float = Field(
        ...,
        ge=0,
        description="New total price for the order",
        examples=[79.90, 12.50],
    )


class OrderError(BaseModel):
    error: str = Field(
        ...,
        description="Error message explaining why the operation failed",
        examples=["Order not found"],
    )
    request_id: str | None = Field(
        None,
        description="Request ID for tracing, if any",
        examples=["abcd1234-5678-90ef-ghij-1234567890kl"],
    )
