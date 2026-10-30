"""Service configuration, read once at startup from environment variables."""

from __future__ import annotations

from decimal import Decimal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed configuration bound to the exact environment variable names the
    platform harness emits. Every field uses an explicit alias so a second,
    differently-cased variable is never required.
    """

    model_config = SettingsConfigDict(populate_by_name=True, extra="ignore")

    dry_run: bool = Field(default=True, alias="DRY_RUN")
    database_url: str = Field(default="", alias="DATABASE_URL")
    orchestrator_events_url: str = Field(
        default="http://orchestrator.internal/events",
        alias="ORCHESTRATOR_EVENTS_URL",
    )
    rate_card_third_party_base_premium: Decimal = Field(
        default=Decimal("2072.00"), alias="RATE_CARD_THIRD_PARTY_BASE_PREMIUM"
    )
    rate_card_own_damage_rate: Decimal = Field(
        default=Decimal("0.035"), alias="RATE_CARD_OWN_DAMAGE_RATE"
    )


def get_settings() -> Settings:
    """Build a fresh Settings instance from the current environment.

    Not cached at module scope: tests set DRY_RUN per-test and must see the
    change without a process restart.
    """

    return Settings()
