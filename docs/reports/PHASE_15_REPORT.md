# Phase 15 Report — User & IAM Administration UI

## 1. Phase Objective
The objective of Phase 15 was to implement a complete, secure **User & Identity and Access Management (IAM) Administration UI** for `ADMIN` users on top of PustakHub's existing backend RBAC, IAM, and audit logging foundations. The implementation provides administrative user oversight, search and multi-attribute filtering, status lifecycle transitions, role granting and revocation, effective dynamic permission resolution, and defensive self-lockout protections.

---

## 2. Existing Implementation Inspected
Prior to modifications, the repository was inspected thoroughly:
- **Backend IAM & RBAC:** Inspected `app/modules/users/router.py`, `app/modules/roles/router.py`, `app/modules/permissions/service.py`, `app/models/user.py`, `app/models/role.py`, `app/models/permission.py`, `app/models/audit_log.py`, and `app/modules/permissions/constants.py`.
- **Frontend Architecture:** Inspected `frontend/src/context/AuthContext.jsx`, `frontend/src/hooks/usePermissions.js`, `frontend/src/components/ProtectedRoute.jsx`, `frontend/src/components/PermissionGate.jsx`, `frontend/src/components/Navbar.jsx`, `frontend/src/pages/DashboardPreviewPage.jsx`, and existing services (`circulation.service.js`, `catalog.service.js`, `audit.service.js`).
- **Reports & Architecture Docs:** Inspected `docs/architecture.md`, `docs/rbac.md`, `docs/authentication.md`, and Phase 04 through Phase 14 completion reports.

---

## 3. Backend Changes
Small, secure, backwards-compatible additions were made to support Phase 15:
1. **`backend/app/modules/users/schemas.py`:**
   - Created `UserStatusUpdateRequest` schema validating `account_status: AccountStatus`.
2. **`backend/app/modules/users/router.py`:**
   - Enhanced `GET /api/v1/users` with optional query parameters: `search`, `account_status` (and `status` alias), and `role`.
   - Implemented `PATCH /api/v1/users/{user_id}/status` allowing administrators with `user:update` permission to transition accounts between `ACTIVE`, `SUSPENDED`, and `DEACTIVATED`. Includes server-side self-lockout enforcement (`current_user.id == target_user.id and status != ACTIVE` -> `400 Bad Request`) and audit logging (`USER_DEACTIVATED`, `USER_SUSPENDED`, `USER_UPDATED`).
   - Implemented `GET /api/v1/users/{user_id}/permissions` returning `UserPermissionsOut` with dynamically resolved permissions from assigned roles.
3. **`backend/app/modules/roles/router.py`:**
   - Enhanced `DELETE /api/v1/users/{user_id}/roles/{role_name}` with server-side self-lockout enforcement (`current_user.id == user_id and role_name.upper() == 'ADMIN'` -> `400 Bad Request`) and audit logging (`ROLE_REVOKED`).

---

## 4. Frontend Changes
1. **`frontend/src/services/user.service.js`:**
   - Created comprehensive API service wrapping `getUsers`, `getUserById`, `updateUserStatus`, `getUserEffectivePermissions`, `assignRole`, `revokeRole`, `getRoles`, and `getRoleById`.
2. **`frontend/src/components/UserStatusBadge.jsx`:**
   - Visual badge component for rendering semantic statuses (`ACTIVE`, `SUSPENDED`, `DEACTIVATED`, `PENDING_VERIFICATION`).
3. **`frontend/src/components/RoleBadge.jsx`:**
   - Visual badge component for system roles (`ADMIN`, `LIBRARIAN`, `STUDENT`, `GUEST`).
4. **`frontend/src/components/RoleAssignmentModal.jsx`:**
   - Accessible dialog for granting system roles, featuring dynamic role fetching, elevated privilege alerts for `ADMIN`/`LIBRARIAN`, and lockout safeguards.
5. **`frontend/src/components/EffectivePermissionsPanel.jsx`:**
   - Domain-grouped dynamic permissions matrix categorized by functional area (`Catalog`, `Circulation`, `Users`, `Roles/IAM`, `Audit`).
6. **`frontend/src/pages/UsersPage.jsx`:**
   - Main `/users` ledger featuring keyword search, status and role filter dropdowns, operational summary metrics, and responsive table layout.
7. **`frontend/src/pages/UserDetailsPage.jsx`:**
   - Main `/users/:id` view with identity card, lifecycle status controls, assigned roles management, effective permissions panel, and patron borrowing history.
8. **`frontend/src/components/Navbar.jsx`:**
   - Added responsive "Users" navigation link for `ADMIN` users in desktop navigation and mobile dropdowns.
9. **`frontend/src/pages/DashboardPreviewPage.jsx`:**
   - Wired "Registered Users" StatCard directly to `/users` and added "Users & IAM" QuickActionCard for administrators.

---

## 5. Routes
The following routes were integrated into `frontend/src/App.jsx`:

| Route Path | Component | Access Control | Purpose |
| :--- | :--- | :--- | :--- |
| `/users` | `UsersPage` | `<ProtectedRoute allowedRoles={["ADMIN"]}>` | Administrative user directory and filtering ledger |
| `/users/:id` | `UserDetailsPage` | `<ProtectedRoute allowedRoles={["ADMIN"]}>` | User identity profile, IAM controls, and effective permissions |

---

## 6. IAM/RBAC Behavior
- **Role Hierarchy Preserved:** User identities map to Roles (`user_roles`), which map to canonical Permissions (`role_permissions`).
- **Dynamic Resolution:** Permissions are resolved at runtime via `PermissionService.get_user_permissions()`, eliminating stale or mismatched frontend lists.
- **Client Gates:** Access to `/users` and `/users/:id` is restricted to users holding the `ADMIN` role via `ProtectedRoute`. Non-admin visitors encounter semantic `Access Denied` UI.
- **Backend Authority:** Backend endpoints enforce `require_permission(AppPermission.USER_VIEW.value)`, `require_permission(AppPermission.USER_UPDATE.value)`, and `require_any_permission(...)` independently of frontend state.

---

## 7. Security Controls
- **Self-Lockout Prevention:** Dual-layer defense preventing administrators from deactivating/suspending their own active session or revoking their own `ADMIN` role. Both frontend button states and backend route dependencies enforce this restriction.
- **Privilege Escalation Defense:** `STUDENT` and `GUEST` personas receive `403 Forbidden` / `401 Unauthorized` on all user listing, status update, and role mutation endpoints.
- **Credential & Secret Protection:** User response schemas strictly omit `password_hash`, `mfa_secret`, `mfa_recovery_codes`, and session token hashes.
- **Client Identifier Disregard:** Self-action detection utilizes cryptographically signed JWT `sub` claims, preventing spoofing via request headers or body identifiers.

---

## 8. Audit Behavior
All security-sensitive operations generate structured audit log rows in the PostgreSQL `audit_logs` table:
- Account suspension: `USER_SUSPENDED` (Resource: `{user_id}:SUSPENDED`)
- Account deactivation: `USER_DEACTIVATED` (Resource: `{user_id}:DEACTIVATED`)
- Account reactivation: `USER_UPDATED` (Resource: `{user_id}:ACTIVE`)
- Role grant: `ROLE_ASSIGNED` (Resource: `{user_id}:{role_name}`)
- Role revocation: `ROLE_REVOKED` (Resource: `{user_id}:{role_name}`)

---

## 9. Tests
Added `backend/tests/test_phase15_user_iam_admin.py` containing 19 comprehensive test cases:
- `TestUserListingAndFilters`: Verified admin user query, search filtering, status filtering, role filtering, student rejection (403), and unauthenticated rejection (401).
- `TestUserDetailsAndPermissions`: Verified user detail retrieval, dynamic effective permission resolution, and student access denial (403).
- `TestAccountStatusTransitionsAndSelfLockout`: Verified account suspension, deactivation, reactivation, audit logging, self-deactivation prevention (400), self-suspension prevention (400), and student mutation denial (403).
- `TestRoleAssignmentRevocationAndSelfLockout`: Verified role assignment, role revocation, audit logging, self-ADMIN revocation prevention (400), and student denial (403).
- `TestSensitiveFieldExposurePrevention`: Verified that user listing and detail payloads strictly exclude password hashes, MFA secrets, and tokens.

### Pytest Results
```text
============================= test session starts ==============================
collected 173 items

173 passed in 15.10s
0 failed, 0 skipped, 0 warnings
```

---

## 10. Frontend Lint & Build
- **ESLint:** Passed cleanly with 0 errors and 0 warnings (`npm run lint`).
- **Vite Production Build:** Passed cleanly (`npm run build`).

---

## 11. Alembic Status
- `alembic current`: `3741532892a9 (head)`
- `alembic heads`: `3741532892a9 (head)`
- **Database Migrations Added:** 0 migrations (schema fully supported by existing models).

---

## 12. Graphify Status
- Ran knowledge graph synchronization (`graphify update .`) to update nodes, code references, and dependency relationships for all Phase 15 modules.

---

## 13. Known Limitations
1. **Frontend Permission Authoring:** Dynamic creation of novel permission keys is not exposed in the UI; permissions remain governed by system constants.
2. **Dedicated Audit Management UI:** Deferred to Phase 16.
3. **Session Invalidation:** Deactivating an account blocks subsequent token refreshes; active in-flight access tokens expire within 15 minutes.

---

## 14. Deferred Work
- **Phase 16:** Dedicated Audit Management UI & Security Event Explorer.
- **Phase 17+:** Advanced real-time notifications and external identity providers.
