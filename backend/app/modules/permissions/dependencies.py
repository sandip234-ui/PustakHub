"""
FastAPI authorization dependencies for RBAC and resource-level access control.

Provides:
  - `require_permission`: Factory ensuring authenticated user has a specific permission.
  - `require_any_permission`: Factory ensuring authenticated user has at least one of the listed permissions.
  - `require_all_permissions`: Factory ensuring authenticated user has all listed permissions.
  - `require_role`: Factory ensuring user has a specific role.
  - `check_resource_access`: Reusable resource-level authorization helper (IDOR / BOLA prevention).
  - `get_user_permissions`: Helper returning the set of permissions for a user.

SECURITY SEMANTICS:
  - 401 Unauthorized: When authentication credentials are missing, invalid, or expired.
  - 403 Forbidden: When user is authenticated but lacks required permission/role or resource ownership.
"""

from typing import Callable, List, Optional, Set
import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.user import User
from app.modules.auth.dependencies import get_current_user, get_optional_current_user
from app.modules.permissions.constants import DEFAULT_ROLE_PERMISSIONS, normalize_permission_name
from app.modules.permissions.service import permission_service

logger = get_logger(__name__)


def get_current_user_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Set[str]:
    """
    Dependency resolving the set of permissions held by the currently authenticated user.
    """
    return permission_service.get_user_permissions(current_user, db)


def require_permission(required_permission: str) -> Callable[..., Optional[User]]:
    """
    FastAPI dependency factory enforcing that the caller has a specific permission.
    If unauthenticated and the permission is granted to the public GUEST role (e.g. book:view),
    access is permitted. Otherwise, HTTP 401 is raised.
    """
    canonical_permission = normalize_permission_name(required_permission)

    def permission_checker(
        current_user: Optional[User] = Depends(get_optional_current_user),
        db: Session = Depends(get_db),
    ) -> Optional[User]:
        guest_perms = DEFAULT_ROLE_PERMISSIONS.get("GUEST", [])
        is_guest_allowed = (
            canonical_permission in guest_perms
            or required_permission in guest_perms
            or required_permission.upper() in guest_perms
        )

        if current_user is None:
            if is_guest_allowed:
                return None
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication credentials were not provided.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_perms = permission_service.get_user_permissions(current_user, db)
        if (
            canonical_permission not in user_perms
            and required_permission not in user_perms
            and required_permission.upper() not in user_perms
        ):
            logger.warning(
                "Access denied for user %s (%s). Required permission: '%s', Available: %s",
                current_user.email,
                current_user.id,
                required_permission,
                user_perms,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: You do not have permission to perform this action (requires '{required_permission}').",
            )
        return current_user

    return permission_checker


def require_any_permission(*required_permissions: str) -> Callable[..., User]:
    """
    FastAPI dependency factory enforcing that the caller has AT LEAST ONE of the specified permissions.
    """
    canonical_perms = [normalize_permission_name(p) for p in required_permissions]

    def any_permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        user_perms = permission_service.get_user_permissions(current_user, db)
        for original, canonical in zip(required_permissions, canonical_perms):
            if (
                canonical in user_perms
                or original in user_perms
                or original.upper() in user_perms
            ):
                return current_user

        logger.warning(
            "Access denied for user %s (%s). Required any of: %s, Available: %s",
            current_user.email,
            current_user.id,
            required_permissions,
            user_perms,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: You do not have any of the required permissions: {list(required_permissions)}.",
        )

    return any_permission_checker


def require_all_permissions(*required_permissions: str) -> Callable[..., User]:
    """
    FastAPI dependency factory enforcing that the caller has ALL of the specified permissions.
    """
    canonical_perms = [normalize_permission_name(p) for p in required_permissions]

    def all_permissions_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        user_perms = permission_service.get_user_permissions(current_user, db)
        for original, canonical in zip(required_permissions, canonical_perms):
            if (
                canonical not in user_perms
                and original not in user_perms
                and original.upper() not in user_perms
            ):
                logger.warning(
                    "Access denied for user %s (%s). Missing permission: '%s'",
                    current_user.email,
                    current_user.id,
                    original,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Forbidden: Missing required permission '{original}'.",
                )
        return current_user

    return all_permissions_checker


def require_role(role_name: str) -> Callable[..., User]:
    """
    FastAPI dependency factory enforcing that the caller possesses the specified role.
    """
    target_role = role_name.strip().upper()

    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        user_roles = {r.name.upper() for r in current_user.roles}
        if target_role not in user_roles:
            logger.warning(
                "Access denied for user %s (%s). Required role: '%s', Assigned roles: %s",
                current_user.email,
                current_user.id,
                target_role,
                user_roles,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Role '{role_name}' is required for this action.",
            )
        return current_user

    return role_checker


def check_resource_access(
    current_user: User,
    resource_owner_id: uuid.UUID,
    admin_permission: str = "user:view",
    db: Optional[Session] = None,
) -> bool:
    """
    Check if the current authenticated user is either the resource owner OR possesses the admin permission.
    
    Prevents IDOR (Insecure Direct Object Reference) and BOLA (Broken Object Level Authorization).
    """
    # 1. Owner can always access their own resource
    if current_user.id == resource_owner_id:
        return True

    # 2. If not owner and DB session provided, check for admin override permission
    if db is not None:
        return permission_service.user_has_permission(current_user, admin_permission, db)

    return False
