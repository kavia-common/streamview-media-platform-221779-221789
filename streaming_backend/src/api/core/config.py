import os
from functools import lru_cache
from typing import List

from pydantic import BaseModel


class Settings(BaseModel):
    """Application settings loaded from environment variables."""
    app_name: str = "StreamView Backend"
    debug: bool = False
    # CORS
    allowed_origins: List[str] = []
    allowed_methods: List[str] = ["*"]
    allowed_headers: List[str] = ["*"]
    allow_credentials: bool = True

    # Cookies / domain
    cookie_domain: str | None = None
    # Secure=False in development, True when NODE_ENV=production
    cookie_secure: bool = True
    # SameSite default Lax to support first-party cookie semantics
    cookie_samesite: str = "lax"

    # JWT
    jwt_secret_key: str = "CHANGE_ME_SECRET"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expires_minutes: int = 60 * 24 * 7  # 7 days

    # Database
    # Resolved from SQLITE_DB (provided by streaming_db) or local fallback ./db/app.db
    sqlite_db_path: str = os.path.join(os.getcwd(), "db", "app.db")

    # Misc
    site_url: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        # Load allowed origins from env (comma separated)
        allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "")
        cookie_domain = os.getenv("COOKIE_DOMAIN")
        site_url = os.getenv("SITE_URL")

        # DB path - prefer SQLITE_DB from database container if set
        sqlite_db_path = os.getenv("SQLITE_DB") or os.path.join(os.getcwd(), "db", "app.db")

        jwt_secret_key = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_SECRET")
        jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        jwt_exp = int(os.getenv("JWT_ACCESS_EXPIRES_MIN", str(60 * 24 * 7)))

        # Default CORS allowlist if env not provided
        default_allowed_origins = ["http://localhost:3000", "http://localhost:5173"]
        env_origins = [o.strip() for o in allowed_origins_raw.split(",") if o.strip()]
        allowed_origins = env_origins or default_allowed_origins

        # Determine secure cookie flag based on environment; default to development
        node_env = os.getenv("NODE_ENV", "development").lower()
        cookie_secure = node_env == "production"

        return cls(
            debug=os.getenv("DEBUG", "false").lower() == "true",
            allowed_origins=allowed_origins,
            allowed_methods=(os.getenv("ALLOWED_METHODS", "") or "*").split(",") if os.getenv("ALLOWED_METHODS") else ["*"],
            allowed_headers=(os.getenv("ALLOWED_HEADERS", "") or "*").split(",") if os.getenv("ALLOWED_HEADERS") else ["*"],
            allow_credentials=True,
            cookie_domain=cookie_domain,
            cookie_secure=cookie_secure,
            cookie_samesite=os.getenv("COOKIE_SAMESITE", "lax"),
            jwt_secret_key=jwt_secret_key,
            jwt_algorithm=jwt_algorithm,
            jwt_access_token_expires_minutes=jwt_exp,
            sqlite_db_path=sqlite_db_path,
            site_url=site_url,
        )


# PUBLIC_INTERFACE
@lru_cache
def get_settings() -> Settings:
    """Return cached application settings loaded from environment variables."""
    return Settings.from_env()
