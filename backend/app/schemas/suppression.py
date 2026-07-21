"""Pydantic schemas for suppression list endpoints."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SuppressionCreate(BaseModel):
    """POST /api/suppression — request body"""
    email_or_domain: str
    reason: str  # bounced, complained, unsubscribed, manual
    country: Optional[str] = None


class SuppressionOut(BaseModel):
    """Suppression entry returned in API responses"""
    id: uuid.UUID
    email_or_domain: str
    reason: str
    country: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
