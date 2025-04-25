from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Account username",
        examples=["jane_doe"],
    )
    email: EmailStr = Field(
        ...,
        description="Account email address",
        examples=["jane_doe@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Account password",
        examples=["testpassword"],
    )


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # pyright:ignore[reportUnannotatedClassAttribute]

    id: int = Field(
        ...,
        description="Unique user ID",
        examples=[1, 5, 15],
    )
    username: str = Field(
        ...,
        description="Account username",
        examples=["jane_doe"],
    )
    email: EmailStr = Field(
        ...,
        description="Account email address",
        examples=["jane_doe@example.com"],
    )


class UserError(BaseModel):
    error: str = Field(
        ...,
        description="Error message explaining why the operation failed",
        examples=["User not found"],
    )
    request_id: str | None = None
    # Field(None, description="Request ID for tracing, if any", examples=["abcd1234-5678-90ef-ghij-1234567890kl"])
