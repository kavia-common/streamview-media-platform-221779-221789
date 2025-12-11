import os
import tempfile
from contextlib import contextmanager
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.api.main import create_app
from src.api.core import db as db_module
from src.api.models.models import Base  # type: ignore[attr-defined]

# Ensure that anything checking APP_ENV or pytest env detects test mode
os.environ.setdefault("APP_ENV", "test")


@contextmanager
def override_db(sqlite_path: str) -> Generator[None, None, None]:
    """
    Temporarily override the DB engine and SessionLocal in src.api.core.db
    to point to the provided sqlite file path.
    """
    original_engine = db_module.engine
    original_sessionlocal = db_module.SessionLocal

    engine = create_engine(
        f"sqlite:///{sqlite_path}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)

    db_module.engine = engine
    db_module.SessionLocal = SessionLocal
    try:
        yield
    finally:
        # restore originals
        db_module.engine = original_engine
        db_module.SessionLocal = original_sessionlocal


@pytest.fixture(scope="session")
def tmp_db_file() -> Generator[str, None, None]:
    """
    Creates a temporary SQLite database file path for the test session.
    The file is cleaned up after tests.
    """
    fd, path = tempfile.mkstemp(prefix="test_app_", suffix=".db")
    os.close(fd)
    try:
        yield path
    finally:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass


@pytest.fixture(scope="session")
def app(tmp_db_file: str):
    """
    Create the FastAPI app and initialize schema on a temporary SQLite DB.
    """
    with override_db(tmp_db_file):
        # Create tables
        Base.metadata.create_all(bind=db_module.engine)
        app = create_app()
        yield app


def _truncate_domain_tables() -> None:
    """
    Ensure a deterministic clean state for domain tables that affect listings.
    Truncates (DELETEs) rows from association and dependent tables first.
    """
    # Import inline to avoid circulars at module import time
    from src.api.models.models import video_categories  # type: ignore
    from src.api.models.models import WatchHistory, Video, Category, User  # noqa

    with db_module.session_scope() as s:
        # Association table must be cleared prior to videos/categories to respect FKs.
        s.execute(video_categories.delete())  # raw delete on association table
        # Clear history then videos and categories
        s.query(WatchHistory).delete()
        s.query(Video).delete()
        s.query(Category).delete()
        # Users are left intact for auth-related tests; they don't affect /videos or /categories


@pytest.fixture(autouse=True)
def clean_tables_before_test():
    """
    Auto-used fixture to clear domain tables before each test to avoid cross-test contamination.
    """
    _truncate_domain_tables()
    yield


@pytest.fixture()
def client(app):
    """
    FastAPI TestClient that preserves cookies between requests for auth flows.
    """
    with TestClient(app) as c:
        yield c
