from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session

from src.api.core.config import get_settings


class Base(DeclarativeBase):
    """Base class for declarative SQLAlchemy models."""


def _ensure_db_dir(path: str) -> None:
    db_dir = os.path.dirname(path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)


def get_engine_url() -> str:
    settings = get_settings()
    _ensure_db_dir(settings.sqlite_db_path)
    return f"sqlite:///{settings.sqlite_db_path}"


engine = create_engine(
    get_engine_url(),
    connect_args={"check_same_thread": False},  # Required for SQLite with threads
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)


# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency to provide a database session per request."""
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager for DB sessions for scripts."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
