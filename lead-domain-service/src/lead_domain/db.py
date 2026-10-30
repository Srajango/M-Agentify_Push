"""Database engine and session management.

When DATABASE_URL is blank (the harness default), the service runs against an
in-process SQLite database held open for the lifetime of the process via
StaticPool, so data survives across requests within a single app instance —
exactly what the test suite and local dev loops need with no live
infrastructure. When DATABASE_URL is set (production), it points at the real
PostgreSQL instance that the authored Alembic migrations under migrations/
target, connected through the psycopg3 driver (psycopg[binary], declared in
requirements.txt) via the postgresql+psycopg:// dialect.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from lead_domain.config import Settings
from lead_domain.exceptions import LeadDomainServiceError
from lead_domain.models import Base


def build_engine(database_url: str):
    """Create a SQLAlchemy engine for the given URL, defaulting to an
    in-process SQLite database when no URL is configured."""

    if not database_url:
        return create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(database_url, pool_pre_ping=True)


class Database:
    """Owns one engine + session factory and creates tables for the
    in-process SQLite fallback (production schema changes are applied by the
    authored Alembic migrations, never by create_all)."""

    def __init__(self, settings: Settings):
        self.engine = build_engine(settings.database_url)
        self.session_factory: sessionmaker[Session] = sessionmaker(
            bind=self.engine, autoflush=False, autocommit=False
        )
        if not settings.database_url:
            Base.metadata.create_all(self.engine)

    def session(self) -> Generator[Session, None, None]:
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except LeadDomainServiceError:
            # A structured domain rejection (404/409/422/403) still commits:
            # automatic transitions already applied earlier in the SAME
            # request (e.g. the quote-expiry check flipping a lead to Lost
            # before raising a 409 on the client's stale accept/decline)
            # are real business state changes, not a failed write, and must
            # not be discarded just because this particular action was
            # itself rejected.
            session.commit()
            raise
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


_database: Database | None = None


def get_database(settings: Settings) -> Database:
    global _database
    if _database is None:
        _database = Database(settings)
    return _database


def reset_database() -> None:
    """Drop the cached Database so a fresh one (and schema) is built on next
    access. Used by tests that need an isolated in-memory database per test."""

    global _database
    _database = None
