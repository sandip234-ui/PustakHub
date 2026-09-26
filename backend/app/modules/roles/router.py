"""
Roles HTTP Router.

Endpoints:
  - GET    /api/v1/roles                        - List all roles with permissions (requires role:view)
  - GET    /api/v1/roles/{role_id}              - Get single role details (requires role:view)
  - POST   /api/v1/roles                        - Create custom role (requires role:create)
  - POST   /api/v1/roles/{role_id}/permissions - Assign permission to role (requires permission:assign)
  - DELETE /api/v1/roles/{role_id}/permissions/{permission_name} - Revoke permission from role (requires permission:assign)
  - POST   /api/v1/users/{user_id}/roles        - Assign role to user (requires role:update or user:update)
  - DELETE /api/v1/users/{user_id}/roles/{role_name} - Revoke role from user (requires role:update or user:update)
"""

from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.audit_log import AuditAction, AuditStatus
from app.models.user import User
from app.modules.audit.service import audit_service
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserOut
from app.modules.permissions.constants import AppPermission
from app.modules.permissions.dependencies import (
    require_any_permission,
    require_permission,
)
from app.modules.roles.schemas import (
    PermissionAssignRequest,
    RoleAssignRequest,
    RoleCreate,
    RoleOut,
)
from app.modules.roles.service import role_service

router = APIRouter(tags=["roles"])


@router.get(
    "/roles",
    response_model=List[RoleOut],
    status_code=status.HTTP_200_OK,
    summary="List all roles",
    description="Returns supported application roles in the system with their associated permissions. Requires 'role:view'.",
    dependencies=[Depends(require_permission(AppPermission.ROLE_VIEW.value))],
)
def list_roles(
    assignable_only: bool = Query(
        False,
        description="Filter to assignable roles only (ADMIN, LIBRARIAN, STUDENT), excluding unauthenticated public roles (GUEST)",
    ),
    db: Session = Depends(get_db),
) -> List[RoleOut]:
    roles = role_service.list_roles(db, assignable_only=assignable_only)
    return [RoleOut.model_validate(r) for r in roles]


@router.get(
    "/roles/{role_id}",
    response_model=RoleOut,
    status_code=status.HTTP_200_OK,
    summary="Get role details",
    description="Returns details and permissions for a specific role. Requires 'role:view'.",
    dependencies=[Depends(require_permission(AppPermission.ROLE_VIEW.value))],
)
def get_role(
    role_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> RoleOut:
    role = role_service.get_role_by_id(db, role_id)
    return RoleOut.model_validate(role)


@router.post(
    "/roles",
    response_model=RoleOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create role",
    description="Creates a new custom system role. Requires 'role:create'.",
    dependencies=[Depends(require_permission(AppPermission.ROLE_CREATE.value))],
)
def create_role(
    data: RoleCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> RoleOut:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    role = role_service.create_role(db, data)
    return RoleOut.model_validate(role)


@router.post(
    "/roles/{role_id}/permissions",
    response_model=RoleOut,
    status_code=status.HTTP_200_OK,
    summary="Assign permission to role",
    description="Assigns a permission to the specified role. Requires 'permission:assign'.",
    dependencies=[Depends(require_permission(AppPermission.PERMISSION_ASSIGN.value))],
)
def assign_permission_to_role(
    role_id: uuid.UUID,
    data: PermissionAssignRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> RoleOut:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    role = role_service.assign_permission_to_role(db, role_id, data.permission_name)
    audit_service.log(
        db,
        action=AuditAction.PERMISSION_GRANTED,
        resource_type="Role",
        resource_id=f"{role.name}:{data.permission_name}",
        status=AuditStatus.SUCCESS,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    return RoleOut.model_validate(role)


@router.delete(
    "/roles/{role_id}/permissions/{permission_name}",
    response_model=RoleOut,
    status_code=status.HTTP_200_OK,
    summary="Revoke permission from role",
    description="Revokes a permission from the specified role. Requires 'permission:assign'.",
    dependencies=[Depends(require_permission(AppPermission.PERMISSION_ASSIGN.value))],
)
def revoke_permission_from_role(
    role_id: uuid.UUID,
    permission_name: str,
    request: Request,
    db: Session = Depends(get_db),
) -> RoleOut:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    role = role_service.revoke_permission_from_role(db, role_id, permission_name)
    audit_service.log(
        db,
        action=AuditAction.PERMISSION_REVOKED,
        resource_type="Role",
        resource_id=f"{role.name}:{permission_name}",
        status=AuditStatus.SUCCESS,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    return RoleOut.model_validate(role)


@router.post(
    "/users/{user_id}/roles",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    summary="Assign role to user",
    description="Assigns an existing role to a target user. Requires 'role:update' or 'user:update'.",
    dependencies=[
        Depends(
            require_any_permission(
                AppPermission.ROLE_UPDATE.value, AppPermission.USER_UPDATE.value
            )
        )
    ],
)
def assign_role_to_user(
    user_id: uuid.UUID,
    data: RoleAssignRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> UserOut:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    user = role_service.assign_role_to_user(db, user_id, data.role_name)
    audit_service.log(
        db,
        action=AuditAction.ROLE_ASSIGNED,
        user_id=user.id,
        resource_type="User",
        resource_id=f"{user.id}:{data.role_name}",
        status=AuditStatus.SUCCESS,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    try:
        from app.modules.realtime.events import RealtimeEventType
        from app.modules.realtime.publisher import publish_realtime_event

        publish_realtime_event(
            event_type=RealtimeEventType.ROLE_ASSIGNED,
            resource_type="User",
            resource_id=str(user.id),
            actor_user_id=user.id,
            target_user_id=user.id,
            data={"role_name": data.role_name},
        )
    except Exception:
        pass
    return UserOut(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        account_status=user.account_status.value,
        roles=[r.name for r in user.roles],
        is_mfa_enabled=getattr(user, "is_mfa_enabled", False),
        is_verified=user.is_verified,
        created_at=user.created_at,
    )


@router.delete(
    "/users/{user_id}/roles/{role_name}",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    summary="Revoke role from user",
    description="Revokes a role from a target user. Requires 'role:update' or 'user:update'.",
    dependencies=[
        Depends(
            require_any_permission(
                AppPermission.ROLE_UPDATE.value, AppPermission.USER_UPDATE.value
            )
        )
    ],
)
def revoke_role_from_user(
    user_id: uuid.UUID,
    role_name: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserOut:
    # Self-protection defense: Prevent an administrator from revoking their own ADMIN role
    if current_user.id == user_id and role_name.upper() == "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Self-lockout protection: You cannot revoke your own ADMIN role. Another administrator must modify your role.",
        )

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    user = role_service.revoke_role_from_user(db, user_id, role_name)
    audit_service.log(
        db,
        action=AuditAction.ROLE_REVOKED,
        user_id=current_user.id,
        resource_type="User",
        resource_id=f"{user.id}:{role_name}",
        status=AuditStatus.SUCCESS,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    try:
        from app.modules.realtime.events import RealtimeEventType
        from app.modules.realtime.publisher import publish_realtime_event

        publish_realtime_event(
            event_type=RealtimeEventType.ROLE_REVOKED,
            resource_type="User",
            resource_id=str(user.id),
            actor_user_id=current_user.id,
            target_user_id=user.id,
            data={"role_name": role_name},
        )
    except Exception:
        pass
    return UserOut(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        account_status=user.account_status.value,
        roles=[r.name for r in user.roles],
        is_mfa_enabled=getattr(user, "is_mfa_enabled", False),
        is_verified=user.is_verified,
        created_at=user.created_at,
    )
