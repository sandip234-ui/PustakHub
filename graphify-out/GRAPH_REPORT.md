# Graph Report - PustakHub  (2026-09-26)

## Corpus Check
- 210 files · ~154,881 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 14 file(s) not represented in the graph (top: (none) 6, .example 3, .ini 2)

## Summary
- 2551 nodes · 5874 edges · 154 communities (128 shown, 26 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 797 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e4065119`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- NotFoundError
- App.jsx
- Phase 3 Completion Report — PustakHub
- package.json
- create_test_user
- exceptions.py
- test_phase1_foundation.py
- books/service.py
- AuditAction
- PustakHub — Post-Remediation Security Verification Report
- Verification Matrix
- PustakHub — Password Reset Frontend Flow Implementation & Verification Report
- 4. Entities
- PustakHub — Phase 12 Report
- Session
- books/router.py
- auth_headers
- Phase 13 Implementation Report — Circulation & Borrowing UI
- catalog_cleanup
- config.py
- PustakHub — Authentication & Identity Architecture (Phase 3 & Phase 7)
- PermissionService
- PustakHub — Phase 11 Demo Data & Seed System
- _validate_password
- PermissionOut
- PustakHub — Role-Based Access Control (RBAC) & Audit Logging
- check_database_connection
- PustakHub — Final UI/UX Polish Pass Completion Report
- TestClient
- seed_demo.py
- rules/graphify.md
- workflows/graphify.md
- execute_create_admin
- PustakHub — Final Security & Architecture Audit Report
- UserDetailsPage.jsx
- PustakHub — Phase 7 Engineering & Verification Report
- PustakHub — Library Catalog Management
- test_phase9_security_remediation.py
- auth/router.py
- PustakHub — System Architecture
- categoryIcons.js
- Phase 4 Completion Report — PustakHub
- auth/service.py
- RealtimeEvent
- PustakHub — Circulation, Borrowing & Fines Architecture
- Navbar.jsx
- Circulation & Borrowing UI Architecture (`docs/circulation-ui.md`)
- Phase 5 Completion Report — PustakHub
- audit/router.py
- auth_headers
- usePermissions
- Real-Time Update Architecture & Specification
- PustakHub — Phase 9 Security Remediation Report
- Phase 14 Implementation Report — Dashboard & Operational Analytics UI
- react-router-dom
- react
- PustakHub — Phase 8 Engineering & Verification Report
- Phase 1 Report — Foundation & Architecture
- PustakHub — API Rate Limiting & Security Hardening (Phase 8)
- AuthService
- PustakHub — Database Design
- return_book
- PustakHub — Administrator Account Reconciliation Report
- update_user_status
- Key Features
- Phase 15 Report — User & IAM Administration UI
- AuditService
- PustakHub
- PHASE 17 REPORT: Real-Time Update Layer & Architecture Completion
- RealtimeClient
- PustakHub — Demo Data & Seed Subsystem
- create_access_token
- Phase 16 Verification & Implementation Report: Audit Management UI
- PustakHub UI & Theme Design System
- PustakHub — Final Runtime Integration & Bug-Fix Report
- test_admin_bootstrap.py
- Running Locally
- Technology Stack
- Example Workflows
- manager.py
- BookCopy
- get_random_ip
- Environment Configuration
- Installation
- Demo Data
- typing
- EmailService
- User
- RealtimeEventType
- clean_redis
- email.py
- _create_admin
- Dashboard & Operational Analytics UI Architecture (`docs/dashboard-ui.md`)
- _auth_headers
- publish_realtime_event
- check_resource_access
- RequestSizeLimitMiddleware
- User & IAM Administration Architecture
- DashboardPreviewPage.jsx
- PustakHub — Production Deployment Guide
- test_phase8_security_hardening.py
- TestClient
- test_phase14_dashboard_analytics.py
- TestWebSocketAuthentication
- datetime
- 5. Components Updated
- TestClient
- TestRealtimeStatusEndpoint
- Backend
- borrowing/service.py
- PustakHub — Audit Management & Forensic Logging Architecture
- Settings
- Frontend
- Testing
- PHASE_02_REPORT — PostgreSQL & Database Foundation
- PustakHub — Password Reset One-Click Link Implementation & Verification Report
- AuditPage.jsx
- Phase 6 Completion Report — Circulation, Borrowing & Fines
- AuditContextMiddleware
- RateLimitMiddleware
- UserPermissionsOut
- RateLimiter
- test_phase7_auth_security.py
- _authenticate_ws_token
- 27. Findings
- 2. Architecture & Flows
- assign_role_to_user
- TestPublicRegistrationIntegrity
- 2. Audit Findings Addressed
- vercel.json
- 5. Dependencies
- .send_registration_otp
- get_realtime_status
- db_session
- main.py
- clean_redis_ratelimits
- test_rate_limiter_concurrency_atomic_evaluation
- test_all_models_import
- 5. Authentication Security
- test_expected_tables_in_metadata
- test_database_url_is_set
- test_engine_initialises
- test_session_can_be_created
- test_rate_limiting_exceeding_limit_returns_429

## God Nodes (most connected - your core abstractions)
1. `User` - 150 edges
2. `AuditAction` - 63 edges
3. `Role` - 62 edges
4. `AccountStatus` - 61 edges
5. `BookCopy` - 47 edges
6. `AuditLog` - 46 edges
7. `AuditStatus` - 44 edges
8. `hash_password()` - 43 edges
9. `BorrowRecord` - 42 edges
10. `publish_realtime_event()` - 40 edges

## Surprising Connections (you probably didn't know these)
- `2. Circulation Policy & Defaults` --references--> `Settings`  [INFERRED]
  docs/circulation.md → backend/app/core/config.py
- `1.1 Backend Configuration (`backend/app/core/config.py`, `.env`, `.env.example`)` --references--> `Settings`  [INFERRED]
  docs/reports/PASSWORD_RESET_LINK_REPORT.md → backend/app/core/config.py
- `Summary of Completed Remediation:` --references--> `RequestSizeLimitMiddleware`  [INFERRED]
  docs/reports/PHASE_09_REPORT.md → backend/app/middleware/request_size.py
- `6. Database Changes` --references--> `AuditAction`  [INFERRED]
  docs/reports/PHASE_04_REPORT.md → backend/app/models/audit_log.py
- `4.4 Security Observations` --references--> `AuditLog`  [INFERRED]
  docs/reports/PHASE_02_VERIFICATION.md → backend/app/models/audit_log.py

## Import Cycles
- None detected.

## Communities (154 total, 26 thin omitted)

### Community 0 - "NotFoundError"
Cohesion: 0.10
Nodes (28): ConflictError, NotFoundError, Raised when a requested resource does not exist., Raised when a resource conflict occurs (e.g., duplicate entry)., BookOut, CategoryOut, Response payload for Book entity., Response payload for Category entity. (+20 more)

### Community 1 - "App.jsx"
Cohesion: 0.13
Nodes (25): 6. Frontend Authentication Routing, 14. Next Phase, 4. Files Modified, Key Highlights, App(), GuestRoute(), ProtectedRoute(), AuthProvider() (+17 more)

### Community 2 - "Phase 3 Completion Report — PustakHub"
Cohesion: 0.14
Nodes (13): 10. Automated Tests Execution, 11. Manual Verification, 12. Known Issues, 13. Deferred Work, 14. Final Status, 1. Summary, 3. Files Created, 6. Database Changes (+5 more)

### Community 3 - "package.json"
Cohesion: 0.05
Nodes (43): dependencies, axios, lucide-react, motion, qrcode.react, react, react-dom, react-router-dom (+35 more)

### Community 4 - "create_test_user"
Cohesion: 0.10
Nodes (26): create_test_user(), _create(), TestClient, Unauthenticated request to permission-protected route returns 401 Unauthorized., Authenticated STUDENT lacks 'permission:view' and receives 403 Forbidden., Authenticated ADMIN has permissions and is granted access (200 OK)., Librarian has user:view but lacks role:create., Any authenticated user can view their own effective permissions via GET… (+18 more)

### Community 5 - "exceptions.py"
Cohesion: 0.10
Nodes (32): _error_json(), ErrorResponse, ForbiddenError, pustak_hub_exception_handler(), PustakHubError, BaseModel, FastAPI, Request (+24 more)

### Community 6 - "test_phase1_foundation.py"
Cohesion: 0.12
Nodes (25): TestClient, Phase 1 foundation tests. Verifies: 1. FastAPI application starts without…, app.main imports cleanly and exposes an `app` object., Requesting a non-existent route returns HTTP 404., A preflight-like GET from the expected origin receives the CORS header., FastAPI application initialises and the test client is usable., GET / returns 200 with expected JSON keys., GET /api/health returns HTTP 200. (+17 more)

### Community 7 - "books/service.py"
Cohesion: 0.11
Nodes (32): Library Catalog Module for PustakHub., BookBase, BookCopyCreate, BookCopyListResponse, BookCopyOut, BookCopyUpdate, BookCreate, BookListResponse (+24 more)

### Community 8 - "AuditAction"
Cohesion: 0.08
Nodes (46): AuditAction, AuditLog, AuditStatus, str, Broad category of the audited event., Outcome of the audited action., Immutable security and operational audit trail. No TimestampMixin: audit rows…, audit_test_context() (+38 more)

### Community 9 - "PustakHub — Post-Remediation Security Verification Report"
Cohesion: 0.18
Nodes (11): 10. Conclusion & Final Security Assessment, 1. Verification Summary, 2. Baseline State, 3. SEC-001 Verification — TOTP Encryption, 5. SEC-003 Verification — Local QR Generation & CSP, 6. SEC-004 Verification — Test Warning, 7. SEC-005 Verification — localStorage Decision, 8. MFA End-to-End Verification (+3 more)

### Community 10 - "Verification Matrix"
Cohesion: 0.12
Nodes (20): TestClient, _random_email(), _random_name(), A real SELECT query executes against the live database., All expected tables actually exist in the PostgreSQL database., Inserting two users with the same email raises IntegrityError., Inserting two roles with the same name raises IntegrityError., Two sessions with the same token_hash must raise IntegrityError. (+12 more)

### Community 11 - "PustakHub — Password Reset Frontend Flow Implementation & Verification Report"
Cohesion: 0.17
Nodes (11): 1. Architecture & Graphify Verification, 2.2 Route Configuration (`frontend/src/App.jsx`), 2.3 Auth Service (`frontend/src/services/auth.service.js`), 2. Implementation Details, 3. Security & IAM Guardrails, 4.1 Backend Test Suite, 4.2 Frontend Quality Gates, 4.3 Browser UI Verification (+3 more)

### Community 12 - "4. Entities"
Cohesion: 0.15
Nodes (13): 4.10 BorrowRecord — IMPLEMENTED, 4.11 Fine — IMPLEMENTED, 4.12 AuditLog — IMPLEMENTED, 4.1 User — IMPLEMENTED, 4.2 Role — IMPLEMENTED, 4.3 Permission — IMPLEMENTED, 4.4 user_roles (association) — IMPLEMENTED, 4.5 role_permissions (association) — IMPLEMENTED (+5 more)

### Community 13 - "PustakHub — Phase 12 Report"
Cohesion: 0.10
Nodes (20): 10. Error Handling, 11. Responsive Design, 12. Accessibility, 13. Tests, 14. Phase 11 Dataset Verification, 15. Security Verification, 16. Build Verification, 17. Graphify Verification (+12 more)

### Community 14 - "Session"
Cohesion: 0.19
Nodes (9): Session, UUID, Revoke a role from a user., Assign a permission to a role., Revoke a permission from a role., List supported application roles with their permissions. Args: db: Database…, Get role by its UUID., Get role by its name. (+1 more)

### Community 15 - "books/router.py"
Cohesion: 0.23
Nodes (28): create_book(), create_book_copy(), create_category(), delete_book(), delete_category(), delete_copy(), _extract_request_meta(), get_book() (+20 more)

### Community 16 - "auth_headers"
Cohesion: 0.06
Nodes (23): auth_headers(), UUID, Tests for GET /api/v1/users with search and filtering., Tests for GET /api/v1/users/{id} and /api/v1/users/{id}/permissions., Active user is verified; PENDING_VERIFICATION user is not verified., Tests for PATCH /api/v1/users/{id}/status and self-lockout prevention., Admin must NOT be allowed to deactivate their own account., Admin must NOT be allowed to suspend their own account. (+15 more)

### Community 17 - "Phase 13 Implementation Report — Circulation & Borrowing UI"
Cohesion: 0.11
Nodes (17): 10. Tests, 11. Database, 12. Demo Data Validation, 13. Security Validation, 14. Documentation, 15. Known Limitations, 16. Final Status, 1. Summary (+9 more)

### Community 18 - "catalog_cleanup"
Cohesion: 0.07
Nodes (38): clean_redis_ratelimits_global(), client(), fixture, TestClient, Verify test database connection and seed baseline roles/permissions., Session-scoped FastAPI test client. Uses a single client instance for the…, Flush rate limit keys in Redis before and after each test., setup_test_database() (+30 more)

### Community 19 - "config.py"
Cohesion: 0.09
Nodes (13): alembic, Application configuration. Uses pydantic-settings to load values from…, Redis-backed sliding window rate limiter for PustakHub. Implements an atomic…, Alembic environment configuration for PustakHub. This file controls how Alembic…, Run migrations in 'online' mode. In online mode, Alembic connects to the…, Run migrations in 'offline' mode. In offline mode, Alembic does not require an…, run_migrations_offline(), run_migrations_online() (+5 more)

### Community 20 - "PustakHub — Authentication & Identity Architecture (Phase 3 & Phase 7)"
Cohesion: 0.11
Nodes (18): 1. Overview, 2. End-to-End Authentication Architecture, 3.1 Forgot-Password Flow, 3.2 Reset-Password Flow, 3. Password Reset & Account Recovery, 4.1 MFA Enrollment, 4.2 Verify Enrollment & Activation, 4.3 MFA Login Challenge & Verification (+10 more)

### Community 21 - "PermissionService"
Cohesion: 0.20
Nodes (9): PermissionService, Session, Check if user possesses the specified permission (normalized)., Return the current role-permission mapping matrix from the database., Core permission management and resolution service., Idempotently populate standard system roles, permissions, and association…, Return all available permissions ordered by name., Authoritatively query and return all effective permission names assigned to the… (+1 more)

### Community 22 - "PustakHub — Phase 11 Demo Data & Seed System"
Cohesion: 0.08
Nodes (23): 10. Production Safety, 11. CLI Usage, 12. Tests, 13. Actual Seeded Counts, 14. Frontend Verification, 15. Graphify Verification, 16. Files Changed, 17. Final Verification (+15 more)

### Community 23 - "_validate_password"
Cohesion: 0.27
Nodes (4): Validate password against the application security policy. Returns a list of…, _validate_password(), Verify the CLI reuses the same password rules as RegisterRequest., TestPasswordValidation

### Community 24 - "PermissionOut"
Cohesion: 0.29
Nodes (10): get_matrix(), get_my_permissions(), list_permissions(), get, Session, PermissionOut, BaseModel, Permission detail response. (+2 more)

### Community 25 - "PustakHub — Role-Based Access Control (RBAC) & Audit Logging"
Cohesion: 0.08
Nodes (24): 10. Audit Event Vocabulary & Data Sanitization, 11. Audit Failure Policy, 12. Anonymous & Unauthenticated Audit Logging, 13. Security Considerations, 14. Future Enhancements & Scope, 1. Architecture Overview, 2. Roles & Principles, 3. Permission Vocabulary (+16 more)

### Community 26 - "check_database_connection"
Cohesion: 0.10
Nodes (21): check_database_connection(), Attempt a lightweight SELECT 1 to verify the database is reachable. Returns…, check_database_connection() must return True. If this fails, the PostgreSQL…, test_database_connection_succeeds(), 9. Security Considerations, 1. Executive Summary, 2. Verification Checklist & Findings, 3. Files Inspected (+13 more)

### Community 27 - "PustakHub — Final UI/UX Polish Pass Completion Report"
Cohesion: 0.11
Nodes (17): 10. Dependencies, 11. Tests, 12. Lint, 13. Build, 14. Backend Regression, 15. Alembic Migrations, 16. Graphify Knowledge Graph, 17. Known Limitations (+9 more)

### Community 28 - "TestClient"
Cohesion: 0.15
Nodes (13): TestClient, Verify issue endpoint requires authentication (401) and book:issue permission…, Test validation and conflict errors when issuing unavailable or nonexistent…, Ensure an already borrowed copy cannot be issued to another user (409 Conflict)., Verify on-time return closes the record as RETURNED and produces no fine., Test resource-level authorization for borrowing history: - Student 1 can access…, Test fine querying and IDOR defenses: - Student 1 views own fines - Student 2…, test_borrowing_history_access_and_idor_prevention() (+5 more)

### Community 29 - "seed_demo.py"
Cohesion: 0.06
Nodes (49): argparse, calculate_isbn13(), check_production_safety(), main(), Session, PustakHub — Demo Data & Seed Subsystem (Phase 11). Provides deterministic,…, Generate a deterministic, mathematically valid ISBN-13 with check digit.…, Ensure seed script cannot accidentally execute in production. (+41 more)

### Community 34 - "execute_create_admin"
Cohesion: 0.14
Nodes (15): execute_create_admin(), Create an ADMIN user account in the database. Raises ValueError with user-…, Session, Validate all 10 required ADMIN bootstrap requirements., Test 1: Creates exactly one user, status ACTIVE, ADMIN role assigned., Test 2: Plaintext password is never stored; verification succeeds., Test 3: Existing user is not modified and no new user is created., Test 4: Running creation twice with same email results in only one user. (+7 more)

### Community 36 - "PustakHub — Final Security & Architecture Audit Report"
Cohesion: 0.07
Nodes (27): 10. RBAC Security Audit, 11. IDOR / BOLA / Resource Authorization Assessment, 12. Library Catalog Security, 13. Borrowing & Circulation Concurrency, 14. Database Integrity, 15. Alembic Migration State, 16. Rate Limiting Audit, 17. Request Size Protection (+19 more)

### Community 37 - "UserDetailsPage.jsx"
Cohesion: 0.19
Nodes (10): 2. User Profile & IAM Inspection (`/users/:id`), EffectivePermissionsPanel(), FALLBACK_ASSIGNABLE_ROLES, RoleAssignmentModal(), RoleAssignmentModalContent(), SUPPORTED_ASSIGNABLE_ROLES, ROLE_CLASSES, RoleBadge() (+2 more)

### Community 38 - "PustakHub — Phase 7 Engineering & Verification Report"
Cohesion: 0.08
Nodes (23): 10. Database Schema & Migration, 11. Frontend Integration, 12.1 Pytest Test Suite, 12.2 OpenAPI Verification, 12.3 Frontend Build Verification, 12. Verification & Test Results, 13. Files Created & Modified, 14. Deferred Work (+15 more)

### Community 44 - "PustakHub — Library Catalog Management"
Cohesion: 0.08
Nodes (23): 10. API Endpoint Reference, 11. Future Enhancements & Scope, 1. Architecture Overview, 2. Data Model & Entity Relationships, 3. Category Management, 4. Book Management, 5. Book Copy Inventory Management, 6. Catalog Search, Filtering & Pagination (+15 more)

### Community 45 - "test_phase9_security_remediation.py"
Cohesion: 0.13
Nodes (26): decrypt_mfa_secret(), encrypt_mfa_secret(), _get_encryption_key(), Application-layer authenticated encryption for sensitive data at rest (e.g.…, Derive a 256-bit (32-byte) AES key from the configured MFA_ENCRYPTION_KEY., Encrypt a Base32 TOTP secret using AES-256-GCM. Returns: Versioned ciphertext…, Decrypt a stored MFA secret. If the value is in versioned ciphertext format…, Phase 9 Security Remediation & Hardening Test Suite. Verifies: - SEC-001:… (+18 more)

### Community 46 - "auth/router.py"
Cohesion: 0.06
Nodes (58): Authentication module package for PustakHub., forgot_password(), get_me(), login(), logout(), mfa_disable(), mfa_enroll(), mfa_status() (+50 more)

### Community 48 - "PustakHub — System Architecture"
Cohesion: 0.13
Nodes (14): API Architecture & Route Categories, Backend Module Responsibilities, Configuration Strategy, Frontend Architecture, Frontend / Backend Relationship, Infrastructure & Security Layer, Logging & Security Rules, Modular Monolith Architecture (+6 more)

### Community 49 - "categoryIcons.js"
Cohesion: 0.23
Nodes (9): BookCard(), CategoryIcon(), sizeMap, CATEGORY_ICONS, CATEGORY_STYLES, DEFAULT_CATEGORY_STYLE, getCategoryIcon(), getCategoryStyle() (+1 more)

### Community 50 - "Phase 4 Completion Report — PustakHub"
Cohesion: 0.11
Nodes (17): 10. Manual Verification, 11. Known Issues, 12. Deferred Work, 13. Final Status, 1. Summary, 2.1 RBAC Evaluation Flow, 2.2 Permission Resolution Logic, 2.3 Resource-Level Authorization Logic (+9 more)

### Community 51 - "auth/service.py"
Cohesion: 0.06
Nodes (60): argon2, argon2_exceptions, generate_otp(), hash_otp(), hash_password(), hash_token(), Security primitives for PustakHub. Provides: - Argon2id password hashing and…, Constant-time comparison between a provided OTP and a stored SHA-256 hash.… (+52 more)

### Community 52 - "RealtimeEvent"
Cohesion: 0.12
Nodes (18): BaseModel, Standardized payload for real-time messages. Attributes: id: Unique identifier…, RealtimeEvent, ConnectionInfo, ConnectionManager, Any, UUID, WebSocket (+10 more)

### Community 53 - "PustakHub — Circulation, Borrowing & Fines Architecture"
Cohesion: 0.17
Nodes (11): 2. Circulation Policy & Defaults, 3. Physical Inventory State Transitions, 4. Book Issue Workflow, 5. Book Return Workflow & Overdue Fine Calculation, 7. RBAC & Resource-Level Authorization (IDOR / BOLA Prevention), 8. Audit Logging & Security Guarantees, Data Privacy & Secret Shielding, Deterministic Overdue Formula (+3 more)

### Community 54 - "Navbar.jsx"
Cohesion: 0.16
Nodes (13): Navbar(), ProfileDropdown(), handler(), ThemeToggle(), applyThemeToDocument(), getStoredTheme(), getSystemPreference(), resolveEffectiveTheme() (+5 more)

### Community 55 - "Circulation & Borrowing UI Architecture (`docs/circulation-ui.md`)"
Cohesion: 0.20
Nodes (9): 1. Overview, 2. Route Map, 3. Component Architecture, 4.1 Issue / Checkout Workflow, 4.2 Return Workflow, 4.3 Fines Ledger & Transparency, 4. Key Workflows, 6. Accessibility & Responsiveness (+1 more)

### Community 56 - "Phase 5 Completion Report — PustakHub"
Cohesion: 0.12
Nodes (16): 10. Files Created, 11. Files Modified, 12. Test Results, 13. Verification, 15. Final Status, 1. Executive Summary, 2. Architecture Implemented, 3. Category Management (+8 more)

### Community 57 - "audit/router.py"
Cohesion: 0.19
Nodes (20): get_audit_actions(), get_audit_log_by_id(), get_audit_logs(), datetime, get, Session, UUID, Audit Logs HTTP Router. Endpoints: - GET /api/v1/audit/logs - Query system… (+12 more)

### Community 58 - "auth_headers"
Cohesion: 0.09
Nodes (12): auth_headers(), UUID, Tests authorization gates for audit management endpoints., Tests multi-parameter filtering and search on audit logs., Tests server-side pagination for audit trails., Tests single audit event inspection, 404 handling, and IDOR protection., Verifies that audit endpoints never leak secrets and reject mutations., TestAuditAuthorization (+4 more)

### Community 59 - "usePermissions"
Cohesion: 0.09
Nodes (26): 1. Architectural Principles, 2. Frontend Routes & Navigation, 3.1 `usePermissions` Hook (`src/hooks/usePermissions.js`), 3.2 `PermissionGate` Component (`src/components/PermissionGate.jsx`), 3.3 Protected Route Guarding (`src/components/ProtectedRoute.jsx`), 3. RBAC UI Architecture, 4.1 Catalog Explorer (`/catalog`), 4.2 Book Details & Bibliographic Records (`/books/:id`) (+18 more)

### Community 60 - "Real-Time Update Architecture & Specification"
Cohesion: 0.11
Nodes (18): 10. Summary of Subsystem Components, 1. Executive Summary & Objective, 2.1 REST as the Authoritative Source of Truth, 2. Core Architectural Principles, 3.1 Transport Selection: WebSocket (`ws://` / `wss://`), 3.2 Multi-Worker Backplane: Redis Pub/Sub, 3. Real-Time Transport: WebSockets & Redis Pub/Sub, 5.1 Strict Secret Exclusion Guarantee (+10 more)

### Community 61 - "PustakHub — Phase 9 Security Remediation Report"
Cohesion: 0.12
Nodes (15): 10. Migration Verification, 11. Graphify Verification, 12. Documentation Updates, 13. Remaining Risks, 14. Deferred Enhancements, 15. Final Verification, 1. Executive Summary, 3. Security Architecture Changes (+7 more)

### Community 62 - "Phase 14 Implementation Report — Dashboard & Operational Analytics UI"
Cohesion: 0.12
Nodes (15): 10. Database, 11. Demo Data, 12. Documentation, 13. Known Limitations, 14. Final Status, 1. Summary, 2. Dashboard Architecture, 3. Role-Specific Features (+7 more)

### Community 63 - "react-router-dom"
Cohesion: 0.26
Nodes (10): 11. Login Message Root Cause, 2.1 ResetPasswordPage (`frontend/src/pages/ResetPasswordPage.jsx`), AuthCard(), AuthError(), AuthLabel(), AuthSuccess(), AuthContext, authService (+2 more)

### Community 64 - "react"
Cohesion: 0.17
Nodes (14): BookFormModal(), CategoryFormModal(), ConfirmDialog(), COPY_STATUSES, CopyFormModal(), IssueBookModal(), IssueBookModalContent(), Toast() (+6 more)

### Community 65 - "PustakHub — Phase 8 Engineering & Verification Report"
Cohesion: 0.12
Nodes (16): 10.1 Pytest Test Suite Results, 10.2 Frontend Build Verification, 10. Verification & Test Results, 11. Deferred Work, 2. Rate-Limiting Architecture, 3. Redis Key Strategy, 4. Route Policies & Limits, 5. Security HTTP Headers & CSP (+8 more)

### Community 66 - "Phase 1 Report — Foundation & Architecture"
Cohesion: 0.10
Nodes (20): 11. Acceptance Criteria, 12. Known Issues, 13. Deferred Work, 15. Final Status, 1. Objective, 2. Initial Project State, 3. Changes Implemented, 4. Files Created (+12 more)

### Community 67 - "PustakHub — API Rate Limiting & Security Hardening (Phase 8)"
Cohesion: 0.08
Nodes (22): BaseHTTPMiddleware, Request, Response, Middleware injecting modern security headers and Content Security Policy (CSP)., Construct the Content Security Policy directive string., SecurityHeadersMiddleware, 10. Frontend Compatibility, 11. Production Deployment Recommendations (+14 more)

### Community 68 - "AuthService"
Cohesion: 0.12
Nodes (18): get_redis_client(), Redis client and connection management for PustakHub. Used in Phase 3…, Get or initialize the shared Redis client instance. Uses…, AuthService, Session, UUID, Disable MFA on user account. Requires current password verification for…, Verify the submitted OTP against Redis temporary storage. Upon successful… (+10 more)

### Community 69 - "PustakHub — Database Design"
Cohesion: 0.14
Nodes (13): 10. Status Key, 1. Database Choice, 2. Architecture Overview, 3. Entity Relationship Diagram, 5. Relationships, 6. Constraints & Indexes, 7. Session / Token Persistence Design, 8. Migration Strategy (+5 more)

### Community 70 - "return_book"
Cohesion: 0.27
Nodes (14): _extract_request_meta(), get_borrowing(), get_user_borrowings(), _is_staff_user(), issue_book(), list_borrowings(), get, post (+6 more)

### Community 71 - "PustakHub — Administrator Account Reconciliation Report"
Cohesion: 0.22
Nodes (8): 1. Database State Before vs. After, 2. Target Administrator Details, 3. Operations & Transaction Safety, 4. Graphify Architecture Verification, 5. Verification & Test Results, Aggregate Summary Table, Executive Summary, PustakHub — Administrator Account Reconciliation Report

### Community 72 - "update_user_status"
Cohesion: 0.29
Nodes (10): _extract_request_meta(), get_user_by_id(), get_user_effective_permissions(), get, Request, Session, UUID, Extract client IP and user agent. (+2 more)

### Community 73 - "Key Features"
Cohesion: 0.25
Nodes (8): Audit & Observability, Authorization & RBAC, Identity & Authentication, Key Features, Library Management, MFA & Account Recovery, Real-Time Updates (WebSocket & Redis Pub/Sub), Security Engineering

### Community 74 - "Phase 15 Report — User & IAM Administration UI"
Cohesion: 0.17
Nodes (11): 10. Frontend Lint & Build, 11. Alembic Status, 12. Graphify Status, 13. Known Limitations, 14. Deferred Work, 1. Phase Objective, 2. Existing Implementation Inspected, 4. Frontend Changes (+3 more)

### Community 75 - "AuditService"
Cohesion: 0.17
Nodes (12): AuditService, datetime, Session, UUID, Retrieve a single audit log entry by UUID., Query audit logs with filtering and pagination. Returns (items, total_count)., Central service for logging and querying security and operational audit entries., Sanitize strings to ensure sensitive tokens or hashes are never recorded. (+4 more)

### Community 76 - "PustakHub"
Cohesion: 0.12
Nodes (17): API Documentation, API Overview, Architecture, Authentication Architecture, Author, Authorization Architecture, Database Architecture, Future Enhancements (+9 more)

### Community 77 - "PHASE 17 REPORT: Real-Time Update Layer & Architecture Completion"
Cohesion: 0.11
Nodes (18): 10. Circulation & Catalog Integration, 11. Reconnection Strategy, 12. Failure Behavior & Graceful Degradation, 13. Security Validation, 14. Test Suite Execution, 15. Frontend Lint & Build, 16. Alembic Database Status, 18. Known Limitations & Operational Considerations (+10 more)

### Community 79 - "PustakHub — Demo Data & Seed Subsystem"
Cohesion: 0.18
Nodes (11): 1. Executive Overview, 2. Dataset Composition, 3. Demo User Credentials (LOCAL DEVELOPMENT ONLY), 4.1 Seed the Database, 4.2 Reset Demo Data, 4.3 CLI Flags Reference, 4. CLI Usage, 5. Security & Safety Invariants (+3 more)

### Community 80 - "create_access_token"
Cohesion: 0.10
Nodes (24): create_access_token(), create_refresh_token(), decode_token(), Any, datetime, UUID, Generate a signed JWT access token. Args: subject: Unique identifier of the…, Generate a signed JWT refresh token and its SHA-256 hash. Args: subject: Unique… (+16 more)

### Community 81 - "Phase 16 Verification & Implementation Report: Audit Management UI"
Cohesion: 0.18
Nodes (10): 10. Frontend Lint & Build, 11. Alembic Status, 12. Graphify Status, 13. Known Limitations, 14. Deferred Work, 1. Phase Objective, 4. Frontend Changes, 7. Authorization & Security Controls (+2 more)

### Community 82 - "PustakHub UI & Theme Design System"
Cohesion: 0.12
Nodes (15): 1. Overview & Architecture, 2. Design Tokens Reference, 3. Light / Dark / System Modes & Anti-FOUC, 4. Dashboard Architecture & Metrics Verification, 5. Animation Strategy & External UI Stack, 6. Accessibility & Responsive Standards, Anti-FOUC Execution, Core Color Palette (CSS Variables) (+7 more)

### Community 83 - "PustakHub — Final Runtime Integration & Bug-Fix Report"
Cohesion: 0.15
Nodes (12): 10. MFA Login Test, 12. Redis Warning Assessment, 13. Security Verification, 14. Validation Results, 16. Remaining Known Limitations, 1. Catalog Issue, 2. Catalog Root Cause, 4. OTP Issue (+4 more)

### Community 84 - "test_admin_bootstrap.py"
Cohesion: 0.19
Nodes (9): execute_reconcile_admin(), _normalize_email(), Atomically reconcile administrator role to exactly ONE target user account. 1.…, Normalize email: strip whitespace and lowercase., Tests for the PustakHub ADMIN bootstrap CLI (app.cli create-admin). Covers all…, Verify email normalization matches the auth service behavior., Verify execute_reconcile_admin assigns ADMIN to target and revokes from all…, TestAdminReconciliation (+1 more)

### Community 85 - "Running Locally"
Cohesion: 0.40
Nodes (5): 1. Database Setup, 2. Redis Setup, 3. Start Backend API Server, 4. Start Frontend Development Server, Running Locally

### Community 86 - "Technology Stack"
Cohesion: 0.40
Nodes (5): Backend, Frontend, Storage & Security Infrastructure, Technology Stack, Testing & Verification

### Community 87 - "Example Workflows"
Cohesion: 0.50
Nodes (4): 1. Registration & Account Activation, 2. Multi-Factor Authentication (MFA) Setup, 3. MFA Login Challenge, Example Workflows

### Community 88 - "manager.py"
Cohesion: 0.16
Nodes (14): asyncio, Real-time Event Taxonomy and Schemas for PustakHub. Defines canonical event…, Realtime module for PustakHub., Connection Manager for WebSockets in PustakHub. Manages authenticated active…, UUID, Real-time Event Publisher for PustakHub. Provides non-blocking, fail-safe…, _listen_redis_channel(), Redis Pub/Sub Subscriber for Distributed Real-time Updates in PustakHub.… (+6 more)

### Community 89 - "BookCopy"
Cohesion: 0.06
Nodes (79): Base, Declarative Base and shared column mixins for all SQLAlchemy models. Every…, Shared declarative base for all PustakHub SQLAlchemy models. Uses SQLAlchemy…, Adds `created_at` and `updated_at` to any model that inherits this mixin. -…, TimestampMixin, Book, BookCopy, CopyStatus (+71 more)

### Community 90 - "get_random_ip"
Cohesion: 0.14
Nodes (14): get_random_ip(), POST /api/v1/auth/login enforces strict category rate limits., POST /api/v1/auth/mfa/verify enforces strict rate limiting against brute-force., When Redis is unreachable, security-critical authentication endpoints fail…, When Redis is unreachable, general non-sensitive API endpoints fail open to…, 429 responses follow the standard error envelope and never expose Redis or SQL…, Generate a unique random IP for isolated client tests., Requests below the category limit succeed and return standard rate-limit… (+6 more)

### Community 91 - "Environment Configuration"
Cohesion: 0.67
Nodes (3): Backend Configuration, Environment Configuration, Frontend Configuration

### Community 92 - "Installation"
Cohesion: 0.67
Nodes (3): Clone the Repository, Installation, Prerequisites

### Community 93 - "Demo Data"
Cohesion: 0.67
Nodes (3): Demo Data, Seeded Demo Accounts (Local Development Only), Seeding the Database

### Community 94 - "typing"
Cohesion: 0.06
Nodes (62): PustakHub — Secure Administrative CLI. Provides a secure, interactive command…, get_db(), Session, SQLAlchemy engine, session factory, and FastAPI session dependency. This module…, FastAPI dependency that yields a SQLAlchemy database session. Usage in a route:…, get_logger(), Application logging configuration. Sets up structured console logging for…, Get a named logger. Usage: from app.core.logging import get_logger logger =… (+54 more)

### Community 95 - "EmailService"
Cohesion: 0.22
Nodes (9): EmailService, Send a password reset email with a secure one-click reset link. Args: to_email:…, Service handling outbound email delivery via SMTP., Verify password reset email construction: - Email contains a one-click reset…, Verify that recipient name with special characters is HTML-escaped to prevent…, test_password_reset_email_format_and_link_construction(), test_password_reset_email_html_escaping(), 5. OTP Root Cause (+1 more)

### Community 96 - "User"
Cohesion: 0.06
Nodes (40): Application role (e.g., ADMIN, LIBRARIAN, STUDENT, GUEST). Roles are assigned…, Role, Application user entity., Indicates whether email verification has completed (status is not…, User, Return non-sensitive MFA status for the authenticated user., db(), fixture (+32 more)

### Community 97 - "RealtimeEventType"
Cohesion: 0.18
Nodes (9): str, Canonical real-time event types., RealtimeEventType, Client sending PING receives PONG with UTC timestamp., Sensitive keys like passwords, tokens, and hashes are automatically redacted., TestEventSecurityAndSanitization, TestWebSocketHeartbeat, 4.1 Canonical Event Taxonomy (+1 more)

### Community 98 - "clean_redis"
Cohesion: 0.29
Nodes (7): clean_redis(), client(), db_session(), fixture, TestClient instance for HTTP endpoint testing., Provides a transactional database session for tests, cleaned up afterwards., Cleans up Redis registration keys created during test runs.

### Community 99 - "email.py"
Cohesion: 0.29
Nodes (6): Email delivery service for PustakHub. Provides email dispatch for registration…, email_mime_multipart, email_mime_text, html, smtplib, urllib_parse

### Community 100 - "_create_admin"
Cohesion: 0.22
Nodes (9): _create_admin(), main(), Session, Interactive bootstrap of the initial ADMIN user account. Steps: 1. Collect full…, Interactive reconciliation of the single intended ADMIN account., Parse CLI arguments and dispatch to the appropriate command., _reconcile_admin(), Test the CLI interactive wrapper functions with simulated inputs. (+1 more)

### Community 101 - "Dashboard & Operational Analytics UI Architecture (`docs/dashboard-ui.md`)"
Cohesion: 0.29
Nodes (6): 1. Overview, 2. Persona Views & Information Architecture, 3. Metrics Matrix & Endpoints, 4. Reusable Components, 5. Security & IDOR Defenses, Dashboard & Operational Analytics UI Architecture (`docs/dashboard-ui.md`)

### Community 102 - "_auth_headers"
Cohesion: 0.24
Nodes (11): _auth_headers(), TestClient, UUID, Verify that staff can issue an available copy, status transitions, and return…, Verify that students only see their own loans/fines and cannot inspect other…, Verify that students and unauthenticated guests cannot issue or return books., Verify that attempting to issue an already borrowed copy returns 409 Conflict., test_concurrency_conflict_when_copy_already_borrowed() (+3 more)

### Community 103 - "publish_realtime_event"
Cohesion: 0.16
Nodes (12): _dispatch_event_async(), publish_realtime_event(), Any, Ensure the data payload contains no sensitive credentials or raw secrets., Internal async dispatch to local connections and Redis Pub/Sub., Publish a real-time event safely from any synchronous or asynchronous context.…, _sanitize_data_payload(), Catalog updates are broadcast to all authenticated subscribers. (+4 more)

### Community 104 - "check_resource_access"
Cohesion: 0.29
Nodes (7): check_resource_access(), get_current_user_permissions(), Session, UUID, Check if the current authenticated user is either the resource owner OR…, Dependency resolving the set of permissions held by the currently authenticated…, Security Controls

### Community 105 - "RequestSizeLimitMiddleware"
Cohesion: 0.16
Nodes (13): PayloadTooLargeError, Raised when request payload exceeds allowed limit (HTTP 413)., BaseHTTPMiddleware, Request, Response, Middleware that rejects requests with body size exceeding…, RequestSizeLimitMiddleware, limited_receive() (+5 more)

### Community 106 - "User & IAM Administration Architecture"
Cohesion: 0.18
Nodes (10): 1. Administrative Users Ledger (`/users`), API Endpoints Reference, Architecture & Security Boundaries, Backend Authoritative Enforcements, Defensive Self-Protection & Lockout Prevention, Frontend UX Guards, Known Limitations & Boundaries, Routes & User Experience (+2 more)

### Community 107 - "DashboardPreviewPage.jsx"
Cohesion: 0.13
Nodes (11): COLOR_MAP, DashboardStatCard(), COLOR_MAP, QuickActionCard(), RealtimeStatusBadge(), RealtimeContext, useRealtime(), FinesPage() (+3 more)

### Community 108 - "PustakHub — Production Deployment Guide"
Cohesion: 0.17
Nodes (11): 1. Frontend Deployment (Vercel), 2. Backend Deployment (Render), 3. Production Environment Variables Reference, 4. Alternative: Docker & Container Orchestration, 5. Post-Deployment Verification Checklist, Architecture Overview, Deployment Steps, Option A: Render Blueprint (Recommended) (+3 more)

### Community 109 - "test_phase8_security_hardening.py"
Cohesion: 0.18
Nodes (10): Phase 8 Security Hardening & Rate Limiting Tests. Verifies: 1. Redis-backed…, POST /api/v1/auth/forgot-password enforces strict rate limiting., HSTS header is absent in local dev, but added when ENABLE_HSTS=True., Exposed headers include X-Request-ID, Retry-After, and X-RateLimit headers., test_cors_exposed_headers_present(), test_hsts_header_controlled_by_config(), test_password_reset_rate_limiting(), concurrent_futures (+2 more)

### Community 110 - "TestClient"
Cohesion: 0.13
Nodes (15): TestClient, Health checks, root, and OpenAPI documentation endpoints are exempt from rate…, Outbound responses contain modern defensive HTTP security headers., Content Security Policy contains restrictive, application-tailored directives., Preflight and requests from configured frontend origins receive CORS headers., Requests with unauthorized origins do not receive allow-origin header., Normal-sized request payloads pass without restriction., Requests exceeding MAX_REQUEST_BODY_SIZE are rejected with HTTP 413 Payload Too… (+7 more)

### Community 111 - "test_phase14_dashboard_analytics.py"
Cohesion: 0.16
Nodes (17): _auth_headers(), dashboard_users(), ensure_rbac_seeded(), fixture, TestClient, UUID, Phase 14 Integration Tests — Operational Analytics & Dashboard Endpoint…, Verify LIBRARIAN can query circulation data but cannot access role management. (+9 more)

### Community 112 - "TestWebSocketAuthentication"
Cohesion: 0.22
Nodes (5): Valid JWT access token successfully establishes WebSocket connection., Connection attempt without token is rejected with policy violation., Connection attempt with corrupted token is rejected., Suspended user token is rejected during handshake., TestWebSocketAuthentication

### Community 113 - "datetime"
Cohesion: 0.09
Nodes (24): Permission, Named application permission., Borrowing and Circulation module for PustakHub., BorrowIssueRequest, BorrowRecordListResponse, BorrowReturnRequest, BaseModel, Pydantic schemas for the Circulation and Borrowing module. Covers: -… (+16 more)

### Community 114 - "5. Components Updated"
Cohesion: 0.24
Nodes (7): 5. Components Updated, 5. Routes, 4. Frontend Implementation, AuditPage(), BorrowingsPage(), CatalogPage(), UsersPage()

### Community 115 - "TestClient"
Cohesion: 0.20
Nodes (9): TestClient, Normal request under payload size limit succeeds., Request with explicit Content-Length exceeding limit is rejected with 413., Streaming request exceeding payload limit without Content-Length is rejected…, Content Security Policy img-src strictly excludes external api.qrserver.com., test_csp_header_excludes_external_qr_provider(), test_request_size_oversized_content_length_rejected(), test_request_size_streaming_chunked_over_limit() (+1 more)

### Community 116 - "TestRealtimeStatusEndpoint"
Cohesion: 0.40
Nodes (3): GET /api/v1/realtime/status returns operational metrics., GET /api/v1/realtime/status requires authentication., TestRealtimeStatusEndpoint

### Community 118 - "borrowing/service.py"
Cohesion: 0.08
Nodes (44): FineReason, FineStatus, str, Fine model. A financial penalty associated with a BorrowRecord (e.g., overdue…, Payment state of a fine., Why the fine was issued., BorrowRecordOut, Response payload representing a single borrowing transaction. (+36 more)

### Community 119 - "PustakHub — Audit Management & Forensic Logging Architecture"
Cohesion: 0.18
Nodes (10): 1. Overview & Objectives, 2. Architecture & Data Model, 2. `GET /api/v1/audit/logs/{audit_id}`, 3. Backend Audit Endpoints, 3. `GET /api/v1/audit/actions`, 4. Frontend Audit Management Console, 5. Security & Immutability Guarantees, Core Tenets (+2 more)

### Community 120 - "Settings"
Cohesion: 0.25
Nodes (7): field_validator, Central application settings. Values are loaded in order of priority: 1. Actual…, Ensure standard postgresql+psycopg:// prefix for SQLAlchemy compatibility., Settings, BaseSettings, 9. Configuration Changes, 5. Due-Date & Fine Policy

### Community 123 - "PHASE_02_REPORT — PostgreSQL & Database Foundation"
Cohesion: 0.29
Nodes (6): Database Statistics, Files Created, Files Modified, PHASE_02_REPORT — PostgreSQL & Database Foundation, Phase Objective, Security Notes

### Community 124 - "PustakHub — Password Reset One-Click Link Implementation & Verification Report"
Cohesion: 0.20
Nodes (9): 1.1 Backend Configuration (`backend/app/core/config.py`, `.env`, `.env.example`), 1.2 Email Service (`backend/app/core/email.py`), 1.3 Frontend Flow Integration (`frontend/src/pages/ResetPasswordPage.jsx`, `frontend/src/pages/ForgotPasswordPage.jsx`), 1. Summary of Changes, 2. Graphify Architecture Verification, 3. Security & Safety Verification, 4. Test Results, Executive Summary (+1 more)

### Community 125 - "AuditPage.jsx"
Cohesion: 0.13
Nodes (11): Key UI Features, AuditDetailModal(), AuditEventBadge(), AuditFilters(), AuditStatusBadge(), FEATURES, api, failedQueue (+3 more)

### Community 126 - "Phase 6 Completion Report — Circulation, Borrowing & Fines"
Cohesion: 0.18
Nodes (10): 11. Files Modified, 12. Test Results, 13. Verification, 14. Deferred Work (Out of Scope for Phase 6), 1. Executive Summary, 2. Circulation Architecture, 3. Book Issue Workflow, 6. Borrowing & Fine History (IDOR / BOLA Defenses) (+2 more)

### Community 127 - "AuditContextMiddleware"
Cohesion: 0.29
Nodes (6): AuditContextMiddleware, BaseHTTPMiddleware, Request, Response, Middleware that populates request context (IP, User-Agent, Request-ID) used for…, 2. Existing Audit Architecture Inspected

### Community 128 - "RateLimitMiddleware"
Cohesion: 0.25
Nodes (7): Resolve the route path and HTTP method into rate limit policy parameters:…, resolve_rate_limit_policy(), BaseHTTPMiddleware, Request, Response, RateLimitMiddleware, Middleware that enforces Redis-backed rate limiting per IP and route category.

### Community 129 - "UserPermissionsOut"
Cohesion: 0.33
Nodes (6): Effective permissions for a user., UserPermissionsOut, BaseModel, Payload for updating user account status., UserStatusUpdateRequest, 3. Backend Changes

### Community 130 - "RateLimiter"
Cohesion: 0.13
Nodes (13): RateLimiter, RateLimitResult, Evaluate rate limit for a given identifier within a category. Args: identifier:…, Encapsulates the result of a rate limit evaluation., Central Redis-backed sliding window rate limiter., Traffic from IP A does not consume or affect the rate limit quota of IP B., Exhausting quota in one category does not affect other categories., Rate limit counters expire and reset after the sliding window elapses. (+5 more)

### Community 131 - "test_phase7_auth_security.py"
Cohesion: 0.13
Nodes (25): create_test_user(), _create(), ensure_rbac_seeded(), fixture, TestClient, Phase 7 Authentication Security, Password Reset & MFA Tests. Comprehensive…, Test complete password reset flow: - Generates token in Redis - Validates and…, Test password reset edge cases: - Weak new password rejected by policy (422) -… (+17 more)

### Community 132 - "_authenticate_ws_token"
Cohesion: 0.33
Nodes (6): _authenticate_ws_token(), Session, websocket, Validate JWT access token and load user identity with dynamic roles and…, Primary authenticated WebSocket connection endpoint. Workflow: 1. Validates JWT…, websocket_endpoint()

### Community 133 - "27. Findings"
Cohesion: 0.33
Nodes (6): 27. Findings, Critical, High, Informational, Low, Medium

### Community 134 - "2. Architecture & Flows"
Cohesion: 0.40
Nodes (5): 2.1 Registration & OTP Flow, 2.2 Login, Token Issuance & Refresh Flow, 2.3 Logout & Session Invalidation, 2.4 Reusable Authentication Dependencies, 2. Architecture & Flows

### Community 135 - "assign_role_to_user"
Cohesion: 0.29
Nodes (15): assign_permission_to_role(), assign_role_to_user(), create_role(), get_role(), list_roles(), delete, get, post (+7 more)

### Community 137 - "TestPublicRegistrationIntegrity"
Cohesion: 0.33
Nodes (4): Verify that the public registration flow cannot create ADMIN accounts., RegisterRequest must not accept a role parameter., Inspect the auth service source to confirm STUDENT is hardcoded in…, TestPublicRegistrationIntegrity

### Community 138 - "2. Audit Findings Addressed"
Cohesion: 0.33
Nodes (6): 2. Audit Findings Addressed, SEC-001 — TOTP Secret Encryption, SEC-002 — Request Size Streaming Protection, SEC-003 — Local QR Generation, SEC-004 — Test Deprecation Warning, SEC-005 — localStorage Decision

### Community 140 - "5. Dependencies"
Cohesion: 0.50
Nodes (4): 5. Dependencies, Frontend, Local Infrastructure, Python (`backend/requirements.txt`)

### Community 142 - "get_realtime_status"
Cohesion: 0.67
Nodes (3): get_realtime_status(), get, Return operational connection statistics.

### Community 143 - "db_session"
Cohesion: 0.67
Nodes (3): db_session(), fixture, Provide a database session for seed testing.

### Community 144 - "main.py"
Cohesion: 0.12
Nodes (22): Parse CORS_ORIGINS from comma-separated string into a list., configure_logging(), Configure the root logger for PustakHub. Should be called once at application…, check_redis_connection(), Check if the Redis server is reachable. Returns: True if Redis responds to…, create_application(), health(), lifespan() (+14 more)

### Community 145 - "clean_redis_ratelimits"
Cohesion: 0.67
Nodes (3): clean_redis_ratelimits(), fixture, Flush rate limit keys before and after each test.

## Knowledge Gaps
- **540 isolated node(s):** `name`, `private`, `version`, `type`, `dev` (+535 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1259 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `App.jsx`, `test_phase7_auth_security.py`, `_authenticate_ws_token`, `create_test_user`, `2. Architecture & Flows`, `assign_role_to_user`, `AuditAction`, `Verification Matrix`, `4. Entities`, `get_realtime_status`, `books/router.py`, `Session`, `auth_headers`, `catalog_cleanup`, `PustakHub — Authentication & Identity Architecture (Phase 3 & Phase 7)`, `PermissionService`, `PermissionOut`, `seed_demo.py`, `execute_create_admin`, `test_phase9_security_remediation.py`, `auth/router.py`, `auth/service.py`, `AuthService`, `return_book`, `update_user_status`, `AuditService`, `create_access_token`, `test_admin_bootstrap.py`, `Example Workflows`, `BookCopy`, `typing`, `_create_admin`, `check_resource_access`, `test_phase14_dashboard_analytics.py`, `datetime`, `borrowing/service.py`, `Phase 6 Completion Report — Circulation, Borrowing & Fines`?**
  _High betweenness centrality (0.270) - this node is a cross-community bridge._
- **Why does `Key Highlights` connect `App.jsx` to `User`, `Phase 3 Completion Report — PustakHub`?**
  _High betweenness centrality (0.125) - this node is a cross-community bridge._
- **Why does `useAuth()` connect `App.jsx` to `react`, `UserDetailsPage.jsx`, `DashboardPreviewPage.jsx`, `Navbar.jsx`, `usePermissions`, `AuditPage.jsx`, `react-router-dom`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Are the 80 inferred relationships involving `User` (e.g. with `_reconcile_admin()` and `AuditService`) actually correct?**
  _`User` has 80 INFERRED edges - model-reasoned connections that need verification._
- **Are the 41 inferred relationships involving `AuditAction` (e.g. with `execute_create_admin()` and `execute_reconcile_admin()`) actually correct?**
  _`AuditAction` has 41 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `Role` (e.g. with `execute_create_admin()` and `execute_reconcile_admin()`) actually correct?**
  _`Role` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 34 inferred relationships involving `AccountStatus` (e.g. with `execute_create_admin()` and `execute_reconcile_admin()`) actually correct?**
  _`AccountStatus` has 34 INFERRED edges - model-reasoned connections that need verification._