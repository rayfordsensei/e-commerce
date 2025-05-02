from typing import Self

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


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


class UserFilter(BaseModel):
    username_contains: str | None = Field(
        None, description="Only return users with username containing this", examples=["th"]
    )
    email_contains: str | None = Field(
        None, description="Only return users with email containing this", examples=[".com"]
    )
    page: int = Field(1, ge=1, description="Page number (1-based)", examples=[3])
    per_page: int = Field(20, ge=1, le=100, description="Number of items per page", examples=[50])


class UserUpdate(BaseModel):
    username: str | None = Field(
        None,
        min_length=3,
        max_length=50,
        description="New account username",
        examples=["jane_new"],
    )
    email: EmailStr | None = Field(
        None,
        description="New account email address",
        examples=["jane_new@example.com"],
    )

    @model_validator(mode="after")
    def require_username_or_email(self) -> Self:
        if self.username is None and self.email is None:
            raise ValueError("At least one of 'username' or 'email' must be provided")  # noqa: EM101, TRY003
        return self


class UserError(BaseModel):
    error: str = Field(
        ...,
        description="Error message explaining why the operation failed",
        examples=["User not found"],
    )
    request_id: str | None = None
