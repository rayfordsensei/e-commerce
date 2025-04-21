from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        description="Account username",
        examples=["jane_doe"],
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Account password",
        examples=["testpassword"],
    )


class TokenOut(BaseModel):
    token: str = Field(
        ...,
        description="JWT access token",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9…"],
    )


class AuthError(BaseModel):
    error: str = Field(
        ...,
        description="Error message explaining why authentication failed",
        examples=["Invalid credentials"],
    )
