"""Application configuration."""
from functools import lru_cache
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_name: str = "Running Stats Dashboard API"
    debug: bool = False

    # Database (Render etc. give postgresql:// – we need postgresql+asyncpg://)
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/running_stats"

    database_echo: bool = False

    @field_validator("database_url")
    @classmethod
    def ensure_asyncpg(cls, v: str) -> str:
        # Render and others may give postgresql:// or postgresql+psycopg2://; we need asyncpg
        if "+asyncpg" in v:
            return v
        if "psycopg2" in v:
            return v.replace("postgresql+psycopg2", "postgresql+asyncpg", 1)
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"

    # JWT
    secret_key: str = "change-me-in-production-use-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # S3 / object storage (optional)
    s3_endpoint_url: Optional[str] = None
    s3_bucket: str = "running-stats-uploads"
    s3_region: str = "us-east-1"
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None
    use_s3: bool = False


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
