import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.core.config import get_settings
from src.api.core.db import Base, engine
from src.api.routers.auth import router as auth_router
from src.api.routers.videos import router as videos_router

openapi_tags = [
    {"name": "Authentication", "description": "User authentication and identity."},
    {"name": "Videos", "description": "Video listing, categories, streaming and history."},
]


def _is_test_env() -> bool:
    """Detect if running under tests to avoid demo seeding and other side effects."""
    # Prefer explicit APP_ENV=test or pytest's injected env var
    return os.getenv("APP_ENV") == "test" or os.getenv("PYTEST_CURRENT_TEST") is not None


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Configures:
    - Database and auto-creates tables
    - CORS (allow_credentials=True, default origins localhost:3000/5173)
    - Routers for authentication and videos
    """
    settings = get_settings()
    app = FastAPI(
        title="StreamView Backend",
        description="REST API for StreamView: auth (JWT via HttpOnly cookie), videos, categories, history, and streaming.",
        version="1.0.0",
        openapi_tags=openapi_tags,
    )

    # Database: create tables if not present
    Base.metadata.create_all(bind=engine)

    # IMPORTANT: Do not auto-seed during tests.
    # If any bootstrap/seed logic is introduced elsewhere, ensure it checks _is_test_env()
    # so that tests control their own fixtures (/videos and /categories reflect only test seeds).
    if not _is_test_env():
        # No implicit seeding here; left intentionally blank to avoid altering DB state unexpectedly.
        # Seeding is available via manual script: python -m src.api.scripts.bootstrap_db
        # If you add any automated seeding, it MUST guard using _is_test_env() or APP_ENV=='test'
        # or presence of PYTEST_CURRENT_TEST to avoid interference with CI.
        pass

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins or ["http://localhost:3000", "http://localhost:5173"],
        allow_credentials=settings.allow_credentials,
        allow_methods=settings.allowed_methods or ["*"],
        allow_headers=settings.allowed_headers or ["*"],
    )

    @app.get("/", summary="Health Check")
    def health_check():
        """Simple health check endpoint."""
        return {"message": "Healthy"}

    # Routers
    app.include_router(auth_router)
    app.include_router(videos_router)

    return app


app = create_app()
