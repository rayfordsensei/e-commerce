from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DEBUG: bool
    SECRET_KEY: str
    SQLITE_URI: str

    class Config:
        env_file: str = ".env"
        env_file_encoding: str = "utf-8"


settings = Settings()  # pyright:ignore[reportCallIssue] # Pydantic loads .env on runtime, so it doesn't matter
