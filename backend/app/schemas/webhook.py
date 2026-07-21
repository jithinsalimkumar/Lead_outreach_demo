"""Pydantic schemas for webhook receiver endpoint."""

from typing import Any, Optional

from pydantic import BaseModel


class WebhookEvent(BaseModel):
    """
    POST /api/webhooks/email-events — request body

    This is intentionally flexible since the exact payload shape from
    the eventual email tool (Instantly) isn't finalized yet.

    The receiver will try to match on email + campaign to find the
    campaign_sends row, then update the relevant boolean field.
    """
    event_type: str  # "open", "click", "reply", "bounce"
    email: Optional[str] = None  # Recipient email
    campaign_id: Optional[str] = None  # Campaign identifier
    timestamp: Optional[str] = None
    # Extra data that we'll store but not process yet
    metadata: Optional[dict[str, Any]] = None
