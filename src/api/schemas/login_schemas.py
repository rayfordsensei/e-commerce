from pydantic import BaseModel, ConfigDict, Field


class LoginIn(BaseModel):
    model_config = ConfigDict(  # pyright:ignore[reportUnannotatedClassAttribute]
        json_schema_extra={
            "description": (
                "Payload for user authentication. Supply `username` and `password` to receive a JWT access token."
            )
        }
    )
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
    model_config = ConfigDict(  # pyright:ignore[reportUnannotatedClassAttribute]
        json_schema_extra={"description": "Authentication response containing the JWT access token."}
    )
    token: str = Field(
        ...,
        description="JWT access token",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9…"],
    )


class AuthError(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Error response returned when authentication fails."})  # pyright:ignore[reportUnannotatedClassAttribute]
    error: str = Field(
        ...,
        description="Error message explaining why authentication failed",
        examples=["Invalid credentials"],
    )
