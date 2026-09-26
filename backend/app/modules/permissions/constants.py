"""
RBAC permission constants, role definitions, and role-permission matrix.

Defines:
  - Canonical permission names (resource:action)
  - Uppercase permission aliases (RESOURCE_ACTION)
  - Default roles (ADMIN, LIBRARIAN, STUDENT, GUEST)
  - Default Role-to-Permission mapping matrix
  - Normalization helpers
"""

import enum
from typing import Dict, List, Set


class AppRole(str, enum.Enum):
    """Core system roles."""
    ADMIN = "ADMIN"
    LIBRARIAN = "LIBRARIAN"
    STUDENT = "STUDENT"
    GUEST = "GUEST"


class AppPermission(str, enum.Enum):
    """
    Standard system permissions.
    
    Format: 'resource:action'
    """
    # Book permissions
    BOOK_VIEW = "book:view"
    BOOK_CREATE = "book:create"
    BOOK_UPDATE = "book:update"
    BOOK_DELETE = "book:delete"

    # Circulation permissions
    BOOK_ISSUE = "book:issue"
    BOOK_RETURN = "book:return"

    # User management permissions
    USER_VIEW = "user:view"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # Role management permissions
    ROLE_VIEW = "role:view"
    ROLE_CREATE = "role:create"
    ROLE_UPDATE = "role:update"
    ROLE_DELETE = "role:delete"

    # Permission management
    PERMISSION_VIEW = "permission:view"
    PERMISSION_ASSIGN = "permission:assign"

    # Audit log permissions
    AUDIT_LOG_VIEW = "audit_log:view"


# Descriptions for each standard permission
PERMISSION_DESCRIPTIONS: Dict[str, str] = {
    AppPermission.BOOK_VIEW.value: "View book catalogue, details, and availability",
    AppPermission.BOOK_CREATE.value: "Create new book entries and catalog records",
    AppPermission.BOOK_UPDATE.value: "Update book metadata and details",
    AppPermission.BOOK_DELETE.value: "Remove book entries from the catalogue",
    AppPermission.BOOK_ISSUE.value: "Issue book copies to library members",
    AppPermission.BOOK_RETURN.value: "Process book copy returns and check-ins",
    AppPermission.USER_VIEW.value: "View user accounts, profiles, and statuses",
    AppPermission.USER_CREATE.value: "Create new user accounts administratively",
    AppPermission.USER_UPDATE.value: "Update user account information and statuses",
    AppPermission.USER_DELETE.value: "Deactivate or delete user accounts",
    AppPermission.ROLE_VIEW.value: "View system roles and member assignments",
    AppPermission.ROLE_CREATE.value: "Create new system roles",
    AppPermission.ROLE_UPDATE.value: "Update roles and manage role permissions",
    AppPermission.ROLE_DELETE.value: "Delete custom system roles",
    AppPermission.PERMISSION_VIEW.value: "View system permissions and authorization matrix",
    AppPermission.PERMISSION_ASSIGN.value: "Assign or revoke permissions to/from roles",
    AppPermission.AUDIT_LOG_VIEW.value: "View security audit trails and operational logs",
}

# Mapping of UPPER_SNAKE_CASE names to canonical 'resource:action' values
_PERMISSION_ALIAS_MAP: Dict[str, str] = {
    "BOOK_VIEW": AppPermission.BOOK_VIEW.value,
    "BOOK_CREATE": AppPermission.BOOK_CREATE.value,
    "BOOK_UPDATE": AppPermission.BOOK_UPDATE.value,
    "BOOK_DELETE": AppPermission.BOOK_DELETE.value,
    "BOOK_ISSUE": AppPermission.BOOK_ISSUE.value,
    "BOOK_RETURN": AppPermission.BOOK_RETURN.value,
    "USER_VIEW": AppPermission.USER_VIEW.value,
    "USER_CREATE": AppPermission.USER_CREATE.value,
    "USER_UPDATE": AppPermission.USER_UPDATE.value,
    "USER_DELETE": AppPermission.USER_DELETE.value,
    "ROLE_VIEW": AppPermission.ROLE_VIEW.value,
    "ROLE_CREATE": AppPermission.ROLE_CREATE.value,
    "ROLE_UPDATE": AppPermission.ROLE_UPDATE.value,
    "ROLE_DELETE": AppPermission.ROLE_DELETE.value,
    "PERMISSION_VIEW": AppPermission.PERMISSION_VIEW.value,
    "PERMISSION_ASSIGN": AppPermission.PERMISSION_ASSIGN.value,
    "AUDIT_LOG_VIEW": AppPermission.AUDIT_LOG_VIEW.value,
}


def normalize_permission_name(perm_name: str) -> str:
    """
    Normalize permission string to canonical 'resource:action' format.
    
    Accepts either 'BOOK_VIEW' or 'book:view' and returns 'book:view'.
    """
    clean = perm_name.strip()
    if clean.upper() in _PERMISSION_ALIAS_MAP:
        return _PERMISSION_ALIAS_MAP[clean.upper()]
    return clean.lower()


# Default Role -> Permission assignment matrix
DEFAULT_ROLE_PERMISSIONS: Dict[str, List[str]] = {
    AppRole.ADMIN.value: [
        AppPermission.BOOK_VIEW.value,
        AppPermission.BOOK_CREATE.value,
        AppPermission.BOOK_UPDATE.value,
        AppPermission.BOOK_DELETE.value,
        AppPermission.BOOK_ISSUE.value,
        AppPermission.BOOK_RETURN.value,
        AppPermission.USER_VIEW.value,
        AppPermission.USER_CREATE.value,
        AppPermission.USER_UPDATE.value,
        AppPermission.USER_DELETE.value,
        AppPermission.ROLE_VIEW.value,
        AppPermission.ROLE_CREATE.value,
        AppPermission.ROLE_UPDATE.value,
        AppPermission.ROLE_DELETE.value,
        AppPermission.PERMISSION_VIEW.value,
        AppPermission.PERMISSION_ASSIGN.value,
        AppPermission.AUDIT_LOG_VIEW.value,
    ],
    AppRole.LIBRARIAN.value: [
        AppPermission.BOOK_VIEW.value,
        AppPermission.BOOK_CREATE.value,
        AppPermission.BOOK_UPDATE.value,
        AppPermission.BOOK_DELETE.value,
        AppPermission.BOOK_ISSUE.value,
        AppPermission.BOOK_RETURN.value,
        AppPermission.USER_VIEW.value,
        AppPermission.AUDIT_LOG_VIEW.value,
    ],
    AppRole.STUDENT.value: [
        AppPermission.BOOK_VIEW.value,
    ],
    AppRole.GUEST.value: [
        AppPermission.BOOK_VIEW.value,
    ],
}

ROLE_DESCRIPTIONS: Dict[str, str] = {
    AppRole.ADMIN.value: "System administrator with full administrative and security access",
    AppRole.LIBRARIAN.value: "Library staff with catalog, circulation, and user viewing capabilities",
    AppRole.STUDENT.value: "Registered library member with standard book viewing and borrowing capabilities",
    AppRole.GUEST.value: "Unauthenticated or public visitor with read-only access to catalog",
}
