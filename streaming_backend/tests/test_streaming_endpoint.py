import os
import tempfile

from src.api.core import db as db_module
from src.api.models.models import Video


def create_temp_media_file(size: int = 4096) -> str:
    fd, path = tempfile.mkstemp(prefix="media_", suffix=".mp4")
    with os.fdopen(fd, "wb") as f:
        f.write(os.urandom(size))
    return path


def test_streaming_requires_auth_and_supports_range(client):
    # Unauthed should 401 due to dependency get_current_user
    r = client.get("/stream/1")
    assert r.status_code == 401

    # Register/login
    r = client.post("/auth/register", json={"email": "s@example.com", "password": "secret123"})
    assert r.status_code == 200
    r = client.post("/auth/login", json={"email": "s@example.com", "password": "secret123"})
    assert r.status_code == 200

    # Seed video with real file
    path = create_temp_media_file(2048)
    try:
        with db_module.session_scope() as s:
            v = Video(title="Streamable", description=None, file_path=path, featured=0)
            s.add(v)
            s.commit()
            vid = v.id

        # Full content (no Range) => 200
        r = client.get(f"/stream/{vid}")
        assert r.status_code == 200
        assert r.headers.get("Content-Type") == "video/mp4"
        assert "Content-Range" in r.headers

        # Valid range => 206
        r = client.get(f"/stream/{vid}", headers={"Range": "bytes=0-99"})
        assert r.status_code == 206
        assert r.headers.get("Content-Range", "").startswith("bytes 0-99/")

        # Invalid range => 416
        r = client.get(f"/stream/{vid}", headers={"Range": "bytes=999999-1000000"})
        assert r.status_code == 416
    finally:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass


def test_streaming_404_missing_file(client):
    # Register/login
    r = client.post("/auth/register", json={"email": "s2@example.com", "password": "secret123"})
    assert r.status_code == 200
    r = client.post("/auth/login", json={"email": "s2@example.com", "password": "secret123"})
    assert r.status_code == 200

    # Seed video referencing nonexistent file
    with db_module.session_scope() as s:
        v = Video(title="MissingFile", description=None, file_path="/tmp/definitely_not_exists.mp4", featured=0)
        s.add(v)
        s.commit()
        vid = v.id

    r = client.get(f"/stream/{vid}")
    assert r.status_code == 404
