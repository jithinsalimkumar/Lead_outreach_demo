"""Pydantic schemas for enrichment data endpoints."""

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class EnrichmentOut(BaseModel):
    """Enrichment data returned in API responses"""
    id: uuid.UUID
    lead_id: uuid.UUID
    email: Optional[str] = None
    phone: Optional[str] = None
    verification_status: str
    provider: str
    score: Optional[int] = None
    raw_response: Optional[Any] = None
    created_at: datetime

    model_config = {"from_attributes": True}
