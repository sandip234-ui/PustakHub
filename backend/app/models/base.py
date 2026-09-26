"""
Declarative Base and shared column mixins for all SQLAlchemy models.

Every model in app/models/ inherits from `Base`.

Naming conventions are explicitly declared so that Alembic-generated
constraint names are deterministic and portable across databases.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Shared declarative base for all PustakHub SQLAlchemy models.

    Uses SQLAlchemy 2.0 mapped_column / Mapped style throughout.
    Constraint naming conventions ensure Alembic produces stable names.
    """

    # Explicit naming conventions keep constraint names deterministic,
    # which is critical for reliable Alembic autogenerate comparisons.
    naming_convention: dict = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }


# ---------------------------------------------------------------------------
# Timestamp mixin
# ---------------------------------------------------------------------------


class TimestampMixin:
    """
    Adds `created_at` and `updated_at` to any model that inherits this mixin.

    - created_at: set once on INSERT, never changes.
    - updated_at: set on INSERT and updated automatically on every UPDATE
                  via a server-side trigger (onupdate).
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
