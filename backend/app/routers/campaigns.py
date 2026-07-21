"""
Campaigns router — create, list, detail with metrics, and lead management.

Campaigns represent outreach sequences targeting a set of enriched leads.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user
from app.models.campaign import Campaign, CampaignSend
from app.models.company import Company
from app.models.enrichment import EnrichmentData
from app.models.lead import Lead
from app.models.user import User
from app.schemas.campaign import (
    CampaignAddLeads,
    CampaignCreate,
    CampaignDetailOut,
    CampaignLeadOut,
    CampaignOut,
    CampaignSendSimple,
)

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


@router.get("", response_model=dict)
async def list_campaigns(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all campaigns with aggregated performance metrics."""
    # Count total campaigns
    total = (await db.execute(select(func.count(Campaign.id)))).scalar()

    # Fetch campaigns
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Campaign)
        .order_by(Campaign.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    campaigns = result.scalars().all()

    # Build response with performance metrics for each campaign
    items = []
    for campaign in campaigns:
        # Aggregate send stats for this campaign
        stats = await db.execute(
            select(
                func.count(CampaignSend.id).label("total"),
                func.count(CampaignSend.id).filter(CampaignSend.opened == True).label("opened"),
                func.count(CampaignSend.id).filter(CampaignSend.clicked == True).label("clicked"),
                func.count(CampaignSend.id).filter(CampaignSend.replied == True).label("replied"),
                func.count(CampaignSend.id).filter(CampaignSend.bounced == True).label("bounced"),
            ).where(CampaignSend.campaign_id == campaign.id)
        )
        row = stats.one()

        campaign_out = CampaignOut(
            id=campaign.id,
            name=campaign.name,
            template_id=campaign.template_id,
            sending_account=campaign.sending_account,
            daily_limit=campaign.daily_limit,
            country_scope=campaign.country_scope,
            created_by=campaign.created_by,
            created_at=campaign.created_at,
            total_sends=row.total,
            total_opened=row.opened,
            total_clicked=row.clicked,
            total_replied=row.replied,
            total_bounced=row.bounced,
        )
        items.append(campaign_out)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
    }


@router.post("", response_model=CampaignOut, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    body: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new outreach campaign."""
    campaign = Campaign(
        name=body.name,
        template_id=body.template_id,
        sending_account=body.sending_account,
        daily_limit=body.daily_limit,
        country_scope=body.country_scope,
        created_by=current_user.id,
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)

    return CampaignOut(
        id=campaign.id,
        name=campaign.name,
        template_id=campaign.template_id,
        sending_account=campaign.sending_account,
        daily_limit=campaign.daily_limit,
        country_scope=campaign.country_scope,
        created_by=campaign.created_by,
        created_at=campaign.created_at,
        total_sends=0,
        total_opened=0,
        total_clicked=0,
        total_replied=0,
        total_bounced=0,
    )


@router.get("/{campaign_id}", response_model=CampaignDetailOut)
async def get_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get campaign detail with performance metrics and all leads."""
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Get aggregate stats
    stats = await db.execute(
        select(
            func.count(CampaignSend.id).label("total"),
            func.count(CampaignSend.id).filter(CampaignSend.opened == True).label("opened"),
            func.count(CampaignSend.id).filter(CampaignSend.clicked == True).label("clicked"),
            func.count(CampaignSend.id).filter(CampaignSend.replied == True).label("replied"),
            func.count(CampaignSend.id).filter(CampaignSend.bounced == True).label("bounced"),
        ).where(CampaignSend.campaign_id == campaign_id)
    )
    stat_row = stats.one()

    # Get all sends for this campaign with lead + company info
    sends_result = await db.execute(
        select(CampaignSend)
        .options(
            selectinload(CampaignSend.lead)
            .selectinload(Lead.company),
            selectinload(CampaignSend.lead)
            .selectinload(Lead.enrichment_data),
        )
        .where(CampaignSend.campaign_id == campaign_id)
        .order_by(CampaignSend.lead_id, CampaignSend.sequence_step)
    )
    sends = sends_result.scalars().all()

    # Group sends by lead
    leads_map: dict[uuid.UUID, CampaignLeadOut] = {}
    for send in sends:
        lead = send.lead
        if lead.id not in leads_map:
            # Get the best email from enrichment data
            best_email = None
            if lead.enrichment_data:
                verified = [e for e in lead.enrichment_data if e.verification_status == "verified"]
                if verified:
                    best_email = verified[0].email
                elif lead.enrichment_data:
                    best_email = lead.enrichment_data[0].email

            leads_map[lead.id] = CampaignLeadOut(
                lead_id=lead.id,
                full_name=lead.full_name,
                job_title=lead.job_title,
                company_name=lead.company.name if lead.company else None,
                email=best_email,
                sends=[],
            )

        leads_map[lead.id].sends.append(CampaignSendSimple(
            id=send.id,
            sequence_step=send.sequence_step,
            sent_at=send.sent_at,
            opened=send.opened,
            clicked=send.clicked,
            replied=send.replied,
            bounced=send.bounced,
        ))

    return CampaignDetailOut(
        id=campaign.id,
        name=campaign.name,
        template_id=campaign.template_id,
        sending_account=campaign.sending_account,
        daily_limit=campaign.daily_limit,
        country_scope=campaign.country_scope,
        created_by=campaign.created_by,
        created_at=campaign.created_at,
        total_sends=stat_row.total,
        total_opened=stat_row.opened,
        total_clicked=stat_row.clicked,
        total_replied=stat_row.replied,
        total_bounced=stat_row.bounced,
        leads=list(leads_map.values()),
    )


@router.post("/{campaign_id}/leads", status_code=status.HTTP_201_CREATED)
async def add_leads_to_campaign(
    campaign_id: uuid.UUID,
    body: CampaignAddLeads,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add leads to a campaign. Creates campaign_send entries for sequence step 1.
    Only leads that aren't already in the campaign are added.
    """
    # Verify campaign exists
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    if not campaign_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Find which leads are already in the campaign
    existing_result = await db.execute(
        select(CampaignSend.lead_id)
        .where(CampaignSend.campaign_id == campaign_id)
        .where(CampaignSend.sequence_step == 1)
    )
    existing_lead_ids = {row[0] for row in existing_result.all()}

    # Add new leads
    added = 0
    for lead_id in body.lead_ids:
        if lead_id in existing_lead_ids:
            continue

        # Verify lead exists
        lead_result = await db.execute(select(Lead).where(Lead.id == lead_id))
        if not lead_result.scalar_one_or_none():
            continue

        send = CampaignSend(
            lead_id=lead_id,
            campaign_id=campaign_id,
            sequence_step=1,
        )
        db.add(send)
        added += 1

    await db.commit()

    return {"message": f"Added {added} leads to campaign", "added": added}


@router.delete("/{campaign_id}/leads/{lead_id}")
async def remove_lead_from_campaign(
    campaign_id: uuid.UUID,
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a lead and all their sends from a campaign."""
    result = await db.execute(
        select(CampaignSend)
        .where(CampaignSend.campaign_id == campaign_id)
        .where(CampaignSend.lead_id == lead_id)
    )
    sends = result.scalars().all()

    if not sends:
        raise HTTPException(status_code=404, detail="Lead not found in this campaign")

    for send in sends:
        await db.delete(send)

    await db.commit()
    return {"message": "Lead removed from campaign"}
