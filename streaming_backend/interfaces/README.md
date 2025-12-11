This directory contains the generated OpenAPI JSON for the backend.

Regenerate steps:
1) Start server (from streaming_backend):
    uvicorn src.api.main:app --app-dir streaming_backend --port 3001
2) Generate (from streaming_backend):
    python -m src.api.generate_openapi

Notes:
- The frontend must send credentials (cookies) with requests, e.g. fetch(url, { credentials: "include" }) or axios(..., { withCredentials: true }).
- If using a Vite proxy, proxy / to http://localhost:3001. Otherwise set an env like REACT_APP_API_BASE=http://localhost:3001 and prefix calls.
