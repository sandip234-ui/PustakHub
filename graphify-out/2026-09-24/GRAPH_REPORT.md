# Graph Report - PustakHub  (2026-09-24)

## Corpus Check
- 173 files · ~123,681 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: .example 3, (none) 3, .ini 2)

## Summary
- 2031 nodes · 4692 edges · 104 communities (89 shown, 15 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 628 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Phase 15 Report — User & IAM Administration UI
- App.jsx
- Phase 3 Completion Report — PustakHub
- package.json
- RequestSizeLimitMiddleware
- exceptions.py
- 10. Tests Executed
- test_phase6_circulation.py
- test_phase7_auth_security.py
- PustakHub — Post-Remediation Security Verification Report
- Verification Matrix
- books/router.py
- typing
- PustakHub — Phase 12 Report
- seed_demo.py
- BookCopy
- auth_headers
- Phase 13 Implementation Report — Circulation & Borrowing UI
- catalog_cleanup
- env.py
- PustakHub — Authentication & Identity Architecture (Phase 3 & Phase 7)
- roles/schemas.py
- PustakHub — Phase 11 Demo Data & Seed System
- RoleService
- test_phase4_rbac.py
- PustakHub — Role-Based Access Control (RBAC) & Audit Logging
- test_phase13_circulation_ui.py
- get_redis_client
- React + Vite
- test_phase8_security_hardening.py
- rules/graphify.md
- workflows/graphify.md
- test_phase3_auth.py
- PustakHub — Final Security & Architecture Audit Report
- UserDetailsPage.jsx
- PustakHub — Phase 7 Engineering & Verification Report
- PustakHub — Library Catalog Management
- test_phase9_security_remediation.py
- Phase 2 Final Verification Report — PustakHub
- PustakHub — System Architecture
- Phase 4 Completion Report — PustakHub
- auth/service.py
- test_phase2_database.py
- PustakHub — Circulation, Borrowing & Fines Architecture
- require_any_permission
- Circulation & Borrowing UI Architecture (`docs/circulation-ui.md`)
- Phase 5 Completion Report — PustakHub
- return_book
- Phase 6 Completion Report — Circulation, Borrowing & Fines
- DashboardPreviewPage.jsx
- api.js
- PustakHub — Demo Data & Seed Subsystem
- borrowing/service.py
- User
- usePermissions
- PustakHub — Phase 8 Engineering & Verification Report
- Phase 1 Report — Foundation & Architecture
- PustakHub — API Rate Limiting & Security Hardening (Phase 8)
- request_size.py
- 4. Entities
- clean_redis
- AuditAction
- test_phase14_dashboard_analytics.py
- Key Features
- RateLimitMiddleware
- AuditContextMiddleware
- PustakHub
- check_database_connection
- PustakHub — Catalog Management UI Specification & Guide
- PustakHubError
- Phase 14 Implementation Report — Dashboard & Operational Analytics UI
- security.py
- list_fines
- Settings
- Role
- Running Locally
- Technology Stack
- Example Workflows
- PHASE_02_REPORT — PostgreSQL & Database Foundation
- TestClient
- db_session
- Environment Configuration
- Installation
- Demo Data
- Backend
- require_permission
- 4. Files Created
- TestClient
- 2. Architecture & Flows
- test_health_endpoint_reports_db_healthy
- Dashboard & Operational Analytics UI Architecture (`docs/dashboard-ui.md`)
- test_expected_tables_exist_in_database
- test_book_with_nonexistent_category_raises

## God Nodes (most connected - your core abstractions)
1. `User` - 124 edges
2. `AuditAction` - 53 edges
3. `Role` - 51 edges
4. `AccountStatus` - 48 edges
5. `BookCopy` - 41 edges
6. `AuditStatus` - 38 edges
7. `BorrowRecord` - 38 edges
8. `AuditLog` - 37 edges
9. `AuthService` - 36 edges
10. `hash_password()` - 34 edges

## Surprising Connections (you probably didn't know these)
- `2. Circulation Policy & Defaults` --references--> `Settings`  [INFERRED]
  docs/circulation.md → backend/app/core/config.py
- `6. Database Changes` --references--> `AuditAction`  [INFERRED]
  docs/reports/PHASE_04_REPORT.md → backend/app/models/audit_log.py
- `4.4 Security Observations` --references--> `AuditLog`  [INFERRED]
  docs/reports/PHASE_02_VERIFICATION.md → backend/app/models/audit_log.py
- `9. Database & Migration Changes` --references--> `CopyStatus`  [INFERRED]
  docs/reports/PHASE_05_REPORT.md → backend/app/models/book_copy.py
- `6. Book Copy Generation` --references--> `BookCopy`  [INFERRED]
  docs/reports/PHASE_11_REPORT.md → backend/app/models/book_copy.py

## Import Cycles
- None detected.

## Communities (104 total, 15 thin omitted)

### Community 0 - "Phase 15 Report — User & IAM Administration UI"
Cohesion: 0.07
Nodes (35): check_resource_access(), get_current_user_permissions(), Session, UUID, Check if the current authenticated user is either the resource owner OR…, Dependency resolving the set of permissions held by the currently authenticated…, Effective permissions for a user., UserPermissionsOut (+27 more)

### Community 1 - "App.jsx"
Cohesion: 0.14
Nodes (26): 6. Frontend Authentication Routing, 14. Next Phase, Key Highlights, 2. Navigation, App(), GuestRoute(), Navbar(), AuthContext (+18 more)

### Community 2 - "Phase 3 Completion Report — PustakHub"
Cohesion: 0.06
Nodes (31): EmailService, Email delivery service for PustakHub. Provides email dispatch for registration…, Send a password reset instructions email with the secure single-use token.…, Service handling outbound email delivery via SMTP., Send a 6-digit registration verification OTP to the user's email. Args:…, 10. Automated Tests Execution, 11. Manual Verification, 12. Known Issues (+23 more)

### Community 3 - "package.json"
Cohesion: 0.05
Nodes (40): dependencies, axios, qrcode.react, react, react-dom, react-router-dom, tailwindcss, @tailwindcss/vite (+32 more)

### Community 4 - "RequestSizeLimitMiddleware"
Cohesion: 0.14
Nodes (15): PayloadTooLargeError, Raised when request payload exceeds allowed limit (HTTP 413)., BaseHTTPMiddleware, Request, Response, Middleware that rejects requests with body size exceeding…, RequestSizeLimitMiddleware, limited_receive() (+7 more)

### Community 5 - "exceptions.py"
Cohesion: 0.15
Nodes (21): _error_json(), ErrorResponse, pustak_hub_exception_handler(), BaseModel, FastAPI, Request, Application-level exception definitions and global exception handlers.…, Handle all domain-level PustakHub exceptions. (+13 more)

### Community 6 - "10. Tests Executed"
Cohesion: 0.11
Nodes (22): TestClient, app.main imports cleanly and exposes an `app` object., Requesting a non-existent route returns HTTP 404., A preflight-like GET from the expected origin receives the CORS header., FastAPI application initialises and the test client is usable., GET / returns 200 with expected JSON keys., GET /api/health returns HTTP 200., GET /api/health returns required fields with correct values. (+14 more)

### Community 7 - "test_phase6_circulation.py"
Cohesion: 0.11
Nodes (34): AuditLog, AuditLog model. Immutable record of security-sensitive and business-critical…, Immutable security and operational audit trail. No TimestampMixin: audit rows…, Base, Declarative Base and shared column mixins for all SQLAlchemy models. Every…, Shared declarative base for all PustakHub SQLAlchemy models. Uses SQLAlchemy…, Adds `created_at` and `updated_at` to any model that inherits this mixin. -…, TimestampMixin (+26 more)

### Community 8 - "test_phase7_auth_security.py"
Cohesion: 0.13
Nodes (28): hash_token(), Compute the SHA-256 hex digest of a token string. Used to store refresh token…, Verify a plaintext password against an Argon2id hash. Args: password: Raw…, verify_password(), create_test_user(), ensure_rbac_seeded(), fixture, TestClient (+20 more)

### Community 9 - "PustakHub — Post-Remediation Security Verification Report"
Cohesion: 0.18
Nodes (11): 10. Conclusion & Final Security Assessment, 1. Verification Summary, 2. Baseline State, 3. SEC-001 Verification — TOTP Encryption, 5. SEC-003 Verification — Local QR Generation & CSP, 6. SEC-004 Verification — Test Warning, 7. SEC-005 Verification — localStorage Decision, 8. MFA End-to-End Verification (+3 more)

### Community 10 - "Verification Matrix"
Cohesion: 0.20
Nodes (12): _random_email(), A real SELECT query executes against the live database., Inserting two users with the same email raises IntegrityError., Two sessions with the same token_hash must raise IntegrityError., Assigning the same role to the same user twice must raise IntegrityError., The database must be at the Alembic head revision. Fails if `alembic upgrade…, test_alembic_migration_at_head(), test_raw_sql_executes() (+4 more)

### Community 11 - "books/router.py"
Cohesion: 0.05
Nodes (91): ConflictError, NotFoundError, Raised when a requested resource does not exist., Raised when business-level validation fails (not Pydantic schema validation)., Raised when a resource conflict occurs (e.g., duplicate entry)., ValidationError, Library Catalog Module for PustakHub., create_book() (+83 more)

### Community 12 - "typing"
Cohesion: 0.13
Nodes (29): get_db(), Session, SQLAlchemy engine, session factory, and FastAPI session dependency. This module…, FastAPI dependency that yields a SQLAlchemy database session. Usage in a route:…, get_logger(), Application logging configuration. Sets up structured console logging for…, Get a named logger. Usage: from app.core.logging import get_logger logger =…, Audit Context & Security Request Middleware. Responsibilities: - Generates a… (+21 more)

### Community 13 - "PustakHub — Phase 12 Report"
Cohesion: 0.10
Nodes (19): 10. Error Handling, 11. Responsive Design, 12. Accessibility, 13. Tests, 14. Phase 11 Dataset Verification, 15. Security Verification, 16. Build Verification, 17. Graphify Verification (+11 more)

### Community 14 - "seed_demo.py"
Cohesion: 0.06
Nodes (50): argparse, calculate_isbn13(), check_production_safety(), main(), Session, PustakHub — Demo Data & Seed Subsystem (Phase 11). Provides deterministic,…, Generate a deterministic, mathematically valid ISBN-13 with check digit.…, Ensure seed script cannot accidentally execute in production. (+42 more)

### Community 15 - "BookCopy"
Cohesion: 0.10
Nodes (26): Book, BookCopy, Physical copy of a book title., Book title record in the library catalogue., BorrowRecord, Single borrowing transaction record., Fine, Financial penalty record for a borrowing transaction. (+18 more)

### Community 16 - "auth_headers"
Cohesion: 0.08
Nodes (17): auth_headers(), UUID, Tests for GET /api/v1/users with search and filtering., Tests for GET /api/v1/users/{id} and /api/v1/users/{id}/permissions., Tests for PATCH /api/v1/users/{id}/status and self-lockout prevention., Admin must NOT be allowed to deactivate their own account., Admin must NOT be allowed to suspend their own account., Tests for Role assignment, revocation, and self-lockout protections. (+9 more)

### Community 17 - "Phase 13 Implementation Report — Circulation & Borrowing UI"
Cohesion: 0.12
Nodes (15): 10. Tests, 11. Database, 12. Demo Data Validation, 14. Documentation, 15. Known Limitations, 16. Final Status, 1. Summary, 3. Components Added / Modified (+7 more)

### Community 18 - "catalog_cleanup"
Cohesion: 0.10
Nodes (30): catalog_cleanup(), create_test_user(), ensure_rbac_seeded(), fixture, TestClient, Verify all catalog endpoints reject unauthenticated calls with 401., Test full Category CRUD and unique name validation., Ensure category cannot be deleted while books are attached to it. (+22 more)

### Community 19 - "env.py"
Cohesion: 0.13
Nodes (8): alembic, Alembic environment configuration for PustakHub. This file controls how Alembic…, Run migrations in 'online' mode. In online mode, Alembic connects to the…, Run migrations in 'offline' mode. In offline mode, Alembic does not require an…, run_migrations_offline(), run_migrations_online(), logging_config, pathlib

### Community 20 - "PustakHub — Authentication & Identity Architecture (Phase 3 & Phase 7)"
Cohesion: 0.13
Nodes (14): 1. Overview, 2. End-to-End Authentication Architecture, 3.1 Forgot-Password Flow, 3.2 Reset-Password Flow, 3. Password Reset & Account Recovery, 4.1 MFA Enrollment, 4.2 Verify Enrollment & Activation, 4.3 MFA Login Challenge & Verification (+6 more)

### Community 21 - "roles/schemas.py"
Cohesion: 0.20
Nodes (13): get_matrix(), get_my_permissions(), list_permissions(), get, Session, PermissionOut, BaseModel, Pydantic schemas for permissions module. (+5 more)

### Community 22 - "PustakHub — Phase 11 Demo Data & Seed System"
Cohesion: 0.08
Nodes (23): 10. Production Safety, 11. CLI Usage, 12. Tests, 13. Actual Seeded Counts, 14. Frontend Verification, 15. Graphify Verification, 16. Files Changed, 17. Final Verification (+15 more)

### Community 23 - "RoleService"
Cohesion: 0.19
Nodes (11): Session, UUID, Assign a permission to a role., Revoke a permission from a role., Service for managing roles, role assignments, and role permissions., List all roles with their permissions., Get role by its UUID., Get role by its name. (+3 more)

### Community 24 - "test_phase4_rbac.py"
Cohesion: 0.11
Nodes (30): AppRole, create_test_user(), ensure_rbac_seeded(), fixture, TestClient, Phase 4 RBAC Authorization & Privilege Escalation Tests. Tests covered: 1.…, Unauthenticated request to permission-protected route returns 401 Unauthorized., Authenticated STUDENT lacks 'permission:view' and receives 403 Forbidden. (+22 more)

### Community 25 - "PustakHub — Role-Based Access Control (RBAC) & Audit Logging"
Cohesion: 0.08
Nodes (24): 10. Audit Event Vocabulary & Data Sanitization, 11. Audit Failure Policy, 12. Anonymous & Unauthenticated Audit Logging, 13. Security Considerations, 14. Future Enhancements & Scope, 1. Architecture Overview, 2. Roles & Principles, 3. Permission Vocabulary (+16 more)

### Community 26 - "test_phase13_circulation_ui.py"
Cohesion: 0.12
Nodes (25): CopyStatus, str, Physical availability status of a book copy., BorrowStatus, str, Current state of a borrow transaction., _auth_headers(), circulation_setup() (+17 more)

### Community 27 - "get_redis_client"
Cohesion: 0.06
Nodes (38): check_redis_connection(), get_redis_client(), Redis client and connection management for PustakHub. Used in Phase 3…, Get or initialize the shared Redis client instance. Uses…, Check if the Redis server is reachable. Returns: True if Redis responds to…, create_application(), health(), lifespan() (+30 more)

### Community 28 - "React + Vite"
Cohesion: 0.50
Nodes (3): Expanding the ESLint configuration, React Compiler, React + Vite

### Community 29 - "test_phase8_security_hardening.py"
Cohesion: 0.05
Nodes (63): Application configuration. Uses pydantic-settings to load values from…, RateLimiter, RateLimitResult, Redis-backed sliding window rate limiter for PustakHub. Implements an atomic…, Evaluate rate limit for a given identifier within a category. Args: identifier:…, Resolve the route path and HTTP method into rate limit policy parameters:…, Encapsulates the result of a rate limit evaluation., Central Redis-backed sliding window rate limiter. (+55 more)

### Community 34 - "test_phase3_auth.py"
Cohesion: 0.07
Nodes (49): hash_otp(), Constant-time comparison between a provided OTP and a stored SHA-256 hash.…, Produce a SHA-256 hex digest of an OTP string. Args: otp: 6-digit OTP string.…, verify_otp_hash(), AccountStatus, str, Lifecycle states for a user account., client() (+41 more)

### Community 36 - "PustakHub — Final Security & Architecture Audit Report"
Cohesion: 0.04
Nodes (48): get_current_user(), Session, Extract, decode, and validate the JWT Bearer token from the request. Returns…, 10. RBAC Security Audit, 11. IDOR / BOLA / Resource Authorization Assessment, 12. Library Catalog Security, 13. Borrowing & Circulation Concurrency, 14. Database Integrity (+40 more)

### Community 37 - "UserDetailsPage.jsx"
Cohesion: 0.20
Nodes (10): 5. Routes, 2. User Profile & IAM Inspection (`/users/:id`), EffectivePermissionsPanel(), RoleAssignmentModal(), RoleAssignmentModalContent(), RoleBadge(), UserStatusBadge(), UserDetailsPage() (+2 more)

### Community 38 - "PustakHub — Phase 7 Engineering & Verification Report"
Cohesion: 0.08
Nodes (23): 10. Database Schema & Migration, 11. Frontend Integration, 12.1 Pytest Test Suite, 12.2 OpenAPI Verification, 12.3 Frontend Build Verification, 12. Verification & Test Results, 13. Files Created & Modified, 14. Deferred Work (+15 more)

### Community 44 - "PustakHub — Library Catalog Management"
Cohesion: 0.08
Nodes (23): 10. API Endpoint Reference, 11. Future Enhancements & Scope, 1. Architecture Overview, 2. Data Model & Entity Relationships, 3. Category Management, 4. Book Management, 5. Book Copy Inventory Management, 6. Catalog Search, Filtering & Pagination (+15 more)

### Community 45 - "test_phase9_security_remediation.py"
Cohesion: 0.05
Nodes (56): decrypt_mfa_secret(), encrypt_mfa_secret(), _get_encryption_key(), Application-layer authenticated encryption for sensitive data at rest (e.g.…, Derive a 256-bit (32-byte) AES key from the configured MFA_ENCRYPTION_KEY., Encrypt a Base32 TOTP secret using AES-256-GCM. Returns: Versioned ciphertext…, Decrypt a stored MFA secret. If the value is in versioned ciphertext format…, TestClient (+48 more)

### Community 46 - "Phase 2 Final Verification Report — PustakHub"
Cohesion: 0.18
Nodes (10): 1. Executive Summary, 3. Files Inspected, 5. Test Suite Execution Results, 6. Discrepancies & Recommended Fixes, 7. Final Verification Status, Configuration & Core Layer, Migrations, Phase 2 Final Verification Report — PustakHub (+2 more)

### Community 48 - "PustakHub — System Architecture"
Cohesion: 0.14
Nodes (13): API Architecture & Route Categories, Backend Module Responsibilities, Configuration Strategy, Frontend / Backend Relationship, Infrastructure & Security Layer, Logging & Security Rules, Modular Monolith Architecture, Project Overview (+5 more)

### Community 50 - "Phase 4 Completion Report — PustakHub"
Cohesion: 0.17
Nodes (11): 10. Manual Verification, 11. Known Issues, 12. Deferred Work, 13. Final Status, 3. Role → Permission Matrix, 6. Database Changes, 7. Authorization Security Review, 8. Audit Logging Security Review (+3 more)

### Community 51 - "auth/service.py"
Cohesion: 0.06
Nodes (71): Authentication module package for PustakHub., forgot_password(), get_me(), login(), logout(), mfa_disable(), mfa_enroll(), mfa_status() (+63 more)

### Community 52 - "test_phase2_database.py"
Cohesion: 0.13
Nodes (15): _random_name(), Phase 2 — PostgreSQL & Database Foundation tests. Tests verify: 1.…, Every model class can be imported from app.models without error., All expected tables are registered in SQLAlchemy Base.metadata., Inserting two roles with the same name raises IntegrityError., DATABASE_URL must be configured — not empty., SQLAlchemy engine object exists and is configured., A database session can be opened and closed without error. (+7 more)

### Community 53 - "PustakHub — Circulation, Borrowing & Fines Architecture"
Cohesion: 0.17
Nodes (11): 2. Circulation Policy & Defaults, 3. Physical Inventory State Transitions, 4. Book Issue Workflow, 5. Book Return Workflow & Overdue Fine Calculation, 7. RBAC & Resource-Level Authorization (IDOR / BOLA Prevention), 8. Audit Logging & Security Guarantees, Data Privacy & Secret Shielding, Deterministic Overdue Formula (+3 more)

### Community 54 - "require_any_permission"
Cohesion: 0.19
Nodes (11): FastAPI dependency factory enforcing that the caller has ALL of the specified…, FastAPI dependency factory enforcing that the caller possesses the specified…, FastAPI dependency factory enforcing that the caller has AT LEAST ONE of the…, require_all_permissions(), require_any_permission(), require_role(), Direct unit testing of authorization dependency functions., test_rbac_dependencies_unit_evaluation() (+3 more)

### Community 55 - "Circulation & Borrowing UI Architecture (`docs/circulation-ui.md`)"
Cohesion: 0.20
Nodes (9): 1. Overview, 2. Route Map, 3. Component Architecture, 4.1 Issue / Checkout Workflow, 4.2 Return Workflow, 4.3 Fines Ledger & Transparency, 4. Key Workflows, 6. Accessibility & Responsiveness (+1 more)

### Community 56 - "Phase 5 Completion Report — PustakHub"
Cohesion: 0.12
Nodes (16): 10. Files Created, 11. Files Modified, 12. Test Results, 13. Verification, 15. Final Status, 1. Executive Summary, 2. Architecture Implemented, 3. Category Management (+8 more)

### Community 57 - "return_book"
Cohesion: 0.27
Nodes (14): _extract_request_meta(), get_borrowing(), get_user_borrowings(), _is_staff_user(), issue_book(), list_borrowings(), get, post (+6 more)

### Community 58 - "Phase 6 Completion Report — Circulation, Borrowing & Fines"
Cohesion: 0.18
Nodes (10): 11. Files Modified, 12. Test Results, 13. Verification, 14. Deferred Work (Out of Scope for Phase 6), 1. Executive Summary, 2. Circulation Architecture, 3. Book Issue Workflow, 6. Borrowing & Fine History (IDOR / BOLA Defenses) (+2 more)

### Community 59 - "DashboardPreviewPage.jsx"
Cohesion: 0.14
Nodes (14): BookFormModal(), CategoryFormModal(), ConfirmDialog(), COPY_STATUSES, CopyFormModal(), DashboardStatCard(), IssueBookModal(), IssueBookModalContent() (+6 more)

### Community 60 - "api.js"
Cohesion: 0.29
Nodes (5): HomePage(), api, failedQueue, auditService, fetchHealth()

### Community 61 - "PustakHub — Demo Data & Seed Subsystem"
Cohesion: 0.18
Nodes (11): 1. Executive Overview, 2. Dataset Composition, 3. Demo User Credentials (LOCAL DEVELOPMENT ONLY), 4.1 Seed the Database, 4.2 Reset Demo Data, 4.3 CLI Flags Reference, 4. CLI Usage, 5. Security & Safety Invariants (+3 more)

### Community 62 - "borrowing/service.py"
Cohesion: 0.07
Nodes (46): FineReason, FineStatus, str, Payment state of a fine., Why the fine was issued., Borrowing and Circulation module for PustakHub., BorrowIssueRequest, BorrowRecordListResponse (+38 more)

### Community 63 - "User"
Cohesion: 0.09
Nodes (32): Any, create_access_token(), decode_token(), hash_password(), Generate a signed JWT access token. Args: subject: Unique identifier of the…, Decode and validate a JWT token's signature and expiration. Args: token: Raw…, Hash a plaintext password using Argon2id. Args: password: Raw password string.…, Application user entity. (+24 more)

### Community 64 - "usePermissions"
Cohesion: 0.11
Nodes (22): Frontend Architecture, 1. Architectural Principles, 3.1 `usePermissions` Hook (`src/hooks/usePermissions.js`), 3.2 `PermissionGate` Component (`src/components/PermissionGate.jsx`), 3.3 Protected Route Guarding (`src/components/ProtectedRoute.jsx`), 3. RBAC UI Architecture, 5. Security & RBAC Matrix, 8. Privilege Escalation Defenses (+14 more)

### Community 65 - "PustakHub — Phase 8 Engineering & Verification Report"
Cohesion: 0.12
Nodes (16): 10.1 Pytest Test Suite Results, 10.2 Frontend Build Verification, 10. Verification & Test Results, 11. Deferred Work, 2. Rate-Limiting Architecture, 3. Redis Key Strategy, 4. Route Policies & Limits, 5. Security HTTP Headers & CSP (+8 more)

### Community 66 - "Phase 1 Report — Foundation & Architecture"
Cohesion: 0.17
Nodes (11): 11. Acceptance Criteria, 12. Known Issues, 13. Deferred Work, 15. Final Status, 1. Objective, 2. Initial Project State, 5. Files Modified, 6. Dependencies Added (+3 more)

### Community 67 - "PustakHub — API Rate Limiting & Security Hardening (Phase 8)"
Cohesion: 0.12
Nodes (15): 10. Frontend Compatibility, 11. Production Deployment Recommendations, 1. Executive Summary, 2.1 Sliding Window Algorithm, 2.2 Redis Key Strategy, 2.3 Route Category Policies & Quotas, 2. Redis-Backed API Rate Limiting, 3. Rate Limit Response Semantics (+7 more)

### Community 68 - "request_size.py"
Cohesion: 0.14
Nodes (12): PustakHub Security & Context Middleware Stack., Request Body Size Protection Middleware for PustakHub. Guards endpoints against…, BaseHTTPMiddleware, Request, Response, Security HTTP Headers & Content Security Policy (CSP) Middleware for PustakHub.…, Middleware injecting modern security headers and Content Security Policy (CSP)., Construct the Content Security Policy directive string. (+4 more)

### Community 69 - "4. Entities"
Cohesion: 0.07
Nodes (26): 10. Status Key, 1. Database Choice, 2. Architecture Overview, 3. Entity Relationship Diagram, 4.10 BorrowRecord — IMPLEMENTED, 4.11 Fine — IMPLEMENTED, 4.12 AuditLog — IMPLEMENTED, 4.1 User — IMPLEMENTED (+18 more)

### Community 70 - "clean_redis"
Cohesion: 0.29
Nodes (7): clean_redis(), client(), db_session(), fixture, TestClient instance for HTTP endpoint testing., Provides a transactional database session for tests, cleaned up afterwards., Cleans up Redis registration keys created during test runs.

### Community 71 - "AuditAction"
Cohesion: 0.05
Nodes (72): AuditAction, AuditStatus, str, Broad category of the audited event., Outcome of the audited action., get_audit_logs(), datetime, get (+64 more)

### Community 72 - "test_phase14_dashboard_analytics.py"
Cohesion: 0.18
Nodes (15): _auth_headers(), ensure_rbac_seeded(), fixture, TestClient, UUID, Phase 14 Integration Tests — Operational Analytics & Dashboard Endpoint…, Verify LIBRARIAN can query circulation data but cannot access role management., Verify STUDENT can only query personal loan/fine metrics and cannot access… (+7 more)

### Community 73 - "Key Features"
Cohesion: 0.29
Nodes (7): Audit & Observability, Authorization & RBAC, Identity & Authentication, Key Features, Library Management, MFA & Account Recovery, Security Engineering

### Community 74 - "RateLimitMiddleware"
Cohesion: 0.33
Nodes (5): BaseHTTPMiddleware, Request, Response, RateLimitMiddleware, Middleware that enforces Redis-backed rate limiting per IP and route category.

### Community 75 - "AuditContextMiddleware"
Cohesion: 0.33
Nodes (5): AuditContextMiddleware, BaseHTTPMiddleware, Request, Response, Middleware that populates request context (IP, User-Agent, Request-ID) used for…

### Community 76 - "PustakHub"
Cohesion: 0.09
Nodes (23): API Documentation, API Overview, Architecture, Authentication Architecture, Author, Authorization Architecture, Backend, Build Verification (+15 more)

### Community 77 - "check_database_connection"
Cohesion: 0.20
Nodes (10): check_database_connection(), Attempt a lightweight SELECT 1 to verify the database is reachable. Returns…, check_database_connection() must return True. If this fails, the PostgreSQL…, test_database_connection_succeeds(), 9. Security Considerations, 4.1 Database Configuration, 4.2 Alembic & Migrations, 4.3 Model Relationships & Foreign Key Strategy (+2 more)

### Community 78 - "PustakHub — Catalog Management UI Specification & Guide"
Cohesion: 0.12
Nodes (13): 2. Frontend Routes & Navigation, 4.1 Catalog Explorer (`/catalog`), 4.2 Book Details & Bibliographic Records (`/books/:id`), 4.3 Physical Copies Management, 4.4 Category Taxonomy Management (`/categories`), 4. Feature Workflows, 5. Demo Account Permissions Matrix, 6. Accessibility & Responsiveness (+5 more)

### Community 79 - "PustakHubError"
Cohesion: 0.22
Nodes (8): ForbiddenError, PustakHubError, RateLimitExceededError, Raised when a required backend service (e.g., Redis for auth) is unavailable…, Base exception for all domain-level PustakHub errors., Raised when an action is not permitted for the caller., Raised when request rate limit is exceeded (HTTP 429)., ServiceUnavailableError

### Community 80 - "Phase 14 Implementation Report — Dashboard & Operational Analytics UI"
Cohesion: 0.13
Nodes (14): 10. Database, 11. Demo Data, 12. Documentation, 13. Known Limitations, 14. Final Status, 1. Summary, 2. Dashboard Architecture, 3. Role-Specific Features (+6 more)

### Community 81 - "security.py"
Cohesion: 0.15
Nodes (13): argon2, argon2_exceptions, create_refresh_token(), generate_otp(), datetime, UUID, Security primitives for PustakHub. Provides: - Argon2id password hashing and…, Generate a signed JWT refresh token and its SHA-256 hash. Args: subject: Unique… (+5 more)

### Community 82 - "list_fines"
Cohesion: 0.50
Nodes (8): get_fine(), get_user_fines(), _is_staff_user(), list_fines(), get, Session, UUID, Determine if user holds administrative/staff circulation permissions.

### Community 83 - "Settings"
Cohesion: 0.29
Nodes (7): Central application settings. Values are loaded in order of priority: 1. Actual…, Settings, Settings can be imported and instantiated without errors., test_settings_load(), BaseSettings, 9. Configuration Changes, 5. Due-Date & Fine Policy

### Community 84 - "Role"
Cohesion: 0.13
Nodes (14): Application role (e.g., ADMIN, LIBRARIAN, STUDENT, GUEST). Roles are assigned…, Role, PermissionService, Session, Check if user possesses the specified permission (normalized)., Return the current role-permission mapping matrix from the database., Core permission management and resolution service., Idempotently populate standard system roles, permissions, and association… (+6 more)

### Community 85 - "Running Locally"
Cohesion: 0.40
Nodes (5): 1. Database Setup, 2. Redis Setup, 3. Start Backend API Server, 4. Start Frontend Development Server, Running Locally

### Community 86 - "Technology Stack"
Cohesion: 0.40
Nodes (5): Backend, Frontend, Storage & Security Infrastructure, Technology Stack, Testing & Verification

### Community 87 - "Example Workflows"
Cohesion: 0.50
Nodes (4): 1. Registration & Account Activation, 2. Multi-Factor Authentication (MFA) Setup, 3. MFA Login Challenge, Example Workflows

### Community 88 - "PHASE_02_REPORT — PostgreSQL & Database Foundation"
Cohesion: 0.29
Nodes (6): Database Statistics, Files Created, Files Modified, PHASE_02_REPORT — PostgreSQL & Database Foundation, Phase Objective, Security Notes

### Community 89 - "TestClient"
Cohesion: 0.13
Nodes (15): TestClient, Test successful issue of an available book copy by staff., Verify issue endpoint requires authentication (401) and book:issue permission…, Test validation and conflict errors when issuing unavailable or nonexistent…, Ensure an already borrowed copy cannot be issued to another user (409 Conflict)., Verify on-time return closes the record as RETURNED and produces no fine., Test resource-level authorization for borrowing history: - Student 1 can access…, Test fine querying and IDOR defenses: - Student 1 views own fines - Student 2… (+7 more)

### Community 90 - "db_session"
Cohesion: 0.67
Nodes (3): db_session(), fixture, Provide a database session for seed testing.

### Community 91 - "Environment Configuration"
Cohesion: 0.67
Nodes (3): Backend Configuration, Environment Configuration, Frontend Configuration

### Community 92 - "Installation"
Cohesion: 0.67
Nodes (3): Clone the Repository, Installation, Prerequisites

### Community 93 - "Demo Data"
Cohesion: 0.67
Nodes (3): Demo Data, Seeded Demo Accounts (Local Development Only), Seeding the Database

### Community 94 - "Backend"
Cohesion: 0.20
Nodes (9): Parse CORS_ORIGINS from comma-separated string into a list., configure_logging(), Configure the root logger for PustakHub. Should be called once at application…, 3. Changes Implemented, 7. Architecture Decisions, Backend, Docs, Frontend (+1 more)

### Community 95 - "require_permission"
Cohesion: 0.40
Nodes (4): FastAPI dependency factory enforcing that the authenticated caller has a…, require_permission(), 13. Security Validation, 8. RBAC / Security

### Community 97 - "4. Files Created"
Cohesion: 0.40
Nodes (5): 4. Files Created, Backend — New Files, Docs — New Files, Frontend — New Files, Repository — New Files

### Community 98 - "TestClient"
Cohesion: 0.18
Nodes (11): TestClient, Verify STUDENT role receives 403 Forbidden when attempting catalog mutations., Verify adding, updating, and deleting physical copies, plus book delete…, Verify deleting a Category containing books returns 409 Conflict., Verify GET /api/v1/books supports search, pagination, and category filtering., Verify ADMIN and LIBRARIAN can create, update, and delete book titles., test_book_copy_management_and_deletion_protection(), test_book_crud_lifecycle_admin_and_librarian() (+3 more)

### Community 99 - "2. Architecture & Flows"
Cohesion: 0.40
Nodes (5): 2.1 RBAC Evaluation Flow, 2.2 Permission Resolution Logic, 2.3 Resource-Level Authorization Logic, 2.4 Audit Logging Flow, 2. Architecture & Flows

### Community 100 - "test_health_endpoint_reports_db_healthy"
Cohesion: 0.67
Nodes (3): TestClient, GET /api/health must report database as 'healthy' when DB is connected., test_health_endpoint_reports_db_healthy()

### Community 101 - "Dashboard & Operational Analytics UI Architecture (`docs/dashboard-ui.md`)"
Cohesion: 0.29
Nodes (6): 1. Overview, 2. Persona Views & Information Architecture, 3. Metrics Matrix & Endpoints, 4. Reusable Components, 5. Security & IDOR Defenses, Dashboard & Operational Analytics UI Architecture (`docs/dashboard-ui.md`)

## Knowledge Gaps
- **423 isolated node(s):** `name`, `private`, `version`, `type`, `dev` (+418 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1015 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `Phase 15 Report — User & IAM Administration UI`, `App.jsx`, `Phase 3 Completion Report — PustakHub`, `test_phase6_circulation.py`, `test_phase7_auth_security.py`, `Verification Matrix`, `books/router.py`, `typing`, `seed_demo.py`, `catalog_cleanup`, `PustakHub — Authentication & Identity Architecture (Phase 3 & Phase 7)`, `roles/schemas.py`, `RoleService`, `test_phase4_rbac.py`, `test_phase13_circulation_ui.py`, `test_phase3_auth.py`, `PustakHub — Final Security & Architecture Audit Report`, `test_phase9_security_remediation.py`, `auth/service.py`, `require_any_permission`, `return_book`, `Phase 6 Completion Report — Circulation, Borrowing & Fines`, `borrowing/service.py`, `4. Entities`, `AuditAction`, `test_phase14_dashboard_analytics.py`, `list_fines`, `Role`, `Example Workflows`, `require_permission`?**
  _High betweenness centrality (0.260) - this node is a cross-community bridge._
- **Why does `Key Highlights` connect `App.jsx` to `usePermissions`, `Phase 3 Completion Report — PustakHub`, `User`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Why does `useAuth()` connect `App.jsx` to `usePermissions`, `DashboardPreviewPage.jsx`, `api.js`, `UserDetailsPage.jsx`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Are the 67 inferred relationships involving `User` (e.g. with `get_current_user()` and `get_me()`) actually correct?**
  _`User` has 67 INFERRED edges - model-reasoned connections that need verification._
- **Are the 34 inferred relationships involving `AuditAction` (e.g. with `get_audit_logs()` and `AuditLogOut`) actually correct?**
  _`AuditAction` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `Role` (e.g. with `AuthService` and `PermissionService`) actually correct?**
  _`Role` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `AccountStatus` (e.g. with `get_current_user()` and `AuthService`) actually correct?**
  _`AccountStatus` has 26 INFERRED edges - model-reasoned connections that need verification._