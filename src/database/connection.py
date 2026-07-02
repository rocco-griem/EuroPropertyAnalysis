"""Database engine/session management.

Centralises SQLAlchemy engine creation so every other module gets the same configured
engine/session instead of re-reading `DATABASE_URL` itself.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config.settings import DATABASE_DIR, DATABASE_URL
from src.database.models import Base

# SQLite needs its parent directory to exist before the engine can create the file.
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

# `check_same_thread` is a SQLite-only connect arg; other drivers (e.g. psycopg) would
# reject it, so only pass it when the URL is actually SQLite.
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    """Create all tables that don't already exist. Safe to call repeatedly."""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session() -> Iterator[Session]:
    """Yield a session; commit on success, roll back and re-raise on error."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
