from src.api.core import db as db_module
from src.api.models.models import Category, Video
from sqlalchemy.orm import Session


def seed_categories_videos(session: Session):
    cat1 = Category(name="Action")
    cat2 = Category(name="Drama")
    v1 = Video(title="Fast Car", description="Fast and furious drive", file_path="/tmp/missing1.mp4", featured=1)
    v2 = Video(title="Deep Story", description="Dramatic scenes", file_path="/tmp/missing2.mp4", featured=0)
    v1.categories.append(cat1)
    v2.categories.append(cat2)
    session.add_all([cat1, cat2, v1, v2])
    session.commit()
    return cat1, cat2, v1, v2


def test_categories_and_videos_listing(client):
    # seed
    with db_module.session_scope() as s:
        seed_categories_videos(s)

    # categories
    r = client.get("/categories")
    assert r.status_code == 200
    cats = r.json()
    assert len(cats) == 2
    names = [c["name"] for c in cats]
    assert set(names) == {"Action", "Drama"}

    # videos
    r = client.get("/videos")
    assert r.status_code == 200
    vids = r.json()
    assert len(vids) == 2
    titles = [v["title"] for v in vids]
    assert set(titles) == {"Fast Car", "Deep Story"}

    # search
    r = client.get("/videos", params={"q": "Fast"})
    assert r.status_code == 200
    vids = r.json()
    assert len(vids) == 1
    assert vids[0]["title"] == "Fast Car"

    # category filter
    action_id = next(c["id"] for c in cats if c["name"] == "Action")
    r = client.get("/videos", params={"category_id": action_id})
    assert r.status_code == 200
    vids = r.json()
    assert len(vids) == 1
    assert vids[0]["title"] == "Fast Car"

    # featured
    r = client.get("/videos/featured")
    assert r.status_code == 200
    fvids = r.json()
    assert len(fvids) == 1
    assert fvids[0]["title"] == "Fast Car"
