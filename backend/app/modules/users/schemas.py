"""
Pydantic schemas for the User management module.
"""

from pydantic import BaseModel, Field
from app.models.user import AccountStatus


class UserStatusUpdateRequest(BaseModel):
    """Payload for updating user account status."""

    account_status: AccountStatus = Field(
        ...,
        description="Target account lifecycle status (ACTIVE, SUSPENDED, DEACTIVATED)",
    )
