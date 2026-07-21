"""
Enrichment router — view enrichment data and stub trigger endpoint.

The actual enrichment logic (calling Prospeo/Vibe Prospecting) will be
implemented in background workers. This router just provides the API
surface for viewing data and triggering enrichment.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.enrichment import EnrichmentData
from app.models.lead import Lead
from app.models.user import User
from app.schemas.enrichment import EnrichmentOut

router = APIRouter(prefix="/api/leads", tags=["enrichment"])


@router.get("/{lead_id}/enrichment", response_model=list[EnrichmentOut])
async def get_lead_enrichment(
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all enrichment data records for a lead."""
    # Verify lead exists
    lead_result = await db.execute(select(Lead).where(Lead.id == lead_id))
    if not lead_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Lead not found")

    result = await db.execute(
        select(EnrichmentData)
        .where(EnrichmentData.lead_id == lead_id)
        .order_by(EnrichmentData.created_at.desc())
    )
    records = result.scalars().all()
    return [EnrichmentOut.model_validate(r) for r in records]


@router.post("/{lead_id}/enrichment/trigger")
async def trigger_enrichment(
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    STUB: Trigger enrichment for a lead.

    This is a placeholder endpoint. The actual enrichment logic will be
    implemented as a background worker that:
    1. Calls Prospeo or Vibe Prospecting API
    2. Saves the enrichment data to the database
    3. Updates the lead's status

    For now, it just returns a message acknowledging the request.
    """
    # Verify lead exists
    lead_result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = lead_result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # TODO: When background workers are built, this will:
    # 1. Enqueue an enrichment job via Arq/Redis
    # 2. Update lead.status to "enriching"
    # For now, just acknowledge the request

    return {
        "message": f"Enrichment trigger acknowledged for lead {lead_id}",
        "status": "stub — background worker not yet implemented",
        "lead_name": lead.full_name,
    }
