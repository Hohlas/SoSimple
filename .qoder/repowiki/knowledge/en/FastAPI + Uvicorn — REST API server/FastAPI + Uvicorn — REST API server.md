---
kind: external_dependency
name: FastAPI + Uvicorn — REST API server
slug: fastapi-uvicorn
category: external_dependency
category_hints:
    - vendor_identity
scope:
    - '**'
---

### FastAPI + Uvicorn
- Role: HTTP API server for exposing ML signal generation and research endpoints.
- Entry point: `API/api_server.py` serves REST endpoints backed by Pydantic models for request/response validation.
- Stable usage: Uvicorn is the ASGI server running the FastAPI application; Pydantic handles schema validation for API contracts.
- Verify exact endpoint definitions and Pydantic model schemas against the API implementation.