"""
UserSession model — persistence foundation for authentication refresh tokens.

DESIGN RATIONALE
================
Rather than storing the raw refresh token string, we store a SHA-256 hash
of the token (token_hash). This approach means:

  - If the sessions table is compromised, attackers cannot replay tokens
    because they do not have the original value.
  - The raw token is held only in the client's secure storage (HttpOnly cookie
    or secure storage). The server only ever sees it during the refresh call,
    hashes it, and compares to the stored digest.
  - This is analogous to how password hashes work but lighter (SHA-256 is
    sufficient here because refresh tokens are high-entropy random strings,
    not low-entropy user-chosen values).

The actual token issuance, hashing, and rotation logic belongs in Phase 3
(Authentication). This model only establishes the schema.

SECURITY NOTES:
  - Never log or return `token_hash` through any API endpoint.
  - The `token_hash` column must never appear in any Pydantic response schema.
  - Expired and revoked sessions should be purged by a background job (planned).
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class UserSession(Base, TimestampMixin):
    """
    Persisted refresh-token session.

    One row per active refresh token issued to a user.
    """

    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # FK → users.id — cascades delete so sessions are removed with the user.
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # SHA-256 hex digest of the raw refresh token.
    # NEVER store the raw token here.
    token_hash: Mapped[str] = mapped_column(
        String(64),   # SHA-256 produces 64 hex characters
        nullable=False,
        unique=True,
        comment="SHA-256 hex digest of the refresh token. Never store the raw token.",
    )

    # When does this session expire?
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Has this session been explicitly revoked (logout / rotation)?
    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # Optional: device/client metadata for security audit display.
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    user: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User",
        back_populates="sessions",
        lazy="select",
    )

    # ------------------------------------------------------------------
    # Constraints & indexes
    # ------------------------------------------------------------------

    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_user_sessions_token_hash"),
        # Fast lookup: find active (non-revoked, non-expired) sessions for a user.
        Index("ix_user_sessions_user_id_is_revoked", "user_id", "is_revoked"),
        Index("ix_user_sessions_expires_at", "expires_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<UserSession id={self.id} user_id={self.user_id} "
            f"revoked={self.is_revoked}>"
        )
