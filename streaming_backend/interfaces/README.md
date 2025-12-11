This directory contains the generated OpenAPI JSON for the backend. Run:
    uvicorn src.api.main:app --port 3001
and then:
    python -m src.api.generate_openapi
to regenerate openapi.json
