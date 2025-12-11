from http.cookies import SimpleCookie
from jose import jwt

from src.api.core.config import get_settings


def test_register_login_me_logout_flow(client):
    # Register
    r = client.post("/auth/register", json={"email": "a@example.com", "password": "secret123"})
    assert r.status_code == 200
    user = r.json()
    assert user["email"] == "a@example.com"
    assert "id" in user

    # Login (sets HttpOnly cookie)
    r = client.post("/auth/login", json={"email": "a@example.com", "password": "secret123"})
    assert r.status_code == 200
    assert "set-cookie" in r.headers or "Set-Cookie" in r.headers
    cookie_header = r.headers.get("set-cookie") or r.headers.get("Set-Cookie")
    ck = SimpleCookie()
    ck.load(cookie_header)
    assert "access_token" in ck

    # /auth/me should work with cookie persisted in TestClient
    r = client.get("/auth/me")
    assert r.status_code == 200
    me = r.json()
    assert me["email"] == "a@example.com"

    # Logout clears cookie, then /me should 401 after clearing
    r = client.post("/auth/logout")
    assert r.status_code == 200
    # Subsequent call (same client) should now be unauthorized
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_login_invalid_credentials(client):
    # Register a user
    r = client.post("/auth/register", json={"email": "b@example.com", "password": "mypassword"})
    assert r.status_code == 200

    # Wrong password should 400
    r = client.post("/auth/login", json={"email": "b@example.com", "password": "wrong"})
    assert r.status_code == 400


def test_jwt_token_contains_expected_claims(client):
    # Register and login
    r = client.post("/auth/register", json={"email": "claims@example.com", "password": "secret123"})
    assert r.status_code == 200
    r = client.post("/auth/login", json={"email": "claims@example.com", "password": "secret123"})
    assert r.status_code == 200
    cookie_header = r.headers.get("set-cookie") or r.headers.get("Set-Cookie")
    assert cookie_header
    # Parse cookie value (format: access_token=<token>; ...)
    token = None
    for part in cookie_header.split(";"):
        if part.strip().startswith("access_token="):
            token = part.strip().split("=", 1)[1]
            break
    assert token

    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    assert "sub" in payload and "email" in payload and "exp" in payload
