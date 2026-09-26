"""
Users HTTP router demonstrating resource-level and route-level authorization.

Endpoints:
  - GET   /api/v1/users                 - List all users with search, status, and role filters (requires user:view)
  - GET   /api/v1/users/{user_id}       - Retrieve user by ID (Resource-level authorization: owner OR user:view)
  - PATCH /api/v1/users/{user_id}/status - Update user account status with self-lockout defense (requires user:update)
  - GET   /api/v1/users/{user_id}/permissions - Get effective permissions for user (requires user:view)
"""

from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.audit_log import AuditAction, AuditStatus
from app.models.role import Role
from app.models.user import AccountStatus, User
from app.modules.audit.service import audit_service
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserOut
from app.modules.permissions.constants import AppPermission
from app.modules.permissions.dependencies import (
    check_resource_access,
    require_permission,
)
from app.modules.permissions.schemas import UserPermissionsOut
from app.modules.permissions.service import permission_service
from app.modules.users.schemas import UserStatusUpdateRequest

router = APIRouter(prefix="/users", tags=["users"])


def _extract_request_meta(request: Request) -> tuple[Optional[str], Optional[str]]:
    """Extract client IP and user agent."""
    ip = getattr(request.state, "client_ip", None) or (
        request.client.host if request.client else None
    )
    ua = getattr(request.state, "user_agent", None) or request.headers.get("user-agent")
    return ip, ua


@router.get(
    "",
    response_model=List[UserOut],
    status_code=status.HTTP_200_OK,
    summary="List all users",
    description="Lists user accounts in the library system with optional search and filters. Requires 'user:view' permission.",
    dependencies=[Depends(require_permission(AppPermission.USER_VIEW.value))],
)
def list_users(
    search: Optional[str] = Query(None, description="Filter by name or email substring"),
    account_status: Optional[AccountStatus] = Query(None, description="Filter by account status"),
    status: Optional[AccountStatus] = Query(None, description="Alias for account_status filter"),
    role: Optional[str] = Query(None, description="Filter by role name (e.g. ADMIN, LIBRARIAN, STUDENT)"),
    db: Session = Depends(get_db),
) -> List[UserOut]:
    query = db.query(User)

    if search:
        term = f"%{search.strip().lower()}%"
        query = query.filter(
            (User.full_name.ilike(term)) | (User.email.ilike(term))
        )

    effective_status = account_status or status
    if effective_status:
        query = query.filter(User.account_status == effective_status)

    if role:
        query = query.join(User.roles).filter(Role.name == role.upper())

    users = query.order_by(User.created_at.desc()).all()
    return [
        UserOut(
            id=u.id,
            full_name=u.full_name,
            email=u.email,
            account_status=u.account_status.value,
            roles=[r.name for r in u.roles],
            is_mfa_enabled=getattr(u, "is_mfa_enabled", False),
            is_verified=u.is_verified,
            created_at=u.created_at,
        )
        for u in users
    ]


@router.get(
    "/{user_id}",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    summary="Get user profile by ID",
    description=(
        "Retrieves a user profile by ID. Enforces resource-level authorization: "
        "a user may view their own profile, or an administrator/librarian with 'user:view' "
        "permission may view other users' profiles. Prevents IDOR/BOLA attacks."
    ),
)
def get_user_by_id(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserOut:
    # Enforce resource-level authorization (IDOR / BOLA prevention)
    has_access = check_resource_access(
        current_user=current_user,
        resource_owner_id=user_id,
        admin_permission=AppPermission.USER_VIEW.value,
        db=db,
    )

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to access another user's profile.",
        )

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found.",
        )

    return UserOut(
        id=target_user.id,
        full_name=target_user.full_name,
        email=target_user.email,
        account_status=target_user.account_status.value,
        roles=[r.name for r in target_user.roles],
        is_mfa_enabled=getattr(target_user, "is_mfa_enabled", False),
        is_verified=target_user.is_verified,
        created_at=target_user.created_at,
    )


@router.patch(
    "/{user_id}/status",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    summary="Update user account status",
    description="Updates account lifecycle status (ACTIVE, SUSPENDED, DEACTIVATED). Requires 'user:update' permission.",
    dependencies=[Depends(require_permission(AppPermission.USER_UPDATE.value))],
)
def update_user_status(
    user_id: uuid.UUID,
    data: UserStatusUpdateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserOut:
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found.",
        )

    # Self-protection defense: Prevent an administrator from deactivating/suspending their own account
    if current_user.id == target_user.id and data.account_status != AccountStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Self-lockout protection: You cannot deactivate or suspend your own active administrator account.",
        )

    old_status = target_user.account_status
    target_user.account_status = data.account_status
    db.commit()
    db.refresh(target_user)

    # Determine specific audit action
    if data.account_status == AccountStatus.DEACTIVATED:
        action = AuditAction.USER_DEACTIVATED
    elif data.account_status == AccountStatus.SUSPENDED:
        action = AuditAction.USER_SUSPENDED
    else:
        action = AuditAction.USER_UPDATED

    ip, ua = _extract_request_meta(request)
    audit_service.log(
        db=db,
        action=action,
        user_id=current_user.id,
        resource_type="User",
        resource_id=f"{target_user.id}:{data.account_status.value}",
        status=AuditStatus.SUCCESS,
        ip_address=ip,
        user_agent=ua,
    )

    try:
        from app.modules.realtime.events import RealtimeEventType
        from app.modules.realtime.publisher import publish_realtime_event

        rt_type = (
            RealtimeEventType.USER_DEACTIVATED
            if data.account_status == AccountStatus.DEACTIVATED
            else RealtimeEventType.USER_SUSPENDED
            if data.account_status == AccountStatus.SUSPENDED
            else RealtimeEventType.USER_UPDATED
        )
        publish_realtime_event(
            event_type=rt_type,
            resource_type="User",
            resource_id=str(target_user.id),
            actor_user_id=current_user.id,
            target_user_id=target_user.id,
            data={"status": target_user.account_status.value, "email": target_user.email},
        )
    except Exception:
        pass

    return UserOut(
        id=target_user.id,
        full_name=target_user.full_name,
        email=target_user.email,
        account_status=target_user.account_status.value,
        roles=[r.name for r in target_user.roles],
        is_mfa_enabled=getattr(target_user, "is_mfa_enabled", False),
        is_verified=target_user.is_verified,
        created_at=target_user.created_at,
    )


@router.get(
    "/{user_id}/permissions",
    response_model=UserPermissionsOut,
    status_code=status.HTTP_200_OK,
    summary="Get user effective permissions",
    description="Returns effective system permissions for a target user based on assigned roles. Requires 'user:view'.",
    dependencies=[Depends(require_permission(AppPermission.USER_VIEW.value))],
)
def get_user_effective_permissions(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> UserPermissionsOut:
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found.",
        )

    user_perms = permission_service.get_user_permissions(target_user, db)
    return UserPermissionsOut(
        user_id=target_user.id,
        roles=[r.name for r in target_user.roles],
        permissions=sorted(list(user_perms)),
    )
