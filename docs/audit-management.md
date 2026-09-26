# PustakHub — Audit Management & Forensic Logging Architecture

## 1. Overview & Objectives

The **PustakHub Audit Management Console** provides a dedicated, read-only interface for authorized administrators and staff (`audit_log:view` permission) to inspect, filter, correlate, and investigate security and operational events across the platform.

### Core Tenets
1. **Immutable Evidence**: Audit records are strictly read-only append-only historical records. The platform provides no capabilities to edit, update, delete, or truncate audit records from API endpoints or frontend controls.
2. **Zero Secret Leakage**: Cryptographic secrets, plaintext/hashed passwords, MFA TOTP secrets, recovery code hashes, session tokens, and refresh tokens are excluded at the persistence and serialization layers.
3. **Correlation by Request ID & Resource**: Operational actions trace actor user IDs, resource IDs, action types, network client IP addresses, and user-agent fingerprints.
4. **Independent Backend Authorization**: Access to audit logs requires the `audit_log:view` permission (held by `ADMIN` and `LIBRARIAN` roles), enforced at the API gateway layer via RBAC dependencies.

---

## 2. Architecture & Data Model

### Database Entity: `audit_logs`
The `AuditLog` table stores structured, timestamped audit events:

| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | Primary key identifier (v4 UUID) |
| `user_id` | `UUID` | Yes | Foreign key to `users.id` (NULL for unauthenticated events) |
| `action` | `Enum (AuditAction)` | No | Canonical event identifier (e.g. `LOGIN_SUCCESS`, `USER_DEACTIVATED`) |
| `resource_type`| `String` | Yes | Target resource entity (e.g. `User`, `Book`, `BookCopy`, `BorrowRecord`) |
| `resource_id` | `String` | Yes | Identifier of target resource |
| `status` | `Enum (AuditStatus)` | No | Outcome status: `SUCCESS`, `FAILURE`, `PARTIAL` |
| `timestamp` | `DateTime (UTC)` | No | Auto-assigned UTC timestamp |
| `ip_address` | `String` | Yes | Client IPv4 or IPv6 address |
| `user_agent` | `String` | Yes | Client User-Agent string (truncated to max 500 chars) |

---

## 3. Backend Audit Endpoints

All endpoints are mounted under `/api/v1/audit` and require authentication + `audit_log:view` permission.

### 1. `GET /api/v1/audit/logs`
Queries audit logs with multi-parameter filtering and server-side pagination.

**Query Parameters**:
- `search` (string): Searches case-insensitively across `resource_type`, `resource_id`, `ip_address`, actor `user.full_name`, and actor `user.email`.
- `user_id` (UUID): Filters records by actor UUID.
- `action` (string): Filters by canonical `AuditAction` enum name.
- `status` (string): Filters by outcome `AuditStatus` (`SUCCESS`, `FAILURE`, `PARTIAL`).
- `resource_type` (string): Filters by target resource entity.
- `start_time` (ISO-8601 UTC datetime): Beginning of time range filter.
- `end_time` (ISO-8601 UTC datetime): End of time range filter.
- `page` (int, default: 1): Page number.
- `page_size` (int, default: 50, max: 200): Items per page.

**Response Schema (`AuditLogListResponse`)**:
```json
{
  "total": 128,
  "page": 1,
  "page_size": 50,
  "items": [
    {
      "id": "e544e38c-bdeb-43a8-a81a-66fc5e2e6409",
      "user_id": "041a3b07-499e-4475-b1ba-b33fb2103fdc",
      "user_email": "admin@pustakhub.local",
      "user_name": "System Administrator",
      "action": "LOGIN_SUCCESS",
      "resource_type": "User",
      "resource_id": "041a3b07-499e-4475-b1ba-b33fb2103fdc",
      "status": "SUCCESS",
      "timestamp": "2026-09-24T18:00:00Z",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0 PustakHub-WebClient"
    }
  ]
}
```

### 2. `GET /api/v1/audit/logs/{audit_id}`
Retrieves full forensic details of a single audit log entry by UUID.
- Returns `200 OK` with `AuditLogOut` if found.
- Returns `404 Not Found` if the log ID does not exist.
- Returns `422 Unprocessable Entity` if the UUID format is invalid.

### 3. `GET /api/v1/audit/actions`
Retrieves all canonical audit actions grouped into functional categories for filter selectors and UI badges.

---

## 4. Frontend Audit Management Console

### Route: `/audit`
- **Protected Route**: Guarded by `<ProtectedRoute allowedRoles={["ADMIN", "LIBRARIAN"]} />` and verifies `audit_log:view` permission.
- **Navigation**: Visible in main desktop navbar and mobile drawer only for users with appropriate permissions.
- **Dashboard Integration**: The Recent Audit Activity stream on `/dashboard` links directly to `/audit`.

### Key UI Features
1. **Summary Metrics**: High-level counters displaying Total Logs, Successful Events, Failed Attempts, and Unique Active Actors.
2. **Multi-Parameter Search & Filter Bar**:
   - Debounced keyword search input (filters actors, IPs, resources).
   - Event category / action type dropdown.
   - Outcome status selector (`All`, `SUCCESS`, `FAILURE`, `PARTIAL`).
   - Resource type filter.
   - Time range date pickers (Start Date, End Date).
   - "Reset Filters" action button.
3. **Responsive Audit Table & Mobile Cards**:
   - Desktop: Tabular presentation showing Timestamp, Event Type, Actor, Target Resource, Outcome Status, IP Address, and View Action.
   - Mobile / Tablet: Clean condensed card view preserving full metadata visibility.
4. **Forensic Event Detail Modal (`AuditDetailModal`)**:
   - Displays event UUID with click-to-copy convenience.
   - Formatted actor identification (Name, Email, or Unauthenticated).
   - Categorized Action Badge with functional color coding.
   - Target Resource details.
   - Client Network Context (IP Address, User-Agent).
   - Raw sanitized context viewer.
5. **Server-Side Pagination**:
   - Displays current page range and total matching records.
   - Previous and Next controls with boundary disabling and loading indicators.

---

## 5. Security & Immutability Guarantees

1. **Strict Read-Only Enforcement**:
   - Backend exposes NO `POST`, `PUT`, `PATCH`, or `DELETE` endpoints on `/api/v1/audit/logs`.
   - Frontend contains no modification, deletion, or manual insertion UI.
2. **Authentication & RBAC Defense**:
   - Unauthorized roles (`STUDENT`, `GUEST`, unauthenticated users) receive `403 Forbidden` or `401 Unauthorized` on all audit endpoints.
   - Direct API requests cannot bypass permission enforcement.
3. **Sensitive Data Redaction**:
   - `AuditService._sanitize_field` rejects and redacts any strings matching token or hash signatures (`$argon2id$`, `bearer `, tokens).
   - Serialized schemas omit sensitive user attributes.
4. **Timezone Uniformity**:
   - All timestamps are generated and stored in UTC and rendered in the operator's localized format.
