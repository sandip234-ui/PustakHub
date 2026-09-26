"""
Pydantic schemas for roles module.
"""

from datetime import datetime
from typing import List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.modules.permissions.schemas import PermissionOut


class RoleOut(BaseModel):
    """Role information with associated permissions."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: Optional[str] = None
    permissions: List[PermissionOut] = []
    created_at: Optional[datetime] = None


class RoleCreate(BaseModel):
    """Schema for creating a new role."""
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None


class RoleAssignRequest(BaseModel):
    """Schema for assigning/revoking role to/from a user."""
    role_name: str = Field(..., description="Name of role to assign (e.g. LIBRARIAN)")


class PermissionAssignRequest(BaseModel):
    """Schema for assigning a permission to a role."""
    permission_name: str = Field(..., description="Canonical name of permission (e.g. book:create)")
