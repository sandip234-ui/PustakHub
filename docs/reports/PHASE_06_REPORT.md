# Phase 6 Completion Report — Circulation, Borrowing & Fines

**PustakHub — Secure Library & Identity Management Platform**  
**Phase:** 06 — Circulation, Borrowing & Fines Management  
**Status:** COMPLETED  
**Date:** September 2026  

---

## 1. Executive Summary

Phase 6 delivers the core operational engine of PustakHub: the **Circulation, Borrowing, and Fines Module**. This module operationalizes physical library inventory through atomic, concurrency-safe borrowing and return workflows, configurable due date policies, automated overdue detection, deterministic fine calculation, and fine-grained resource-level access control.

All circulation operations integrate with Phase 4 RBAC (`book:issue`, `book:return`, `book:view`), enforce row-level locking (`SELECT ... FOR UPDATE`) to prevent double-borrowing race conditions, write immutable audit records (`COPY_ISSUED`, `COPY_RETURNED`, `FINE_ISSUED`), and enforce strict IDOR/BOLA protections between library patrons.

---

## 2. Circulation Architecture

```
User (Member / Staff)
  │
  └── BorrowRecord (Circulation Transaction)
          │
          ├── BookCopy (Physical Unit with Barcode/Identifier)
          │       │
          │       └── Book (Bibliographic Title / ISBN)
          │
          └── Fine (Late Return / Overdue Penalty)
```

The circulation module is organized into two cohesive, loosely coupled domain packages:
1. `backend/app/modules/borrowing`: Handles loan issuing, return check-ins, due date calculations, and borrow history.
2. `backend/app/modules/fines`: Handles querying fine balances and penalties, scoped by member or library administration.

---

## 3. Book Issue Workflow

- **Endpoint:** `POST /api/v1/borrow`
- **Required RBAC Permission:** `book:issue`
- **Workflow & Safeguards:**
  1. Authenticates requester and verifies `book:issue` privilege (Librarian/Admin).
  2. Resolves borrower `User` and validates `account_status == ACTIVE` (rejects `SUSPENDED` / `DEACTIVATED` accounts with `409 Conflict`).
  3. Acquires exclusive row-level lock (`SELECT ... FOR UPDATE`) on target `BookCopy`.
  4. Asserts copy status is `AVAILABLE` (rejects `BORROWED`, `MAINTENANCE`, `LOST` with `409 Conflict`).
  5. Verifies no prior active borrowing record exists for the copy.
  6. Computes `due_at = issued_at + loan_period_days` (using request parameter or default 14 days).
  7. Inserts `BorrowRecord(status=ACTIVE)` and transitions `BookCopy(status=BORROWED)` atomically.
  8. Emits `COPY_ISSUED` audit log entry with IP, User-Agent, and actor ID.
  9. Commits the transaction and returns `201 Created`.

---

## 4. Book Return Workflow & Overdue Fine Calculation

- **Endpoint:** `POST /api/v1/borrow/{borrow_id}/return`
- **Required RBAC Permission:** `book:return`
- **Workflow & Safeguards:**
  1. Authenticates requester and verifies `book:return` privilege.
  2. Acquires row-level lock on `BorrowRecord` and verifies `status == ACTIVE` and `returned_at IS NULL` (rejects duplicate returns with `409 Conflict`).
  3. Acquires row-level lock on associated `BookCopy`.
  4. Sets `returned_at = now()` (or client timestamp if supplied).
  5. Determines overdue condition: if `returned_at > due_at`:
     - Calculates overdue days: $\max(1, \lceil \Delta\text{seconds} / 86400 \rceil)$.
     - Computes fine amount: $\text{overdue\_days} \times \text{DAILY\_FINE\_RATE}$.
     - Creates `Fine` record (`reason=OVERDUE`, `status=PENDING`).
     - Emits `FINE_ISSUED` audit log entry.
  6. Transitions `BookCopy(status=AVAILABLE)` and `BorrowRecord(status=RETURNED)`.
  7. Emits `COPY_RETURNED` audit log entry.
  8. Commits the database transaction atomically and returns `200 OK`.

---

## 5. Due-Date & Fine Policy

Configured centrally in `app.core.config.Settings`:
- `DEFAULT_LOAN_PERIOD_DAYS = 14`: Default lending window.
- `DAILY_FINE_RATE = 2.00`: Daily overdue fine rate ($2.00/day).
- `MAX_ACTIVE_BORROWS_PER_USER = 5`: Limit of simultaneous active loans.
- Deterministic fine calculations guarantee zero negative fines, zero fines on on-time returns, and idempotent penalty records.

---

## 6. Borrowing & Fine History (IDOR / BOLA Defenses)

Endpoints provided:
- `GET /api/v1/borrowings`: Paginated list of borrowings. Students only see their own records; staff can inspect all or filter by member.
- `GET /api/v1/borrowings/{borrow_id}`: Single borrowing details. Students forbidden from accessing records belonging to other users (`403 Forbidden`).
- `GET /api/v1/users/{user_id}/borrowings`: User-scoped loan history with pagination and status filters.
- `GET /api/v1/fines`: Paginated list of fine penalties.
- `GET /api/v1/fines/{fine_id}`: Single fine penalty details with ownership verification.
- `GET /api/v1/users/{user_id}/fines`: User-scoped fine history.

---

## 7. Concurrency / Transaction Strategy

- **Pessimistic Locking (`SELECT ... FOR UPDATE`):**
  Applied to `BookCopy` during issue and both `BorrowRecord` and `BookCopy` during return.
- **Race Condition Immunity:**
  If two concurrent requests attempt to issue the same physical copy, the second request is serialized behind the first's row lock. Upon lock acquisition, the second request detects `status = BORROWED` and terminates cleanly with `409 Conflict`.
- **Database Integrity:**
  Zero or one active `BorrowRecord` per `BookCopy` invariant is strictly preserved.

---

## 8. Audit Logging

Circulation events are logged to the immutable `audit_logs` table via `AuditService`:
- `COPY_ISSUED`: Triggered on book checkout.
- `COPY_RETURNED`: Triggered on book check-in.
- `FINE_ISSUED`: Triggered on overdue fine generation.
- **Zero Secrets Recorded:** IP and User-Agent are recorded; sensitive credentials and tokens are strictly excluded.

---

## 9. Database & Migration Changes

The Phase 2 schema migration (`0438258645fa`) already contained complete schema definitions for `borrow_records`, `fines`, `book_copies`, `books`, `users`, and `audit_logs`.
- **No new Alembic migration was required.**
- **No `Base.metadata.create_all()` was executed.**
- Database remains clean at Alembic revision `0438258645fa (head)`.

---

## 10. Files Created

1. `backend/app/modules/borrowing/__init__.py`: Borrowing module public exports.
2. `backend/app/modules/borrowing/schemas.py`: Pydantic models (`BorrowIssueRequest`, `BorrowReturnRequest`, `BorrowRecordOut`, `BorrowRecordListResponse`).
3. `backend/app/modules/borrowing/service.py`: `BorrowingService` encapsulating issue, return, row-level locking, fine calculation, and queries.
4. `backend/app/modules/borrowing/router.py`: HTTP endpoints for `/api/v1/borrow`, `/api/v1/borrowings`, `/api/v1/users/{user_id}/borrowings`.
5. `backend/app/modules/fines/__init__.py`: Fines module public exports.
6. `backend/app/modules/fines/schemas.py`: Pydantic models (`FineOut`, `FineListResponse`).
7. `backend/app/modules/fines/service.py`: `FineService` for fine record lookups and filtered listings.
8. `backend/app/modules/fines/router.py`: HTTP endpoints for `/api/v1/fines`, `/api/v1/fines/{fine_id}`, `/api/v1/users/{user_id}/fines`.
9. `backend/tests/test_phase6_circulation.py`: 8 comprehensive test scenarios covering all circulation features and edge cases.
10. `frontend/src/services/circulation.service.js`: Frontend API client for circulation operations.
11. `docs/circulation.md`: Comprehensive circulation architecture and workflow specification.
12. `docs/reports/PHASE_06_REPORT.md`: This completion report.

---

## 11. Files Modified

1. `backend/app/core/config.py`: Added `DEFAULT_LOAN_PERIOD_DAYS`, `DAILY_FINE_RATE`, and `MAX_ACTIVE_BORROWS_PER_USER` settings.
2. `backend/app/main.py`: Mounted `borrowing_router` and `fines_router` under `/api/v1`.

---

## 12. Test Results

Exact pytest execution result:

```text
======================== 87 passed, 1 warning in 6.15s =========================
```

- **Phase 1 Foundation:** 11 tests passing
- **Phase 2 Database:** 15 tests passing
- **Phase 3 Auth & JWT:** 18 tests passing
- **Phase 4 RBAC & Audit:** 24 tests passing
- **Phase 5 Catalog:** 11 tests passing
- **Phase 6 Circulation & Fines:** 8 tests passing
- **Total:** 87 tests passing (100% pass rate)

---

## 13. Verification

- **Pytest Suite:** 87 passed (`./venv/bin/pytest tests/ -v`).
- **Alembic State:** Revision `0438258645fa (head)`.
- **OpenAPI Schema:** Verified mounting of `/borrow`, `/borrow/{borrow_id}/return`, `/borrowings`, `/borrowings/{borrow_id}`, `/users/{user_id}/borrowings`, `/fines`, `/fines/{fine_id}`, `/users/{user_id}/fines`.
- **Forbidden Methods:** Checked `grep -R "create_all" app/` — zero calls found.
- **Security Check:** Verified IDOR prevention, row-level locking, fine calculation determinism, and absence of secrets in audit logs.

---

## 14. Deferred Work (Out of Scope for Phase 6)

The following capabilities are reserved for future phases:
- Online fine payments and payment gateway integration (Stripe/PayPal)
- Password reset, MFA, and account recovery workflows (Phase 7)
- Google OAuth & external identity providers
- Redis token bucket rate limiting on API routes
- Automated email loan reminders and overdue notices
- Hold requests and book reservation queues
