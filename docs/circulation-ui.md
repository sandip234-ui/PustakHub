# Circulation & Borrowing UI Architecture (`docs/circulation-ui.md`)

## 1. Overview

The **Circulation & Borrowing UI** delivers a robust, accessible, and reactive frontend workflow on top of PustakHub's existing backend loan and fine management engines (`backend/app/modules/borrowing/` and `backend/app/modules/fines/`).

The module supports two core personas:
1. **Patrons / Students (`STUDENT`)**: Personal dashboard for viewing active loans, overdue items, borrowing history, fine assessments, and due dates.
2. **Library Staff (`ADMIN`, `LIBRARIAN`)**: Operational interface for issuing available book copies to registered members, processing returns, reviewing global loan ledgers with multi-dimensional filtering, inspecting borrower profiles, and auditing fines.

---

## 2. Route Map

All circulation routes are protected by `<ProtectedRoute>` and integrated into the global navigation layout.

| Route | Page Component | Allowed Roles | Description |
| :--- | :--- | :--- | :--- |
| `/borrowings` | [BorrowingsPage.jsx](file:///Users/sandipbiswal/Desktop/PustakHub/frontend/src/pages/BorrowingsPage.jsx) | `STUDENT`, `LIBRARIAN`, `ADMIN` | Borrowing dashboard. Shows student's own loans or global library loans for staff. Supports filtering by tab (`ALL`, `ACTIVE`, `OVERDUE`, `RETURNED`), keyword search, and pagination. |
| `/borrowings/:id` | [BorrowingDetailsPage.jsx](file:///Users/sandipbiswal/Desktop/PustakHub/frontend/src/pages/BorrowingDetailsPage.jsx) | `STUDENT`, `LIBRARIAN`, `ADMIN` | Deep-dive loan record view displaying book meta, barcode, loan period, return status, borrower contact, and linked fine records. |
| `/fines` | [FinesPage.jsx](file:///Users/sandipbiswal/Desktop/PustakHub/frontend/src/pages/FinesPage.jsx) | `STUDENT`, `LIBRARIAN`, `ADMIN` | Fines ledger displaying financial liabilities, fine calculation breakdown, payment status (`PENDING`, `PAID`, `WAIVED`), and links to original borrowing records. |

---

## 3. Component Architecture

```text
frontend/src/
├── components/
│   ├── IssueBookModal.jsx          # Reusable modal for member selection, copy selection & loan duration
│   ├── ConfirmDialog.jsx           # Accessible confirmation modal for processing book returns
│   ├── PermissionGate.jsx          # Conditional DOM rendering based on user roles and permissions
│   ├── Navbar.jsx                  # Top & mobile navigation with dynamic Borrowings & Fines links
│   └── Toast.jsx                   # Feedback notifications (success, conflict 409, errors)
├── pages/
│   ├── BorrowingsPage.jsx          # Loan ledger with stats cards, filter tabs, search, and return actions
│   ├── BorrowingDetailsPage.jsx    # Complete loan record breakdown with return action and fine details
│   ├── FinesPage.jsx               # Fines ledger with status tabs, balance metrics, and loan references
│   ├── BookDetailsPage.jsx         # Catalog integration with 'Issue This Book' & copy-level 'Issue' buttons
│   └── DashboardPreviewPage.jsx    # Quick cards directing users to Loans and Fines ledgers
├── services/
│   └── circulation.service.js      # Axios client for /borrowings, /borrow, /fines, and /users endpoints
└── hooks/
    └── usePermissions.js           # RBAC helper flags (canIssueBook, canReturnBook, canManageCatalog)
```

---

## 4. Key Workflows

### 4.1 Issue / Checkout Workflow
1. **Trigger**: Staff clicks **"Issue Book"** on `/borrowings` or **"Issue This Book"** on `/books/:id`.
2. **Member Selection**: Type-ahead search against `GET /api/v1/users` (name, email, member ID).
3. **Copy Selection**: If not pre-selected from book details, staff selects an available physical copy with an active barcode. Unavailable copies (`BORROWED`, `LOST`, `MAINTENANCE`) are non-selectable.
4. **Loan Duration**: Configured loan duration (1–90 days, default 14 days) displays calculated due date based on current client/server time.
5. **Submission**: Staff submits `POST /api/v1/borrow` with payload `{ "user_id": "...", "book_copy_id": "...", "loan_days": 14 }`.
6. **Concurrency / Conflict Handling**: If another staff member issues the copy simultaneously, backend returns `409 Conflict`. The UI traps the `409` and displays an explicit toast: *"This copy is no longer available. Refresh the inventory and choose another copy."*
7. **State Refresh**: Inventory counts and active borrowing lists refresh reactively.

### 4.2 Return Workflow
1. **Trigger**: Staff clicks **"Return Book"** on `/borrowings` row or `/borrowings/:id` action bar.
2. **Confirmation**: An accessible [ConfirmDialog](file:///Users/sandipbiswal/Desktop/PustakHub/frontend/src/components/ConfirmDialog.jsx) modal prompts confirmation before modifying database state.
3. **Submission**: Staff sends `POST /api/v1/borrow/{id}/return`.
4. **Fine Assessment**: The backend calculates whether the loan is overdue, records the return date, updates copy status to `AVAILABLE`, and returns any assessed fine in the response.
5. **Feedback**: If overdue, a warning toast alerts: *"Book returned. Overdue fine assessed: $X.XX"*. If on time: *"Book returned successfully."*

### 4.3 Fines Ledger & Transparency
1. Patrons and staff access `/fines` to review outstanding balances and historical settlements.
2. Status tabs filter by `ALL`, `PENDING` (unpaid fines), `PAID`, and `WAIVED`.
3. Cards summarize total fine liability, total settled, and unpaid balances.

---

## 5. Security & RBAC Matrix

| Role | View Own Loans | View All Loans | Issue Copy | Return Copy | View Own Fines | View All Fines |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`STUDENT`** | Yes (Scoping) | No (`403`) | No (`403`) | No (`403`) | Yes (Scoping) | No (`403`) |
| **`LIBRARIAN`** | Yes | Yes | Yes | Yes | Yes | Yes |
| **`ADMIN`** | Yes | Yes | Yes | Yes | Yes | Yes |

- **Zero Client-Side Trust**: Client-side visibility (`PermissionGate`, `usePermissions`) controls UI display only; backend dependencies (`require_permission("borrow:create")`, `require_permission("borrow:return")`, `get_current_active_user`) strictly enforce authorization and prevent IDOR exploits.
- **Strict Read-Only Fines**: The fines UI mirrors the backend state without fake frontend payment endpoints.

---

## 6. Accessibility & Responsiveness

- **Semantic HTML & Badges**: Distinct visual badges for `ACTIVE` (blue), `OVERDUE` (red), `RETURNED` (emerald), with accompanying icons (`Clock`, `AlertTriangle`, `CheckCircle2`) so status is never conveyed by color alone.
- **Responsive Layout**: Data tables feature horizontal scroll containers on mobile/tablet and card summaries.
- **Focus & Keyboard Navigation**: Modals feature auto-focus, accessible backdrop close, escape handling, and keyboard tab trapping.
