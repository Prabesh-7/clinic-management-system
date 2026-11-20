from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Clinic Management System API"
    app_env: Literal["development", "testing", "production"] = "development"
    debug: bool = False
    database_url: str | None = None
    jwt_secret: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_minutes: int = 60
    invite_token_hours: int = 72
    invite_accept_url: str = "http://localhost:3000/set-password"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_use_tls: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
