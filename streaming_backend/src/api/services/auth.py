from __future__ import annotations

import time
from typing import Optional

from fastapi import Depends, HTTPException, Request, Response, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.api.core.config import get_settings
from src.api.core.db import get_db
from src.api.models.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user: User) -> str:
    settings = get_settings()
    expire_min = settings.jwt_access_token_expires_minutes
    exp = int(time.time() + expire_min * 60)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "exp": exp,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def set_auth_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,  # 'lax' or 'none' if cross-site
        domain=settings.cookie_domain,
        max_age=settings.jwt_access_token_expires_minutes * 60,
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key="access_token",
        domain=settings.cookie_domain,
        path="/",
    )


# PUBLIC_INTERFACE
def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency that extracts current user from JWT cookie, or raises 401."""
    token: Optional[str] = request.cookies.get("access_token")
    settings = get_settings()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id: int = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
