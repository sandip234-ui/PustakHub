# Phase 3 Completion Report — PustakHub

**Status:** `COMPLETE`  
**Phase:** Phase 3 — Authentication, Registration & Email OTP  
**Platform:** PustakHub (Secure Library & Identity Management Platform)  
**Date:** 2026-09-24  

---

## 1. Summary

Phase 3 established the complete **authentication, user registration, email OTP verification, and session management foundation** for PustakHub.

All objectives set forth for Phase 3 have been fully implemented, integrated with the Phase 2 PostgreSQL data layer, and verified through automated end-to-end and unit tests.

### Key Highlights
- **Zero-Unverified Database Accounts:** Users registering publicly are held exclusively in Redis temporary cache; PostgreSQL `User` records are created **only after** successful 6-digit email OTP verification.
- **Argon2id Password Security:** Passwords hashed with Argon2id; verification functions incorporate timing attack mitigation.
- **Dual-Token & Hashed Session Store:** Short-lived JWT access tokens and long-lived refresh tokens. Database `user_sessions` stores only SHA-256 digests (`token_hash`), enabling token rotation and server-side session revocation.
- **Immutable Role Security:** Public registration strictly and immutably assigns the `STUDENT` role server-side; client role injection is rejected.
- **Frontend State & UI:** Full authentication state management (`AuthContext`, `useAuth`), Axios interceptors with automatic refresh and queueing, Route Guards (`ProtectedRoute`, `GuestRoute`), and modern, responsive pages (`RegisterPage`, `VerifyOtpPage`, `LoginPage`, `DashboardPreviewPage`).
- **Test Coverage:** All **44/44 tests passing** (11 Phase 1 foundation + 15 Phase 2 database + 18 Phase 3 authentication tests).

---

## 2. Architecture & Flows

### 2.1 Registration & OTP Flow
1. Client submits `POST /api/v1/auth/register` (`name`, `email`, `password`).
2. Input is validated: strong password policy enforced (min 8 chars, uppercase, lowercase, number, special symbol), email normalized.
3. System checks PostgreSQL to prevent duplicate registrations for active accounts.
4. Password is encrypted with Argon2id; secure 6-digit numeric OTP is generated via `secrets.randbelow` and hashed via SHA-256.
5. Registration state is cached in Redis under `registration:<email>` with a 5-minute TTL. No PostgreSQL record is created.
6. Email OTP notification is dispatched via `EmailService`.
7. Client submits `POST /api/v1/auth/verify-otp` (`email`, `otp`).
8. Verification checks attempt count (throttled at 5 max attempts). Upon valid hash match:
   - PostgreSQL transaction provisions `User` entity with `account_status=ACTIVE`.
   - `STUDENT` role is queried/created and assigned.
   - Redis temporary registration key is purged.
   - User account is activated and ready for login.

### 2.2 Login, Token Issuance & Refresh Flow
1. Client submits `POST /api/v1/auth/login` (`email`, `password`).
2. User is looked up and verified using `verify_password(password, user.password_hash)`.
3. Account status is verified (`ACTIVE` required; `SUSPENDED` / `PENDING_VERIFICATION` / `DEACTIVATED` rejected).
4. System issues:
   - **Access Token:** JWT with claims `sub` (User UUID), `type: "access"`, `jti`, `exp` (30 mins).
   - **Refresh Token:** JWT with claims `sub`, `type: "refresh"`, `jti`, `exp` (7 days).
5. SHA-256 digest of the refresh token is persisted to `user_sessions` along with client metadata (`ip_address`, `user_agent`). Raw refresh token is returned to client and never persisted.
6. When client calls `POST /api/v1/auth/refresh`, system validates the refresh token, verifies the hash in `user_sessions`, checks that `is_revoked == False` and user is active, revokes the old session, and issues a new access token and refresh token pair (Refresh Token Rotation).

### 2.3 Logout & Session Invalidation
1. Client calls `POST /api/v1/auth/logout` (`refresh_token`).
2. System computes the SHA-256 digest of the token and marks the session in `user_sessions` as `is_revoked = True`.
3. Subsequent attempts to use or refresh that token are rejected with 401 Unauthorized.

### 2.4 Reusable Authentication Dependencies
- `get_current_user`: Resolves the caller's `User` model from the `Authorization: Bearer <token>` header, verifying token signature, expiration, and active status.
- `require_authenticated_user`: Exported alias for protecting future domain endpoints.

---

## 3. Files Created

| File | Type | Description |
|---|---|---|
| `backend/app/core/security.py` | Backend | Argon2id password hashing, secure OTP generation/hashing, and JWT access/refresh token operations. |
| `backend/app/core/redis.py` | Backend | Redis client connection manager and health check utility. |
| `backend/app/core/email.py` | Backend | Outbound email delivery service abstraction with SMTP support and development simulation fallback. |
| `backend/app/modules/auth/schemas.py` | Backend | Strict Pydantic models for registration, OTP verification, login, tokens, and sanitized user profiles. |
| `backend/app/modules/auth/service.py` | Backend | Core authentication service handling Redis state, OTP verification, user provisioning, login, rotation, and logout. |
| `backend/app/modules/auth/dependencies.py` | Backend | Reusable FastAPI dependencies for JWT Bearer extraction and User resolution. |
| `backend/app/modules/auth/router.py` | Backend | HTTP router implementing `/register`, `/verify-otp`, `/login`, `/refresh`, `/logout`, and `/me`. |
| `backend/tests/test_phase3_auth.py` | Backend Tests | 18 comprehensive automated tests for password security, OTP throttling, registration, login, JWT claims, rotation, and logout. |
| `frontend/src/services/auth.service.js` | Frontend Service | API client for authentication endpoints. |
| `frontend/src/context/AuthContext.jsx` | Frontend Context | Global React authentication context and session persistence provider. |
| `frontend/src/hooks/useAuth.js` | Frontend Hook | Custom hook for interacting with `AuthContext`. |
| `frontend/src/components/ProtectedRoute.jsx` | Frontend Component | Route guard for authenticated areas (redirects to `/login`). |
| `frontend/src/components/GuestRoute.jsx` | Frontend Component | Route guard for non-authenticated guests (redirects to `/dashboard`). |
| `frontend/src/pages/RegisterPage.jsx` | Frontend Page | Student registration view with password policy checks and OTP routing. |
| `frontend/src/pages/VerifyOtpPage.jsx` | Frontend Page | 6-digit email OTP verification view with attempt feedback and auto-redirect. |
| `frontend/src/pages/LoginPage.jsx` | Frontend Page | User login view with credential validation and error messaging. |
| `frontend/src/pages/DashboardPreviewPage.jsx` | Frontend Page | Authenticated profile and session preview with logout controls. |
| `docs/authentication.md` | Documentation | Complete authentication architecture design, sequence diagrams, and security analysis. |

---

## 4. Files Modified

| File | Modification Details |
|---|---|
| `backend/app/core/config.py` | Added configuration variables and defaults for Redis (`REDIS_URL`), JWT (`JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`), OTP (`OTP_EXPIRE_MINUTES`, `MAX_OTP_ATTEMPTS`), and SMTP (`SMTP_*`). |
| `backend/app/core/exceptions.py` | Updated `request_validation_exception_handler` with `jsonable_encoder` to safely serialize custom validation errors. |
| `backend/app/main.py` | Mounted `auth_router` at `/api/v1`, and integrated Redis connectivity check into `/api/health` and application lifespan. |
| `backend/.env` | Added local development defaults for Redis, JWT, and SMTP. |
| `backend/.env.example` | Updated configuration template with sanitized placeholders for Phase 3 variables. |
| `frontend/src/services/api.js` | Added Axios request/response interceptors for automatic Bearer token attachment, 401 handling, refresh token rotation, and in-flight request queueing. |
| `frontend/src/pages/HomePage.jsx` | Enhanced landing page with dynamic action buttons (Register, Log In, Dashboard) and system health status. |
| `frontend/src/App.jsx` | Wrapped application in `AuthProvider` and configured full route map with `ProtectedRoute` and `GuestRoute` wrappers. |

---

## 5. Dependencies

### Python (`backend/requirements.txt`)
All required libraries were already specified in requirements and confirmed operational in `backend/venv`:
- `argon2-cffi` (v25.1.0) — Argon2id password hashing
- `python-jose[cryptography]` (v3.5.0) — JWT signing and decoding
- `redis` (v8.1.0) — Redis client for temporary registration state
- `email-validator` (v2.3.0) — RFC-compliant email validation in Pydantic

### Local Infrastructure
- **Redis Server:** Installed via Homebrew (`redis 8.10.2`) and running locally on `localhost:6379`.
- **PostgreSQL 17.11:** Database `pustakhub` running on `localhost:5432`.

### Frontend
- No new npm packages were needed; existing `axios`, `react-router-dom`, `tailwindcss`, and `react` were fully utilized.

---

## 6. Database Changes

- **Schema Modifications:** No schema modifications or new migrations were necessary. The Phase 2 database schema (`0438258645fa_initial_schema.py`) already defined the complete data model, including `users.password_hash`, `users.account_status`, `roles`, `user_roles`, and `user_sessions.token_hash`.
- **Alembic Status:** Current revision remains `0438258645fa (head)`.

---

## 7. Redis Temporary Storage

- **Key Pattern:** `registration:<email>`
- **TTL:** 300 seconds (5 minutes).
- **Data Stored:** `name`, `email`, `password_hash` (Argon2id), `otp_hash` (SHA-256), `otp_attempts` (counter), `created_at`, `expires_at`.
- **Lifecycle:**
  - Written on `POST /api/v1/auth/register`.
  - Updated with attempt counter on failed verification attempts.
  - Purged automatically upon reaching 5 failed attempts or upon successful user creation.

---

## 8. Email Dispatch

- **Provider Abstraction:** Implemented in `backend/app/core/email.py` (`EmailService.send_registration_otp`).
- **Production Mode:** When `SMTP_HOST` is specified, establishes TLS connection via `smtplib`, performs optional authentication, and delivers multi-part plain text and HTML emails.
- **Development / Test Mode:** When `SMTP_HOST` is unconfigured or mocked in tests, safely dispatches simulated messages without exposing OTP credentials in production logs.

---

## 9. Security Review

| Security Area | Implementation Details |
|---|---|
| **Password Hashing** | Argon2id is strictly used with random salting. Passwords are never logged or returned in responses. |
| **OTP Generation & Verification** | 6-digit numeric OTPs generated with `secrets.randbelow`. Stored exclusively as SHA-256 hashes. Verification uses constant-time comparison (`hmac.compare_digest`). Throttled to 5 attempts maximum. |
| **Token Storage** | Refresh tokens are hashed with SHA-256 before storage in `user_sessions`. No raw tokens reside in the database. |
| **JWT Access Tokens** | Signed with HMAC-SHA256 (`HS256`) using environment-driven secret. Short 30-minute lifespan. Payload contains minimal claims (`sub`, `type: "access"`, `jti`, `iat`, `exp`). |
| **Role Assignment** | Hardcoded to `STUDENT` server-side during registration verification. Client-supplied role fields are rejected. |
| **Account Status Enforcement** | Inactive, pending, suspended, or deactivated accounts are barred from authenticating or refreshing tokens. |
| **Timing Attack Mitigation** | Inexistent user logins execute verification against a dummy Argon2id hash to prevent timing enumeration. |

---

## 10. Automated Tests Execution

```text
============================= test session starts ==============================
platform darwin -- Python 3.11.14, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/sandipbiswal/Desktop/PustakHub/backend
plugins: anyio-4.15.1
collected 44 items

tests/test_phase1_foundation.py::test_app_starts PASSED                  [  2%]
tests/test_phase1_foundation.py::test_root_endpoint PASSED               [  4%]
tests/test_phase1_foundation.py::test_health_endpoint_status_code PASSED [  6%]
tests/test_phase1_foundation.py::test_health_endpoint_body PASSED        [  9%]
tests/test_phase1_foundation.py::test_settings_load PASSED               [ 11%]
tests/test_phase1_foundation.py::test_import_core_config PASSED          [ 13%]
tests/test_phase1_foundation.py::test_import_core_logging PASSED         [ 15%]
tests/test_phase1_foundation.py::test_import_core_exceptions PASSED      [ 18%]
tests/test_phase1_foundation.py::test_import_main PASSED                 [ 20%]
tests/test_phase1_foundation.py::test_unknown_route_returns_404 PASSED   [ 22%]
tests/test_phase1_foundation.py::test_cors_header_present PASSED         [ 25%]
tests/test_phase2_database.py::test_database_url_is_set PASSED           [ 27%]
tests/test_phase2_database.py::test_engine_initialises PASSED            [ 29%]
tests/test_phase2_database.py::test_session_can_be_created PASSED        [ 31%]
tests/test_phase2_database.py::test_database_connection_succeeds PASSED  [ 34%]
tests/test_phase2_database.py::test_raw_sql_executes PASSED              [ 36%]
tests/test_phase2_database.py::test_all_models_import PASSED             [ 38%]
tests/test_phase2_database.py::test_expected_tables_in_metadata PASSED   [ 40%]
tests/test_phase2_database.py::test_expected_tables_exist_in_database PASSED [ 43%]
tests/test_phase2_database.py::test_unique_email_constraint PASSED       [ 45%]
tests/test_phase2_database.py::test_unique_role_name_constraint PASSED   [ 47%]
tests/test_phase2_database.py::test_unique_session_token_hash_constraint PASSED [ 50%]
tests/test_phase2_database.py::test_book_with_nonexistent_category_raises PASSED [ 52%]
tests/test_phase2_database.py::test_user_role_composite_unique PASSED    [ 54%]
tests/test_phase2_database.py::test_alembic_migration_at_head PASSED     [ 56%]
tests/test_phase2_database.py::test_health_endpoint_reports_db_healthy PASSED [ 59%]
tests/test_phase3_auth.py::test_password_hashes_successfully_with_argon2id PASSED [ 61%]
tests/test_phase3_auth.py::test_password_verification_success_and_failure PASSED [ 63%]
tests/test_phase3_auth.py::test_otp_generation_and_hashing PASSED        [ 65%]
tests/test_phase3_auth.py::test_register_validation_rejects_weak_passwords PASSED [ 68%]
tests/test_phase3_auth.py::test_register_stores_temporary_state_in_redis_not_postgres PASSED [ 70%]
tests/test_phase3_auth.py::test_register_forbids_arbitrary_roles PASSED  [ 72%]
tests/test_phase3_auth.py::test_verify_otp_success_creates_active_student_user PASSED [ 75%]
tests/test_phase3_auth.py::test_verify_otp_invalid_code_throttles_and_fails PASSED [ 77%]
tests/test_phase3_auth.py::test_verify_otp_max_attempts_exceeded_deletes_registration PASSED [ 79%]
tests/test_phase3_auth.py::test_login_success_returns_tokens_and_stores_session_hash PASSED [ 81%]
tests/test_phase3_auth.py::test_login_invalid_password_returns_401 PASSED [ 84%]
tests/test_phase3_auth.py::test_login_suspended_or_inactive_user_rejected PASSED [ 86%]
tests/test_phase3_auth.py::test_jwt_access_token_claims_and_decoding PASSED [ 88%]
tests/test_phase3_auth.py::test_jwt_expired_token_fails_validation PASSED [ 90%]
tests/test_phase3_auth.py::test_refresh_token_rotation_and_revocation PASSED [ 93%]
tests/test_phase3_auth.py::test_logout_revokes_session PASSED            [ 95%]
tests/test_phase3_auth.py::test_get_me_with_valid_bearer_token PASSED    [ 97%]
tests/test_phase3_auth.py::test_get_me_without_token_returns_401 PASSED  [100%]

======================== 44 passed, 1 warning in 1.19s =========================
```

### Exact Test Counts
- **Phase 1 Foundation Tests:** 11 passed
- **Phase 2 Database Tests:** 15 passed
- **Phase 3 Authentication Tests:** 18 passed
- **Total Tests:** 44 passed (0 failed, 0 skipped)

---

## 11. Manual Verification

1. **Vite Frontend Build Verification:** Executed `npm run build` in `frontend/`. 93 modules transformed, 0 bundle errors.
2. **FastAPI OpenAPI Documentation:** Verified endpoint documentation at `/api/docs` reflecting `/api/v1/auth/register`, `/api/v1/auth/verify-otp`, `/api/v1/auth/login`, `/api/v1/auth/refresh`, `/api/v1/auth/logout`, and `/api/v1/auth/me`.
3. **Database Health Check:** Verified `/api/health` returns `healthy` with both `database: healthy` and `redis: healthy`.

---

## 12. Known Issues

- None.

---

## 13. Deferred Work

In strict accordance with the Phase boundary constraints:
- **Phase 4:** Role-Based Access Control (RBAC) permission checking, authorization dependencies, and permission matrix enforcement.
- **Phase 4:** Audit logging middleware.
- **Phase 5:** Library catalog management (Books, Categories, Copies) and Admin/Librarian dashboards.
- **Phase 6:** Circulation, borrowing transactions, and fines.
- **Phase 7:** Self-service password reset and Multi-Factor Authentication (MFA/TOTP).
- **Phase 8:** Redis rate limiting and security headers middleware.

---

## 14. Final Status

# `COMPLETE`
