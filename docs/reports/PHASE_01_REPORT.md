# Phase 1 Report — Foundation & Architecture

**Project:** PustakHub — Secure Library & Identity Management Platform
**Phase:** 1 — Foundation & Architecture
**Date:** 2026-09-24
**Status:** COMPLETE

---

## 1. Objective

Establish a clean, scalable project foundation that all future phases can build upon without needing to retrofit or undo:

- Structured backend module layout (modular monolith)
- Core infrastructure: centralised config, logging, and error handling
- Maintainable frontend directory structure with a service layer and router
- Environment configuration templates (no secrets committed)
- Root `.gitignore` protecting all sensitive files
- Versioned API-ready structure (`/api/v1/` prefix prepared)
- Minimal but real test suite
- Architecture documentation

---

## 2. Initial Project State

| Area | Pre-Phase 1 State |
|---|---|
| Backend | Single file: `backend/app/main.py` with a FastAPI instance, CORS middleware, and two hardcoded endpoints. No config module, no logging, no error handling, no tests. |
| Frontend | `src/App.jsx` with inline `fetch()` call. `src/services/api.js` existed (axios). No pages/, layouts/, hooks/, context/, utils/, or router. |
| Environment | Frontend `.env` existed with `VITE_API_URL`. No backend `.env`. |
| `.gitignore` | Only `frontend/.gitignore` (basic Vite default). No root `.gitignore`. |
| Tests | None |
| Docs | None |
| Dependencies | `react-router-dom` not installed on frontend |

---

## 3. Changes Implemented

### Backend

1. Created `app/__init__.py` — package marker.
2. Created `app/core/config.py` — pydantic-settings `Settings` class; loads all env vars; exposes `cors_origins_list` property.
3. Created `app/core/logging.py` — `configure_logging()` + `get_logger()`; includes security rules docstring.
4. Created `app/core/exceptions.py` — `PustakHubError` hierarchy + three FastAPI exception handlers + `register_exception_handlers()`.
5. Rewrote `app/main.py` — application factory pattern, lifespan context manager, CORS driven by settings, all existing endpoints preserved and enriched.
6. Created `app/core/__init__.py`, `app/middleware/__init__.py`, `app/modules/__init__.py`.
7. Created stub `__init__.py` for all eight module directories: `auth`, `users`, `roles`, `permissions`, `books`, `borrowing`, `fines`, `audit`.
8. Created `backend/.env` (development defaults, not committed in real setup).
9. Created `backend/.env.example` (committed template, no secrets).
10. Created `tests/__init__.py`, `tests/conftest.py`, `tests/test_phase1_foundation.py`.
11. Created `migrations/README.md` placeholder.

### Frontend

12. Installed `react-router-dom`.
13. Updated `src/services/api.js` — added timeout, improved comments.
14. Created `src/services/health.service.js` — encapsulates `/health` API call.
15. Created `src/layouts/MainLayout.jsx` — React Router `Outlet`-based wrapper.
16. Created `src/pages/HomePage.jsx` — home page using health service (replaces inline fetch in App.jsx).
17. Created `src/pages/NotFoundPage.jsx` — 404 fallback route.
18. Rewrote `src/App.jsx` — React Router `BrowserRouter` + route tree; no auth logic.
19. Created placeholder barrel files: `src/hooks/index.js`, `src/context/index.js`, `src/components/index.js`, `src/utils/index.js`.
20. Created `frontend/.env.example`.
21. Updated `frontend/.gitignore` — added `.env` protection.

### Repository

22. Created root `.gitignore` — covers Python venvs, secrets, test caches, Node modules, build artifacts, IDE files.

### Docs

23. Created `docs/architecture.md` — full architecture document with CURRENT/PLANNED distinctions.

---

## 4. Files Created

### Backend — New Files

| File | Purpose |
|---|---|
| `backend/app/__init__.py` | Package marker |
| `backend/app/core/__init__.py` | Package marker |
| `backend/app/core/config.py` | pydantic-settings configuration |
| `backend/app/core/logging.py` | Logging configuration + get_logger |
| `backend/app/core/exceptions.py` | Exception classes + handlers |
| `backend/app/middleware/__init__.py` | Package marker |
| `backend/app/modules/__init__.py` | Package marker |
| `backend/app/modules/auth/__init__.py` | Module stub |
| `backend/app/modules/users/__init__.py` | Module stub |
| `backend/app/modules/roles/__init__.py` | Module stub |
| `backend/app/modules/permissions/__init__.py` | Module stub |
| `backend/app/modules/books/__init__.py` | Module stub |
| `backend/app/modules/borrowing/__init__.py` | Module stub |
| `backend/app/modules/fines/__init__.py` | Module stub |
| `backend/app/modules/audit/__init__.py` | Module stub |
| `backend/tests/__init__.py` | Package marker |
| `backend/tests/conftest.py` | Pytest fixtures (TestClient) |
| `backend/tests/test_phase1_foundation.py` | 11-test foundation suite |
| `backend/migrations/README.md` | Placeholder for Phase 3 Alembic setup |
| `backend/.env` | Development defaults (should not be committed in real repo) |
| `backend/.env.example` | Committed template |

### Frontend — New Files

| File | Purpose |
|---|---|
| `frontend/src/services/health.service.js` | Health endpoint service function |
| `frontend/src/layouts/MainLayout.jsx` | Page shell with Outlet |
| `frontend/src/pages/HomePage.jsx` | Home page component |
| `frontend/src/pages/NotFoundPage.jsx` | 404 fallback page |
| `frontend/src/hooks/index.js` | Hooks barrel (placeholder) |
| `frontend/src/context/index.js` | Context barrel (placeholder) |
| `frontend/src/components/index.js` | Components barrel (placeholder) |
| `frontend/src/utils/index.js` | Utils barrel (placeholder) |
| `frontend/.env.example` | Committed template |

### Docs — New Files

| File | Purpose |
|---|---|
| `docs/architecture.md` | Architecture documentation |

### Repository — New Files

| File | Purpose |
|---|---|
| `.gitignore` | Root gitignore |

---

## 5. Files Modified

| File | Change |
|---|---|
| `backend/app/main.py` | Rewritten: application factory, lifespan, settings-driven CORS, enriched endpoints |
| `backend/app/core/exceptions.py` | Fixed deprecation: `HTTP_422_UNPROCESSABLE_ENTITY` → `HTTP_422_UNPROCESSABLE_CONTENT` |
| `frontend/src/App.jsx` | Rewritten: React Router BrowserRouter + route tree |
| `frontend/src/services/api.js` | Updated: added timeout, improved documentation |
| `frontend/.gitignore` | Updated: added `.env` protection |

---

## 6. Dependencies Added

### Frontend (npm)

| Package | Version | Reason |
|---|---|---|
| `react-router-dom` | ^7.x | Client-side routing (was not installed) |

No new Python packages were added. All required packages (`pydantic-settings`, `fastapi`, `uvicorn`, `pytest`, `httpx`) were already listed in `requirements.txt` and installed in the venv.

---

## 7. Architecture Decisions

| Decision | Rationale |
|---|---|
| Modular monolith over microservices | Appropriate scale for a library system; avoids premature complexity |
| Application factory pattern in `main.py` | Makes `create_application()` independently testable; mirrors production-grade FastAPI patterns |
| pydantic-settings for config | Type-safe, env-var-first, auto-documents all config keys; consistent with Pydantic v2 |
| Centralised error response shape | Future APIs automatically return predictable JSON; clients need one error-handling path |
| `cors_origins_list` as env-var | Wildcard CORS intentionally avoided; credentials will be used in later phases |
| React Router + layout pattern | Clean separation of navigation shell from page content; easy to add nav bar/auth guards |
| Service layer (`src/services/`) | HTTP calls never scattered in components; easy to add auth headers in one place later |
| Module stub `__init__.py` files | Reserves the correct directory structure; prevents "where does this go?" confusion in later phases |

---

## 8. API Changes

| Endpoint | Change |
|---|---|
| `GET /` | Preserved; now includes `version` and `docs` fields |
| `GET /api/health` | Preserved; now includes `service`, `version`, `redis` fields |
| `GET /api/docs` | **NEW** — Swagger UI (was at default `/docs` before, now at `/api/docs`) |
| `GET /api/redoc` | **NEW** — ReDoc UI |
| `GET /api/openapi.json` | **NEW** — OpenAPI schema JSON |

> **Note:** Frontend `App.jsx` previously called `http://localhost:8000/api/health` directly. `HomePage.jsx` still calls the same URL via `health.service.js`. The connection is preserved.

---

## 9. Configuration Changes

| Item | Before | After |
|---|---|---|
| CORS origins | Hardcoded `["http://localhost:5173"]` in `main.py` | Loaded from `CORS_ORIGINS` env var via `Settings` |
| App title/version | Hardcoded strings | Loaded from `APP_NAME` / `APP_VERSION` env vars |
| Frontend API URL | Hardcoded `http://localhost:8000/api/health` in App.jsx | `VITE_API_URL` env var via `api.js` |
| Backend `.env` | Did not exist | Created with development defaults |
| Root `.gitignore` | Did not exist | Created |

---

## 10. Tests Executed

**Test suite:** `backend/tests/test_phase1_foundation.py`
**Command:** `venv/bin/python -m pytest tests/test_phase1_foundation.py -v`
**Runner:** Python 3.11.14 / pytest 9.1.1

| # | Test | Result |
|---|---|---|
| 1 | `test_app_starts` — app initialises and client is usable | **PASS** |
| 2 | `test_root_endpoint` — GET / returns 200 with project/status fields | **PASS** |
| 3 | `test_health_endpoint_status_code` — GET /api/health returns 200 | **PASS** |
| 4 | `test_health_endpoint_body` — health JSON contains required fields | **PASS** |
| 5 | `test_settings_load` — Settings instantiates; APP_NAME is correct | **PASS** |
| 6 | `test_import_core_config` — app.core.config imports cleanly | **PASS** |
| 7 | `test_import_core_logging` — app.core.logging imports cleanly | **PASS** |
| 8 | `test_import_core_exceptions` — app.core.exceptions imports cleanly | **PASS** |
| 9 | `test_import_main` — app.main imports cleanly; app object exists | **PASS** |
| 10 | `test_unknown_route_returns_404` — non-existent route returns 404 | **PASS** |
| 11 | `test_cors_header_present` — CORS header returned for allowed origin | **PASS** |

**Total: 11 passed, 0 failed**

**Warnings (non-blocking):**
- `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` — this comes from the installed version of `httpx`/`starlette` in the venv, not from PustakHub code. No action required for Phase 1.

---

## 11. Acceptance Criteria

| Criterion | Status |
|---|---|
| Existing React frontend still works | **PASS** — HomePage.jsx renders same UI via health.service.js |
| Existing React → FastAPI connection still works | **PASS** — CORS preserved, same /api/health endpoint, tested |
| FastAPI starts successfully | **PASS** — test_app_starts passes; lifespan executes cleanly |
| Health endpoint works | **PASS** — test_health_endpoint_status_code + test_health_endpoint_body both pass |
| Backend has a clean modular structure | **PASS** — core/, modules/ (8 domain stubs), middleware/, tests/, migrations/ |
| Frontend has a maintainable structure | **PASS** — pages/, layouts/, services/, hooks/, context/, components/, utils/ |
| Environment configuration is established | **PASS** — backend .env + .env.example; frontend .env.example; pydantic-settings |
| `.gitignore` is correct | **PASS** — root .gitignore + updated frontend .gitignore; .env protected |
| Basic logging exists | **PASS** — app/core/logging.py with configure_logging() + get_logger() |
| Basic error handling exists | **PASS** — exception hierarchy + 3 FastAPI handlers + consistent JSON shape |
| Basic tests pass | **PASS** — 11/11 tests pass |
| `docs/architecture.md` exists | **PASS** — comprehensive doc with CURRENT/PLANNED distinctions |
| No future-phase business logic implemented | **PASS** — no auth, JWT, DB models, Redis, RBAC, OTP, borrowing, or fines code |

---

## 12. Known Issues

| Issue | Severity | Notes |
|---|---|---|
| `StarletteDeprecationWarning: Using httpx with starlette.testclient` | Low | Comes from the installed `httpx` version in the venv. Can be resolved by running `pip install httpx2` when the package stabilises, or is a non-issue when using pytest-asyncio in later phases. Does not affect test results. |
| `backend/.env` is tracked by git in the current bare repo | Low | In a real git repo this would be excluded by `.gitignore`. The root `.gitignore` is in place. If git is initialised, `.env` will be correctly ignored. |

---

## 13. Deferred Work

The following functionality was **intentionally NOT implemented** in Phase 1 and is deferred to later phases:

| Item | Phase |
|---|---|
| JWT authentication (login, token issuance, refresh) | Phase 2 |
| Argon2id password hashing | Phase 2 |
| User registration, OTP | Phase 2 |
| React auth context + ProtectedRoute | Phase 2 |
| PostgreSQL database connection | Phase 3 |
| SQLAlchemy models | Phase 3 |
| Alembic migrations | Phase 3 |
| User, Role, Permission database models | Phase 3 |
| RBAC permission enforcement | Phase 4 |
| Redis integration | Phase 5 |
| Book catalogue API | Phase 6 |
| Borrowing workflow | Phase 7 |
| Fines system | Phase 8 |
| Audit logging | Phase 9 |
| SMTP email delivery | TBD |
| Rate limiting middleware | TBD |
| Request ID middleware | TBD |

---

## 14. Next Phase

**Phase 2 — Authentication & JWT**

Phase 2 will implement:

- Argon2id password hashing for secure credential storage.
- JWT access token and refresh token issuance.
- `POST /api/v1/auth/register` — user registration (without DB — stub or in-memory).
- `POST /api/v1/auth/login` — credential validation and token issuance.
- `POST /api/v1/auth/refresh` — silent token renewal.
- `POST /api/v1/auth/logout` — token invalidation.
- Frontend: `AuthContext`, `useAuth()` hook, `ProtectedRoute` and `GuestRoute` components.
- Frontend: login page, registration page.
- Axios interceptors to attach the Authorization header and handle 401 → refresh → retry.
- Tests covering all auth flows.

> Phase 2 depends on Phase 3 (database) for persistent user storage. The order may be: Phase 3 first (PostgreSQL + user model), then Phase 2 (auth logic). This sequencing decision belongs to the project roadmap, not Phase 1.

---

## 15. Final Status

**COMPLETE**

All 13 acceptance criteria pass. 11/11 tests pass. No required functionality is missing. No future-phase code was introduced. The project is ready for Phase 2.
