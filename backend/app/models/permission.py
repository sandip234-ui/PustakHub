"""
Permission model.

A permission is a named capability (e.g., "book:create", "user:suspend").
Permissions are assigned to roles; roles are assigned to users.

The complete permission matrix is defined in the RBAC phase.
This model only establishes the database schema.
"""

import uuid

from sqlalchemy import Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Permission(Base, TimestampMixin):
    """Named application permission."""

    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
        comment=(
            "Unique permission name, e.g. 'book:create', 'user:suspend'. "
            "Format is 'resource:action'."
        ),
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    # Many-to-many: Permission ↔ Role (back-reference)
    roles: Mapped[list["Role"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Role",
        secondary="role_permissions",
        back_populates="permissions",
        lazy="select",
    )

    # ------------------------------------------------------------------
    # Constraints & indexes
    # ------------------------------------------------------------------

    __table_args__ = (
        UniqueConstraint("name", name="uq_permissions_name"),
        Index("ix_permissions_name", "name"),
    )

    def __repr__(self) -> str:
        return f"<Permission id={self.id} name={self.name!r}>"
