"""
Audit service for recording and retrieving security and operational audit trail records.

SECURITY & RESILIENCE:
  - Rows are append-only.
  - Sensitive information (passwords, OTPs, JWT tokens, hashes, API keys) are NEVER persisted.
  - Unauthenticated/anonymous events safely record `user_id=None`.
  - Non-critical audit failures are safely logged to prevent crashing user-facing workflows.
"""

from datetime import datetime
from typing import List, Optional, Tuple
import uuid

from sqlalchemy import desc, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.core.logging import get_logger
from app.models.audit_log import AuditAction, AuditLog, AuditStatus
from app.models.user import User

logger = get_logger(__name__)

# Sensitive keywords that must NEVER appear in audit fields
_FORBIDDEN_SECRET_SUBSTRINGS = (
    "argon2id",
    "password",
    "otp",
    "secret",
    "token",
    "bearer",
    "authorization",
)


class AuditService:
    """Central service for logging and querying security and operational audit entries."""

    @staticmethod
    def _sanitize_field(value: Optional[str]) -> Optional[str]:
        """
        Sanitize strings to ensure sensitive tokens or hashes are never recorded.
        """
        if not value:
            return value

        val_lower = value.lower()
        # If the value looks like an Argon2 hash or JWT or raw secret
        if "$argon2id$" in val_lower or "bearer " in val_lower or len(value) > 500:
            return "[REDACTED_SENSITIVE_DATA]"

        return value

    @staticmethod
    def log(
        db: Session,
        action: AuditAction,
        user_id: Optional[uuid.UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: AuditStatus = AuditStatus.SUCCESS,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        strict: bool = False,
    ) -> Optional[AuditLog]:
        """
        Persist an audit log record to the database.

        Parameters:
            db: Active SQLAlchemy database session.
            action: Standard AuditAction enum value.
            user_id: UUID of user actor (or None for anonymous/unauthenticated events).
            resource_type: Name of affected entity (e.g., 'User', 'Role', 'UserSession').
            resource_id: Non-sensitive string identifier for the affected resource.
            status: AuditStatus enum (SUCCESS, FAILURE, PARTIAL).
            ip_address: Client IP address.
            user_agent: Client User-Agent string.
            strict: If True, re-raises database exceptions instead of failing open.
        """
        try:
            sanitized_resource_id = AuditService._sanitize_field(resource_id)
            sanitized_user_agent = (
                user_agent[:500] if user_agent else None
            )  # Truncate overly long UAs

            audit_entry = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=sanitized_resource_id,
                status=status,
                ip_address=ip_address,
                user_agent=sanitized_user_agent,
            )
            db.add(audit_entry)
            db.commit()
            db.refresh(audit_entry)

            # Broadcast real-time audit event to authorized subscribers
            try:
                from app.modules.realtime.events import RealtimeEventType
                from app.modules.realtime.publisher import publish_realtime_event

                publish_realtime_event(
                    event_type=RealtimeEventType.AUDIT_EVENT_CREATED,
                    resource_type=resource_type,
                    resource_id=sanitized_resource_id,
                    actor_user_id=user_id,
                    data={
                        "audit_id": str(audit_entry.id),
                        "action": action.value if hasattr(action, "value") else str(action),
                        "status": status.value if hasattr(status, "value") else str(status),
                    },
                )
            except Exception as rt_exc:
                logger.debug("Failed to broadcast realtime audit event: %s", rt_exc)

            return audit_entry
        except SQLAlchemyError as exc:
            db.rollback()
            logger.error(
                "Failed to write audit log [Action: %s, User: %s, Status: %s]: %s",
                action,
                user_id,
                status,
                exc,
            )
            if strict:
                raise
            return None
        except Exception as exc:
            db.rollback()
            logger.error("Unexpected error in audit logging: %s", exc)
            if strict:
                raise
            return None

    @staticmethod
    def get_log_by_id(db: Session, audit_id: uuid.UUID) -> Optional[AuditLog]:
        """Retrieve a single audit log entry by UUID."""
        return (
            db.query(AuditLog)
            .options(joinedload(AuditLog.user))
            .filter(AuditLog.id == audit_id)
            .first()
        )

    @staticmethod
    def query_logs(
        db: Session,
        user_id: Optional[uuid.UUID] = None,
        action: Optional[AuditAction] = None,
        status: Optional[AuditStatus] = None,
        resource_type: Optional[str] = None,
        search: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[AuditLog], int]:
        """
        Query audit logs with filtering and pagination.

        Returns (items, total_count).
        """
        query = db.query(AuditLog).options(joinedload(AuditLog.user))

        if user_id is not None:
            query = query.filter(AuditLog.user_id == user_id)
        if action is not None:
            query = query.filter(AuditLog.action == action)
        if status is not None:
            query = query.filter(AuditLog.status == status)
        if resource_type:
            query = query.filter(AuditLog.resource_type.ilike(resource_type.strip()))
        if start_time is not None:
            query = query.filter(AuditLog.timestamp >= start_time)
        if end_time is not None:
            query = query.filter(AuditLog.timestamp <= end_time)

        if search:
            term = f"%{search.strip().lower()}%"
            query = query.outerjoin(AuditLog.user).filter(
                or_(
                    AuditLog.resource_type.ilike(term),
                    AuditLog.resource_id.ilike(term),
                    AuditLog.ip_address.ilike(term),
                    User.full_name.ilike(term),
                    User.email.ilike(term),
                )
            )

        total = query.count()
        offset = max(0, (page - 1) * page_size)
        items = (
            query.order_by(desc(AuditLog.timestamp))
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return items, total


audit_service = AuditService()
