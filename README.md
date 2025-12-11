# StreamView - Backend and Integration Notes

This workspace contains the FastAPI backend for StreamView.

Quick start:
- Install deps: pip install -r streaming_backend/requirements.txt
- Start backend: uvicorn src.api.main:app --app-dir streaming_backend --reload --port 3001

Database:
- Uses SQLite by default. The backend will read SQLITE_DB from the environment if provided by the streaming_db container; otherwise it falls back to ./db/app.db under the working directory and creates the folder if missing.

CORS and Cookies:
- CORS allow-origins defaults to http://localhost:3000 and http://localhost:5173 with allow_credentials=true.
- Auth uses an HttpOnly cookie named access_token with SameSite=Lax by default. In development cookie Secure=False; in production set NODE_ENV=production to enable Secure cookies and configure COOKIE_DOMAIN as needed.

Media placeholders:
- Demo seed creates a demo_videos directory and placeholder file paths (no binaries). The /stream/{video_id} endpoint will 404 if the file is not present. Place your mp4 files under the printed demo_videos path or update file_path in the DB.

OpenAPI:
- Run the server: uvicorn src.api.main:app --app-dir streaming_backend --port 3001
- Regenerate spec: python -m src.api.generate_openapi (from streaming_backend directory). The JSON is written to streaming_backend/interfaces/openapi.json

Frontend integration:
- Frontend should call the backend with credentials (cookies):
  - fetch: fetch("/auth/me", { credentials: "include" })
  - axios: axios.get("/auth/me", { withCredentials: true })
- Use either Vite dev proxy to 3001 or set REACT_APP_API_BASE=http://localhost:3001 and prefix requests with that value. Ensure credentials option is set on every request.

Seeding:
- Seed demo data: python -m src.api.scripts.bootstrap_db (from streaming_backend directory)