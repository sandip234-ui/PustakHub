# Real-Time Update Architecture & Specification

## 1. Executive Summary & Objective

PustakHub Phase 17 implements a high-performance, security-hardened **real-time update layer** using authenticated WebSockets and Redis Pub/Sub backplane synchronization.

The real-time subsystem solves operational latency across the library platform by delivering instantaneous notifications for catalog modifications, circulation events (issue/return), fine assessments, user IAM mutations, and audit activity.

---

## 2. Core Architectural Principles

### 2.1 REST as the Authoritative Source of Truth
The real-time layer is strictly a **notification and invalidation transport**. It is **never** the source of truth or state storage.
- All persistent operations originate in standard REST endpoints, execute through transactional business services, and commit to PostgreSQL.
- Real-time events contain only minimal resource metadata (`type`, `timestamp`, `resource_type`, `resource_id`, `target_user_id`, `request_id`).
- When a client receives a real-time event, or recovers from a disconnect, it invalidates cached query state and performs an authoritative REST `GET` request.
- Dropped, delayed, or missed WebSocket packets **never** corrupt client state because REST synchronization immediately restores accuracy.

```
       Existing REST APIs
              │
              ▼
        Database State (PostgreSQL)
              │
              ▼
       Domain Operation Execution
              │
              ├──────────────► AuditLog Recording
              │
              ▼
       Event Publisher (`publish_realtime_event`)
              │
              ├──────────────► Redis Pub/Sub (`pustakhub:realtime:events`)
              ▼
    WebSocket Connection Manager (Asyncio)
              │
    ┌─────────┼─────────┐ (RBAC & Scoped Filtering)
    ▼         ▼         ▼
Dashboard   Audit   Circulation / Fines / Catalog
    │         │         │
    └─────────┼─────────┘
              ▼
        React UI Query Invalidation / REST Fetch
```

---

## 3. Real-Time Transport: WebSockets & Redis Pub/Sub

### 3.1 Transport Selection: WebSocket (`ws://` / `wss://`)
WebSocket was chosen over Server-Sent Events (SSE) and heavy libraries (Socket.IO) because:
1. **Full-Duplex Heartbeat:** Native ping/pong framing enables continuous connection health checks and rapid stale-connection reclamation without HTTP connection overhead.
2. **FastAPI Native Integration:** FastAPI/Starlette provides robust, standards-compliant ASGI WebSocket endpoints with zero external wrapper bloat.
3. **Cross-Tab & Low-Latency Efficiency:** Maintains a single lightweight multiplexed stream per client session for all operational domain notifications.

### 3.2 Multi-Worker Backplane: Redis Pub/Sub
- In production with multiple Uvicorn worker processes, clients connect to different worker nodes.
- When an event is published on Worker A, `publish_realtime_event` broadcasts the serialized JSON event to the Redis channel `pustakhub:realtime:events`.
- An asynchronous background listener (`RedisRealtimeSubscriber`) on every worker consumes messages from Redis and fans out delivery to locally connected WebSockets via `ConnectionManager`.
- **Fault-Tolerant Fallback:** If Redis is unavailable or disabled, the publisher immediately falls back to in-process dispatch, ensuring local connections still receive updates without throwing 500 errors to REST callers.

---

## 4. Centralized Event Model & Taxonomy

Events are strongly typed via Python `Enum` (`RealtimeEventType`) and validated with Pydantic v2 schemas (`RealtimeEvent`).

### 4.1 Canonical Event Taxonomy
| Domain | Event Type | Trigger Condition |
| :--- | :--- | :--- |
| **Catalog** | `CATEGORY_CREATED`, `CATEGORY_UPDATED`, `CATEGORY_DELETED` | Category taxonomy changes |
| **Catalog** | `BOOK_CREATED`, `BOOK_UPDATED`, `BOOK_DELETED` | Book title, author, metadata updates |
| **Catalog** | `COPY_CREATED`, `COPY_UPDATED`, `COPY_DELETED` | Copy inventory or condition adjustments |
| **Circulation** | `COPY_ISSUED` | Book copy checked out to a borrower |
| **Circulation** | `COPY_RETURNED` | Book copy returned to library |
| **Circulation** | `FINE_ISSUED` | Overdue penalty or damaged item fine assessed |
| **Circulation** | `FINE_PAID`, `FINE_WAIVED` | Fine payment settlement or administrative waiver |
| **IAM** | `USER_CREATED`, `USER_UPDATED` | Account registration or profile changes |
| **IAM** | `USER_SUSPENDED`, `USER_DEACTIVATED` | Administrative account lockdown |
| **IAM** | `ROLE_ASSIGNED`, `ROLE_REVOKED` | RBAC role privilege mutations |
| **Audit** | `AUDIT_EVENT_CREATED` | Immutable security log record added |
| **System** | `SYSTEM_NOTIFICATION`, `SYSTEM_RECONNECTED` | Connectivity / maintenance alerts |

---

## 5. Event Payload Security & Data Sanitization

### 5.1 Strict Secret Exclusion Guarantee
Real-time payloads are strictly scrubbed at multiple pipeline stages. Under no circumstances are credentials or sensitive keys broadcast. The publisher explicitly filters:
- Passwords and Argon2id password hashes
- JWT access tokens and refresh tokens
- TOTP MFA secrets and encryption keys
- Backup/recovery codes and password reset tokens
- Raw internal database ORM model dumps

### 5.2 Schema Definition
```json
{
  "type": "COPY_ISSUED",
  "timestamp": "2026-09-24T18:30:00.000000Z",
  "resource_type": "borrow",
  "resource_id": "7b8f9e12-3456-7890-abcd-ef1234567890",
  "target_user_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "data": {
    "book_title": "Clean Architecture",
    "copy_identifier": "PUSTAK-00142-01",
    "due_at": "2026-10-08T18:30:00Z"
  },
  "request_id": "req-987654321"
}
```

---

## 6. Authentication & Security Boundary

The WebSocket endpoint `WS /api/v1/realtime/ws` is protected under the platform security boundary.

### 6.1 Handshake Authentication
1. **Token Extraction:** The WebSocket client supplies the JWT access token in the query parameters (`?token=<jwt_access_token>`) or `Authorization: Bearer <jwt_access_token>` header.
2. **Signature & Expiration Verification:** Decoded and validated with `verify_token` against the application secret key and algorithm.
3. **Database Identity Verification:** The subject user is queried from PostgreSQL to verify:
   - Account existence
   - Account status is `ACTIVE` (locks out `SUSPENDED`, `DEACTIVATED`, or `PENDING` accounts immediately with code `1008 Policy Violation`).
4. **Role & Permission Resolution:** The user's active roles and permissions are resolved from the database and bound to the in-memory connection object.

---

## 7. Authorization & Scoped Fan-Out

Delivery is determined entirely by the server-side `ConnectionManager`. Clients cannot craft arbitrary subscription scopes.

```
                  Published Event
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
   Audit Event      IAM Event     Circulation Event   Catalog Event
   (Requires       (Admin/Staff   (Staff or Target    (All Authenticated
  audit_log:view)   or Target)      User Only)             Users)
```

1. **Audit Logs (`AUDIT_EVENT_CREATED`):** Broadcast **only** to connections possessing `audit_log:view` permission or `ADMIN` role.
2. **IAM Events (`USER_*`, `ROLE_*`):** Delivered to administrators with `user:view` or `ADMIN`, and to the specific targeted user whose account status changed.
3. **Circulation Events (`COPY_ISSUED`, `COPY_RETURNED`, `FINE_*`):**
   - Delivered to staff (`book:issue`, `book:return`, `ADMIN`, `LIBRARIAN`) for operational tracking.
   - Delivered to the specific student/borrower matching `target_user_id`.
   - **Isolation Guarantee:** Student A cannot receive Student B's borrowing or fine notifications.
4. **Catalog Events (`BOOK_*`, `COPY_*`, `CATEGORY_*`):** Visible to all authenticated members for live search and availability updates.

---

## 8. Connection Lifecycle, Heartbeat & Reconnection

### 8.1 Heartbeat Protocol
- The server periodically responds to client ping frames with JSON `{"type": "PONG", "timestamp": "..."}` messages.
- The frontend `RealtimeClient` sends a heartbeat ping every 25 seconds.
- Stale or unresponsive sockets are automatically closed and evicted from memory.

### 8.2 Client Bounded Reconnection Strategy
The frontend client implements exponential backoff with jitter to prevent thundering-herd issues on backend restarts:
$$\text{delay} = \min(\text{baseDelay} \times 2^{\text{retryCount}} + \text{jitter}, 30000\text{ms})$$
- Maximum retry limit: 10 attempts.
- On successful reconnection, the client emits `SYSTEM_RECONNECTED` to all subscribed React pages, triggering an automatic REST resynchronization.

---

## 9. Failure Mode & Resilience

Real-time delivery is non-critical to core platform functionality:
1. **WebSocket Outage:** If the WebSocket server is unavailable, the UI gracefully switches to `Offline` mode. Users can continue borrowing, returning, searching, managing users, and paying fines without interruption.
2. **Redis Outage:** If the Redis Pub/Sub broker disconnects, REST operations continue uninterrupted; real-time notifications degrade to single-process in-memory distribution.
3. **Network Hiccups:** When connectivity resumes, the client reconnects and refreshes authoritative REST state.

---

## 10. Summary of Subsystem Components

- **Backend:**
  - `backend/app/modules/realtime/events.py`: Canonical event enum and Pydantic schemas.
  - `backend/app/modules/realtime/manager.py`: RBAC-aware connection manager and memory registry.
  - `backend/app/modules/realtime/publisher.py`: Sanitized event publisher with Redis Pub/Sub broadcast.
  - `backend/app/modules/realtime/redis_subscriber.py`: Background Redis subscriber for multi-worker support.
  - `backend/app/modules/realtime/router.py`: WebSocket route (`/api/v1/realtime/ws`) and status endpoint.
- **Frontend:**
  - `frontend/src/services/realtime.service.js`: Singleton WebSocket client with reconnect and heartbeat loops.
  - `frontend/src/context/RealtimeContext.jsx`: React provider and subscription context.
  - `frontend/src/components/RealtimeStatusBadge.jsx`: Real-time status badge (`Live`, `Connecting`, `Reconnecting`, `Offline`).
