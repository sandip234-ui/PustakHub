"""
AuditLog model.

Immutable record of security-sensitive and business-critical events.

Design principles:
  - Rows are append-only; no UPDATE or DELETE should ever be issued against this table.
  - Sensitive data is NEVER stored here: no passwords, OTP values, tokens, or hashes.
  - user_id is nullable because some events occur before authentication (e.g., failed login).
  - resource_id is stored as a TEXT string to accommodate any UUID or integer PK.

Audit middleware logic belongs to a later phase. This model establishes the schema.
"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AuditAction(str, enum.Enum):
    """Broad category of the audited event."""

    # Authentication events
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILURE = "LOGIN_FAILURE"
    LOGOUT = "LOGOUT"
    TOKEN_REFRESH = "TOKEN_REFRESH"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    PASSWORD_RESET_REQUESTED = "PASSWORD_RESET_REQUESTED"
    PASSWORD_RESET_COMPLETED = "PASSWORD_RESET_COMPLETED"
    PASSWORD_RESET_FAILED = "PASSWORD_RESET_FAILED"

    # Multi-Factor Authentication
    MFA_ENROLLMENT_STARTED = "MFA_ENROLLMENT_STARTED"
    MFA_ENABLED = "MFA_ENABLED"
    MFA_VERIFICATION_FAILED = "MFA_VERIFICATION_FAILED"
    MFA_RECOVERY_USED = "MFA_RECOVERY_USED"
    MFA_DISABLED = "MFA_DISABLED"

    # User management
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_SUSPENDED = "USER_SUSPENDED"
    USER_DEACTIVATED = "USER_DEACTIVATED"
    ROLE_ASSIGNED = "ROLE_ASSIGNED"
    ROLE_REVOKED = "ROLE_REVOKED"

    # Library operations
    BOOK_CREATED = "BOOK_CREATED"
    BOOK_UPDATED = "BOOK_UPDATED"
    BOOK_DELETED = "BOOK_DELETED"
    COPY_ISSUED = "COPY_ISSUED"
    COPY_RETURNED = "COPY_RETURNED"
    FINE_ISSUED = "FINE_ISSUED"
    FINE_WAIVED = "FINE_WAIVED"

    # Admin
    PERMISSION_GRANTED = "PERMISSION_GRANTED"
    PERMISSION_REVOKED = "PERMISSION_REVOKED"


class AuditStatus(str, enum.Enum):
    """Outcome of the audited action."""

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PARTIAL = "PARTIAL"


class AuditLog(Base):
    """
    Immutable security and operational audit trail.

    No TimestampMixin: audit rows have a single `timestamp` field that is
    set once on insert and never changed.
    """

    __tablename__ = "audit_logs"

    # Use a sequential UUID or ULID in production for natural time ordering.
    # UUID v4 is used here for simplicity.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Audit event identifier",
    )

    # Nullable: pre-authentication events (e.g., failed login) have no user_id.
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Actor — NULL for unauthenticated events",
    )

    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction, name="audit_action_enum", create_constraint=True),
        nullable=False,
    )

    resource_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Entity type affected, e.g. 'User', 'BookCopy'",
    )
    resource_id: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="String representation of the affected resource PK",
    )

    status: Mapped[AuditStatus] = mapped_column(
        Enum(AuditStatus, name="audit_status_enum", create_constraint=True),
        nullable=False,
        default=AuditStatus.SUCCESS,
        server_default=AuditStatus.SUCCESS.value,
    )

    # Immutable creation timestamp — set by the database on insert.
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Event timestamp — set once on insert, never updated",
    )

    # Request metadata for security forensics.
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
    )
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    user: Mapped[Optional["User"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User",
        back_populates="audit_logs",
        lazy="select",
    )

    # ------------------------------------------------------------------
    # Indexes — optimised for security queries and dashboards
    # ------------------------------------------------------------------

    __table_args__ = (
        Index("ix_audit_logs_user_id", "user_id"),
        Index("ix_audit_logs_timestamp", "timestamp"),
        Index("ix_audit_logs_action", "action"),
        # Composite: find all events for a user within a time range
        Index("ix_audit_logs_user_id_timestamp", "user_id", "timestamp"),
        Index("ix_audit_logs_resource_type_id", "resource_type", "resource_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} action={self.action} "
            f"user_id={self.user_id} status={self.status}>"
        )
