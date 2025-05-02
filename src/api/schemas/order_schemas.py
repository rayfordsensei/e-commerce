from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, FieldSerializationInfo, field_serializer


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
    created_at: datetime = Field(
        ...,
        description="Timestamp when the order was created (ISO 8601)",
        examples=["2025-04-22T12:34:56.789012+00:00"],
    )

    @field_serializer("created_at")
    @staticmethod
    def _serialize_created_at(dt: datetime, _info: FieldSerializationInfo) -> str:
        # Accept the datetime from domain/repo and emit an ISO string
        return dt.isoformat()


class OrderFilter(BaseModel):
    user_id: int | None = Field(None, gt=0, description="Only return orders for this user ID", examples=[1, 15, 25])
    page: int = Field(1, ge=1, description="Page number (1-based)", examples=[3])
    per_page: int = Field(20, ge=1, le=100, description="Number of items per page", examples=[50])


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
    request_id: str | None = None
    # Field(None, description="Request ID for tracing, if any", examples=["abcd1234-5678-90ef-ghij-1234567890kl"])
