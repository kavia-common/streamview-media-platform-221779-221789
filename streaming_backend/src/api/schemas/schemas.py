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
    password: str = Field(..., min_length=6, description="User password.")


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
