"""Pydantic schemas for settings endpoints."""

from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel


class SettingOut(BaseModel):
    """Setting returned in API responses — value is masked for security"""
    id: uuid.UUID
    key: str
    masked_value: str  # e.g. "****abcd"
    updated_by: Optional[uuid.UUID] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SettingUpdate(BaseModel):
    """PUT /api/settings/{key} — request body"""
    value: str  # The plaintext value to encrypt and store


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper"""
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int
