# PustakHub

## Secure Library & Identity Management Platform

[![CI / Test Suite](<https://img.shields.io/badge/tests-238%20passed%20%7C%200%20warnings-brightgreen.svg>)](docs/reports/PHASE_17_REPORT.md)
[![Security Audit](<https://img.shields.io/badge/security%20audit-0%20findings%20%28verified%29-blue.svg>)](docs/reports/POST_REMEDIATION_SECURITY_VERIFICATION.md)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141.1-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.2-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7.x-DC382D.svg?logo=redis&logoColor=white)](https://redis.io)
[![Alembic](<https://img.shields.io/badge/Alembic-3741532892a9%20%28head%29-orange.svg>)](backend/migrations)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **A security-first Library & Identity Management Platform combining enterprise library circulation workflows with defense-in-depth authentication, dynamic database-backed RBAC, encrypted RFC 6238 TOTP Multi-Factor Authentication, resource-level authorization (IDOR/BOLA prevention), atomic Redis sliding-window rate limiting, request size protection, tamper-resistant security audit logging, and authenticated WebSocket real-time updates.**

* **Demo:** Coming soon
* **Interactive API Documentation:** `http://localhost:8000/api/docs` (Swagger UI) / `http://localhost:8000/api/redoc` (ReDoc)
* **Real-Time Update Specification:** [docs/realtime.md](docs/realtime.md)
* **Architecture & Security Specifications:** [docs/](docs/)

---

## Overview

Modern applications often treat security as an afterthought, relying on rudimentary table-level CRUD checks or static token payload roles. **PustakHub** was engineered from the ground up to demonstrate enterprise-grade **Identity and Access Management (IAM)** and defensible systems engineering applied to real-world domain workflows.

While PustakHub delivers full library cataloging, physical inventory copy tracking, row-level locked circulation checkouts, and automated overdue fine calculations, its central differentiator is its **security core**:

- **Zero unverified accounts in persistent storage** (unverified registrations are isolated in Redis).
- **Argon2id password hashing** paired with timing-attack resistant dummy evaluations.
- **Stateless signed JWT access tokens** (15-minute lifetime) coupled with **server-tracked refresh session rotation and revocation** in PostgreSQL.
- **RFC 6238 TOTP Multi-Factor Authentication** with **AES-256-GCM encryption at rest** and single-use, SHA-256 hashed emergency recovery codes.
- **Dynamic database-backed RBAC** where fine-grained permissions (`book:create`, `user:view`, etc.) are resolved directly from database relations on every request—never trusted from stale client-side token claims.
- **Fine-grained Resource-Level Authorization** ensuring strict object-ownership scoping to eliminate Insecure Direct Object References (IDOR / BOLA).
- **Atomic Redis sliding-window rate limiting** via server-side Lua scripts with a fail-closed policy on critical authentication endpoints and fail-open policy on standard APIs.
- **Comprehensive security middleware** including streaming request body size limits, strict Content Security Policy (CSP) with local browser QR code generation, hardened CORS, and tamper-resistant audit trails.

---

## Why PustakHub?

PustakHub evolved from a standard library management system into a **security-first identity and resource management platform**.

```text
       ┌─────────────────────────────────────────────────────────┐
       │             Client HTTP Request (Browser/CLI)            │
       └────────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │              Security Request Pipeline                   │
       │   CORS ➔ Size Limit ➔ Audit Context ➔ Rate Limiter ➔ CSP │
       └────────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │                Authentication Layer                      │
       │       Bearer JWT Validation ➔ Refresh Token Sessions     │
       └────────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │          Multi-Factor Authentication (MFA)               │
       │     RFC 6238 TOTP Challenge ➔ AES-256-GCM Decryption    │
       └────────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │             Role-Based Access Control (RBAC)            │
       │     DB Permission Resolution (resource:action checks)   │
       └────────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │          Resource-Level Authorization (IDOR)            │
       │        Object Ownership Scoping & Admin Overrides       │
       └────────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │               Business Domain Execution                 │
       │    Catalog ➔ Inventory ➔ Locked Circulation ➔ Fines     │
       └────────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │              Tamper-Resistant Audit Trail               │
       │       Structured Event Logged to PostgreSQL (audit_logs) │
       └─────────────────────────────────────────────────────────┘
```

---

## Key Features

### Identity & Authentication

- **Zero Unverified User Footprint:** Public registrations stage user data and salted OTP digests exclusively in Redis (5-minute TTL). PostgreSQL `users` records are provisioned only upon successful OTP verification.
- **Argon2id Password Security:** Passwords hashed with standard Argon2id parameters. Anti-enumeration protections execute dummy hashes on nonexistent accounts to normalize response latency.
- **JWT & Session Lifecycle:** Dual-token model issuing short-lived signed JWT access tokens (15m) and persistent refresh tokens (7d).
- **Refresh Token Rotation & Revocation:** Every refresh call consumes the old token, invalidates the previous session hash, and issues a fresh token pair. Calling `/logout` or resetting a password instantly revokes server-side sessions.

### Authorization & RBAC

- **Authoritative Database RBAC:** Permissions are decoupled from hardcoded roles. Four system roles (`ADMIN`, `LIBRARIAN`, `STUDENT`, `GUEST`) map to 16 fine-grained permissions (`book:view`, `book:create`, `book:update`, `book:delete`, `book:issue`, `book:return`, `user:view`, `user:create`, `user:update`, `user:delete`, `role:view`, `role:create`, `role:update`, `role:delete`, `permission:view`, `permission:assign`, `audit_log:view`).
- **Dynamic Dependency Enforcement:** Endpoints declare declarative permission gates (`require_permission("book:create")`). Permissions are evaluated dynamically against live database tables (`user_roles` and `role_permissions`).
- **Resource-Level Authorization (IDOR & BOLA Defenses):** Enforces strict ownership checks on member resources (e.g., student borrowing history, user profiles, unpaid fines) while allowing authorized staff administrative overrides.

### MFA & Account Recovery

- **RFC 6238 TOTP Two-Factor Auth:** Compatible with Google Authenticator, Microsoft Authenticator, 1Password, and Authy.
- **Envelope Encryption at Rest:** TOTP Base32 secrets are encrypted using authenticated **AES-256-GCM** with a distinct 96-bit random nonce per encryption before persistence in PostgreSQL. Secrets are decrypted in application memory only during verification.
- **Single-Use Emergency Recovery Codes:** Issues 8 cryptographically secure recovery codes stored strictly as SHA-256 digests. Consumed codes are removed from the database immediately.
- **Anti-Enumeration Password Reset:** The forgot-password endpoint returns identical 200 OK responses regardless of email existence. Reset tokens are single-use, 15-minute TTL, SHA-256 hashed strings that invalidate all active sessions upon completion.

### Library Management

- **Catalog & Taxonomy:** Hierarchical categories with dynamic book count aggregation and deletion protection.
- **Bibliographic Metadata:** Books maintain title, author, unique ISBN, publisher, publication year, and descriptions.
- **Physical Copy Inventory:** Physical books are tracked independently as `BookCopy` units with individual barcodes (`copy_identifier`), shelf locations, and availability statuses (`AVAILABLE`, `BORROWED`, `MAINTENANCE`, `LOST`).
- **Full-Text Catalog Search:** Keyword search across titles, authors, ISBNs, and publishers with multi-attribute filtering and pagination metadata.

### Borrowing & Fines

- **Pessimistic Row-Level Locking:** Book checkout transactions execute `SELECT ... FOR UPDATE` on `BookCopy` rows, eliminating race conditions and double-issuance bugs during concurrent requests.
- **Configurable Circulation Rules:** 14-day default loan period and maximum 5 active loans per patron.
- **Automated Overdue Fine Calculation:** Returning an overdue book computes elapsed calendar days via UTC timestamps and automatically generates a `Fine` record (`$2.00/day`) in the same database transaction.
- **Referential Integrity Protection:** Prevents deletion of categories with books, books with registered physical copies, or copies with active borrow records.

### Security Engineering

- **Atomic Sliding Window Rate Limiter:** Redis sorted-set (`ZSET`) Lua script enforces exact per-IP request quotas (Auth: 20 req/min, General API: 200 req/min) returning standard `429 Too Many Requests` with `X-RateLimit-*` and `Retry-After` headers.
- **Fail-Closed Auth & Fail-Open API Policy:** If Redis becomes unavailable, security-critical authentication endpoints fail closed (HTTP 503) to prevent unthrottled brute-force attacks, while catalog endpoints fail open to maintain public service uptime.
- **Request Size Limiter:** ASGI middleware rejects oversized payloads exceeding 2 MB with `413 Request Entity Too Large` across both `Content-Length` headers and chunked transfer streams.
- **Strict Security Headers & CSP:** Emits `Content-Security-Policy`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, and `Permissions-Policy`.
- **Local QR Code Generation:** Client-side SVG QR code rendering via `qrcode.react` guarantees zero transmission of private TOTP provisioning URIs to third-party APIs.

### Audit & Observability

- **Tamper-Resistant Audit Trails:** Records all sensitive actions (`USER_CREATED`, `LOGIN_SUCCESS`, `LOGIN_FAILURE`, `LOGOUT`, `TOKEN_REFRESH`, `ROLE_ASSIGNED`, `PASSWORD_RESET_COMPLETED`, `MFA_ENABLED`, `COPY_ISSUED`, `COPY_RETURNED`, `FINE_ISSUED`) into PostgreSQL `audit_logs`.
- **Strict Data Redaction:** Sanitization layer intercepts audit parameters to ensure plaintext passwords, hashes, tokens, OTPs, TOTP keys, and database credentials are never stored.
- **Context Injection:** Middleware automatically captures and logs the actor `user_id`, client IP address, and User-Agent.

### Real-Time Updates (WebSocket & Redis Pub/Sub)

- **Authenticated WebSocket Transport:** Real-time updates delivered via `WS /api/v1/realtime/ws` authenticated with JWT access tokens and database account status validation.
- **Multi-Worker Synchronization:** Redis Pub/Sub channel (`pustakhub:realtime:events`) synchronizes events across multiple ASGI worker instances with seamless fallback to in-memory dispatch.
- **RBAC & Scoped Event Fan-Out:** Strict server-side filtering ensures audit logs are sent only to auditors/admins, circulation updates only to staff and the specific borrower, and catalog updates to all active members.
- **REST as Source of Truth:** Events act as invalidation triggers; clients refresh authoritative REST endpoints upon event arrival or connection recovery.

---

## Architecture

PustakHub is structured as a clean **modular monolith** with distinct boundaries for core infrastructure, authentication, RBAC authorization, catalog management, circulation, and audit forensics:

```mermaid
flowchart TB
    subgraph ClientLayer["Frontend Application"]
        UI["React 19 SPA (Vite + Tailwind CSS v4)"]
        Router["React Router v7 (Protected Routes & Auth Context)"]
        QRGen["Local QR Code Generator (qrcode.react)"]
        AxiosClient["Axios HTTP Service (Auth Interceptor)"]
        UI --> Router --> QRGen --> AxiosClient
    end

    subgraph APILayer["FastAPI Application Server (:8000)"]
        direction TB
      
        subgraph MiddlewareStack["Security Middleware Pipeline"]
            MW_CORS["1. Hardened CORSMiddleware"]
            MW_Size["2. RequestSizeLimitMiddleware (2MB Limit)"]
            MW_Audit["3. AuditContextMiddleware (IP & User-Agent)"]
            MW_Rate["4. RateLimitMiddleware (Redis Sliding Window)"]
            MW_SecHeaders["5. SecurityHeadersMiddleware (CSP, HSTS, X-Frame)"]
            MW_CORS --> MW_Size --> MW_Audit --> MW_Rate --> MW_SecHeaders
        end

        subgraph Routers["FastAPI Modular Routers (40 Routes)"]
            R_Auth["/api/v1/auth (Register, Login, MFA, Reset)"]
            R_Roles["/api/v1/roles & /api/v1/permissions"]
            R_Users["/api/v1/users"]
            R_Catalog["/api/v1/categories, /books, /copies"]
            R_Circ["/api/v1/borrow, /borrowings, /fines"]
            R_Audit["/api/v1/audit/logs"]
        end

        subgraph CoreServices["Domain & Security Services"]
            S_Auth["AuthService (Argon2id, JWT, OTP)"]
            S_Crypto["EncryptionService (AES-256-GCM)"]
            S_RBAC["PermissionService & RBAC Engine"]
            S_Catalog["CatalogService & InventoryEngine"]
            S_Circ["CirculationService (Row-Locked Transactions)"]
            S_Audit["AuditService (Redaction & Event Logging)"]
        end
    end

    subgraph DataLayer["Storage & Cache Infrastructure"]
        subgraph PostgreSQL["PostgreSQL 17 Database"]
            T_Users["users (Encrypted MFA Secrets)"]
            T_Sessions["user_sessions (Hashed Refresh Tokens)"]
            T_RBAC["roles, permissions, user_roles, role_permissions"]
            T_Catalog["categories, books, book_copies"]
            T_Circ["borrow_records, fines"]
            T_Audit["audit_logs (Immutable Security Trail)"]
        end

        subgraph RedisStore["Redis 7 In-Memory Engine"]
            K_OTP["Registration OTP State (TTL 5m)"]
            K_Reset["Password Reset Token Digests (TTL 15m)"]
            K_MFA["Pending MFA Enrollment & Challenge (TTL 5m)"]
            K_RateLimit["Rate Limiting Sliding Window (ZSET + Lua)"]
        end
    end

    AxiosClient -->|HTTP / JSON| MW_CORS
    MW_SecHeaders --> Routers
    Routers --> CoreServices
    CoreServices --> S_Crypto
    CoreServices --> PostgreSQL
    CoreServices --> RedisStore
    MW_Rate -->|Sliding Window Lua| K_RateLimit
```

---

## Authentication Architecture

PustakHub implements a multi-stage authentication lifecycle separating unverified public registration, standard credential authentication, multi-factor challenges, and token refreshes.

```mermaid
sequenceDiagram
    autonumber
    actor User as User (Client)
    participant API as FastAPI Backend (/api/v1/auth)
    participant Redis as Redis 7 (Ephemeral Cache)
    participant Crypto as AES-256-GCM Engine
    participant DB as PostgreSQL 17 (Persistent DB)

    %% Registration Flow
    rect rgb(240, 248, 255)
    Note over User,DB: 1. Registration & Email OTP Verification
    User->>API: POST /auth/register (email, password, full_name)
    API->>API: Validate strength & compute Argon2id hash
    API->>Redis: Store pending registration + SHA-256(OTP) (TTL 5m)
    API-->>User: 200 OK (OTP dispatched via mock/SMTP)
    User->>API: POST /auth/verify-otp (email, otp_code)
    API->>Redis: Validate OTP digest & retrieve staged registration
    API->>DB: INSERT INTO users (status=ACTIVE) + Assign STUDENT role
    API->>Redis: Evict registration key
    API-->>User: 201 Created (User verified and provisioned)
    end

    %% Login Flow with MFA
    rect rgb(255, 250, 240)
    Note over User,DB: 2. Login & MFA Challenge
    User->>API: POST /auth/login (email, password)
    API->>DB: Query user & verify Argon2id hash
    alt MFA is Enabled on Account
        API->>Redis: Store mfa_challenge token (TTL 5m)
        API-->>User: 200 OK (mfa_required=true, mfa_token)
        User->>API: POST /auth/mfa/verify (mfa_token, totp_code)
        API->>DB: Fetch user.mfa_secret (AES-256-GCM ciphertext)
        API->>Crypto: decrypt_mfa_secret(ciphertext)
        Crypto-->>API: Plaintext Base32 secret
        API->>API: pyotp.TOTP(secret).verify(totp_code)
        API->>Redis: Evict mfa_challenge key
    end
    API->>DB: INSERT INTO user_sessions (SHA-256(refresh_token))
    API-->>User: 200 OK (access_token [15m], refresh_token [7d])
    end

    %% Refresh Token Rotation
    rect rgb(240, 255, 240)
    Note over User,DB: 3. Refresh Token Rotation & Invalidation
    User->>API: POST /auth/refresh (refresh_token)
    API->>DB: Find active session by SHA-256(refresh_token)
    API->>DB: UPDATE user_sessions SET is_revoked=true (Revoke old)
    API->>DB: INSERT INTO user_sessions (SHA-256(new_refresh_token))
    API-->>User: 200 OK (new access_token, new refresh_token)
    end
```

---

## Authorization Architecture

Authorization in PustakHub is **backend-enforced, dynamic, and database-backed**. Frontend UI routing guards are purely for user experience; every API request strictly evaluates permissions against PostgreSQL relations.

```mermaid
flowchart TD
    subgraph RequestContext["Incoming Request Context"]
        Req[HTTP Request] --> JWT[FastAPI Dependency: get_current_user]
        JWT -->|Verify Signature & Expiry| ActiveUser[Load Active User from DB]
    end

    subgraph RBAC["Dynamic DB-Backed RBAC Engine"]
        ActiveUser --> PermCheck{require_permission Gate}
        PermCheck --> QueryDB[(Query: user_roles ➔ role_permissions ➔ permissions)]
        QueryDB --> HasPerm{Permission Granted?}
        HasPerm -->|No| F403[403 Forbidden: Insufficient Permissions]
        HasPerm -->|Yes| ResCheck{Resource-Level Ownership Check}
    end

    subgraph ResourceAuth["Resource-Level Authorization (IDOR Defense)"]
        ResCheck --> OwnerCheck{current_user.id == resource.owner_id ?}
        OwnerCheck -->|Yes: Owner| Execute[Execute Service Logic]
        OwnerCheck -->|No: Not Owner| AdminCheck{Holds Administrative Permission?}
        AdminCheck -->|Yes: Staff Override| Execute
        AdminCheck -->|No: Unauthorized Probe| IDOR403[403 Forbidden: Access Denied to Target Resource]
    end

    subgraph RolesMatrix["Authoritative System Roles"]
        ADMIN["ADMIN<br/>(Full system control, roles, user lifecycle, audit logs)"]
        LIBRARIAN["LIBRARIAN<br/>(Catalog management, physical copies, checkout, return)"]
        STUDENT["STUDENT<br/>(Catalog browsing, personal borrowing history, fine inspection)"]
        GUEST["GUEST<br/>(Unauthenticated public catalog access)"]
    end
```

---

## Database Architecture

The PostgreSQL schema is managed exclusively through versioned **Alembic migrations** (`3741532892a9`). Relationships, indexes, and constraints guarantee referential integrity and high-speed lookups:

```mermaid
erDiagram
    users ||--o{ user_roles : "assigned"
    roles ||--o{ user_roles : "held by"
    roles ||--o{ role_permissions : "contains"
    permissions ||--o{ role_permissions : "granted to"
  
    users ||--o{ user_sessions : "maintains"
    users ||--o{ borrow_records : "borrows"
    users ||--o{ audit_logs : "triggers"

    categories ||--o{ books : "classifies"
    books ||--o{ book_copies : "manifests in"
    book_copies ||--o{ borrow_records : "loaned through"
    borrow_records ||--o| fines : "generates penalty"

    users {
        UUID id PK
        VARCHAR full_name
        VARCHAR email UK
        TEXT password_hash
        ENUM account_status
        BOOLEAN is_mfa_enabled
        TEXT mfa_secret "AES-256-GCM Encrypted"
        JSON mfa_recovery_codes "SHA-256 Hashed"
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    roles {
        UUID id PK
        VARCHAR name UK "ADMIN | LIBRARIAN | STUDENT | GUEST"
        TEXT description
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    permissions {
        UUID id PK
        VARCHAR name UK "resource:action"
        TEXT description
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    user_sessions {
        UUID id PK
        UUID user_id FK
        VARCHAR refresh_token_hash UK "SHA-256 Digest"
        VARCHAR user_agent
        VARCHAR ip_address
        BOOLEAN is_revoked
        TIMESTAMPTZ expires_at
        TIMESTAMPTZ created_at
    }

    categories {
        UUID id PK
        VARCHAR name UK
        TEXT description
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    books {
        UUID id PK
        VARCHAR title
        VARCHAR author
        VARCHAR isbn UK
        VARCHAR publisher
        INTEGER publication_year
        TEXT description
        UUID category_id FK
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    book_copies {
        UUID id PK
        UUID book_id FK
        VARCHAR copy_identifier UK "Barcode"
        ENUM status "AVAILABLE | BORROWED | MAINTENANCE | LOST"
        VARCHAR shelf_location
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    borrow_records {
        UUID id PK
        UUID user_id FK
        UUID book_copy_id FK
        TIMESTAMPTZ issued_at
        TIMESTAMPTZ due_at
        TIMESTAMPTZ returned_at
        ENUM status "ACTIVE | RETURNED | OVERDUE"
        TIMESTAMPTZ created_at
    }

    fines {
        UUID id PK
        UUID user_id FK
        UUID borrow_record_id FK "1:1 Unique"
        NUMERIC amount "2 Decimal Precision"
        ENUM reason "OVERDUE | DAMAGED | LOST"
        ENUM status "PENDING | PAID | WAIVED"
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    audit_logs {
        UUID id PK
        UUID user_id FK "Nullable for anonymous events"
        ENUM action "Security & Business Event Types"
        VARCHAR resource_type
        VARCHAR resource_id
        ENUM status "SUCCESS | FAILURE"
        VARCHAR ip_address
        VARCHAR user_agent
        TIMESTAMPTZ timestamp
    }
```

---

## Security Architecture

The HTTP request pipeline applies layered security controls before any route or business code is reached:

```mermaid
flowchart TD
    Client([HTTP Client / Browser]) --> MW_CORS[1. CORS Check<br/>Explicit Origin Whitelist]
  
    MW_CORS -->|Valid Origin| MW_Size[2. Request Size Limiter<br/>Content-Length & Stream <= 2MB]
    MW_CORS -->|Forbidden Origin| ErrCORS[403 / CORS Block]
  
    MW_Size -->|<= 2MB| MW_AuditCtx[3. Audit Context<br/>Extract Client IP & User-Agent]
    MW_Size -->|> 2MB| Err413[413 Request Entity Too Large]
  
    MW_AuditCtx --> MW_Rate[4. Rate Limiter<br/>Redis Sliding Window Lua Script]
    MW_Rate -->|Within Quota| MW_SecHead[5. Security Headers & CSP<br/>Attach CSP, X-Frame: DENY, nosniff]
    MW_Rate -->|Quota Exceeded| Err429[429 Too Many Requests + Retry-After]
  
    MW_SecHead --> Router[6. FastAPI Router & Route Dispatch]
    Router --> AuthCheck[7. JWT Bearer Token Validation]
  
    AuthCheck -->|Valid Token| RBACGate[8. DB RBAC Permission Gate<br/>require_permission Evaluation]
    AuthCheck -->|Invalid / Missing| Err401[401 Unauthorized]
  
    RBACGate -->|Has Permission| ResAuth[9. Resource-Level Authorization<br/>IDOR & Ownership Scoping]
    RBACGate -->|Missing Permission| Err403[403 Forbidden]
  
    ResAuth -->|Authorized Owner/Staff| Service[10. Domain Service Execution<br/>PostgreSQL Row Locks + Redis]
    ResAuth -->|Unauthorized Object Access| ErrIDOR[403 Forbidden: Resource Scoped]
  
    Service --> AuditLog[(11. Tamper-Resistant Audit Log<br/>Sanitized Event Written to DB)]
    AuditLog --> Response([HTTP 200 / 201 Response])
```

---

## Technology Stack

### Frontend

- **Framework:** React 19 (`react` 19.2.8, `react-dom` 19.2.8)
- **Tooling & Bundler:** Vite 8.3 (`@vitejs/plugin-react` 6.1)
- **Styling:** Tailwind CSS v4 (`@tailwindcss/vite` 4.3.3)
- **Routing:** React Router v7 (`react-router-dom` 7.18.4)
- **HTTP Client:** Axios 1.20 (configured with centralized auth interceptors)
- **QR Code Rendering:** `qrcode.react` 4.2 (client-side SVG generation)

### Backend

- **Framework:** Python 3.11+ / FastAPI 0.141+
- **ASGI Server:** Uvicorn with standard workers
- **Data Validation & Settings:** Pydantic v2 & `pydantic-settings`
- **ORM & Database Toolkit:** SQLAlchemy 2.0 (`selectin`, `Mapped`, `mapped_column`)
- **Database Driver:** `psycopg2-binary`
- **Schema Migrations:** Alembic 1.20

### Storage & Security Infrastructure

- **Relational Database:** PostgreSQL 17
- **Caching & Rate Limiting:** Redis 7 (Sorted Sets `ZSET` + Lua scripts)
- **Password Hashing:** `argon2-cffi` (Argon2id algorithm)
- **Token Signing:** `python-jose[cryptography]` (HMAC-SHA256 JWTs)
- **MFA Engine:** `pyotp` (RFC 6238 Time-based One-Time Passwords)
- **Symmetric Encryption:** `cryptography` AES-256-GCM AEAD (for TOTP secrets at rest)
- **Email Delivery:** SMTP abstraction with mock local development fallbacks

### Testing & Verification

- **Test Framework:** Pytest 9+ with `fastapi.testclient.TestClient` and `httpx`
- **Frontend Build Verification:** Production Vite bundle compilation (`npm run build`)

---

## Project Structure

```text
PustakHub/
├── .env.example                      # Root configuration template
├── .gitignore                        # Git exclusion rules
├── LICENSE                           # MIT Open Source License
├── README.md                         # Project documentation and architecture guide
├── docker-compose.yml                # Multi-container orchestration (DB, Redis, Backend, Frontend)
├── render.yaml                       # Render Blueprint specification for FastAPI, Postgres & Redis
│
├── backend/
│   ├── alembic.ini                   # Alembic database migration configuration
│   ├── Dockerfile                    # Production container specification for FastAPI backend
│   ├── pytest.ini                    # Pytest test suite configuration & filters
│   ├── requirements.txt              # Production and test Python dependencies
│   ├── .env.example                  # Backend environment template
│   │
│   ├── app/
│   │   ├── main.py                   # FastAPI app factory, lifespan, and router mounting
│   │   │
│   │   ├── core/                     # Core infrastructure & shared services
│   │   │   ├── config.py             # Pydantic Settings management
│   │   │   ├── database.py           # SQLAlchemy engine, session factory, connection checks
│   │   │   ├── encryption.py         # AES-256-GCM authenticated encryption for secrets
│   │   │   ├── exceptions.py         # Custom application exceptions and error envelopes
│   │   │   ├── logging.py            # Structured logging configuration
│   │   │   ├── redis.py              # Redis client pool and connectivity checks
│   │   │   └── security.py           # Argon2id hashing and JWT token management
│   │   │
│   │   ├── middleware/               # Security and request processing pipeline
│   │   │   ├── audit_context.py      # IP address and user-agent context extractor
│   │   │   ├── rate_limit.py         # Atomic Redis sliding-window rate limiter
│   │   │   ├── request_size.py       # 2MB payload protection (Content-Length + Streaming)
│   │   │   └── security_headers.py   # CSP, HSTS, X-Frame-Options, nosniff headers
│   │   │
│   │   ├── models/                   # SQLAlchemy declarative ORM models
│   │   │   ├── base.py               # Base class and TimestampMixin
│   │   │   ├── user.py               # User model with MFA fields and status enums
│   │   │   ├── role.py               # Role model and user_roles / role_permissions associations
│   │   │   ├── permission.py         # Permission model
│   │   │   ├── session.py            # UserSession model (hashed refresh token storage)
│   │   │   ├── category.py           # Category taxonomy model
│   │   │   ├── book.py               # Book bibliographic metadata model
│   │   │   ├── book_copy.py          # BookCopy physical inventory model
│   │   │   ├── borrow_record.py      # BorrowRecord circulation transaction model
│   │   │   ├── fine.py               # Fine penalty model
│   │   │   └── audit_log.py          # Immutable AuditLog model
│   │   │
│   │   └── modules/                  # Domain feature modules (Routers, Services, Schemas)
│   │       ├── audit/                # Audit trail query router and logging service
│   │       ├── auth/                 # Registration, Login, MFA, Reset, Refresh services
│   │       ├── books/                # Catalog, categories, and inventory copy management
│   │       ├── borrowing/            # Circulation, checkout, and return logic
│   │       ├── fines/                # Overdue fine queries and payment tracking
│   │       ├── permissions/          # Permission matrix and user permission resolution
│   │       ├── realtime/             # Authenticated WebSocket hub and Redis event publisher
│   │       ├── roles/                # Role CRUD and user-role assignment
│   │       └── users/                # User profile inspection and administration
│   │
│   ├── migrations/                   # Alembic migration scripts
│   │   ├── env.py                    # Alembic environment runner
│   │   └── versions/                 # Versioned migration files (0438258645fa, 3741532892a9)
│   │
│   └── tests/                        # Comprehensive Pytest test suite (238 tests)
│       ├── test_phase1_foundation.py
│       ├── test_phase2_database.py
│       ├── test_phase3_auth.py
│       ├── test_phase4_audit.py
│       ├── test_phase4_rbac.py
│       ├── test_phase5_catalog.py
│       ├── test_phase6_circulation.py
│       ├── test_phase7_auth_security.py
│       ├── test_phase8_security_hardening.py
│       ├── test_phase9_security_remediation.py
│       ├── test_phase11_seed.py
│       ├── test_phase12_catalog_ui.py
│       ├── test_phase13_circulation_ui.py
│       ├── test_phase14_dashboard_analytics.py
│       ├── test_phase15_user_iam_admin.py
│       ├── test_phase16_audit_management.py
│       └── test_phase17_realtime.py
│
├── frontend/
│   ├── package.json                  # Node dependencies and build scripts
│   ├── vite.config.js                # Vite bundler configuration
│   ├── vercel.json                   # Vercel SPA routing and rewrite rules
│   ├── Dockerfile                    # Production Nginx SPA container image
│   ├── index.html                    # Single Page Application HTML shell
│   │
│   └── src/
│       ├── App.jsx                   # React Router route declarations and layout wrapping
│       ├── main.jsx                  # Application entry point
│       ├── index.css                 # Tailwind CSS v4 design system
│       │
│       ├── components/               # Reusable UI components (Navbar, Alert, Modal, etc.)
│       ├── context/                  # React contexts (AuthContext, RealtimeContext, ThemeContext)
│       ├── hooks/                    # Custom React hooks (useAuth, usePermissions, useRealtime)
│       ├── layouts/                  # Shared layouts (MainLayout)
│       ├── pages/                    # Page components (Login, Register, MFA, Dashboard, Catalog, etc.)
│       └── services/                 # Centralized Axios API service layer (api.js, auth.service.js, etc.)
│
└── docs/                             # Engineering architecture & audit documentation
    ├── architecture.md               # System architecture and module boundaries
    ├── authentication.md             # Authentication, MFA, and session design
    ├── deployment.md                 # Production cloud deployment guide (Vercel + Render + Docker)
    ├── realtime.md                   # Authenticated WebSocket real-time update protocol
    ├── rbac.md                       # Role-Based Access Control and permission matrix
    ├── catalog.md                    # Library catalog management specification
    ├── circulation.md                # Circulation, borrowing, and fine calculation engine
    ├── database-design.md            # PostgreSQL schema design and entity relationships
    ├── security-hardening.md         # Rate limiting, security headers, CSP, and size limits
    ├── demo-data.md                  # Seed system architecture and demo credentials guide
    └── reports/                      # Phase milestone reports & security verification audits
```

---

## API Overview

PustakHub exposes **45+ registered endpoints** across 11 modular controllers (including authenticated WebSocket real-time event streaming):

| Module / Domain          | Base Path               | Key Capabilities                                                                                                                                                                                                                            |
| :----------------------- | :---------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Authentication** | `/api/v1/auth`        | User registration, email OTP verification, Argon2id login, refresh token rotation, logout revocation, authenticated profile (`/me`), forgot password, password reset, and RFC 6238 TOTP MFA setup, verification, status, and disablement. |
| **Users**          | `/api/v1/users`       | List user accounts, inspect individual profiles with assigned roles, and manage account statuses.                                                                                                                                           |
| **Roles**          | `/api/v1/roles`       | Create custom roles, list roles, inspect role definitions, assign permissions to roles, and manage user role bindings.                                                                                                                      |
| **Permissions**    | `/api/v1/permissions` | Inspect global permissions catalog, retrieve full Role-Permission Matrix (`/matrix`), and view caller's resolved permissions (`/me`).                                                                                                   |
| **Categories**     | `/api/v1/categories`  | Create, list, search, update, and delete catalog categories with dynamic book count tracking.                                                                                                                                               |
| **Books**          | `/api/v1/books`       | Search catalog with multi-field filtering (title, author, ISBN, year), register new book titles, update bibliographic metadata, and delete book entries.                                                                                    |
| **Book Copies**    | `/api/v1/copies`      | Register physical inventory copies with unique barcodes, inspect copy details, update shelf location or maintenance status, and delete un-borrowed copies.                                                                                  |
| **Borrowing**      | `/api/v1/borrow`      | Staff book checkout (`POST /borrow`) with row-level locking, book return (`POST /borrow/{id}/return`) with automated overdue fine calculation, and IDOR-protected borrowing history.                                                    |
| **Fines**          | `/api/v1/fines`       | Query overdue fines, inspect fine details, and access member-specific fine records with resource-level authorization.                                                                                                                       |
| **Realtime**       | `/api/v1/realtime`    | Authenticated WebSocket stream (`/ws`) delivering real-time event updates for catalog and circulation state synchronization across clients.                                                                                                |
| **Audit Logs**     | `/api/v1/audit/logs`  | Query immutable security audit trail with filtering by action, actor UUID, resource type, and timestamp range (restricted to`ADMIN` and `LIBRARIAN`).                                                                                   |
| **Health**         | `/api/health`         | Non-sensitive system health status reporting operational health for FastAPI, PostgreSQL, and Redis.                                                                                                                                         |

---

## Security Controls

| Security Area                         | Implementation Architecture                                                                                                                                                                                     |
| :------------------------------------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Password Hashing**            | **Argon2id** with memory-hard parameters via `argon2-cffi`. Timing attack mitigation executes dummy hashes on non-existent usernames.                                                                   |
| **Registration Verification**   | **Two-stage email OTP verification**. Unverified registration state is held strictly in Redis (TTL 5m); unverified users never touch PostgreSQL.                                                          |
| **OTP Storage**                 | **SHA-256 digest** storage in Redis. Plaintext OTP codes are never logged or persisted.                                                                                                                   |
| **Password Reset**              | **Cryptographically secure single-use tokens** (`secrets.token_urlsafe(32)`). Stored as SHA-256 digests in Redis (TTL 15m) with anti-enumeration responses.                                             |
| **Session Security**            | **Refresh token rotation and server-side revocation**. Refresh tokens are stored exclusively as SHA-256 digests in `user_sessions`. Successful password resets invalidate all active sessions.          |
| **Authentication**              | **HMAC-SHA256 signed JWTs** for stateless 15-minute access tokens.                                                                                                                                        |
| **Multi-Factor Auth (MFA)**     | **RFC 6238 TOTP** standard Time-based One-Time Passwords compatible with Google Authenticator and 1Password.                                                                                              |
| **MFA Secret Storage**          | **AES-256-GCM envelope encryption at rest** in PostgreSQL with versioned nonces (`v1:<nonce>:<ciphertext>`), decrypted in application memory only during verification.                                  |
| **Recovery Codes**              | **SHA-256 hashed emergency recovery codes**. Single-use consumption removes the code from the database upon valid use.                                                                                    |
| **Authorization**               | **Dynamic database-backed RBAC**. Fine-grained permissions (`book:create`, `user:view`) are resolved from PostgreSQL relations on every request.                                                      |
| **Resource Authorization**      | **Object-level ownership verification** (`check_resource_access`) to eliminate Insecure Direct Object References (IDOR / BOLA).                                                                         |
| **Rate Limiting**               | **Atomic sliding-window rate limiter** powered by Redis sorted sets (`ZSET`) and Lua scripts. Fail-closed on auth endpoints; fail-open on standard APIs.                                                |
| **Request Size Protection**     | **2 MB body size limiter** enforcing limits across both `Content-Length` headers and un-buffered streaming chunks (`Transfer-Encoding: chunked`).                                                     |
| **Security HTTP Headers**       | Strict**Content-Security-Policy (CSP)**, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy`, and optional HSTS. |
| **CORS Policy**                 | **Explicit origin whitelisting** from environment configuration with strict method and header control.                                                                                                    |
| **Audit Forensics**             | **Immutable PostgreSQL audit logs** capturing actor UUID, client IP, User-Agent, and action status with automatic sensitive data redaction.                                                               |
| **Database Integrity**          | **PostgreSQL 17** schema governed strictly through versioned Alembic migrations.                                                                                                                          |
| **Concurrency & Race Defenses** | **Pessimistic row locking (`SELECT ... FOR UPDATE`)** on book copies during checkout to eliminate double-issuance race conditions.                                                                      |

---

## Testing

The backend test suite verifies functionality, authorization rules, cryptographic integrity, and security hardening across all application layers:

```text
============================== 238 passed in 18.68s ==============================
```

- **Total Tests:** 238
- **Failures:** 0
- **Skipped:** 0
- **Warnings:** 0

### Test Coverage Areas

- **Foundation & Health:** Root endpoint, health probe checks, Redis/DB connectivity diagnostics.
- **Database & Migrations:** Table schemas, foreign key cascade behaviors, unique constraints, enum definitions, Alembic head synchronization.
- **Authentication & Sessions:** Redis-staged OTP registration, Argon2id verification, JWT issuance, refresh token rotation, logout revocation, profile inspection.
- **RBAC & Authorization:** Default role-permission seeding, dynamic permission resolution, unauthenticated 401 rejections, unauthorized 403 forbidden gates, role assignment security.
- **Resource-Level Authorization (IDOR):** Personal record access vs. cross-tenant IDOR attacks and administrative overrides.
- **Library Catalog:** Category hierarchy and delete protection, book title CRUD, physical copy inventory tracking, full-text catalog search and filtering.
- **Circulation & Fines:** Book checkout, row-level locking race prevention, double-issue protection, on-time returns, automated overdue fine calculation, and fine queries.
- **Auth Security & MFA:** Anti-enumeration password reset, token digestion, TOTP enrollment, challenge state machine, single-use recovery code consumption, MFA disablement re-authentication, secret masking.
- **Security Hardening:** Redis sliding-window rate limiting, fail-closed auth handling, request size limit enforcement, HTTP security headers, CORS preflight checks.
- **Post-Remediation Verification:** AES-256-GCM encryption round-trip, nonce variance, tamper-resistance validation, streaming chunk size rejection, local QR code generation.
- **Demo Data & Seeding System:** Deterministic generation, valid ISBN-13 check digits, production environment protection, password hashing with Argon2id, loan/copy synchronization, fine calculations, and idempotency.
- **UI Management & Administrative Workflows:** Catalog exploration, book & copy management, member loan dashboards, operational analytics, user IAM lifecycle, and forensic audit trail inspection.
- **Realtime WebSocket Synchronization:** Authenticated WebSocket connection lifecycle, Redis pub/sub message dispatching, and multi-client event-driven UI updates.

---

## Installation

### Prerequisites

- **Python:** Version 3.11 or higher
- **Node.js:** Version 18 or higher (Node 20+ recommended)
- **PostgreSQL:** Version 16 or 17
- **Redis:** Version 6 or 7

### Clone the Repository

```bash
git clone https://github.com/<YOUR-GITHUB-USERNAME>/PustakHub.git
cd PustakHub
```

---

## Environment Configuration

### Backend Configuration

Create a local `.env` file inside the `backend/` directory from the provided template:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your local connection credentials:

```ini
APP_NAME=PustakHub
APP_VERSION=0.1.0
DEBUG=false
ENVIRONMENT=development

# Server
HOST=0.0.0.0
PORT=8000

# CORS
CORS_ORIGINS=http://localhost:5173

# Database & Redis
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/pustakhub
REDIS_URL=redis://localhost:6379/0

# JWT & Crypto Secrets (Generate secure keys in production)
JWT_SECRET=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# MFA Encryption Key (AES-256-GCM 32-byte hex key)
MFA_ENCRYPTION_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_AUTH_REQUESTS=20
RATE_LIMIT_AUTH_WINDOW_SECONDS=60
RATE_LIMIT_API_REQUESTS=200
RATE_LIMIT_API_WINDOW_SECONDS=60
RATE_LIMIT_FAIL_CLOSED_AUTH=true

# Security Headers & Request Limits
MAX_REQUEST_BODY_SIZE=2097152
ENABLE_SECURITY_HEADERS=true
ENABLE_CSP=true
ENABLE_HSTS=false
```

### Frontend Configuration

Create a `.env` file in the `frontend/` directory:

```bash
cp frontend/.env.example frontend/.env
```

```ini
VITE_API_URL=http://localhost:8000/api/v1
```

---

## Running Locally

### 1. Database Setup

Ensure PostgreSQL is running and create the `pustakhub` database:

```bash
createdb pustakhub
```

Run database migrations to apply the complete schema and seed default roles:

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run migrations to head revision
alembic upgrade head
```

### 2. Redis Setup

Ensure your local Redis server is active:

```bash
# macOS (Homebrew)
brew services start redis

# Linux (systemd)
sudo systemctl start redis-server
```

Verify Redis is responsive:

```bash
redis-cli ping
# Response: PONG
```

### 3. Start Backend API Server

From the `backend/` directory (with your virtual environment activated):

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will start at `http://localhost:8000`.

### 4. Start Frontend Development Server

In a separate terminal window:

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`.

---

## Demo Data

PustakHub includes an optional deterministic demo-data seed system for local development and demonstrations.

It can populate the database with approximately:

- 20 categories
- 500 books
- 1,000+ book copies
- demo users for each role
- borrowing records
- representative fines

### Seeding the Database

From the `backend/` directory:

```bash
# Deterministic seed (seed=20260924)
python scripts/seed_demo.py

# Or safely reset demo data and re-seed
python scripts/seed_demo.py --reset-demo
```

### Seeded Demo Accounts (Local Development Only)

| Role                | Email                            | Password                                        | Scope                                                    |
| :------------------ | :------------------------------- | :---------------------------------------------- | :------------------------------------------------------- |
| **ADMIN**     | `admin.demo@pustakhub.com`     | *Configured locally (see `docs/demo-data.md`)*  | Full administrative control, user lifecycle, audit trail |
| **LIBRARIAN** | `librarian.demo@pustakhub.com` | *Configured locally (see `docs/demo-data.md`)*  | Catalog management, book checkouts, returns              |
| **STUDENT**   | `student.demo@pustakhub.com`   | *Configured locally (see `docs/demo-data.md`)*  | Catalog search, borrowing history, fines inspection      |
| **GUEST**     | `guest.demo@pustakhub.com`     | *Configured locally (see `docs/demo-data.md`)*  | Read-only catalog browsing                               |

> **Safety Notice:** Demo credentials are provided exclusively for **local development and demonstration**. Passwords can be customized via environment variable overrides (`DEMO_ADMIN_PASSWORD`, `DEMO_LIBRARIAN_PASSWORD`, etc.) during local seeding. The seeding script refuses to execute in production (`ENVIRONMENT=production`) without an explicit `--force-production-seed` override. MFA is disabled by default for demo users to allow immediate access.

See [docs/demo-data.md](docs/demo-data.md) for full seed architecture details.

---

## Frontend

The frontend is a single-page application built with **React 19**, **Vite**, and **Tailwind CSS v4**.

- **Routing & State:** Managed via React Router v7 with an application-wide `AuthContext` tracking active user identity, token refresh loops, and permissions.
- **Client-Side Security:**
  - Token interceptors automatically inject `Authorization: Bearer <token>` on API requests.
  - Automatic refresh token renewal on access token expiration.
  - Local QR code generation renders TOTP setup QR codes in-memory via `qrcode.react`, keeping private keys off third-party imaging servers.
  - UI permissions checks conditionally display staff/admin action buttons while relying on backend APIs for actual enforcement.

### Build Verification

To test the production frontend build:

```bash
cd frontend
npm run build
```

---

## Backend

The backend is built with **FastAPI** following a modular monolith pattern:

- **Entry Point:** `app/main.py` configures the application lifespan, mounts security middleware, registers exception handlers, and attaches modular routers.
- **Database Engine:** `app/core/database.py` manages SQLAlchemy connection pooling and provides request-scoped database sessions (`get_db`).
- **Cryptographic Subsystem:** `app/core/encryption.py` implements AES-256-GCM AEAD encryption with per-record random nonces.
- **Access Control:** `app/modules/permissions/service.py` evaluates permission matrices dynamically against PostgreSQL tables.
- **Circulation Concurrency:** `app/modules/borrowing/service.py` utilizes pessimistic database row locks during book issue workflows.

### Running Backend Tests

Execute the full Pytest regression suite:

```bash
cd backend
./venv/bin/pytest -v
```

---

## Example Workflows

### 1. Registration & Account Activation

1. **User Registration:** Client calls `POST /api/v1/auth/register` with name, email, and password. Data is staged in Redis with a 5-minute TTL, and an email OTP is dispatched.
2. **OTP Verification:** Client calls `POST /api/v1/auth/verify-otp` with email and OTP. Backend verifies OTP against Redis, inserts the `User` into PostgreSQL with status `ACTIVE`, assigns the default `STUDENT` role, and clears Redis state.

### 2. Multi-Factor Authentication (MFA) Setup

1. **Enrollment Request:** Authenticated user calls `POST /api/v1/auth/mfa/enroll`.
2. **Local QR Display:** Backend generates a TOTP secret and recovery codes, staging them temporarily in Redis. Frontend renders the `otpauth://` URI locally as an SVG QR code using `qrcode.react`.
3. **Activation Verification:** User scans the QR code into an authenticator app and submits the 6-digit TOTP code to `POST /api/v1/auth/mfa/verify-enrollment`.
4. **Encrypted Persistence:** Backend validates the code, encrypts the secret with AES-256-GCM, stores SHA-256 hashes of the recovery codes, commits `is_mfa_enabled = True` to PostgreSQL, and logs an `MFA_ENABLED` audit event.

### 3. MFA Login Challenge

1. **Credential Check:** User submits credentials to `POST /api/v1/auth/login`. Backend verifies password with Argon2id and detects `is_mfa_enabled = True`.
2. **Challenge Issuance:** Backend stages an `mfa_challenge` token in Redis (TTL 5m) and returns `{"mfa_required": true, "mfa_token": "..."}`.
3. **Second Factor Verification:** User submits `POST /api/v1/auth/mfa/verify` with `mfa_token` and TOTP code (or single-use recovery code). Backend decrypts the MFA secret in memory, verifies the code, issues JWT access and refresh tokens, and registers the session in PostgreSQL.

### 4. Book Borrowing & Overdue Fine Generation

1. **Issue Book:** Staff member calls `POST /api/v1/borrow` with `user_id` and `book_copy_id`. Backend locks the physical copy (`SELECT ... FOR UPDATE`), verifies `status = AVAILABLE`, sets status to `BORROWED`, computes `due_at = now + 14 days`, creates a `BorrowRecord`, and logs `COPY_ISSUED`.
2. **Return Book:** Staff calls `POST /api/v1/borrow/{id}/return`. Backend locks the `BorrowRecord`, marks the copy `AVAILABLE`, and calculates overdue days. If overdue, a `Fine` record is automatically inserted at `$2.00/day` and a `FINE_ISSUED` audit log is recorded in the same database transaction.

---

## API Documentation

PustakHub includes interactive OpenAPI documentation available directly when running the backend:

- **Swagger UI:** `http://localhost:8000/api/docs`
- **ReDoc:** `http://localhost:8000/api/redoc`
- **Raw OpenAPI Schema:** `http://localhost:8000/api/openapi.json`

---

## Development Phases

|      Phase      | Title                                          | Core Focus & Milestone Delivery                                                                                                                                                                                                                                    |
| :-------------: | :--------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|   **1**   | **Foundation**                           | Project architecture, FastAPI application factory, logging standards, exception handlers, and baseline health checks.                                                                                                                                              |
|   **2**   | **Database**                             | PostgreSQL 17 models, SQLAlchemy 2.0 declarative mappings, Alembic migration framework, foreign keys, and indexes.                                                                                                                                                 |
|   **3**   | **Authentication**                       | Redis-staged OTP registration, Argon2id password hashing, JWT access tokens, refresh token rotation, and server-side session tracking.                                                                                                                             |
|   **4**   | **RBAC & Audit**                         | Database-backed Role-Based Access Control, dynamic permission resolution, IDOR resource-level authorization, and immutable audit logs.                                                                                                                             |
|   **5**   | **Library Catalog**                      | Category taxonomy, book bibliographic metadata, physical copy inventory tracking, and full-text search with pagination.                                                                                                                                            |
|   **6**   | **Borrowing & Fines**                    | Row-locked circulation engine (`SELECT ... FOR UPDATE`), book checkout, return workflows, automated overdue fine calculation, and loan limits.                                                                                                                   |
|   **7**   | **Password Reset & MFA**                 | Anti-enumeration password reset, RFC 6238 TOTP enrollment, MFA login challenges, and single-use emergency recovery codes.                                                                                                                                          |
|   **8**   | **Security Hardening**                   | Redis sliding-window rate limiting, fail-closed auth handling, 2MB request body protection, HTTP security headers, and hardened CORS.                                                                                                                              |
|   **9**   | **Security Remediation**                 | AES-256-GCM encryption at rest for TOTP secrets, streaming chunked size enforcement, and client-side SVG QR code generation for CSP hardening.                                                                                                                     |
|  **10**  | **Documentation & Architecture**         | Architecture presentation, enterprise audit reporting, forensic logging analysis, and developer documentation.                                                                                                                                                     |
|  **11**  | **Deterministic Demo Seed System**       | Realistic synthetic dataset generation (500 books, 1,178 copies, 20 categories, 100 borrow records, 9 demo users) with reproducible seed CLI.                                                                                                                       |
|  **12**  | **Catalog Management UI**                | Production-quality React catalog explorer, server-side search & filters, bibliographic details, physical copy inventory management, category taxonomy CRUD, and dynamic RBAC UI gates (`PermissionGate`, `usePermissions`).                                    |
|  **13**  | **Circulation & Borrowing UI**           | Full-featured circulation experience: member loan dashboards, staff book issue modals with available copy selection & loan duration controls, return check-in with automatic overdue fine assessment, and transparent fines accounting ledgers.                    |
|  **14**  | **Dashboard & Operational Analytics UI** | Role-aware operational command center (`/dashboard`): administrative and circulation analytics, overdue alerts, recent loan and PostgreSQL audit activity streams, personal student borrowing summaries, and rapid action shortcuts.                             |
|  **15**  | **User & IAM Administration UI**         | Administrative user management (`/users`, `/users/:id`), multi-criteria filtering, lifecycle status management, role assignment & revocation, dynamic effective permissions hierarchy, self-lockout defenses, and zero-exposure credential guarantees.         |
|  **16**  | **Audit Management UI**                  | Read-only forensic audit console (`/audit`), multi-parameter server-side searching & filtering, single-event forensic inspection modal (`/api/v1/audit/logs/:id`), action categorization, client IP & User-Agent capture, and strict immutability enforcement. |
|  **17**  | **Real-Time WebSocket Synchronization**  | Authenticated WebSocket connection lifecycle (`/api/v1/realtime/ws`), Redis pub/sub event broadcasting, connection heartbeats, and client-side reactive UI updates for catalog & circulation. |
| **Final** | **Security Verification**                | Comprehensive independent post-remediation audit verifying 0 Critical, 0 High, 0 Medium, 0 Low, and 0 Informational findings.                                                                                                                                      |

---

## Security Verification

PustakHub underwent an extensive, multi-stage security review and independent post-remediation audit:

```text
Phase 8 Security Hardening ➔ Independent Security Audit (5 Findings)
                           ➔ Phase 9 Targeted Remediation
                           ➔ Independent Post-Remediation Verification (0 Findings)
```

> **Verification Statement:** The implemented security controls were independently verified against the audited scope, with no remaining Critical, High, Medium, Low, or Informational findings identified during the post-remediation verification.

Detailed verification reports:

- [Final Security Architecture Audit](docs/reports/FINAL_SECURITY_ARCHITECTURE_AUDIT.md)
- [Post-Remediation Security Verification Report](docs/reports/POST_REMEDIATION_SECURITY_VERIFICATION.md)

---

## Future Enhancements

The following capabilities are intentionally deferred architectural opportunities for future production hardening:

- **WebAuthn & FIDO2 Passkeys:** Hardware-backed biometric and security key authentication for passwordless sign-in.
- **HttpOnly Cookie Refresh Architecture:** Migrating refresh token storage from browser `localStorage` to secure, HttpOnly, SameSite cookies.
- **Hardware Security Module (HSM) / Cloud KMS:** Integrating AWS KMS, Azure Key Vault, or HashiCorp Vault for envelope master key management.
- **Web Application Firewall (WAF):** Edge-level DDoS mitigation, automated IP reputation filtering, and bot protection.
- **Catalog Reservation Queue:** Hold requests and automated waitlist notifications for checked-out book titles.

---

## Learning Outcomes

PustakHub serves as a reference architecture demonstrating:

- **Defense-in-Depth IAM Design:** Implementing multi-layered identity, session rotation, and dynamic permission resolution without trusting client state.
- **Cryptographic Engineering:** Applying modern memory-hard hashing (Argon2id), symmetric authenticated encryption (AES-256-GCM), and cryptographic entropy (`secrets`).
- **Concurrency & Transaction Safety:** Utilizing PostgreSQL row-level locking (`SELECT ... FOR UPDATE`) to prevent race conditions in financial and circulation operations.
- **Distributed Rate Limiting:** Developing atomic Redis Lua scripts to enforce sliding-window quotas across distributed application workers.
- **Auditing & Compliance:** Structuring forensic security logs with automated data redaction to maintain tamper-resistant accountability.

---

## Author

* **Sandip Biswal** — *Architect & Developer*

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
