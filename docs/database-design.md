# PustakHub — Database Design

> **Phase 2 — PostgreSQL & Database Foundation**
> Status: IMPLEMENTED
> Last updated: 2026-09-24

---

## Table of Contents

1. [Database Choice](#1-database-choice)
2. [Architecture Overview](#2-architecture-overview)
3. [Entity Relationship Diagram](#3-entity-relationship-diagram)
4. [Entities](#4-entities)
5. [Relationships](#5-relationships)
6. [Constraints & Indexes](#6-constraints--indexes)
7. [Session / Token Persistence Design](#7-session--token-persistence-design)
8. [Migration Strategy](#8-migration-strategy)
9. [Security Considerations](#9-security-considerations)
10. [Status Key](#10-status-key)

---

## 1. Database Choice

**PostgreSQL 17** (Homebrew, local development)

**Why PostgreSQL:**
- Native UUID primary key support (`uuid` type)
- Native enum types (`CREATE TYPE ... AS ENUM`)
- ACID transactions with strong integrity guarantees
- `NUMERIC(10,2)` for precise financial amounts (fines)
- Rich constraint support: CHECK, UNIQUE, COMPOSITE, FK with CASCADE/RESTRICT
- `TIMESTAMP WITH TIME ZONE` for correct cross-timezone timestamp storage
- Proven track record for IAM and financial systems

**Driver:** `psycopg2-binary` (synchronous driver; async driver can be added later with `asyncpg`)
**ORM:** SQLAlchemy 2.0 (declarative mapping, `Mapped[]`/`mapped_column()` style)
**Migrations:** Alembic 1.20 (autogenerate + manual refinement)

---

## 2. Architecture Overview

```
backend/
├── app/
│   ├── core/
│   │   └── database.py        # Engine, session factory, get_db dependency
│   └── models/
│       ├── base.py            # DeclarativeBase + TimestampMixin
│       ├── __init__.py        # Imports all models (required for Alembic)
│       ├── user.py            # User entity
│       ├── role.py            # Role entity + user_roles + role_permissions tables
│       ├── permission.py      # Permission entity
│       ├── session.py         # UserSession (refresh token foundation)
│       ├── category.py        # Category entity
│       ├── book.py            # Book entity
│       ├── book_copy.py       # BookCopy entity
│       ├── borrow_record.py   # BorrowRecord entity
│       ├── fine.py            # Fine entity
│       └── audit_log.py       # AuditLog entity
├── migrations/
│   ├── env.py                 # Alembic environment (loads DB URL from settings)
│   ├── script.py.mako         # Migration file template
│   └── versions/
│       ├── 0438258645fa_initial_schema.py
│       └── 3741532892a9_add_mfa_and_password_reset_support.py
└── alembic.ini                # Alembic configuration (no credentials)
```

**Key principles:**
- `Base.metadata.create_all()` is **never** called — all schema changes go through Alembic.
- DATABASE_URL is loaded exclusively from environment variables.
- Models are imported in `models/__init__.py` to guarantee Alembic autogenerate sees all tables.

---

## 3. Entity Relationship Diagram

```mermaid
erDiagram
    users {
        UUID id PK
        VARCHAR full_name
        VARCHAR email UK
        TEXT password_hash
        ENUM account_status
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    roles {
        UUID id PK
        VARCHAR name UK
        TEXT description
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    permissions {
        UUID id PK
        VARCHAR name UK
        TEXT description
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    user_roles {
        UUID user_id FK
        UUID role_id FK
    }

    role_permissions {
        UUID role_id FK
        UUID permission_id FK
    }

    user_sessions {
        UUID id PK
        UUID user_id FK
        VARCHAR token_hash UK
        TIMESTAMPTZ expires_at
        BOOLEAN is_revoked
        TEXT user_agent
        VARCHAR ip_address
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
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
        SMALLINT publication_year
        TEXT description
        UUID category_id FK
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    book_copies {
        UUID id PK
        UUID book_id FK
        VARCHAR copy_identifier UK
        ENUM status
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
        ENUM status
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    fines {
        UUID id PK
        UUID borrow_record_id FK UK
        NUMERIC amount
        ENUM reason
        ENUM status
        TEXT notes
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    audit_logs {
        UUID id PK
        UUID user_id FK
        ENUM action
        VARCHAR resource_type
        TEXT resource_id
        ENUM status
        TIMESTAMPTZ timestamp
        VARCHAR ip_address
        TEXT user_agent
    }

    users ||--o{ user_roles : "assigned"
    roles ||--o{ user_roles : "assigned to"
    roles ||--o{ role_permissions : "has"
    permissions ||--o{ role_permissions : "granted via"
    users ||--o{ user_sessions : "owns"
    categories ||--o{ books : "contains"
    books ||--o{ book_copies : "has copies"
    users ||--o{ borrow_records : "borrows"
    book_copies ||--o{ borrow_records : "borrowed as"
    borrow_records ||--o| fines : "may incur"
    users ||--o{ audit_logs : "generates"
```

---

## 4. Entities

### 4.1 User — IMPLEMENTED

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK, generated client-side (uuid4) |
| full_name | VARCHAR(255) | NOT NULL |
| email | VARCHAR(320) | NOT NULL, UNIQUE — RFC 5321 max length |
| password_hash | TEXT | Nullable — Argon2id hash (Phase 3); never plaintext |
| account_status | ENUM | `ACTIVE`, `SUSPENDED`, `DEACTIVATED`, `PENDING_VERIFICATION` |
| created_at | TIMESTAMPTZ | Server default: now() |
| updated_at | TIMESTAMPTZ | Server default: now(), auto-updated |

**Indexes:** `uq_users_email`, `ix_users_account_status`, `ix_users_created_at`

---

### 4.2 Role — IMPLEMENTED

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| name | VARCHAR(100) | NOT NULL, UNIQUE — e.g., `ADMIN`, `LIBRARIAN`, `STUDENT`, `GUEST` |
| description | TEXT | Nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**Indexes:** `uq_roles_name`, `ix_roles_name`

---

### 4.3 Permission — IMPLEMENTED

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| name | VARCHAR(150) | NOT NULL, UNIQUE — e.g., `book:create`, `user:suspend` |
| description | TEXT | Nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**Indexes:** `uq_permissions_name`, `ix_permissions_name`

---

### 4.4 user_roles (association) — IMPLEMENTED

| Field | Type | Notes |
|---|---|---|
| user_id | UUID | FK → users.id, CASCADE DELETE |
| role_id | UUID | FK → roles.id, CASCADE DELETE |

**Constraints:** `uq_user_roles_user_role` (composite unique on user_id, role_id)
**Indexes:** `ix_user_roles_user_id`, `ix_user_roles_role_id`

---

### 4.5 role_permissions (association) — IMPLEMENTED

| Field | Type | Notes |
|---|---|---|
| role_id | UUID | FK → roles.id, CASCADE DELETE |
| permission_id | UUID | FK → permissions.id, CASCADE DELETE |

**Constraints:** `uq_role_permissions_role_permission` (composite unique)
**Indexes:** `ix_role_permissions_role_id`, `ix_role_permissions_permission_id`

---

### 4.6 UserSession — IMPLEMENTED

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id, CASCADE DELETE |
| token_hash | VARCHAR(64) | SHA-256 hex digest — NOT the raw token |
| expires_at | TIMESTAMPTZ | NOT NULL |
| is_revoked | BOOLEAN | Default: false |
| user_agent | TEXT | Nullable — client metadata |
| ip_address | VARCHAR(45) | Nullable — IPv6-safe length |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**Indexes:** `uq_user_sessions_token_hash`, `ix_user_sessions_user_id_is_revoked`, `ix_user_sessions_expires_at`

---

### 4.7 Category — IMPLEMENTED

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| name | VARCHAR(150) | NOT NULL, UNIQUE |
| description | TEXT | Nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

---

### 4.8 Book — IMPLEMENTED

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| title | VARCHAR(500) | NOT NULL |
| author | VARCHAR(500) | NOT NULL |
| isbn | VARCHAR(20) | UNIQUE, Nullable (books without ISBNs exist) |
| publisher | VARCHAR(300) | Nullable |
| publication_year | SMALLINT | Nullable |
| description | TEXT | Nullable |
| category_id | UUID | FK → categories.id, SET NULL on delete |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**Indexes:** `ix_books_title`, `ix_books_author`, `ix_books_isbn`, `ix_books_category_id`, `ix_books_publication_year`

---

### 4.9 BookCopy — IMPLEMENTED

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| book_id | UUID | FK → books.id, CASCADE DELETE |
| copy_identifier | VARCHAR(100) | UNIQUE — barcode / label |
| status | ENUM | `AVAILABLE`, `BORROWED`, `MAINTENANCE`, `LOST` |
| shelf_location | VARCHAR(100) | Nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**Indexes:** `uq_book_copies_copy_identifier`, `ix_book_copies_book_id`, `ix_book_copies_status`, `ix_book_copies_book_id_status`

---

### 4.10 BorrowRecord — IMPLEMENTED

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id, RESTRICT delete |
| book_copy_id | UUID | FK → book_copies.id, RESTRICT delete |
| issued_at | TIMESTAMPTZ | NOT NULL |
| due_at | TIMESTAMPTZ | NOT NULL |
| returned_at | TIMESTAMPTZ | Nullable — set on return |
| status | ENUM | `ACTIVE`, `RETURNED`, `OVERDUE`, `LOST` |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**FK on delete:** RESTRICT — borrow history must not be silently deleted.

---

### 4.11 Fine — IMPLEMENTED

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| borrow_record_id | UUID | FK → borrow_records.id, UNIQUE, RESTRICT |
| amount | NUMERIC(10,2) | CHECK: amount >= 0 |
| reason | ENUM | `OVERDUE`, `LOST`, `DAMAGED` |
| status | ENUM | `PENDING`, `PAID`, `WAIVED` |
| notes | TEXT | Nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

---

### 4.12 AuditLog — IMPLEMENTED

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id, SET NULL — nullable for pre-auth events |
| action | ENUM | 20+ actions covering auth and library operations |
| resource_type | VARCHAR(100) | Nullable — e.g., `User`, `BookCopy` |
| resource_id | TEXT | Nullable — string PK of the affected resource |
| status | ENUM | `SUCCESS`, `FAILURE`, `PARTIAL` |
| timestamp | TIMESTAMPTZ | Server default: now(), immutable |
| ip_address | VARCHAR(45) | Nullable |
| user_agent | TEXT | Nullable |

**Design:** Append-only. No `updated_at`. No `created_at` — only `timestamp`.

---

## 5. Relationships

| Relationship | Type | FK Behaviour |
|---|---|---|
| User ↔ Role | M:N via user_roles | CASCADE DELETE |
| Role ↔ Permission | M:N via role_permissions | CASCADE DELETE |
| User → UserSession | 1:N | CASCADE DELETE |
| Category → Book | 1:N | SET NULL |
| Book → BookCopy | 1:N | CASCADE DELETE |
| User → BorrowRecord | 1:N | RESTRICT |
| BookCopy → BorrowRecord | 1:N | RESTRICT |
| BorrowRecord → Fine | 1:0-1 | RESTRICT |
| User → AuditLog | 1:N | SET NULL |

---

## 6. Constraints & Indexes

### Critical Unique Constraints

| Table | Column(s) | Constraint Name |
|---|---|---|
| users | email | uq_users_email |
| roles | name | uq_roles_name |
| permissions | name | uq_permissions_name |
| user_roles | (user_id, role_id) | uq_user_roles_user_role |
| role_permissions | (role_id, permission_id) | uq_role_permissions_role_permission |
| user_sessions | token_hash | uq_user_sessions_token_hash |
| book_copies | copy_identifier | uq_book_copies_copy_identifier |
| fines | borrow_record_id | (unique on FK) |

### Check Constraints

| Table | Constraint | Name |
|---|---|---|
| fines | amount >= 0 | ck_fines_amount_non_negative |

### Key Performance Indexes

| Table | Columns | Purpose |
|---|---|---|
| users | account_status | Filter active/suspended users |
| books | title, author, isbn | Search catalogue |
| book_copies | (book_id, status) | Find available copies of a title |
| borrow_records | (book_copy_id, status) | Active borrow check |
| borrow_records | due_at | Overdue detection jobs |
| audit_logs | (user_id, timestamp) | User activity timeline |
| user_sessions | (user_id, is_revoked) | Fast active session lookup |

---

## 7. Session / Token Persistence Design

The `user_sessions` table stores a **SHA-256 hash** of the refresh token — not the raw token.

**Rationale:**

1. **If the sessions table is compromised**, attackers cannot replay refresh tokens because they do not possess the pre-image. They only have the hash.
2. **The raw token** is held exclusively in the client's secure storage (e.g., HttpOnly cookie). The server only hashes it during the refresh call.
3. **SHA-256 is appropriate** here because refresh tokens are high-entropy random strings (not low-entropy user-chosen secrets like passwords). Argon2id is unnecessary for token storage.
4. **Revocation** is handled by the `is_revoked` flag. Expired and revoked sessions will be purged by a background job in a future phase.

**Auth logic is PLANNED for Phase 3.** The schema is established in Phase 2 only.

---

## 8. Migration Strategy

- Alembic is configured with **autogenerate** — it diffs the live database schema against `Base.metadata`.
- `migrations/env.py` loads `DATABASE_URL` exclusively from `app.core.config.settings`, never from `alembic.ini`.
- `alembic.ini` does **not** contain credentials and may be committed safely.
- **Production migrations** must be reviewed manually after autogenerate and applied with `alembic upgrade head` during a deploy pipeline.
- **Rollbacks** use `alembic downgrade -1` or `alembic downgrade <rev>`.
- **Never** use `Base.metadata.create_all()` to bypass migrations.

---

## 9. Security Considerations

| Concern | Mitigation |
|---|---|
| Credentials in config files | DATABASE_URL only in `.env` (gitignored) |
| Passwords in database | `password_hash` column — Argon2id in Phase 3; plaintext never stored |
| Token exposure | Only SHA-256 hash stored in `user_sessions.token_hash` |
| Audit log tampering | Append-only table; no `updated_at`; no application-level DELETE permitted |
| Sensitive data in audit logs | AuditLog model explicitly excludes passwords, OTP, tokens |
| Database credentials in logs | `check_database_connection()` logs only exception type, never DATABASE_URL |
| Credentials in API responses | Health endpoint returns `"healthy"` / `"unreachable"` only |
| Borrow history deletion | RESTRICT FK prevents accidental user/copy deletion when records exist |

---

## 10. Status Key

| Tag | Meaning |
|---|---|
| IMPLEMENTED | Schema created and migration applied in Phase 2 |
| PLANNED | Deferred to a later named phase |
