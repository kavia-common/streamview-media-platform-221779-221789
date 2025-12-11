from src.api.core import db as db_module
from src.api.models.models import Video
from sqlalchemy.orm import Session


def seed_video(session: Session) -> int:
    v = Video(title="Watchable", description="History test", file_path="/tmp/missing3.mp4", featured=0)
    session.add(v)
    session.commit()
    return v.id


def test_history_requires_auth_and_records(client):
    # Without login, history endpoints should 401
    r = client.get("/history")
    assert r.status_code == 401

    # Register & login
    r = client.post("/auth/register", json={"email": "h@example.com", "password": "secret123"})
    assert r.status_code == 200
    r = client.post("/auth/login", json={"email": "h@example.com", "password": "secret123"})
    assert r.status_code == 200

    # Seed a video
    with db_module.session_scope() as s:
        vid = seed_video(s)

    # Add history
    r = client.post(f"/history/{vid}")
    assert r.status_code == 200
    assert r.json()["message"] == "History recorded"

    # Fetch history
    r = client.get("/history")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["video"]["title"] == "Watchable"
