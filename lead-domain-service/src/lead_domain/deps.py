"""FastAPI dependency providers: config, database session and event
publisher, all built from the single Settings object read once per
request."""

from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from lead_domain.config import Settings, get_settings
from lead_domain.db import get_database
from lead_domain.events import EventPublisher


def settings_dependency() -> Settings:
    return get_settings()


def session_dependency(
    settings: Settings = Depends(settings_dependency),
) -> Generator[Session, None, None]:
    database = get_database(settings)
    yield from database.session()


def publisher_dependency(settings: Settings = Depends(settings_dependency)) -> EventPublisher:
    return EventPublisher(settings)
