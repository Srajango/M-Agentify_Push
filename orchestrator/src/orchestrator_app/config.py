"""Runtime configuration for the orchestrator service.

Settings bind environment variables using Pydantic aliases so the harness's
upper-snake-case env vars (``DRY_RUN``, ``DATABASE_URL``, ``LEAD_DOMAIN_SERVICE_URL``)
are read directly without a second lowercase fallback.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Service settings sourced from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    dry_run: bool = Field(default=True, alias="DRY_RUN")
    database_url: str = Field(default="", alias="DATABASE_URL")
    lead_domain_service_url: str = Field(
        default="http://mock-lead-domain-service:5097",
        alias="LEAD_DOMAIN_SERVICE_URL",
    )
    domain_client_timeout_seconds: float = Field(
        default=5.0, alias="DOMAIN_CLIENT_TIMEOUT_SECONDS"
    )
    domain_client_max_retries: int = Field(
        default=3, alias="DOMAIN_CLIENT_MAX_RETRIES"
    )
    domain_client_backoff_base_seconds: float = Field(
        default=0.1, alias="DOMAIN_CLIENT_BACKOFF_BASE_SECONDS"
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Cached so every module shares one parsed configuration; tests that need a
    fresh read after mutating ``os.environ`` should call ``get_settings.cache_clear()``.
    """

    return Settings()
