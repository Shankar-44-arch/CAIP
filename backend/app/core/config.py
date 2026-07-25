"""
CAIP-Karnataka — Application Configuration
Simplified per infra instructions: PostgreSQL + Redis only.
No Neo4j, no Kafka — those were removed because (a) no offender graph
data exists to justify Neo4j, and (b) no live incident stream exists
to justify Kafka. See docs/DATA_LIMITATIONS.md and
docs/MIGRATION_MANIFEST.md §1.
"""
from __future__ import annotations

import secrets
from functools import lru_cache
from typing import Any, List, Optional, Union

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore",
    )

    APP_NAME: str = "CAIP — Karnataka Crime Intelligence Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    SECRET_KEY: str = secrets.token_urlsafe(64)
    API_V1_PREFIX: str = "/api/v1"

    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"]
    FRONTEND_URL: Optional[str] = None

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",")]
        return v

    @model_validator(mode="after")
    def add_frontend_url_to_origins(self) -> Settings:
        if self.FRONTEND_URL:
            url = self.FRONTEND_URL.strip()
            if not url.startswith("http://") and not url.startswith("https://"):
                url = f"https://{url}"
            if url not in self.ALLOWED_ORIGINS:
                self.ALLOWED_ORIGINS.append(url)
        return self

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── PostgreSQL ───────────────────────────────────────────
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "caip_karnataka"
    POSTGRES_USER: str = "caip"
    POSTGRES_PASSWORD: str = "caip_secret"
    DATABASE_URL: Optional[str] = None
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    # Supabase / Render-managed Postgres requires SSL; auto-detected from URL
    # when unset. Explicitly set DATABASE_SSL=false for local Docker Postgres.
    DATABASE_SSL: Optional[bool] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def build_db_url(cls, v: Optional[str], info: Any) -> str:
        if v:
            url = v.strip()
            # Normalize postgresql:// -> postgresql+asyncpg://
            if url.startswith("postgresql://") and "+asyncpg" not in url:
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        data = info.data
        return (
            f"postgresql+asyncpg://{data['POSTGRES_USER']}:{data['POSTGRES_PASSWORD']}"
            f"@{data['POSTGRES_HOST']}:{data['POSTGRES_PORT']}/{data['POSTGRES_DB']}"
        )

    @property
    def database_ssl_enabled(self) -> bool:
        if self.DATABASE_SSL is not None:
            return self.DATABASE_SSL
        # Auto-enable SSL for known managed hosts (Supabase, Render, Neon, etc.)
        if self.DATABASE_URL:
            return any(host in self.DATABASE_URL for host in ("supabase.co", "render.com", "neon.tech", "amazonaws.com"))
        return False

    # ── Redis (optional — used only for rate limiting) ──────
    REDIS_ENABLED: bool = False  # off by default in the simplified stack
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: Optional[str] = None

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def build_redis_url(cls, v: Optional[str], info: Any) -> str:
        if v:
            return v
        data = info.data
        return f"redis://{data['REDIS_HOST']}:{data['REDIS_PORT']}/0"

    RATE_LIMIT_PER_MINUTE: int = 120
    LOG_LEVEL: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
