from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator, model_validator
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
    jwt_secret: str | None = None
    jwt_algorithm: str = "HS256"
    jwt_access_token_minutes: int = 60

    @field_validator("jwt_secret", mode="before")
    @classmethod
    def validate_jwt_secret(cls, value: str | None) -> str:
        if value is None or not value.strip():
            raise ValueError("JWT_SECRET is required")
        if len(value.strip()) < 32:
            raise ValueError(
                "JWT_SECRET must contain at least 32 characters"
            )
        if value.strip().lower() in {
            "change-this-in-production",
            "replace-with-at-least-32-random-characters",
        }:
            raise ValueError("JWT_SECRET must be replaced with a random secret")
        return value

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.app_env == "production" and self.debug:
            raise ValueError("DEBUG must be false in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
