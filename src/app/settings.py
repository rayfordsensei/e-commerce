from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DEBUG: bool
    SECRET_KEY: str
    SQLITE_URI: str
    ALEMBIC_URI: str


settings = Settings()  # pyright:ignore[reportCallIssue] # Pydantic loads .env on runtime, so it doesn't matter
