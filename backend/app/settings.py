"""Explicit local-only settings; database credentials never have a default."""

from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SIPRE_", extra="ignore", hide_input_in_errors=True
    )

    mode: Literal["SIMULATED"] = "SIMULATED"
    database_url: SecretStr | None = None
    db_connect_timeout_seconds: int = Field(default=3, ge=1, le=10)
    session_hours: int = Field(default=8, ge=1, le=24)
    cookie_secure: bool = False  # HTTP localhost demo; require true behind HTTPS.

    @field_validator("database_url")
    @classmethod
    def postgres_only(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None:
            try:
                parsed = make_url(value.get_secret_value())
            except Exception:
                raise ValueError("Database URL must be a PostgreSQL psycopg URL") from None
            if parsed.drivername != "postgresql+psycopg" or not parsed.database:
                raise ValueError("Use postgresql+psycopg and an explicit database")
        return value
