"""
Permissions HTTP Router.

Endpoints:
  - GET /api/v1/permissions        - List all system permissions (requires permission:view)
  - GET /api/v1/permissions/matrix - Get role-permission matrix (requires permission:view)
  - GET /api/v1/permissions/me     - Get current user's effective permissions (authenticated user)
"""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.modules.auth.dependencies import get_current_user
from app.modules.permissions.constants import AppPermission
from app.modules.permissions.dependencies import require_permission
from app.modules.permissions.schemas import (
    PermissionOut,
    RolePermissionsMatrixOut,
    UserPermissionsOut,
)
from app.modules.permissions.service import permission_service

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get(
    "",
    response_model=List[PermissionOut],
    status_code=status.HTTP_200_OK,
    summary="List all permissions",
    description="Returns all registered permissions in the system. Requires 'permission:view' permission.",
    dependencies=[Depends(require_permission(AppPermission.PERMISSION_VIEW.value))],
)
def list_permissions(
    db: Session = Depends(get_db),
) -> List[PermissionOut]:
    perms = permission_service.list_all_permissions(db)
    return [PermissionOut.model_validate(p) for p in perms]


@router.get(
    "/matrix",
    response_model=RolePermissionsMatrixOut,
    status_code=status.HTTP_200_OK,
    summary="Get role-permission matrix",
    description="Returns the full role-to-permission mapping matrix. Requires 'permission:view' permission.",
    dependencies=[Depends(require_permission(AppPermission.PERMISSION_VIEW.value))],
)
def get_matrix(
    db: Session = Depends(get_db),
) -> RolePermissionsMatrixOut:
    perms = permission_service.list_all_permissions(db)
    matrix = permission_service.get_matrix(db)
    return RolePermissionsMatrixOut(
        roles=list(matrix.keys()),
        permissions=[PermissionOut.model_validate(p) for p in perms],
        matrix=matrix,
    )


@router.get(
    "/me",
    response_model=UserPermissionsOut,
    status_code=status.HTTP_200_OK,
    summary="Get caller permissions",
    description="Returns the effective permissions for the currently authenticated user based on their active roles.",
)
def get_my_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserPermissionsOut:
    user_perms = permission_service.get_user_permissions(current_user, db)
    return UserPermissionsOut(
        user_id=current_user.id,
        roles=[r.name for r in current_user.roles],
        permissions=sorted(list(user_perms)),
    )
