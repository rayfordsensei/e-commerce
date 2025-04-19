from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)


class TokenOut(BaseModel):
    token: str
