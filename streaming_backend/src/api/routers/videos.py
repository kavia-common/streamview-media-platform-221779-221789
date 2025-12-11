from __future__ import annotations

import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.api.core.db import get_db
from src.api.models.models import Category, Video, WatchHistory
from src.api.schemas.schemas import CategoryOut, HistoryOut, Message, VideoOut
from src.api.services.auth import get_current_user

router = APIRouter(tags=["Videos"])


@router.get("/videos", response_model=List[VideoOut], summary="List Videos", description="List videos optionally filtered by category or search.")
def list_videos(
    q: Optional[str] = Query(None, description="Search term on title/description"),
    category_id: Optional[int] = Query(None, description="Filter by category id"),
    db: Session = Depends(get_db),
):
    query = db.query(Video)
    if q:
        like = f"%{q}%"
        query = query.filter((Video.title.like(like)) | (Video.description.like(like)))
    if category_id:
        query = query.join(Video.categories).filter(Category.id == category_id)
    videos = query.order_by(Video.created_at.desc()).all()
    return videos


@router.get("/videos/featured", response_model=List[VideoOut], summary="Featured Videos", description="List featured videos.")
def featured_videos(db: Session = Depends(get_db)):
    videos = db.query(Video).filter(Video.featured == 1).order_by(Video.created_at.desc()).all()
    return videos


@router.get("/categories", response_model=List[CategoryOut], summary="Categories", description="List all categories.")
def categories(db: Session = Depends(get_db)):
    cats = db.query(Category).order_by(Category.name.asc()).all()
    return cats


def _open_file_range(file_path: str, start: int, end: int, chunk_size: int = 1024 * 1024):
    with open(file_path, "rb") as f:
        f.seek(start)
        remaining = end - start + 1
        while remaining > 0:
            read_len = min(chunk_size, remaining)
            data = f.read(read_len)
            if not data:
                break
            remaining -= len(data)
            yield data


@router.get("/stream/{video_id}", summary="Stream Video", description="Stream video content with HTTP Range support.", responses={
    200: {"description": "OK"},
    206: {"description": "Partial Content"},
    404: {"description": "Video not found"},
})
def stream_video(
    video_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),  # require auth to stream
):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    file_path = video.file_path
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video file missing")

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("range")
    start, end = 0, file_size - 1

    if range_header:
        # Example: "bytes=0-1023"
        units, _, range_spec = range_header.partition("=")
        if units.strip().lower() != "bytes":
            raise HTTPException(status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE, detail="Invalid unit")
        start_s, _, end_s = range_spec.partition("-")
        if start_s:
            start = int(start_s)
        if end_s:
            end = int(end_s)
        end = min(end, file_size - 1)
        if start > end or start >= file_size:
            raise HTTPException(status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE, detail="Invalid range")
        status_code = status.HTTP_206_PARTIAL_CONTENT
    else:
        status_code = status.HTTP_200_OK

    chunk_iter = _open_file_range(file_path, start, end)
    content_length = end - start + 1
    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Content-Type": "video/mp4",
    }
    return StreamingResponse(chunk_iter, status_code=status_code, headers=headers, media_type="video/mp4")


@router.post("/history/{video_id}", response_model=Message, summary="Add History", description="Record that the current user watched a video.")
def add_history(video_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    # ensure video exists
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    record = WatchHistory(user_id=current_user.id, video_id=video_id)
    db.add(record)
    db.flush()
    return Message(message="History recorded")


@router.get("/history", response_model=List[HistoryOut], summary="User History", description="Get the current user's watch history.")
def get_history(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    q = (
        db.query(WatchHistory)
        .filter(WatchHistory.user_id == current_user.id)
        .order_by(WatchHistory.watched_at.desc())
        .all()
    )
    return q
