"""
Pydantic schemas for audit logs module.
"""

from datetime import datetime
from typing import List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.audit_log import AuditAction, AuditStatus


class AuditLogOut(BaseModel):
    """Sanitized representation of an audit log entry."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    action: AuditAction
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    status: AuditStatus
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditLogListResponse(BaseModel):
    """Paginated list response of audit logs."""
    total: int
    page: int
    page_size: int
    items: List[AuditLogOut]


class AuditActionInfo(BaseModel):
    """Metadata describing a canonical audit action."""
    action: str
    category: str
    description: str


class AuditActionsResponse(BaseModel):
    """List of all supported audit actions grouped by category."""
    actions: List[AuditActionInfo]
    categories: List[str]
