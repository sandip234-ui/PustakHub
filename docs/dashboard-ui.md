# Dashboard & Operational Analytics UI Architecture (`docs/dashboard-ui.md`)

## 1. Overview

The **Dashboard & Operational Analytics UI** transforms PustakHub's primary post-authentication view (`/dashboard`) into an adaptive, role-aware operational command center.

Instead of generic placeholder statistics, the dashboard dynamically queries live backend data sources and adjusts its layout, metrics, alerts, and quick actions based on the authenticated persona (`ADMIN`, `LIBRARIAN`, `STUDENT`, `GUEST`).

---

## 2. Persona Views & Information Architecture

```text
                                ┌────────────────────────────────────┐
                                │   Authenticated User (/dashboard)  │
                                └─────────────────┬──────────────────┘
                                                  │
                 ┌────────────────────────────────┼────────────────────────────────┐
                 ▼                                ▼                                ▼
       ┌───────────────────┐            ┌───────────────────┐            ┌───────────────────┐
       │       ADMIN       │            │     LIBRARIAN     │            │      STUDENT      │
       └─────────┬─────────┘            └─────────┬─────────┘            └─────────┬─────────┘
                 │                                │                                │
       ├─ Global Catalog Metrics        ├─ Catalog Holdings              ├─ My Active Loans (Personal)
       ├─ Circulation Totals            ├─ Active Circulation            ├─ Overdue Alerts (Personal)
       ├─ Overdue Items Alert           ├─ Overdue Items Alert           ├─ Borrowing History
       ├─ Pending Fines Count           ├─ Pending Fines Count           ├─ My Fines ($ / Unpaid)
       ├─ Registered Users Count        ├─ Issue Book Modal              ├─ Personal Loan Cards
       ├─ PostgreSQL Audit Trail        └─ Recent Transactions           └─ Catalog Quick Search
       └─ Full Management Actions
```

---

## 3. Metrics Matrix & Endpoints

All operational statistics are derived from existing backend endpoints without creating redundant analytical routes or altering database tables:

| Persona | Metric Displayed | Backend API Endpoint | Scoping / Protection |
| :--- | :--- | :--- | :--- |
| **Staff / Admin** | Catalog Books | `GET /api/v1/books?page=1&page_size=1` (`total`) | Requires `book:view` |
| **Staff / Admin** | Active Loans | `GET /api/v1/borrowings?page=1&page_size=1&status=ACTIVE` | Staff global view |
| **Staff / Admin** | Overdue Loans | `GET /api/v1/borrowings?page=1&page_size=1&status=OVERDUE` | Staff global view |
| **Staff / Admin** | Pending Fines | `GET /api/v1/fines?page=1&page_size=1&status=PENDING` | Staff global view |
| **Admin** | Registered Users | `GET /api/v1/users?page=1&page_size=1` (`total`) | Requires `user:view` |
| **Admin** | Taxonomy Categories | `GET /api/v1/categories?page=1&page_size=100` | Requires `book:view` |
| **Admin** | System Audit Logs | `GET /api/v1/audit/logs?page=1&page_size=5` | Requires `audit_log:view` |
| **Student** | My Active Loans | `GET /api/v1/borrowings?page=1&page_size=1&status=ACTIVE` | Automatically scoped to `current_user.id` |
| **Student** | My Overdue Books | `GET /api/v1/borrowings?page=1&page_size=1&status=OVERDUE` | Automatically scoped to `current_user.id` |
| **Student** | My Borrowing History | `GET /api/v1/borrowings?page=1&page_size=1` | Automatically scoped to `current_user.id` |
| **Student** | My Pending Fines | `GET /api/v1/fines?page=1&page_size=1&status=PENDING` | Automatically scoped to `current_user.id` |

---

## 4. Reusable Components

- **[DashboardStatCard.jsx](file:///Users/sandipbiswal/Desktop/PustakHub/frontend/src/components/DashboardStatCard.jsx)**: Reusable metric card with loading pulse skeletons, semantic status themes (`indigo`, `emerald`, `amber`, `rose`, `purple`, `blue`), accessible screen-reader labels, and optional drill-down navigation links.
- **[QuickActionCard.jsx](file:///Users/sandipbiswal/Desktop/PustakHub/frontend/src/components/QuickActionCard.jsx)**: Role-gated action shortcut card supporting direct client-side routing or modal triggering (`onClick`).
- **[IssueBookModal.jsx](file:///Users/sandipbiswal/Desktop/PustakHub/frontend/src/components/IssueBookModal.jsx)**: Embedded checkout workflow allowing staff to issue copies directly from the dashboard.

---

## 5. Security & IDOR Defenses

1. **Strict Backend Scoping**: When a student queries `GET /api/v1/borrowings` or `GET /api/v1/fines`, the backend automatically overrides any provided filters to `current_user.id`.
2. **Access Control on Sensitive Endpoints**: Attempting to query `/api/v1/users` or `/api/v1/audit/logs` as a student or librarian returns `403 Forbidden`.
3. **Zero Sensitive Leakage**: Audit log summaries render only high-level metadata (`action`, `resource_type`, `status`, `timestamp`) and never leak tokens, hashes, or payload bodies.
