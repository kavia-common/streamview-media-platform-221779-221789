from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.api.core.db import Base

# Association table for many-to-many Videos <-> Categories
video_categories = Table(
    "video_categories",
    Base.metadata,
    Column("video_id", ForeignKey("videos.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    history: Mapped[List["WatchHistory"]] = relationship("WatchHistory", back_populates="user", cascade="all, delete-orphan")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)

    videos: Mapped[List["Video"]] = relationship(
        secondary=video_categories,
        back_populates="categories",
        lazy="selectin",
    )


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    featured: Mapped[int] = mapped_column(Integer, default=0)  # 0/1 to keep SQLite simple
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    categories: Mapped[List[Category]] = relationship(
        secondary=video_categories,
        back_populates="videos",
        lazy="selectin",
    )

    history: Mapped[List["WatchHistory"]] = relationship("WatchHistory", back_populates="video", cascade="all, delete-orphan")


class WatchHistory(Base):
    __tablename__ = "watch_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    watched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship("User", back_populates="history")
    video: Mapped[Video] = relationship("Video", back_populates="history")
