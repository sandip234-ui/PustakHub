# PustakHub — Catalog Management UI Specification & Guide

## Overview

The **PustakHub Catalog Management UI** provides an enterprise-grade, responsive React interface for exploring library collections, inspecting real-time physical inventory availability, and managing bibliographic metadata, physical copy units, and category taxonomies under strict database-backed Role-Based Access Control (RBAC).

---

## 1. Architectural Principles

1. **Backend as the Authoritative Boundary:**
   - The FastAPI backend strictly enforces database-resolved RBAC permissions (`book:create`, `book:update`, `book:delete`, `category:manage`, etc.).
   - Frontend permission gates (`PermissionGate`, `usePermissions`, `allowedRoles` in `ProtectedRoute`) are **strictly UX controls** designed to declutter navigation and prevent unauthorized user friction.
   - Any manual or intercepted API mutation attempted without sufficient backend permissions will receive a `403 Forbidden` or `401 Unauthorized` response.

2. **Zero API Duplication:**
   - All network interactions flow through the centralized `catalog.service.js` abstraction and standard Axios interceptor pipeline.
   - Server-side pagination, search debouncing, and category filtering operate directly against backend query endpoints.

3. **Optimistic Error & Conflict Handling:**
   - Deletion of book titles with registered physical copies returns a structured `409 Conflict`.
   - Deletion of physical copies with active loan records returns a structured `409 Conflict`.
   - Deletion of categories containing assigned books returns a structured `409 Conflict`.
   - The UI surfaces these domain constraints via clear, actionable feedback dialogues rather than generic errors.

---

## 2. Frontend Routes & Navigation

| Route | Page Component | Access Level | Description |
| :--- | :--- | :--- | :--- |
| `/catalog` | `CatalogPage` | Authenticated | Main Catalog Explorer with server search, category filters, pagination, availability pills, and staff CRUD triggers. |
| `/books/:id` | `BookDetailsPage` | Authenticated | Bibliographic detail record, copy breakdown cards, and Physical Inventory Copies table. |
| `/categories` | `CategoriesPage` | Staff (`ADMIN`, `LIBRARIAN`) | Taxonomy management table displaying categorized book counts and CRUD controls. |
| `/dashboard` | `DashboardPreviewPage` | Authenticated | User identity hub, role resolution display, and navigation tiles. |

---

## 3. RBAC UI Architecture

### 3.1 `usePermissions` Hook (`src/hooks/usePermissions.js`)
Extracts assigned roles and granular permission strings from `AuthContext` and provides helper flags:
```javascript
const {
  roles,
  permissions,
  hasRole,
  hasAnyRole,
  hasPermission,
  hasAllPermissions,
  canCreateBook,
  canUpdateBook,
  canDeleteBook,
  isStaff,
  isAdmin,
  isLibrarian,
  isStudent,
} = usePermissions();
```

### 3.2 `PermissionGate` Component (`src/components/PermissionGate.jsx`)
Declarative conditional rendering of action buttons, modals, and management table columns:
```jsx
// Single permission check
<PermissionGate permission="book:create">
  <button onClick={handleCreateBook}>Add New Book</button>
</PermissionGate>

// Multiple permissions check (OR logic by default)
<PermissionGate permissions={["book:update", "book:delete"]}>
  <th scope="col">Actions</th>
</PermissionGate>
```

### 3.3 Protected Route Guarding (`src/components/ProtectedRoute.jsx`)
Guards staff routes (e.g. `/categories`) against unauthorized access while rendering an accessible 403 Access Denied fallback banner with redirection links.

---

## 4. Feature Workflows

### 4.1 Catalog Explorer (`/catalog`)
- **Server-Side Search:** Debounced input (250ms) matching book `title`, `author`, `isbn`, or `publisher`.
- **Category Filter:** Dynamic dropdown populated from `catalogService.getCategories()` displaying real-time title counts.
- **Configurable Pagination:** Server-side pagination supporting 12, 20, 50, or 100 items per page with smart jump buttons.
- **Copy Availability Badges:** Color-coded badges indicating `Available`, `Out / Borrowed`, or `No Copies`.

### 4.2 Book Details & Bibliographic Records (`/books/:id`)
- Displays complete bibliographic metadata: Title, Author, ISBN, Publisher, Publication Year, Category, and Description.
- Provides an **Inventory Availability Summary** breakdown showing Total Copies, Available, Borrowed, and In-Maintenance counts.

### 4.3 Physical Copies Management
- **Inventory Table:** Lists all copy units with barcode identifiers (`copy_identifier`), availability status (`AVAILABLE`, `BORROWED`, `MAINTENANCE`, `LOST`), shelf locations (`shelf_location`), and registration dates.
- **Add Copy Modal:** Allows staff to register new physical units with custom barcodes and shelf placement.
- **Edit Copy Modal:** Allows updating shelf coordinates and maintenance statuses.
- **Delete Copy Guard:** Enforces confirmation modal and displays 409 conflict warnings if the copy is currently checked out.

### 4.4 Category Taxonomy Management (`/categories`)
- **Taxonomy Table:** Displays category names, descriptions, and number of catalog books currently assigned.
- **Category CRUD:** Allows creating new disciplines and modifying descriptions.
- **Safe Deletion:** Confirms category deletion and surfaces backend constraints if books remain assigned.

---

## 5. Demo Account Permissions Matrix

| Account Persona | Email | Role | Catalog Browse | Book CRUD | Copy CRUD | Category CRUD |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **System Administrator** | `admin.demo@pustakhub.com` | `ADMIN` | ✅ | ✅ | ✅ | ✅ |
| **Senior Librarian** | `librarian.demo@pustakhub.com` | `LIBRARIAN` | ✅ | ✅ | ✅ | ✅ |
| **Student Member** | `student.demo@pustakhub.com` | `STUDENT` | ✅ | ❌ | ❌ | ❌ |
| **Guest Observer** | `guest.demo@pustakhub.com` | `GUEST` | ✅ | ❌ | ❌ | ❌ |

---

## 6. Accessibility & Responsiveness

- **WCAG 2.2 AA Compliance:** Semantic heading hierarchies (`h1` to `h4`), aria labels, focus indicators, modal focus traps with escape handling, and redundant textual status indicators (never relying on color alone).
- **Responsive Layouts:** Desktop grid structures gracefully transition to single-column card views on mobile viewports without horizontal scroll overflow.
