from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProductCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the product",
        examples=["Wireless Mouse"],
    )
    description: str = Field(
        default="",
        max_length=255,
        description="Longer description or details about the product",
        examples=["A comfortable ergonomic wireless mouse"],
    )
    price: float = Field(
        ...,
        ge=0,
        description="Unit price",
        examples=[29.99],
    )
    stock: int = Field(
        ...,
        ge=0,
        description="Available inventory count",
        examples=[150],
    )


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # pyright:ignore[reportUnannotatedClassAttribute]

    id: int = Field(
        ...,
        description="Unique product ID",
        examples=[123],
    )
    name: str = Field(
        ...,
        description="Name of the product",
        examples=["Wireless Mouse"],
    )
    description: str = Field(
        ...,
        description="Product details",
        examples=["A comfortable ergonomic wireless mouse"],
    )
    price: float = Field(
        ...,
        description="Unit price in EUR",
        examples=[29.99],
    )
    stock: int = Field(
        ...,
        description="Available inventory",
        examples=[150],
    )


class ProductUpdate(BaseModel):
    price: float | None = Field(
        None,
        ge=0,
        description="New unit price in EUR",
        examples=[24.99],
    )
    stock: int | None = Field(
        None,
        ge=0,
        description="New inventory count",
        examples=[200],
    )

    @model_validator(mode="after")
    def require_price_or_stock(self) -> Self:
        """Ensure that at least one of price or stock is provided."""  # noqa: DOC201, DOC501
        if self.price is None and self.stock is None:
            raise ValueError("At least one of 'price' or 'stock' must be provided")  # noqa: EM101, TRY003
        return self


class ProductError(BaseModel):
    error: str = Field(
        ...,
        description="Error message explaining why the operation failed",
        examples=["Product not found"],
    )
    request_id: str | None = None
    # Field(None, description="Request ID for tracing, if any", examples=["abcd1234-5678-90ef-ghij-1234567890kl"])
