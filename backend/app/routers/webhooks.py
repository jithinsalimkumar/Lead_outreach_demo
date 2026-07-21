"""
Webhooks router — receives email engagement events from external tools.

This endpoint is designed to be generic since the exact payload shape
from Instantly (or whatever email tool is used) isn't finalized yet.
It tries to match incoming events to campaign_sends rows by email
and updates the relevant engagement flags.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.campaign import CampaignSend
from app.models.enrichment import EnrichmentData
from app.models.lead import Lead
from app.schemas.webhook import WebhookEvent

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

# Map event types to the boolean field names on CampaignSend
EVENT_FIELD_MAP = {
    "open": "opened",
    "click": "clicked",
    "reply": "replied",
    "bounce": "bounced",
}


@router.post("/email-events")
async def receive_email_event(
    event: WebhookEvent,
    db: AsyncSession = Depends(get_db),
):
    """
    Receive an email engagement event and update the corresponding
    campaign_sends row.

    The matching logic:
    1. If campaign_id is provided, use it directly
    2. Find the lead by matching the email against enrichment_data
    3. Find the most recent campaign_send for that lead in that campaign
    4. Update the relevant boolean field (opened/clicked/replied/bounced)

    This endpoint is intentionally unauthenticated since it will be
    called by external webhook services. In production, you'd want to
    add webhook signature verification.
    """
    # Validate event type
    field_name = EVENT_FIELD_MAP.get(event.event_type)
    if not field_name:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown event type '{event.event_type}'. "
                   f"Must be one of: {', '.join(EVENT_FIELD_MAP.keys())}",
        )

    if not event.email:
        raise HTTPException(status_code=400, detail="Email is required")

    # Find lead(s) by email through enrichment_data
    enrichment_result = await db.execute(
        select(EnrichmentData.lead_id)
        .where(EnrichmentData.email == event.email)
        .distinct()
    )
    lead_ids = [row[0] for row in enrichment_result.all()]

    if not lead_ids:
        return {
            "status": "no_match",
            "message": f"No lead found with email {event.email}",
        }

    # Find campaign sends for these leads
    sends_query = select(CampaignSend).where(CampaignSend.lead_id.in_(lead_ids))

    # If campaign_id is provided, narrow down further
    if event.campaign_id:
        try:
            campaign_uuid = uuid.UUID(event.campaign_id)
            sends_query = sends_query.where(
                CampaignSend.campaign_id == campaign_uuid
            )
        except ValueError:
            pass  # campaign_id isn't a valid UUID, skip this filter

    # Get the most recent send
    sends_query = sends_query.order_by(CampaignSend.sequence_step.desc())
    result = await db.execute(sends_query)
    send = result.scalars().first()

    if not send:
        return {
            "status": "no_match",
            "message": f"No campaign send found for email {event.email}",
        }

    # Update the engagement flag
    setattr(send, field_name, True)
    await db.commit()

    return {
        "status": "updated",
        "message": f"Marked {field_name}=True for campaign_send {send.id}",
        "campaign_send_id": str(send.id),
    }
