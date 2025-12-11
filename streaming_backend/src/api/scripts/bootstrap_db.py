from __future__ import annotations

import os

from sqlalchemy.orm import Session

from src.api.core.db import Base, engine, session_scope
from src.api.models.models import Category, User, Video
from src.api.services.auth import hash_password


def _is_test_env() -> bool:
    """Detect test execution to avoid seeding during tests."""
    return os.getenv("APP_ENV") == "test" or os.getenv("PYTEST_CURRENT_TEST") is not None


def ensure_seed() -> None:
    """Create tables and seed demo data unless running in test environment."""
    Base.metadata.create_all(bind=engine)
    if _is_test_env():
        # Skip seeding in tests so test fixtures remain authoritative.
        return
    with session_scope() as db:
        _seed(db)


def _get_or_create_category(db: Session, name: str) -> Category:
    """Idempotently fetch or create a category by unique name."""
    c = db.query(Category).filter(Category.name == name).first()
    if c:
        return c
    c = Category(name=name)
    db.add(c)
    db.flush()  # Ensure id is available
    return c


def _get_or_create_video(db: Session, title: str, description: str | None, file_path: str, featured: int) -> Video:
    """Idempotently fetch or create a video by title (acting as a unique business key for demo data)."""
    v = db.query(Video).filter(Video.title == title).first()
    if v:
        # Optionally update fields to keep seed current without duplication
        v.description = description
        v.file_path = file_path
        v.featured = featured
        return v
    v = Video(title=title, description=description, file_path=file_path, featured=featured)
    db.add(v)
    db.flush()
    return v


def _get_or_create_user(db: Session, email: str, password: str) -> User:
    """Idempotently fetch or create a user by unique email."""
    u = db.query(User).filter(User.email == email).first()
    if u:
        return u
    u = User(email=email, password_hash=hash_password(password))
    db.add(u)
    db.flush()
    return u


def _seed(db: Session) -> None:
    """Seed demo data idempotently. Safe to run multiple times."""
    # Create demo categories
    demo_categories = ["Action", "Comedy", "Drama", "Documentary"]
    categories = {name: _get_or_create_category(db, name) for name in demo_categories}

    # Ensure demo dir exists (no binaries included)
    demo_dir = os.path.join(os.getcwd(), "demo_videos")
    os.makedirs(demo_dir, exist_ok=True)

    # Create demo videos idempotently
    v1 = _get_or_create_video(
        db,
        title="Sample Action",
        description="An exciting action clip.",
        file_path=os.path.join(demo_dir, "action.mp4"),
        featured=1,
    )
    v2 = _get_or_create_video(
        db,
        title="Funny Moments",
        description="Compilation of funny moments.",
        file_path=os.path.join(demo_dir, "comedy.mp4"),
        featured=0,
    )

    # Map categories if not already linked
    if categories["Action"] not in v1.categories:
        v1.categories.append(categories["Action"])
    if categories["Comedy"] not in v2.categories:
        v2.categories.append(categories["Comedy"])

    # Create demo user idempotently
    _get_or_create_user(db, email="demo@example.com", password="password123")

    db.flush()


if __name__ == "__main__":
    ensure_seed()
