"""
Permissions service for RBAC resolution, role-permission matrix management, and seeding.
"""

from typing import Dict, List, Optional, Set
import uuid

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.permission import Permission
from app.models.role import Role, role_permissions, user_roles
from app.models.user import User
from app.modules.permissions.constants import (
    DEFAULT_ROLE_PERMISSIONS,
    PERMISSION_DESCRIPTIONS,
    ROLE_DESCRIPTIONS,
    normalize_permission_name,
)

logger = get_logger(__name__)


class PermissionService:
    """Core permission management and resolution service."""

    @staticmethod
    def seed_default_roles_and_permissions(db: Session) -> None:
        """
        Idempotently populate standard system roles, permissions, and association mappings.
        """
        # 1. Seed / ensure permissions exist
        existing_perms = {p.name: p for p in db.query(Permission).all()}
        for perm_name, perm_desc in PERMISSION_DESCRIPTIONS.items():
            if perm_name not in existing_perms:
                new_perm = Permission(
                    name=perm_name,
                    description=perm_desc,
                )
                db.add(new_perm)
                db.flush()
                existing_perms[perm_name] = new_perm

        # 2. Seed / ensure roles exist
        existing_roles = {r.name: r for r in db.query(Role).all()}
        for role_name, role_desc in ROLE_DESCRIPTIONS.items():
            if role_name not in existing_roles:
                new_role = Role(
                    name=role_name,
                    description=role_desc,
                )
                db.add(new_role)
                db.flush()
                existing_roles[role_name] = new_role

        # 3. Associate permissions with roles based on matrix
        for role_name, perm_list in DEFAULT_ROLE_PERMISSIONS.items():
            role = existing_roles.get(role_name)
            if not role:
                continue

            current_role_perm_ids = {
                row.permission_id
                for row in db.execute(
                    role_permissions.select().where(role_permissions.c.role_id == role.id)
                ).fetchall()
            }

            for perm_name in perm_list:
                perm = existing_perms.get(perm_name)
                if perm and perm.id not in current_role_perm_ids:
                    db.execute(
                        role_permissions.insert().values(
                            role_id=role.id,
                            permission_id=perm.id,
                        )
                    )
                    current_role_perm_ids.add(perm.id)

        db.commit()
        logger.info("Default roles and permissions verified and synchronized.")

    @staticmethod
    def list_all_permissions(db: Session) -> List[Permission]:
        """Return all available permissions ordered by name."""
        return db.query(Permission).order_by(Permission.name.asc()).all()

    @staticmethod
    def get_user_permissions(user: User, db: Session) -> Set[str]:
        """
        Authoritatively query and return all effective permission names assigned to the user
        via their active roles.
        """
        if not user or not user.id:
            return set()

        # Query permissions joined via user_roles and role_permissions
        rows = (
            db.query(Permission.name)
            .join(role_permissions, Permission.id == role_permissions.c.permission_id)
            .join(user_roles, role_permissions.c.role_id == user_roles.c.role_id)
            .filter(user_roles.c.user_id == user.id)
            .all()
        )
        perms = {r[0] for r in rows}

        # If user.roles is attached in-memory (e.g. transient or unpersisted instance)
        if not perms and hasattr(user, "roles") and user.roles:
            role_ids = [r.id for r in user.roles if r.id]
            if role_ids:
                in_mem_rows = (
                    db.query(Permission.name)
                    .join(role_permissions, Permission.id == role_permissions.c.permission_id)
                    .filter(role_permissions.c.role_id.in_(role_ids))
                    .all()
                )
                perms = {r[0] for r in in_mem_rows}

        return perms

    @staticmethod
    def user_has_permission(user: User, permission_name: str, db: Session) -> bool:
        """
        Check if user possesses the specified permission (normalized).
        """
        canonical = normalize_permission_name(permission_name)
        perms = PermissionService.get_user_permissions(user, db)
        return (
            canonical in perms
            or permission_name in perms
            or permission_name.upper() in perms
        )

    @staticmethod
    def get_matrix(db: Session) -> Dict[str, List[str]]:
        """
        Return the current role-permission mapping matrix from the database.
        """
        roles = db.query(Role).all()
        matrix: Dict[str, List[str]] = {}
        for role in roles:
            perm_rows = (
                db.query(Permission.name)
                .join(role_permissions, Permission.id == role_permissions.c.permission_id)
                .filter(role_permissions.c.role_id == role.id)
                .all()
            )
            matrix[role.name] = sorted([r[0] for r in perm_rows])
        return matrix


permission_service = PermissionService()
