# PustakHub — System Architecture

> **Secure Library & Identity Management Platform**  
> **Final Architecture Specification (Phase 10)**  
> Last updated: 2026-09-24

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Repository Structure](#repository-structure)
3. [Frontend / Backend Relationship](#frontend--backend-relationship)
4. [Modular Monolith Architecture](#modular-monolith-architecture)
5. [Backend Module Responsibilities](#backend-module-responsibilities)
6. [Why Authentication is Isolated](#why-authentication-is-isolated)
7. [Infrastructure & Security Layer](#infrastructure--security-layer)
8. [Configuration Strategy](#configuration-strategy)
9. [Logging & Security Rules](#logging--security-rules)
10. [Error Handling Contract](#error-handling-contract)
11. [API Architecture & Route Categories](#api-architecture--route-categories)
12. [Frontend Architecture](#frontend-architecture)
13. [Security Request Pipeline](#security-request-pipeline)

---

## Project Overview

**PustakHub** is a production-grade, security-first **Library & Identity Management Platform**.

Its foundational engineering discipline is **Identity & Access Management (IAM)** — providing defense-in-depth, auditable, and fine-grained access control over users, roles, permissions, and resources. Domain library operations (cataloging, physical copy inventory, row-locked borrowing, and overdue fines) build directly on this secure IAM core.

---

## Repository Structure

```text
PustakHub/
├── backend/                  # Python / FastAPI backend
│   ├── app/
│   │   ├── main.py           # Application factory, lifespan context & router mounting
│   │   ├── core/             # Shared infrastructure (config, database, redis, encryption, security, logging, exceptions)
│   │   ├── modules/          # Feature domain modules (auth, users, roles, permissions, books, borrowing, fines, audit)
│   │   ├── models/           # SQLAlchemy declarative ORM models
│   │   └── middleware/       # Security pipeline middleware (CORS, request size, audit context, rate limit, headers)
│   ├── tests/                # Pytest test suite (128 passing regression tests)
│   ├── migrations/           # Alembic database migrations (Head revision: 3741532892a9)
│   ├── requirements.txt      # Python dependencies
│   ├── pytest.ini            # Pytest configuration and warning filters
│   ├── alembic.ini           # Alembic database configuration
│   └── .env.example          # Environment template
│
├── frontend/                 # React 19 / Vite / Tailwind CSS v4 frontend
│   ├── src/
│   │   ├── App.jsx            # Root component + React Router v7 routes
│   │   ├── layouts/           # Shared page shells (MainLayout, AuthLayout)
│   │   ├── pages/             # Page components (Login, Register, MFA, Dashboard, Catalog)
│   │   ├── components/        # Reusable UI components
│   │   ├── services/          # Centralized Axios API service layer with JWT interceptors
│   │   ├── hooks/             # Custom React hooks (useAuth, usePermissions)
│   │   ├── context/           # React Context (AuthContext)
│   │   └── utils/             # Helper utilities
│   ├── package.json           # Node dependencies
│   └── .env.example           # Frontend environment template
│
├── docs/                     # System architecture and security specifications
│   ├── architecture.md       # Complete system architecture specification
│   ├── authentication.md     # IAM, JWT, OTP, MFA, and recovery specifications
│   ├── rbac.md               # Dynamic DB RBAC and IDOR defense rules
│   ├── catalog.md            # Category, book, and inventory copy management
│   ├── circulation.md        # Borrowing transactions, row locking, and fine calculation
│   ├── database-design.md    # PostgreSQL schema, indexes, and ER diagrams
│   ├── security-hardening.md # Rate limiting, security headers, CSP, and size protection
│   └── reports/              # Milestone audit and verification reports
│
├── .env.example              # Root environment template
├── .gitignore                # Git ignore rules
└── README.md                 # Portfolio overview and system documentation
```

---

## Frontend / Backend Relationship

```text
┌─────────────────────────────────────────┐         HTTP/JSON (REST)         ┌─────────────────────────────────────────┐
│              React 19 SPA               │  ──────────────────────────────►  │             FastAPI Backend             │
│   (Vite dev server: port 5173           │                                  │        (Uvicorn: port 8000)             │
│    Production build: static bundle)     │  ◄──────────────────────────────  │                                         │
└─────────────────────────────────────────┘                                  └─────────────────────────────────────────┘
```

- **Axios HTTP Client:** All client requests are centralized in `src/services/api.js`. Token interceptors attach `Authorization: Bearer <access_token>` automatically.
- **CORS Hardening:** FastAPI explicitly configures CORS origins (e.g. `http://localhost:5173`) with strict methods, headers, and exposed response headers.
- **Local QR Code Generation:** MFA setup renders `otpauth://` QR codes client-side as inline SVGs via `qrcode.react`, keeping private keys away from external image APIs.

---

## Modular Monolith Architecture

PustakHub uses a **modular monolith** — a single deployable FastAPI service whose business logic is partitioned into clearly bounded modules inside `app/modules/`:

Each module contains:
- `router.py` — Versioned FastAPI route definitions and dependency injection.
- `schemas.py` — Pydantic request and response contracts.
- `service.py` — Core domain business logic and database transaction handling.
- `dependencies.py` — Specialized authorization and resource-scoping dependencies.

Cross-module interaction occurs via explicit service interfaces rather than tight direct coupling.

---

## Backend Module Responsibilities

| Module | Status | Responsibility |
|---|---|---|
| `core/` | IMPLEMENTED | Application settings, database session pooling, Redis connections, AES-256-GCM encryption, Argon2id security, logging, and error handling. |
| `middleware/` | IMPLEMENTED | Multi-layered security request pipeline: CORS, request size limiting (2MB), audit context extraction, sliding-window rate limiting, and HTTP security headers (CSP, X-Frame). |
| `auth/` | IMPLEMENTED | User registration, email OTP verification, login, refresh token rotation, logout revocation, password reset, and RFC 6238 TOTP MFA. |
| `users/` | IMPLEMENTED | User profile queries, user administration, and account status management. |
| `roles/` | IMPLEMENTED | Role CRUD, role-permission association, and user role assignment. |
| `permissions/` | IMPLEMENTED | Permission catalog, role-permission matrix resolution, and `/permissions/me` inspection. |
| `books/` | IMPLEMENTED | Category taxonomy, book bibliographic metadata, physical copy inventory tracking, and full-text search. |
| `borrowing/` | IMPLEMENTED | Pessimistic row-locked book checkout (`SELECT ... FOR UPDATE`), book check-in, and borrow history. |
| `fines/` | IMPLEMENTED | Automated overdue fine calculations ($2.00/day), fine detail queries, and member fine history. |
| `audit/` | IMPLEMENTED | Tamper-resistant, sanitized security audit trail persistence into PostgreSQL. |

---

## Why Authentication is Isolated

The `auth` module is isolated from `users`, `roles`, and `permissions`:

1. **Single Responsibility:** Proving identity (authentication) is distinct from evaluating privilege (authorization).
2. **Reduced Blast Radius:** Vulnerabilities or changes in domain modules cannot corrupt credential or token issuance mechanics.
3. **Auditability:** Credential operations (login, logout, refresh, reset, MFA challenges) are cleanly intercepted and auditable.
4. **Defense-in-Depth:** Zero unverified registrations touch PostgreSQL; unverified state is isolated in Redis until OTP confirmation.

---

## Infrastructure & Security Layer

| Component | Status | Implementation Details |
|---|---|---|
| **PostgreSQL 17** | IMPLEMENTED | Primary ACID relational database storing users, RBAC mappings, catalog, circulation, fines, and audit logs. |
| **SQLAlchemy 2.0** | IMPLEMENTED | Declarative ORM models using `Mapped[]` and `mapped_column()` with `selectin` relationships. |
| **Alembic 1.20** | IMPLEMENTED | Database schema migrations with revision tracking up to head (`3741532892a9`). |
| **Redis 7** | IMPLEMENTED | Ephemeral OTP state (TTL 5m), password reset tokens (TTL 15m), MFA challenges (TTL 5m), and sliding-window rate limiting. |
| **Argon2id** | IMPLEMENTED | Memory-hard, timing-resistant password hashing via `argon2-cffi`. |
| **Signed JWTs** | IMPLEMENTED | Stateless access tokens (15m) using HMAC-SHA256 via `python-jose`. |
| **AES-256-GCM** | IMPLEMENTED | Authenticated AEAD symmetric encryption for TOTP secrets stored at rest in PostgreSQL. |
| **PyOTP (RFC 6238)** | IMPLEMENTED | Standards-compliant Time-based One-Time Passwords. |

---

## Configuration Strategy

- Configuration is managed via Pydantic Settings (`app/core/config.py`).
- Secrets and connection strings are injected via environment variables (`.env`).
- `.env.example` templates document all configurable options without storing plaintext production keys.
- Production environments enforce strict validation on `MFA_ENCRYPTION_KEY`, `JWT_SECRET`, and `DATABASE_URL`.

---

## Logging & Security Rules

Structured logging is configured in `app/core/logging.py`:

- ❌ **NEVER logged:** Passwords, password hashes, OTP codes, TOTP secrets, recovery codes, JWT tokens, database passwords.
- ✅ **Logged:** Actor user IDs, client IP addresses, HTTP methods, route paths, and sanitized error envelopes.

---

## Error Handling Contract

All API error responses conform to a standardized JSON schema:

```json
{
  "error": "machine_readable_error_code",
  "message": "Human-readable description",
  "detail": null
}
```

Standard application exceptions (`app/core/exceptions.py`):
- `NotFoundError` — 404 Not Found
- `ValidationError` — 422 Unprocessable Entity
- `ConflictError` — 409 Conflict
- `ForbiddenError` — 403 Forbidden
- `UnauthorizedError` — 401 Unauthorized
- `PayloadTooLargeError` — 413 Request Entity Too Large
- `RateLimitExceededError` — 429 Too Many Requests

---

## API Architecture & Route Categories

The backend exposes **40 registered REST routes**:

```text
/api/v1/auth/*         - Registration, OTP, Login, Refresh, Logout, Profile, MFA, Password Reset
/api/v1/users/*        - User list, user details, role assignments
/api/v1/roles/*        - Role list, create, update, delete, permission bindings
/api/v1/permissions/*  - Global permissions, role-permission matrix, user permissions
/api/v1/categories/*   - Category CRUD and book association counts
/api/v1/books/*        - Book search, catalog CRUD, copy associations
/api/v1/copies/*       - Physical copy barcode management, status transitions
/api/v1/borrow*        - Book issue (row-locked), return, borrow history
/api/v1/fines/*        - Fine queries and user fine history
/api/v1/audit/logs     - Security audit trail queries (Admin / Librarian)
/api/health            - System health diagnostics (DB & Redis)
```

---

## Frontend Architecture

- **React 19 SPA** initialized with Vite and styled using Tailwind CSS v4.
- **Global Auth State:** `AuthContext` provides authenticated user profile, login/logout handlers, and token refresh loops.
- **Protected Routing:** `ProtectedRoute` guards authenticated views and redirects unverified sessions to login or MFA verification.
- **Client-Side Security:** TOTP setup QR codes rendered in-browser using `qrcode.react` (zero external API leakage).

---

## Security Request Pipeline

```text
Client HTTP Request
       │
       ▼
1. Hardened CORS Middleware (Origin check)
       │
       ▼
2. Request Size Limiter (2MB limit on headers & streams)
       │
       ▼
3. Audit Context Middleware (Client IP & User-Agent capture)
       │
       ▼
4. Rate Limiting Middleware (Redis sliding-window Lua script)
       │
       ▼
5. Security Headers & CSP Middleware (CSP, X-Frame, nosniff)
       │
       ▼
6. FastAPI Router & Route Dispatch
       │
       ▼
7. JWT Bearer Token Authentication
       │
       ▼
8. Database RBAC Permission Gate (require_permission)
       │
       ▼
9. Resource-Level Authorization (Ownership scoping & IDOR prevention)
       │
       ▼
10. Domain Service Execution (PostgreSQL row locks & transactions)
       │
       ▼
11. Security Audit Log (Sanitized event stored to audit_logs)
       │
       ▼
HTTP 200 / 201 Response
```
