"""
Real-time Event Taxonomy and Schemas for PustakHub.

Defines canonical event types and strictly validated Pydantic schemas for
server-to-client real-time updates over WebSocket / Redis Pub/Sub.

SECURITY:
  - Events MUST NEVER contain raw secrets, passwords, password hashes, JWTs,
    refresh tokens, OTPs, MFA secrets, or encryption keys.
  - Payloads are minimized to resource metadata and identifiers necessary for UI cache invalidation.
"""

from datetime import datetime, timezone
import enum
from typing import Any, Dict, Optional, Set
import uuid

from pydantic import BaseModel, ConfigDict, Field


class RealtimeEventType(str, enum.Enum):
    """Canonical real-time event types."""

    # IAM & Account lifecycle
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_SUSPENDED = "USER_SUSPENDED"
    USER_DEACTIVATED = "USER_DEACTIVATED"
    ROLE_ASSIGNED = "ROLE_ASSIGNED"
    ROLE_REVOKED = "ROLE_REVOKED"

    # Catalog & Taxonomy
    BOOK_CREATED = "BOOK_CREATED"
    BOOK_UPDATED = "BOOK_UPDATED"
    BOOK_DELETED = "BOOK_DELETED"
    COPY_CREATED = "COPY_CREATED"
    COPY_UPDATED = "COPY_UPDATED"
    COPY_DELETED = "COPY_DELETED"
    CATEGORY_CREATED = "CATEGORY_CREATED"
    CATEGORY_UPDATED = "CATEGORY_UPDATED"
    CATEGORY_DELETED = "CATEGORY_DELETED"

    # Circulation & Fines
    COPY_ISSUED = "COPY_ISSUED"
    COPY_RETURNED = "COPY_RETURNED"
    FINE_ISSUED = "FINE_ISSUED"
    FINE_PAID = "FINE_PAID"
    FINE_WAIVED = "FINE_WAIVED"

    # Audit Trail
    AUDIT_EVENT_CREATED = "AUDIT_EVENT_CREATED"

    # System & Heartbeat
    PING = "PING"
    PONG = "PONG"
    SYSTEM_NOTIFICATION = "SYSTEM_NOTIFICATION"


# Event Categories for Authorization & Routing
CATALOG_EVENTS: Set[RealtimeEventType] = {
    RealtimeEventType.BOOK_CREATED,
    RealtimeEventType.BOOK_UPDATED,
    RealtimeEventType.BOOK_DELETED,
    RealtimeEventType.COPY_CREATED,
    RealtimeEventType.COPY_UPDATED,
    RealtimeEventType.COPY_DELETED,
    RealtimeEventType.CATEGORY_CREATED,
    RealtimeEventType.CATEGORY_UPDATED,
    RealtimeEventType.CATEGORY_DELETED,
}

CIRCULATION_EVENTS: Set[RealtimeEventType] = {
    RealtimeEventType.COPY_ISSUED,
    RealtimeEventType.COPY_RETURNED,
    RealtimeEventType.FINE_ISSUED,
    RealtimeEventType.FINE_PAID,
    RealtimeEventType.FINE_WAIVED,
}

IAM_EVENTS: Set[RealtimeEventType] = {
    RealtimeEventType.USER_CREATED,
    RealtimeEventType.USER_UPDATED,
    RealtimeEventType.USER_SUSPENDED,
    RealtimeEventType.USER_DEACTIVATED,
    RealtimeEventType.ROLE_ASSIGNED,
    RealtimeEventType.ROLE_REVOKED,
}

AUDIT_EVENTS: Set[RealtimeEventType] = {
    RealtimeEventType.AUDIT_EVENT_CREATED,
}


class RealtimeEvent(BaseModel):
    """
    Standardized payload for real-time messages.

    Attributes:
        id: Unique identifier for event deduplication.
        type: Canonical RealtimeEventType.
        timestamp: UTC timestamp when the event occurred.
        resource_type: Type of resource affected (e.g. 'Book', 'BorrowRecord', 'User').
        resource_id: Non-sensitive string identifier of the resource.
        actor_user_id: User who triggered the action (if applicable).
        target_user_id: Recipient user ID for user-scoped private delivery.
        data: Optional sanitized metadata dictionary (zero secrets).
        request_id: Optional correlation ID for distributed tracing.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: RealtimeEventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    actor_user_id: Optional[str] = None
    target_user_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
    )
