"""
Pydantic schemas for permissions module.
"""

from datetime import datetime
from typing import Dict, List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field


class PermissionOut(BaseModel):
    """Permission detail response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str = Field(..., description="Canonical permission name (resource:action)")
    description: Optional[str] = None
    created_at: Optional[datetime] = None


class RolePermissionsMatrixOut(BaseModel):
    """Role-permission mapping matrix response."""
    roles: List[str]
    permissions: List[PermissionOut]
    matrix: Dict[str, List[str]] = Field(
        ...,
        description="Dictionary mapping role name to list of permission names",
    )


class UserPermissionsOut(BaseModel):
    """Effective permissions for a user."""
    user_id: uuid.UUID
    roles: List[str]
    permissions: List[str]
