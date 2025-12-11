from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class Message(BaseModel):
    message: str = Field(..., description="Human-readable message.")


class TokenPayload(BaseModel):
    sub: str = Field(..., description="Subject (user id).")
    email: EmailStr = Field(..., description="User email.")
    exp: int = Field(..., description="Expiration as epoch seconds.")


class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="User email address.")
    # We enforce bcrypt-safe limits by rejecting passwords longer than 72 bytes,
    # which for UTF-8 is approximated here by max_length=72 characters.
    # This aligns with auth service which truncates to 72 bytes before hashing.
    password: str = Field(
        ...,
        min_length=6,
        max_length=72,
        description="User password. Max 72 characters due to bcrypt limits.",
    )


class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


class CategoryOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class VideoOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    featured: int
    created_at: datetime
    categories: List[CategoryOut] = []

    class Config:
        from_attributes = True


class HistoryOut(BaseModel):
    id: int
    watched_at: datetime
    video: VideoOut

    class Config:
        from_attributes = True
