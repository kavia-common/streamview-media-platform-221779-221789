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


def _seed(db: Session) -> None:
    # If there is at least one video, assume seeded
    if db.query(Video).count() > 0:
        return

    # Categories
    cats = ["Action", "Comedy", "Drama", "Documentary"]
    cat_objs = []
    for name in cats:
        c = Category(name=name)
        db.add(c)
        cat_objs.append(c)
    db.flush()

    # Create demo files directory
    demo_dir = os.path.join(os.getcwd(), "demo_videos")
    os.makedirs(demo_dir, exist_ok=True)
    # We won't include actual binaries; file paths can be placeholders. Streaming endpoint will 404 if missing.
    # Add videos
    v1 = Video(title="Sample Action", description="An exciting action clip.", file_path=os.path.join(demo_dir, "action.mp4"), featured=1)
    v2 = Video(title="Funny Moments", description="Compilation of funny moments.", file_path=os.path.join(demo_dir, "comedy.mp4"), featured=0)
    db.add_all([v1, v2])
    db.flush()

    # Map categories
    v1.categories.append(cat_objs[0])  # Action
    v2.categories.append(cat_objs[1])  # Comedy

    # Create demo user
    user = User(email="demo@example.com", password_hash=hash_password("password123"))
    db.add(user)

    db.flush()


if __name__ == "__main__":
    ensure_seed()
