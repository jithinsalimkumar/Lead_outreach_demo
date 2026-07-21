"""Pydantic schemas for user endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    """User data returned in API responses"""
    id: uuid.UUID
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserRoleUpdate(BaseModel):
    """PATCH /api/users/{id}/role — request body"""
    role: str  # "admin" or "member"
