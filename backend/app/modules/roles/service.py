"""
Roles business logic and database management service.
"""

from typing import List, Optional
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.permission import Permission
from app.models.role import Role, role_permissions, user_roles
from app.models.user import User
from app.modules.permissions.constants import (
    AppRole,
    normalize_permission_name,
)
from app.modules.roles.schemas import RoleCreate

logger = get_logger(__name__)

ASSIGNABLE_USER_ROLES = {
    AppRole.ADMIN.value,
    AppRole.LIBRARIAN.value,
    AppRole.STUDENT.value,
}
SUPPORTED_APPLICATION_ROLES = [r.value for r in AppRole]


class RoleService:
    """Service for managing roles, role assignments, and role permissions."""

    @staticmethod
    def list_roles(db: Session, assignable_only: bool = False) -> List[Role]:
        """
        List supported application roles with their permissions.

        Args:
            db: Database session.
            assignable_only: When True, returns only roles assignable to user accounts
                             (ADMIN, LIBRARIAN, STUDENT), excluding GUEST.
        """
        if assignable_only:
            target_roles = [AppRole.ADMIN.value, AppRole.LIBRARIAN.value, AppRole.STUDENT.value]
        else:
            target_roles = [r.value for r in AppRole]

        return (
            db.query(Role)
            .filter(Role.name.in_(target_roles))
            .order_by(Role.name.asc())
            .all()
        )

    @staticmethod
    def get_role_by_id(db: Session, role_id: uuid.UUID) -> Role:
        """Get role by its UUID."""
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID '{role_id}' not found.",
            )
        return role

    @staticmethod
    def get_role_by_name(db: Session, role_name: str) -> Optional[Role]:
        """Get role by its name."""
        return db.query(Role).filter(Role.name == role_name.strip().upper()).first()

    @staticmethod
    def create_role(db: Session, data: RoleCreate) -> Role:
        """Create a new role."""
        name = data.name.strip().upper()
        existing = db.query(Role).filter(Role.name == name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with name '{name}' already exists.",
            )

        role = Role(name=name, description=data.description)
        db.add(role)
        db.commit()
        db.refresh(role)
        logger.info("Created new role: %s (%s)", role.name, role.id)
        return role

    @staticmethod
    def assign_role_to_user(db: Session, user_id: uuid.UUID, role_name: str) -> User:
        """Assign a supported application role to a user."""
        name_clean = role_name.strip().upper()

        if name_clean == AppRole.GUEST.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GUEST is a public, unauthenticated role concept and cannot be assigned to user accounts.",
            )

        if name_clean not in ASSIGNABLE_USER_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role '{role_name}' is not a supported assignable application role. Supported roles: {sorted(list(ASSIGNABLE_USER_ROLES))}.",
            )

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID '{user_id}' not found.",
            )

        role = RoleService.get_role_by_name(db, name_clean)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role '{name_clean}' not found.",
            )

        if role not in user.roles:
            user.roles.append(role)
            db.commit()
            db.refresh(user)
            logger.info("Assigned role %s to user %s (%s)", role.name, user.email, user.id)

        return user

    @staticmethod
    def revoke_role_from_user(db: Session, user_id: uuid.UUID, role_name: str) -> User:
        """Revoke a role from a user."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID '{user_id}' not found.",
            )

        role = RoleService.get_role_by_name(db, role_name)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role '{role_name}' not found.",
            )

        if role in user.roles:
            user.roles.remove(role)
            db.commit()
            db.refresh(user)
            logger.info("Revoked role %s from user %s (%s)", role.name, user.email, user.id)

        return user

    @staticmethod
    def assign_permission_to_role(
        db: Session, role_id: uuid.UUID, permission_name: str
    ) -> Role:
        """Assign a permission to a role."""
        role = RoleService.get_role_by_id(db, role_id)
        canonical = normalize_permission_name(permission_name)

        perm = (
            db.query(Permission)
            .filter((Permission.name == canonical) | (Permission.name == permission_name))
            .first()
        )
        if not perm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permission '{permission_name}' not found.",
            )

        if perm not in role.permissions:
            role.permissions.append(perm)
            db.commit()
            db.refresh(role)
            logger.info("Assigned permission %s to role %s", perm.name, role.name)

        return role

    @staticmethod
    def revoke_permission_from_role(
        db: Session, role_id: uuid.UUID, permission_name: str
    ) -> Role:
        """Revoke a permission from a role."""
        role = RoleService.get_role_by_id(db, role_id)
        canonical = normalize_permission_name(permission_name)

        perm = (
            db.query(Permission)
            .filter((Permission.name == canonical) | (Permission.name == permission_name))
            .first()
        )
        if not perm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permission '{permission_name}' not found.",
            )

        if perm in role.permissions:
            role.permissions.remove(perm)
            db.commit()
            db.refresh(role)
            logger.info("Revoked permission %s from role %s", perm.name, role.name)

        return role


role_service = RoleService()
