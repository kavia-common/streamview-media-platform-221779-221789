from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from src.api.core.db import get_db
from src.api.models.models import User
from src.api.schemas.schemas import Message, UserCreate, UserOut
from src.api.services.auth import clear_auth_cookie, create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, summary="Register", description="Register a new user account.")
def register(data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = User(email=data.email, password_hash=hash_password(data.password))
    db.add(user)
    db.flush()
    return user


@router.post("/login", response_model=UserOut, summary="Login", description="Login and set JWT in HttpOnly cookie.")
def login(data: UserCreate, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")

    token = create_access_token(user)
    set_cookie_response(response=response, token=token)
    return user


def set_cookie_response(response: Response, token: str) -> None:
    # wrapper so it shows up in docs more clearly
    from src.api.services.auth import set_auth_cookie

    set_auth_cookie(response, token)


@router.post("/logout", response_model=Message, summary="Logout", description="Clear the auth cookie to logout.")
def logout(response: Response):
    clear_auth_cookie(response)
    return Message(message="Logged out")


@router.get("/me", response_model=UserOut, summary="Current User", description="Return the current authenticated user.")
def me(current_user: User = Depends(get_current_user)):
    return current_user
