"""
User model.

Represents an application user (student, librarian, admin, etc.).
Role assignment is handled via the UserRole association table.

SECURITY NOTES:
- `password_hash` stores the Argon2id digest — NEVER the plaintext password.
- Hashing logic belongs in the auth module (Phase 3).
- This model must never expose password_hash through any API response schema.
"""

import enum
import uuid

from sqlalchemy import Boolean, Enum, Index, JSON, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class AccountStatus(str, enum.Enum):
    """Lifecycle states for a user account."""

    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DEACTIVATED = "DEACTIVATED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"


class User(Base, TimestampMixin):
    """Application user entity."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Primary key — UUID v4",
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(320),  # RFC 5321 maximum email length
        nullable=False,
        unique=True,
        comment="User email — must be unique and is used as login identifier",
    )
    # Argon2id hash stored here. Hashing belongs to the auth phase.
    # This field is nullable during Phase 2 to allow schema creation before auth.
    password_hash: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Argon2id hash. NEVER store plaintext passwords.",
    )
    account_status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus, name="account_status_enum", create_constraint=True),
        nullable=False,
        default=AccountStatus.PENDING_VERIFICATION,
        server_default=AccountStatus.PENDING_VERIFICATION.value,
    )

    # ------------------------------------------------------------------
    # Multi-Factor Authentication (Phase 7)
    # ------------------------------------------------------------------
    is_mfa_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
        comment="Flag indicating if TOTP MFA is active for this account",
    )
    mfa_secret: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Base32 TOTP secret. Never expose in API responses or audit logs.",
    )
    mfa_recovery_codes: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="List of SHA-256 hashes of one-time recovery codes.",
    )

    @property
    def is_verified(self) -> bool:
        """Indicates whether email verification has completed (status is not PENDING_VERIFICATION)."""
        return self.account_status != AccountStatus.PENDING_VERIFICATION

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    # Many-to-many: User ↔ Role via user_roles association table
    roles: Mapped[list["Role"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Role",
        secondary="user_roles",
        back_populates="users",
        lazy="selectin",
    )

    # One-to-many: User → Session (auth refresh tokens)
    sessions: Mapped[list["UserSession"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # One-to-many: User → BorrowRecord
    borrow_records: Mapped[list["BorrowRecord"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "BorrowRecord",
        back_populates="user",
        lazy="select",
    )

    # One-to-many: User → AuditLog
    audit_logs: Mapped[list["AuditLog"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "AuditLog",
        back_populates="user",
        lazy="select",
    )

    # ------------------------------------------------------------------
    # Constraints & indexes
    # ------------------------------------------------------------------

    __table_args__ = (
        # Unique index on email (fast login lookup)
        UniqueConstraint("email", name="uq_users_email"),
        # Composite index to support status-filtered user queries
        Index("ix_users_account_status", "account_status"),
        Index("ix_users_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} status={self.account_status}>"
