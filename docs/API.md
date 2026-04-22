# LabReport Pro — API

## Conventions

- All endpoints are **versioned** under `/api/v1/`.
- Health checks are **unversioned** under `/api/`.
- OpenAPI schema: `/api/schema/`. Swagger UI: `/api/docs/`. ReDoc: `/api/redoc/`.
- **Authentication**: JWT in `Authorization: Bearer <token>` (see
  `/api/v1/auth/login/` once Phase 1 ships).
- **All domain endpoints are lab-scoped** — the middleware filters by the
  authenticated user's `lab_id`.
- **Pagination**: `?page=N&page_size=M`. Default page size 25.
- **Filtering**: `django-filter` backend — see each endpoint's schema for
  filter params.
- **Errors**: DRF default envelope. `X-Request-ID` returned on every
  response for log correlation.

## Phase 0 endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health/` | Liveness probe. Returns 200 if the process is alive. |
| GET | `/api/ready/` | Readiness probe. 200 only when DB + cache are reachable. |
| GET | `/api/schema/` | OpenAPI 3 JSON schema. |
| GET | `/api/docs/` | Swagger UI. |
| GET | `/api/redoc/` | ReDoc. |

## Planned endpoints (Phases 1–4)

Added as phases land. See `docs/ROADMAP.md` for the full list; examples:

- `/api/v1/auth/{login,refresh,logout,me}/`
- `/api/v1/lab/` and `/api/v1/lab/branches/`
- `/api/v1/patients/...`
- `/api/v1/catalog/{categories,tests,templates}/`
- `/api/v1/reports/...` (CRUD + lifecycle actions: verify, sign, amend,
  regenerate-pdf, download)
- `/api/v1/referring-doctors/...`
- `/api/v1/users/...` (admin)

Placeholder endpoints for future apps will return **501 Not Implemented**
and be documented in Swagger so frontend contracts can be stubbed early.
