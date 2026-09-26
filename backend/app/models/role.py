"""
Role model and UserRole / RolePermission association tables.

Role names are conceptual (ADMIN, LIBRARIAN, STUDENT, GUEST).
The actual assignment of permissions to roles is handled in the RBAC phase.

Association tables are declared here (not as ORM models) to avoid
circular-import issues while keeping the schema in one clear place.
"""

import uuid

from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

# ---------------------------------------------------------------------------
# Many-to-many association: users ↔ roles
# ---------------------------------------------------------------------------

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "role_id",
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    ),
    # Composite PK enforces uniqueness — no duplicate role assignments.
    UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
    Index("ix_user_roles_user_id", "user_id"),
    Index("ix_user_roles_role_id", "role_id"),
)


# ---------------------------------------------------------------------------
# Many-to-many association: roles ↔ permissions
# ---------------------------------------------------------------------------

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id",
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "permission_id",
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
    ),
    UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_role_permission"),
    Index("ix_role_permissions_role_id", "role_id"),
    Index("ix_role_permissions_permission_id", "permission_id"),
)


# ---------------------------------------------------------------------------
# Role model
# ---------------------------------------------------------------------------


class Role(Base, TimestampMixin):
    """
    Application role (e.g., ADMIN, LIBRARIAN, STUDENT, GUEST).

    Roles are assigned to users and carry permissions.
    The full role-permission matrix is defined in the RBAC phase.
    """

    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="Role name — must be unique (e.g., ADMIN, LIBRARIAN, STUDENT, GUEST)",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    # Many-to-many: Role ↔ User
    users: Mapped[list["User"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User",
        secondary="user_roles",
        back_populates="roles",
        lazy="select",
    )

    # Many-to-many: Role ↔ Permission
    permissions: Mapped[list["Permission"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Permission",
        secondary="role_permissions",
        back_populates="roles",
        lazy="select",
    )

    # ------------------------------------------------------------------
    # Constraints & indexes
    # ------------------------------------------------------------------

    __table_args__ = (
        UniqueConstraint("name", name="uq_roles_name"),
        Index("ix_roles_name", "name"),
    )

    def __repr__(self) -> str:
        return f"<Role id={self.id} name={self.name!r}>"
