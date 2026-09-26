# Graph Report - PustakHub  (2026-09-25)

## Corpus Check
- 206 files · ~318,027 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: .example 3, (none) 3, .ini 2)

## Summary
- 2520 nodes · 5803 edges · 129 communities (111 shown, 18 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 788 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- CopyStatus
- App.jsx
- PustakHub — Final Runtime Integration & Bug-Fix Report
- package.json
- PustakHub — Phase 9 Security Remediation Report
- exceptions.py
- test_phase1_foundation.py
- books/service.py
- AuditAction
- PustakHub — Post-Remediation Security Verification Report
- test_phase2_database.py
- PustakHub — Password Reset Frontend Flow Implementation & Verification Report
- BookCopy
- PustakHub — Phase 12 Report
- auth/router.py
- books/router.py
- auth_headers
- Phase 13 Implementation Report — Circulation & Borrowing UI
- catalog_cleanup
- env.py
- PustakHub — Authentication & Identity Architecture (Phase 3 & Phase 7)
- Role
- PustakHub — Phase 11 Demo Data & Seed System
- _validate_password
- test_phase4_rbac.py
- PustakHub — Role-Based Access Control (RBAC) & Audit Logging
- Phase 2 Final Verification Report — PustakHub
- PustakHub — Final UI/UX Polish Pass Completion Report
- React + Vite
- seed_database
- rules/graphify.md
- workflows/graphify.md
- User
- PustakHub — Final Security & Architecture Audit Report
- UsersPage.jsx
- PustakHub — Phase 7 Engineering & Verification Report
- PustakHub — Library Catalog Management
- test_phase9_security_remediation.py
- RegisterRequest
- PustakHub — System Architecture
- Phase 4 Completion Report — PustakHub
- hash_otp
- ConnectionManager
- PustakHub — Circulation, Borrowing & Fines Architecture
- Navbar.jsx
- Circulation & Borrowing UI Architecture (`docs/circulation-ui.md`)
- Phase 5 Completion Report — PustakHub
- audit/router.py
- auth_headers
- usePermissions
- Real-Time Update Architecture & Specification
- TestClient
- Phase 14 Implementation Report — Dashboard & Operational Analytics UI
- react-router-dom
- react
- PustakHub — Phase 8 Engineering & Verification Report
- Phase 1 Report — Foundation & Architecture
- PustakHub — API Rate Limiting & Security Hardening (Phase 8)
- TestClient
- 4. Entities
- .connect
- PustakHub — Administrator Account Reconciliation Report
- AuditPage.jsx
- Key Features
- RoleService
- audit/service.py
- PustakHub
- PHASE 17 REPORT: Real-Time Update Layer & Architecture Completion
- RealtimeClient
- PustakHub — Demo Data & Seed Subsystem
- AuthService
- Phase 16 Verification & Implementation Report: Audit Management UI
- PustakHub UI & Theme Design System
- Phase 15 Report — User & IAM Administration UI
- users/router.py
- Running Locally
- Technology Stack
- Example Workflows
- typing
- user.py
- borrowing/service.py
- Environment Configuration
- Installation
- Demo Data
- logging.py
- _normalize_email
- db
- .subscribeMany
- clean_redis
- .check_rate_limit
- 4. Feature Workflows
- Dashboard & Operational Analytics UI Architecture (`docs/dashboard-ui.md`)
- auth/service.py
- publish_realtime_event
- Settings
- db_session
- User & IAM Administration Architecture
- HomePage.jsx
- test_phase8_security_hardening.py
- _auth_headers
- TestWebSocketAuthentication
- TestRealtimeStatusEndpoint
- Backend
- fines/router.py
- PustakHub — Audit Management & Forensic Logging Architecture
- Frontend
- Testing
- PustakHub — Password Reset One-Click Link Implementation & Verification Report
- DashboardPreviewPage.jsx
- Phase 6 Completion Report — Circulation, Borrowing & Fines
- AuditLog
- 27. Findings
- roles/router.py
- TestPublicRegistrationIntegrity
- 4. Files Created
- get_realtime_status
- main.py
- 5. Authentication Security

## God Nodes (most connected - your core abstractions)
1. `User` - 150 edges
2. `AuditAction` - 63 edges
3. `Role` - 62 edges
4. `AccountStatus` - 61 edges
5. `AuditLog` - 46 edges
6. `AuditStatus` - 44 edges
7. `BookCopy` - 44 edges
8. `hash_password()` - 43 edges
9. `BorrowRecord` - 41 edges
10. `publish_realtime_event()` - 40 edges

## Surprising Connections (you probably didn't know these)
- `2. Circulation Policy & Defaults` --references--> `Settings`  [INFERRED]
  docs/circulation.md → backend/app/core/config.py
- `1.1 Backend Configuration (`backend/app/core/config.py`, `.env`, `.env.example`)` --references--> `Settings`  [INFERRED]
  docs/reports/PASSWORD_RESET_LINK_REPORT.md → backend/app/core/config.py
- `9. Security Considerations` --references--> `check_database_connection()`  [INFERRED]
  docs/database-design.md → backend/app/core/database.py
- `4.1 Database Configuration` --references--> `check_database_connection()`  [INFERRED]
  docs/reports/PHASE_02_VERIFICATION.md → backend/app/core/database.py
- `Summary of Completed Remediation:` --references--> `RequestSizeLimitMiddleware`  [INFERRED]
  docs/reports/PHASE_09_REPORT.md → backend/app/middleware/request_size.py

## Import Cycles
- None detected.

## Communities (129 total, 18 thin omitted)

### Community 0 - "CopyStatus"
Cohesion: 0.09
Nodes (36): ConflictError, NotFoundError, Raised when a requested resource does not exist., Raised when a resource conflict occurs (e.g., duplicate entry)., CopyStatus, str, Physical availability status of a book copy., BookCopyOut (+28 more)

### Community 1 - "App.jsx"
Cohesion: 0.15
Nodes (21): 6. Frontend Authentication Routing, 14. Next Phase, Key Highlights, 5. Routes, App(), GuestRoute(), RealtimeProvider(), useAuth() (+13 more)

### Community 2 - "PustakHub — Final Runtime Integration & Bug-Fix Report"
Cohesion: 0.04
Nodes (44): EmailService, Send a password reset email with a secure one-click reset link. Args: to_email:…, Service handling outbound email delivery via SMTP., Send a 6-digit registration verification OTP to the user's email. Args:…, Verify password reset email construction: - Email contains a one-click reset…, Verify that recipient name with special characters is HTML-escaped to prevent…, test_password_reset_email_format_and_link_construction(), test_password_reset_email_html_escaping() (+36 more)

### Community 3 - "package.json"
Cohesion: 0.05
Nodes (42): dependencies, axios, lucide-react, motion, qrcode.react, react, react-dom, react-router-dom (+34 more)

### Community 4 - "PustakHub — Phase 9 Security Remediation Report"
Cohesion: 0.10
Nodes (20): 10. Migration Verification, 11. Graphify Verification, 12. Documentation Updates, 13. Remaining Risks, 14. Deferred Enhancements, 15. Final Verification, 1. Executive Summary, 2. Audit Findings Addressed (+12 more)

### Community 5 - "exceptions.py"
Cohesion: 0.08
Nodes (37): _error_json(), ErrorResponse, ForbiddenError, PayloadTooLargeError, pustak_hub_exception_handler(), PustakHubError, BaseModel, FastAPI (+29 more)

### Community 6 - "test_phase1_foundation.py"
Cohesion: 0.13
Nodes (23): TestClient, Phase 1 foundation tests. Verifies: 1. FastAPI application starts without…, app.main imports cleanly and exposes an `app` object., Requesting a non-existent route returns HTTP 404., A preflight-like GET from the expected origin receives the CORS header., FastAPI application initialises and the test client is usable., GET / returns 200 with expected JSON keys., GET /api/health returns HTTP 200. (+15 more)

### Community 7 - "books/service.py"
Cohesion: 0.13
Nodes (27): Library Catalog Module for PustakHub., BookBase, BookCopyCreate, BookCopyListResponse, BookCopyUpdate, BookCreate, BookListResponse, BookUpdate (+19 more)

### Community 8 - "AuditAction"
Cohesion: 0.13
Nodes (31): AuditAction, AuditStatus, str, Broad category of the audited event., Outcome of the audited action., create_test_user(), fixture, TestClient (+23 more)

### Community 9 - "PustakHub — Post-Remediation Security Verification Report"
Cohesion: 0.18
Nodes (11): 10. Conclusion & Final Security Assessment, 1. Verification Summary, 2. Baseline State, 3. SEC-001 Verification — TOTP Encryption, 5. SEC-003 Verification — Local QR Generation & CSP, 6. SEC-004 Verification — Test Warning, 7. SEC-005 Verification — localStorage Decision, 8. MFA End-to-End Verification (+3 more)

### Community 10 - "test_phase2_database.py"
Cohesion: 0.06
Nodes (42): TestClient, _random_email(), _random_name(), Phase 2 — PostgreSQL & Database Foundation tests. Tests verify: 1.…, check_database_connection() must return True. If this fails, the PostgreSQL…, A real SELECT query executes against the live database., Every model class can be imported from app.models without error., All expected tables are registered in SQLAlchemy Base.metadata. (+34 more)

### Community 11 - "PustakHub — Password Reset Frontend Flow Implementation & Verification Report"
Cohesion: 0.17
Nodes (11): 1. Architecture & Graphify Verification, 2.2 Route Configuration (`frontend/src/App.jsx`), 2.3 Auth Service (`frontend/src/services/auth.service.js`), 2. Implementation Details, 3. Security & IAM Guardrails, 4.1 Backend Test Suite, 4.2 Frontend Quality Gates, 4.3 Browser UI Verification (+3 more)

### Community 12 - "BookCopy"
Cohesion: 0.08
Nodes (33): Book, BookCopy, Physical copy of a book title., Book title record in the library catalogue., BorrowRecord, Single borrowing transaction record., Fine, Financial penalty record for a borrowing transaction. (+25 more)

### Community 13 - "PustakHub — Phase 12 Report"
Cohesion: 0.07
Nodes (33): _auth_headers(), TestClient, UUID, Verify that staff can issue an available copy, status transitions, and return…, Verify that an overdue loan calculates and records a fine on return., Verify that students only see their own loans/fines and cannot inspect other…, Verify that students and unauthenticated guests cannot issue or return books., Verify that attempting to issue an already borrowed copy returns 409 Conflict. (+25 more)

### Community 14 - "auth/router.py"
Cohesion: 0.17
Nodes (26): Authentication module package for PustakHub., forgot_password(), get_me(), login(), logout(), mfa_disable(), mfa_enroll(), mfa_status() (+18 more)

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
Cohesion: 0.10
Nodes (32): catalog_cleanup(), create_test_user(), ensure_rbac_seeded(), fixture, TestClient, Verify unauthenticated catalog mutations reject with 401, while public read…, Test full Category CRUD and unique name validation., Ensure category cannot be deleted while books are attached to it. (+24 more)

### Community 19 - "env.py"
Cohesion: 0.12
Nodes (9): alembic, Alembic environment configuration for PustakHub. This file controls how Alembic…, Run migrations in 'online' mode. In online mode, Alembic connects to the…, Run migrations in 'offline' mode. In offline mode, Alembic does not require an…, run_migrations_offline(), run_migrations_online(), logging_config, pathlib (+1 more)

### Community 20 - "PustakHub — Authentication & Identity Architecture (Phase 3 & Phase 7)"
Cohesion: 0.11
Nodes (18): 1. Overview, 2. End-to-End Authentication Architecture, 3.1 Forgot-Password Flow, 3.2 Reset-Password Flow, 3. Password Reset & Account Recovery, 4.1 MFA Enrollment, 4.2 Verify Enrollment & Activation, 4.3 MFA Login Challenge & Verification (+10 more)

### Community 21 - "Role"
Cohesion: 0.11
Nodes (17): Application role (e.g., ADMIN, LIBRARIAN, STUDENT, GUEST). Roles are assigned…, Role, PermissionService, Session, Check if user possesses the specified permission (normalized)., Return the current role-permission mapping matrix from the database., Core permission management and resolution service., Idempotently populate standard system roles, permissions, and association… (+9 more)

### Community 22 - "PustakHub — Phase 11 Demo Data & Seed System"
Cohesion: 0.08
Nodes (23): 10. Production Safety, 11. CLI Usage, 12. Tests, 13. Actual Seeded Counts, 14. Frontend Verification, 15. Graphify Verification, 16. Files Changed, 17. Final Verification (+15 more)

### Community 23 - "_validate_password"
Cohesion: 0.27
Nodes (4): Validate password against the application security policy. Returns a list of…, _validate_password(), Verify the CLI reuses the same password rules as RegisterRequest., TestPasswordValidation

### Community 24 - "test_phase4_rbac.py"
Cohesion: 0.06
Nodes (49): Permission, Named application permission., AppRole, normalize_permission_name(), RBAC permission constants, role definitions, and role-permission matrix.…, Normalize permission string to canonical 'resource:action' format. Accepts…, FastAPI dependency factory enforcing that the caller has ALL of the specified…, FastAPI dependency factory enforcing that the caller possesses the specified… (+41 more)

### Community 25 - "PustakHub — Role-Based Access Control (RBAC) & Audit Logging"
Cohesion: 0.08
Nodes (25): 10. Audit Event Vocabulary & Data Sanitization, 11. Audit Failure Policy, 12. Anonymous & Unauthenticated Audit Logging, 13. Security Considerations, 14. Future Enhancements & Scope, 1. Architecture Overview, 2. Roles & Principles, 3. Permission Vocabulary (+17 more)

### Community 26 - "Phase 2 Final Verification Report — PustakHub"
Cohesion: 0.12
Nodes (16): 1. Executive Summary, 2. Verification Checklist & Findings, 3. Files Inspected, 4.1 Database Configuration, 4.2 Alembic & Migrations, 4.3 Model Relationships & Foreign Key Strategy, 4.4 Security Observations, 4. Detailed Technical Findings (+8 more)

### Community 27 - "PustakHub — Final UI/UX Polish Pass Completion Report"
Cohesion: 0.11
Nodes (17): 10. Dependencies, 11. Tests, 12. Lint, 13. Build, 14. Backend Regression, 15. Alembic Migrations, 16. Graphify Knowledge Graph, 17. Known Limitations (+9 more)

### Community 28 - "React + Vite"
Cohesion: 0.50
Nodes (3): Expanding the ESLint configuration, React Compiler, React + Vite

### Community 29 - "seed_database"
Cohesion: 0.06
Nodes (41): calculate_isbn13(), check_production_safety(), main(), Session, Generate a deterministic, mathematically valid ISBN-13 with check digit.…, Ensure seed script cannot accidentally execute in production., Seed the 20 standard library categories idempotently., Seed dedicated demo users for each existing role. (+33 more)

### Community 34 - "User"
Cohesion: 0.04
Nodes (102): argparse, _create_admin(), execute_create_admin(), execute_reconcile_admin(), main(), Session, PustakHub — Secure Administrative CLI. Provides a secure, interactive command…, Interactive bootstrap of the initial ADMIN user account. Steps: 1. Collect full… (+94 more)

### Community 36 - "PustakHub — Final Security & Architecture Audit Report"
Cohesion: 0.08
Nodes (26): 10. RBAC Security Audit, 11. IDOR / BOLA / Resource Authorization Assessment, 12. Library Catalog Security, 13. Borrowing & Circulation Concurrency, 14. Database Integrity, 15. Alembic Migration State, 16. Rate Limiting Audit, 17. Request Size Protection (+18 more)

### Community 37 - "UsersPage.jsx"
Cohesion: 0.17
Nodes (9): 2. User Profile & IAM Inspection (`/users/:id`), FALLBACK_ASSIGNABLE_ROLES, RoleAssignmentModal(), RoleAssignmentModalContent(), SUPPORTED_ASSIGNABLE_ROLES, ROLE_CLASSES, RoleBadge(), UserStatusBadge() (+1 more)

### Community 38 - "PustakHub — Phase 7 Engineering & Verification Report"
Cohesion: 0.08
Nodes (23): 10. Database Schema & Migration, 11. Frontend Integration, 12.1 Pytest Test Suite, 12.2 OpenAPI Verification, 12.3 Frontend Build Verification, 12. Verification & Test Results, 13. Files Created & Modified, 14. Deferred Work (+15 more)

### Community 44 - "PustakHub — Library Catalog Management"
Cohesion: 0.08
Nodes (23): 10. API Endpoint Reference, 11. Future Enhancements & Scope, 1. Architecture Overview, 2. Data Model & Entity Relationships, 3. Category Management, 4. Book Management, 5. Book Copy Inventory Management, 6. Catalog Search, Filtering & Pagination (+15 more)

### Community 45 - "test_phase9_security_remediation.py"
Cohesion: 0.09
Nodes (37): decrypt_mfa_secret(), encrypt_mfa_secret(), _get_encryption_key(), Application-layer authenticated encryption for sensitive data at rest (e.g.…, Derive a 256-bit (32-byte) AES key from the configured MFA_ENCRYPTION_KEY., Encrypt a Base32 TOTP secret using AES-256-GCM. Returns: Versioned ciphertext…, Decrypt a stored MFA secret. If the value is in versioned ciphertext format…, TestClient (+29 more)

### Community 46 - "RegisterRequest"
Cohesion: 0.14
Nodes (9): MfaVerifyRequest, Payload for initiating public student registration., Payload for setting a new password using a valid reset token., Payload to solve MFA challenge during login using TOTP code or recovery code., Payload for submitting the 6-digit registration verification OTP., RegisterRequest, ResetPasswordRequest, VerifyOtpRequest (+1 more)

### Community 48 - "PustakHub — System Architecture"
Cohesion: 0.13
Nodes (14): API Architecture & Route Categories, Backend Module Responsibilities, Configuration Strategy, Frontend Architecture, Frontend / Backend Relationship, Infrastructure & Security Layer, Logging & Security Rules, Modular Monolith Architecture (+6 more)

### Community 50 - "Phase 4 Completion Report — PustakHub"
Cohesion: 0.11
Nodes (17): 10. Manual Verification, 11. Known Issues, 12. Deferred Work, 13. Final Status, 1. Summary, 2.1 RBAC Evaluation Flow, 2.2 Permission Resolution Logic, 2.3 Resource-Level Authorization Logic (+9 more)

### Community 51 - "hash_otp"
Cohesion: 0.24
Nodes (9): generate_otp(), hash_otp(), Constant-time comparison between a provided OTP and a stored SHA-256 hash.…, Generate a cryptographically secure numeric OTP string. Args: length: Number of…, Produce a SHA-256 hex digest of an OTP string. Args: otp: 6-digit OTP string.…, verify_otp_hash(), Initiate student registration by storing state in Redis and dispatching an OTP.…, OTP is 6 digits; hash is 64-char SHA-256; verification works. (+1 more)

### Community 52 - "ConnectionManager"
Cohesion: 0.15
Nodes (10): ConnectionManager, Any, Evaluate whether a connected user is authorized to receive a specific real-time…, Broadcast an event to all authorized connected WebSocket clients. Returns count…, Return operational connection metrics., Thread-safe connection manager for WebSocket clients., 3.1 Transport Selection: WebSocket (`ws://` / `wss://`), 3.2 Multi-Worker Backplane: Redis Pub/Sub (+2 more)

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
Cohesion: 0.12
Nodes (22): 1. Architectural Principles, 2. Frontend Routes & Navigation, 3.1 `usePermissions` Hook (`src/hooks/usePermissions.js`), 3.2 `PermissionGate` Component (`src/components/PermissionGate.jsx`), 3.3 Protected Route Guarding (`src/components/ProtectedRoute.jsx`), 3. RBAC UI Architecture, 5. Demo Account Permissions Matrix, 6. Accessibility & Responsiveness (+14 more)

### Community 60 - "Real-Time Update Architecture & Specification"
Cohesion: 0.13
Nodes (15): 10. Summary of Subsystem Components, 1. Executive Summary & Objective, 2.1 REST as the Authoritative Source of Truth, 2. Core Architectural Principles, 5.1 Strict Secret Exclusion Guarantee, 5.2 Schema Definition, 5. Event Payload Security & Data Sanitization, 6.1 Handshake Authentication (+7 more)

### Community 61 - "TestClient"
Cohesion: 0.15
Nodes (13): TestClient, Test successful issue of an available book copy by staff., Verify issue endpoint requires authentication (401) and book:issue permission…, Ensure an already borrowed copy cannot be issued to another user (409 Conflict)., Verify on-time return closes the record as RETURNED and produces no fine., Test resource-level authorization for borrowing history: - Student 1 can access…, Test fine querying and IDOR defenses: - Student 1 views own fines - Student 2…, test_borrowing_history_access_and_idor_prevention() (+5 more)

### Community 62 - "Phase 14 Implementation Report — Dashboard & Operational Analytics UI"
Cohesion: 0.12
Nodes (15): 10. Database, 11. Demo Data, 12. Documentation, 13. Known Limitations, 14. Final Status, 1. Summary, 2. Dashboard Architecture, 3. Role-Specific Features (+7 more)

### Community 63 - "react-router-dom"
Cohesion: 0.26
Nodes (12): 11. Login Message Root Cause, 2.1 ResetPasswordPage (`frontend/src/pages/ResetPasswordPage.jsx`), AuthCard(), AuthError(), AuthLabel(), AuthSuccess(), AuthContext, ResetPasswordPage() (+4 more)

### Community 64 - "react"
Cohesion: 0.14
Nodes (17): 5. Components Updated, BookFormModal(), CategoryFormModal(), ConfirmDialog(), COPY_STATUSES, CopyFormModal(), EffectivePermissionsPanel(), IssueBookModal() (+9 more)

### Community 65 - "PustakHub — Phase 8 Engineering & Verification Report"
Cohesion: 0.12
Nodes (16): 10.1 Pytest Test Suite Results, 10.2 Frontend Build Verification, 10. Verification & Test Results, 11. Deferred Work, 2. Rate-Limiting Architecture, 3. Redis Key Strategy, 4. Route Policies & Limits, 5. Security HTTP Headers & CSP (+8 more)

### Community 66 - "Phase 1 Report — Foundation & Architecture"
Cohesion: 0.12
Nodes (15): 11. Acceptance Criteria, 12. Known Issues, 13. Deferred Work, 15. Final Status, 1. Objective, 2. Initial Project State, 3. Changes Implemented, 5. Files Modified (+7 more)

### Community 67 - "PustakHub — API Rate Limiting & Security Hardening (Phase 8)"
Cohesion: 0.08
Nodes (22): BaseHTTPMiddleware, Request, Response, Middleware injecting modern security headers and Content Security Policy (CSP)., Construct the Content Security Policy directive string., SecurityHeadersMiddleware, 10. Frontend Compatibility, 11. Production Deployment Recommendations (+14 more)

### Community 68 - "TestClient"
Cohesion: 0.18
Nodes (11): TestClient, Verify STUDENT role receives 403 Forbidden when attempting catalog mutations., Verify adding, updating, and deleting physical copies, plus book delete…, Verify deleting a Category containing books returns 409 Conflict., Verify GET /api/v1/books supports search, pagination, and category filtering., Verify ADMIN and LIBRARIAN can create, update, and delete book titles., test_book_copy_management_and_deletion_protection(), test_book_crud_lifecycle_admin_and_librarian() (+3 more)

### Community 69 - "4. Entities"
Cohesion: 0.07
Nodes (26): 10. Status Key, 1. Database Choice, 2. Architecture Overview, 3. Entity Relationship Diagram, 4.10 BorrowRecord — IMPLEMENTED, 4.11 Fine — IMPLEMENTED, 4.1 User — IMPLEMENTED, 4.2 Role — IMPLEMENTED (+18 more)

### Community 70 - ".connect"
Cohesion: 0.22
Nodes (7): ConnectionInfo, UUID, WebSocket, Unregister an active WebSocket connection., Send an event directly to all active connections for a specific user ID., Metadata associated with an active authenticated WebSocket connection., Register a new authenticated WebSocket connection. Returns True if registered…

### Community 71 - "PustakHub — Administrator Account Reconciliation Report"
Cohesion: 0.22
Nodes (8): 1. Database State Before vs. After, 2. Target Administrator Details, 3. Operations & Transaction Safety, 4. Graphify Architecture Verification, 5. Verification & Test Results, Aggregate Summary Table, Executive Summary, PustakHub — Administrator Account Reconciliation Report

### Community 72 - "AuditPage.jsx"
Cohesion: 0.38
Nodes (5): Key UI Features, AuditDetailModal(), AuditEventBadge(), AuditFilters(), AuditStatusBadge()

### Community 73 - "Key Features"
Cohesion: 0.25
Nodes (8): Audit & Observability, Authorization & RBAC, Identity & Authentication, Key Features, Library Management, MFA & Account Recovery, Real-Time Updates (WebSocket & Redis Pub/Sub), Security Engineering

### Community 74 - "RoleService"
Cohesion: 0.19
Nodes (11): Session, UUID, Revoke a role from a user., Assign a permission to a role., Revoke a permission from a role., Service for managing roles, role assignments, and role permissions., List supported application roles with their permissions. Args: db: Database…, Get role by its UUID. (+3 more)

### Community 75 - "audit/service.py"
Cohesion: 0.18
Nodes (12): AuditService, datetime, Session, UUID, Audit service for recording and retrieving security and operational audit trail…, Retrieve a single audit log entry by UUID., Query audit logs with filtering and pagination. Returns (items, total_count)., Central service for logging and querying security and operational audit entries. (+4 more)

### Community 76 - "PustakHub"
Cohesion: 0.12
Nodes (17): API Documentation, API Overview, Architecture, Authentication Architecture, Author, Authorization Architecture, Database Architecture, Future Enhancements (+9 more)

### Community 77 - "PHASE 17 REPORT: Real-Time Update Layer & Architecture Completion"
Cohesion: 0.11
Nodes (18): 10. Circulation & Catalog Integration, 11. Reconnection Strategy, 12. Failure Behavior & Graceful Degradation, 13. Security Validation, 14. Test Suite Execution, 15. Frontend Lint & Build, 16. Alembic Database Status, 18. Known Limitations & Operational Considerations (+10 more)

### Community 79 - "PustakHub — Demo Data & Seed Subsystem"
Cohesion: 0.18
Nodes (11): 1. Executive Overview, 2. Dataset Composition, 3. Demo User Credentials (LOCAL DEVELOPMENT ONLY), 4.1 Seed the Database, 4.2 Reset Demo Data, 4.3 CLI Flags Reference, 4. CLI Usage, 5. Security & Safety Invariants (+3 more)

### Community 80 - "AuthService"
Cohesion: 0.09
Nodes (29): get_redis_client(), Get or initialize the shared Redis client instance. Uses…, create_refresh_token(), hash_token(), datetime, Compute the SHA-256 hex digest of a token string. Used to store refresh token…, Generate a signed JWT refresh token and its SHA-256 hash. Args: subject: Unique…, Safe user representation for API responses. (+21 more)

### Community 81 - "Phase 16 Verification & Implementation Report: Audit Management UI"
Cohesion: 0.18
Nodes (10): 10. Frontend Lint & Build, 11. Alembic Status, 12. Graphify Status, 13. Known Limitations, 14. Deferred Work, 1. Phase Objective, 4. Frontend Changes, 7. Authorization & Security Controls (+2 more)

### Community 82 - "PustakHub UI & Theme Design System"
Cohesion: 0.12
Nodes (15): 1. Overview & Architecture, 2. Design Tokens Reference, 3. Light / Dark / System Modes & Anti-FOUC, 4. Dashboard Architecture & Metrics Verification, 5. Animation Strategy & External UI Stack, 6. Accessibility & Responsive Standards, Anti-FOUC Execution, Core Color Palette (CSS Variables) (+7 more)

### Community 83 - "Phase 15 Report — User & IAM Administration UI"
Cohesion: 0.06
Nodes (39): get_matrix(), get_my_permissions(), list_permissions(), get, Session, PermissionOut, BaseModel, Pydantic schemas for permissions module. (+31 more)

### Community 84 - "users/router.py"
Cohesion: 0.10
Nodes (24): get_db(), Session, FastAPI dependency that yields a SQLAlchemy database session. Usage in a route:…, Persisted refresh-token session. One row per active refresh token issued to a…, UserSession, get_current_user(), get_optional_current_user(), Session (+16 more)

### Community 85 - "Running Locally"
Cohesion: 0.40
Nodes (5): 1. Database Setup, 2. Redis Setup, 3. Start Backend API Server, 4. Start Frontend Development Server, Running Locally

### Community 86 - "Technology Stack"
Cohesion: 0.40
Nodes (5): Backend, Frontend, Storage & Security Infrastructure, Technology Stack, Testing & Verification

### Community 87 - "Example Workflows"
Cohesion: 0.50
Nodes (4): 1. Registration & Account Activation, 2. Multi-Factor Authentication (MFA) Setup, 3. MFA Login Challenge, Example Workflows

### Community 88 - "typing"
Cohesion: 0.11
Nodes (26): asyncio, BaseModel, str, Real-time Event Taxonomy and Schemas for PustakHub. Defines canonical event…, Canonical real-time event types., Standardized payload for real-time messages. Attributes: id: Unique identifier…, RealtimeEvent, RealtimeEventType (+18 more)

### Community 89 - "user.py"
Cohesion: 0.09
Nodes (55): argon2, argon2_exceptions, SQLAlchemy engine, session factory, and FastAPI session dependency. This module…, UUID, Security primitives for PustakHub. Provides: - Argon2id password hashing and…, AuditLog model. Immutable record of security-sensitive and business-critical…, Base, Declarative Base and shared column mixins for all SQLAlchemy models. Every… (+47 more)

### Community 90 - "borrowing/service.py"
Cohesion: 0.10
Nodes (41): BorrowStatus, str, Current state of a borrow transaction., Borrowing and Circulation module for PustakHub., _extract_request_meta(), get_borrowing(), get_user_borrowings(), _is_staff_user() (+33 more)

### Community 91 - "Environment Configuration"
Cohesion: 0.67
Nodes (3): Backend Configuration, Environment Configuration, Frontend Configuration

### Community 92 - "Installation"
Cohesion: 0.67
Nodes (3): Clone the Repository, Installation, Prerequisites

### Community 93 - "Demo Data"
Cohesion: 0.67
Nodes (3): Demo Data, Seeded Demo Accounts (Local Development Only), Seeding the Database

### Community 94 - "logging.py"
Cohesion: 0.06
Nodes (37): Application configuration. Uses pydantic-settings to load values from…, Email delivery service for PustakHub. Provides email dispatch for registration…, get_logger(), Application logging configuration. Sets up structured console logging for…, Get a named logger. Usage: from app.core.logging import get_logger logger =…, Redis-backed sliding window rate limiter for PustakHub. Implements an atomic…, Resolve the route path and HTTP method into rate limit policy parameters:…, resolve_rate_limit_policy() (+29 more)

### Community 95 - "_normalize_email"
Cohesion: 0.38
Nodes (4): _normalize_email(), Normalize email: strip whitespace and lowercase., Verify email normalization matches the auth service behavior., TestEmailNormalization

### Community 96 - "db"
Cohesion: 0.05
Nodes (39): websocket, Primary authenticated WebSocket connection endpoint. Workflow: 1. Validates JWT…, websocket_endpoint(), clean_redis_ratelimits_global(), client(), fixture, TestClient, Verify test database connection and seed baseline roles/permissions. (+31 more)

### Community 97 - ".subscribeMany"
Cohesion: 0.25
Nodes (5): 4. Files Modified, 4. Frontend Implementation, AuthProvider(), AuditPage(), BorrowingsPage()

### Community 98 - "clean_redis"
Cohesion: 0.29
Nodes (7): clean_redis(), client(), db_session(), fixture, TestClient instance for HTTP endpoint testing., Provides a transactional database session for tests, cleaned up afterwards., Cleans up Redis registration keys created during test runs.

### Community 99 - ".check_rate_limit"
Cohesion: 0.40
Nodes (3): RateLimitResult, Evaluate rate limit for a given identifier within a category. Args: identifier:…, Encapsulates the result of a rate limit evaluation.

### Community 100 - "4. Feature Workflows"
Cohesion: 0.40
Nodes (5): 4.1 Catalog Explorer (`/catalog`), 4.2 Book Details & Bibliographic Records (`/books/:id`), 4.3 Physical Copies Management, 4.4 Category Taxonomy Management (`/categories`), 4. Feature Workflows

### Community 101 - "Dashboard & Operational Analytics UI Architecture (`docs/dashboard-ui.md`)"
Cohesion: 0.29
Nodes (6): 1. Overview, 2. Persona Views & Information Architecture, 3. Metrics Matrix & Endpoints, 4. Reusable Components, 5. Security & IDOR Defenses, Dashboard & Operational Analytics UI Architecture (`docs/dashboard-ui.md`)

### Community 102 - "auth/service.py"
Cohesion: 0.09
Nodes (27): ForgotPasswordRequest, LoginRequest, LogoutRequest, MfaDisableRequest, MfaEnrollResponse, MfaStatusResponse, MfaVerifyEnrollmentRequest, BaseModel (+19 more)

### Community 103 - "publish_realtime_event"
Cohesion: 0.14
Nodes (13): publish_realtime_event(), Any, UUID, Ensure the data payload contains no sensitive credentials or raw secrets., Publish a real-time event safely from any synchronous or asynchronous context.…, _sanitize_data_payload(), Catalog updates are broadcast to all authenticated subscribers., Borrowing events targeting Student A are received by Student A. (+5 more)

### Community 104 - "Settings"
Cohesion: 0.29
Nodes (7): Central application settings. Values are loaded in order of priority: 1. Actual…, Settings, Settings can be imported and instantiated without errors., test_settings_load(), BaseSettings, 9. Configuration Changes, 5. Due-Date & Fine Policy

### Community 105 - "db_session"
Cohesion: 0.67
Nodes (3): db_session(), fixture, Provide a database session for seed testing.

### Community 106 - "User & IAM Administration Architecture"
Cohesion: 0.17
Nodes (11): 1. Administrative Users Ledger (`/users`), API Endpoints Reference, Architecture & Security Boundaries, Backend Authoritative Enforcements, Defensive Self-Protection & Lockout Prevention, Frontend UX Guards, IAM Audit Trail Integration, Known Limitations & Boundaries (+3 more)

### Community 107 - "HomePage.jsx"
Cohesion: 0.19
Nodes (7): FEATURES, HomePage(), api, failedQueue, auditService, fetchHealth(), motion

### Community 110 - "test_phase8_security_hardening.py"
Cohesion: 0.06
Nodes (52): RateLimiter, Central Redis-backed sliding window rate limiter., get_random_ip(), TestClient, Phase 8 Security Hardening & Rate Limiting Tests. Verifies: 1. Redis-backed…, Traffic from IP A does not consume or affect the rate limit quota of IP B., Exhausting quota in one category does not affect other categories., Rate limit counters expire and reset after the sliding window elapses. (+44 more)

### Community 111 - "_auth_headers"
Cohesion: 0.22
Nodes (11): _auth_headers(), TestClient, UUID, Verify LIBRARIAN can query circulation data but cannot access role management., Verify STUDENT can only query personal loan/fine metrics and cannot access…, Verify unauthenticated guests receive 401 on protected dashboard endpoints., Verify ADMIN can query all operational dashboard data sources., test_admin_dashboard_metrics_endpoints() (+3 more)

### Community 112 - "TestWebSocketAuthentication"
Cohesion: 0.22
Nodes (5): Valid JWT access token successfully establishes WebSocket connection., Connection attempt without token is rejected with policy violation., Connection attempt with corrupted token is rejected., Suspended user token is rejected during handshake., TestWebSocketAuthentication

### Community 116 - "TestRealtimeStatusEndpoint"
Cohesion: 0.40
Nodes (3): GET /api/v1/realtime/status returns operational metrics., GET /api/v1/realtime/status requires authentication., TestRealtimeStatusEndpoint

### Community 118 - "fines/router.py"
Cohesion: 0.12
Nodes (32): FineReason, FineStatus, str, Payment state of a fine., Why the fine was issued., Fines module for PustakHub., get_fine(), get_user_fines() (+24 more)

### Community 119 - "PustakHub — Audit Management & Forensic Logging Architecture"
Cohesion: 0.17
Nodes (11): 1. `GET /api/v1/audit/logs`, 1. Overview & Objectives, 2. Architecture & Data Model, 2. `GET /api/v1/audit/logs/{audit_id}`, 3. Backend Audit Endpoints, 3. `GET /api/v1/audit/actions`, 4. Frontend Audit Management Console, 5. Security & Immutability Guarantees (+3 more)

### Community 124 - "PustakHub — Password Reset One-Click Link Implementation & Verification Report"
Cohesion: 0.20
Nodes (9): 1.1 Backend Configuration (`backend/app/core/config.py`, `.env`, `.env.example`), 1.2 Email Service (`backend/app/core/email.py`), 1.3 Frontend Flow Integration (`frontend/src/pages/ResetPasswordPage.jsx`, `frontend/src/pages/ForgotPasswordPage.jsx`), 1. Summary of Changes, 2. Graphify Architecture Verification, 3. Security & Safety Verification, 4. Test Results, Executive Summary (+1 more)

### Community 125 - "DashboardPreviewPage.jsx"
Cohesion: 0.13
Nodes (11): COLOR_MAP, DashboardStatCard(), COLOR_MAP, QuickActionCard(), RealtimeStatusBadge(), RealtimeContext, useRealtime(), FinesPage() (+3 more)

### Community 126 - "Phase 6 Completion Report — Circulation, Borrowing & Fines"
Cohesion: 0.18
Nodes (10): 11. Files Modified, 12. Test Results, 13. Verification, 14. Deferred Work (Out of Scope for Phase 6), 1. Executive Summary, 2. Circulation Architecture, 6. Borrowing & Fine History (IDOR / BOLA Defenses), 8. Audit Logging (+2 more)

### Community 131 - "AuditLog"
Cohesion: 0.13
Nodes (22): AuditLog, Immutable security and operational audit trail. No TimestampMixin: audit rows…, create_test_user(), TestClient, Test complete password reset flow: - Generates token in Redis - Validates and…, Test password reset edge cases: - Weak new password rejected by policy (422) -…, Test TOTP MFA enrollment: - Unauthenticated cannot enroll (401) - Authenticated…, Test login flow for MFA-enabled accounts: - Non-MFA accounts log in normally… (+14 more)

### Community 133 - "27. Findings"
Cohesion: 0.33
Nodes (6): 27. Findings, Critical, High, Informational, Low, Medium

### Community 135 - "roles/router.py"
Cohesion: 0.18
Nodes (24): assign_permission_to_role(), assign_role_to_user(), create_role(), get_role(), list_roles(), delete, get, post (+16 more)

### Community 137 - "TestPublicRegistrationIntegrity"
Cohesion: 0.33
Nodes (4): Verify that the public registration flow cannot create ADMIN accounts., RegisterRequest must not accept a role parameter., Inspect the auth service source to confirm STUDENT is hardcoded in…, TestPublicRegistrationIntegrity

### Community 138 - "4. Files Created"
Cohesion: 0.40
Nodes (5): 4. Files Created, Backend — New Files, Docs — New Files, Frontend — New Files, Repository — New Files

### Community 141 - "get_realtime_status"
Cohesion: 0.67
Nodes (3): get_realtime_status(), get, Return operational connection statistics.

### Community 144 - "main.py"
Cohesion: 0.08
Nodes (32): Parse CORS_ORIGINS from comma-separated string into a list., check_database_connection(), Attempt a lightweight SELECT 1 to verify the database is reachable. Returns…, Register all exception handlers on the FastAPI application. Call this once in…, register_exception_handlers(), configure_logging(), Configure the root logger for PustakHub. Should be called once at application…, check_redis_connection() (+24 more)

## Knowledge Gaps
- **527 isolated node(s):** `name`, `private`, `version`, `type`, `dev` (+522 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1242 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `App.jsx`, `PustakHub — Final Runtime Integration & Bug-Fix Report`, `AuditLog`, `roles/router.py`, `AuditAction`, `test_phase2_database.py`, `BookCopy`, `get_realtime_status`, `auth/router.py`, `books/router.py`, `auth_headers`, `catalog_cleanup`, `PustakHub — Authentication & Identity Architecture (Phase 3 & Phase 7)`, `Role`, `test_phase4_rbac.py`, `seed_database`, `test_phase9_security_remediation.py`, `RoleService`, `audit/service.py`, `AuthService`, `Phase 15 Report — User & IAM Administration UI`, `users/router.py`, `Example Workflows`, `user.py`, `borrowing/service.py`, `auth/service.py`, `fines/router.py`?**
  _High betweenness centrality (0.281) - this node is a cross-community bridge._
- **Why does `Key Highlights` connect `App.jsx` to `PustakHub — Final Runtime Integration & Bug-Fix Report`, `usePermissions`, `User`?**
  _High betweenness centrality (0.121) - this node is a cross-community bridge._
- **Why does `useAuth()` connect `App.jsx` to `react`, `HomePage.jsx`, `Navbar.jsx`, `usePermissions`, `DashboardPreviewPage.jsx`, `react-router-dom`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Are the 80 inferred relationships involving `User` (e.g. with `_reconcile_admin()` and `AuditService`) actually correct?**
  _`User` has 80 INFERRED edges - model-reasoned connections that need verification._
- **Are the 41 inferred relationships involving `AuditAction` (e.g. with `execute_create_admin()` and `execute_reconcile_admin()`) actually correct?**
  _`AuditAction` has 41 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `Role` (e.g. with `execute_create_admin()` and `execute_reconcile_admin()`) actually correct?**
  _`Role` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 34 inferred relationships involving `AccountStatus` (e.g. with `execute_create_admin()` and `execute_reconcile_admin()`) actually correct?**
  _`AccountStatus` has 34 INFERRED edges - model-reasoned connections that need verification._