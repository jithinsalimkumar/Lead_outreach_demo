"""
Leads router — listing, detail, and manual override endpoints.

Leads are discovered by the scraping pipeline. This router provides
read access with rich filtering, plus manual actions like marking
a lead as excluded or changing their pipeline status.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user
from app.models.campaign import CampaignSend, Campaign
from app.models.company import Company
from app.models.enrichment import EnrichmentData
from app.models.lead import Lead
from app.models.user import User
from app.schemas.lead import (
    CampaignSendOut,
    LeadDetailOut,
    LeadExcludeUpdate,
    LeadOut,
    LeadStatusUpdate,
)
from app.schemas.company import CompanyOut, JobPostingOut
from app.schemas.enrichment import EnrichmentOut

router = APIRouter(prefix="/api/leads", tags=["leads"])

# Valid lead statuses for validation
VALID_STATUSES = {
    "new", "filtered", "scraping_contacts", "contacts_found", "enriching",
    "enriched", "queued_for_outreach", "sent", "replied", "bounced", "unsubscribed",
}


@router.get("", response_model=dict)
async def list_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, description="Filter by pipeline status"),
    country: str | None = Query(None, description="Filter by company country"),
    size_bucket: str | None = Query(None, description="Filter by company size bucket"),
    score_min: int | None = Query(None, description="Minimum enrichment score"),
    score_max: int | None = Query(None, description="Maximum enrichment score"),
    is_excluded: bool | None = Query(None, description="Filter by excluded status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List leads with filtering and pagination.

    Joins with company for country/size filtering, and with enrichment_data
    for score filtering. Returns flattened company info for table display.
    """
    # Base query with company join for filters
    query = (
        select(Lead)
        .join(Company, Lead.company_id == Company.id)
        .options(selectinload(Lead.company))
    )
    count_query = (
        select(func.count(Lead.id))
        .join(Company, Lead.company_id == Company.id)
    )

    # Apply filters
    if status:
        query = query.where(Lead.status == status)
        count_query = count_query.where(Lead.status == status)
    if country:
        query = query.where(Company.country == country)
        count_query = count_query.where(Company.country == country)
    if size_bucket:
        query = query.where(Company.size_bucket == size_bucket)
        count_query = count_query.where(Company.size_bucket == size_bucket)
    if is_excluded is not None:
        query = query.where(Lead.is_excluded == is_excluded)
        count_query = count_query.where(Lead.is_excluded == is_excluded)

    # Score filtering requires a subquery on enrichment_data
    if score_min is not None or score_max is not None:
        # Get lead IDs that have enrichment scores in the requested range
        score_subquery = select(EnrichmentData.lead_id).distinct()
        if score_min is not None:
            score_subquery = score_subquery.where(EnrichmentData.score >= score_min)
        if score_max is not None:
            score_subquery = score_subquery.where(EnrichmentData.score <= score_max)
        query = query.where(Lead.id.in_(score_subquery))
        count_query = count_query.where(Lead.id.in_(score_subquery))

    # Get total count
    total = (await db.execute(count_query)).scalar()

    # Paginate and fetch
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Lead.created_at.desc()).offset(offset).limit(page_size)
    )
    leads = result.scalars().unique().all()

    # Build response with flattened company info and best score
    items = []
    for lead in leads:
        lead_dict = LeadOut.model_validate(lead)
        # Add flattened company info
        if lead.company:
            lead_dict.company_name = lead.company.name
            lead_dict.company_country = lead.company.country
            lead_dict.company_size_bucket = lead.company.size_bucket
        # Get best enrichment score for this lead
        score_result = await db.execute(
            select(func.max(EnrichmentData.score))
            .where(EnrichmentData.lead_id == lead.id)
        )
        lead_dict.best_score = score_result.scalar()
        items.append(lead_dict)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
    }


@router.get("/{lead_id}", response_model=LeadDetailOut)
async def get_lead(
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get full lead detail including company info, job postings,
    enrichment history, and campaign send history.
    """
    result = await db.execute(
        select(Lead)
        .options(
            selectinload(Lead.company).selectinload(Company.job_postings),
            selectinload(Lead.enrichment_data),
            selectinload(Lead.campaign_sends).selectinload(CampaignSend.campaign),
        )
        .where(Lead.id == lead_id)
    )
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Build campaign sends with campaign name
    sends = []
    for send in lead.campaign_sends:
        send_out = CampaignSendOut(
            id=send.id,
            campaign_id=send.campaign_id,
            campaign_name=send.campaign.name if send.campaign else None,
            sequence_step=send.sequence_step,
            sent_at=send.sent_at,
            opened=send.opened,
            clicked=send.clicked,
            replied=send.replied,
            bounced=send.bounced,
        )
        sends.append(send_out)

    return LeadDetailOut(
        id=lead.id,
        full_name=lead.full_name,
        job_title=lead.job_title,
        linkedin_url=lead.linkedin_url,
        is_excluded=lead.is_excluded,
        status=lead.status,
        created_at=lead.created_at,
        company=CompanyOut.model_validate(lead.company) if lead.company else None,
        job_postings=[
            JobPostingOut.model_validate(jp)
            for jp in (lead.company.job_postings if lead.company else [])
        ],
        enrichment_data=[
            EnrichmentOut.model_validate(e) for e in lead.enrichment_data
        ],
        campaign_sends=sends,
    )


@router.patch("/{lead_id}/exclude", response_model=LeadOut)
async def toggle_exclude(
    lead_id: uuid.UUID,
    body: LeadExcludeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark or unmark a lead as excluded (e.g. HR/recruiter filtering)."""
    result = await db.execute(
        select(Lead).options(selectinload(Lead.company)).where(Lead.id == lead_id)
    )
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead.is_excluded = body.is_excluded
    await db.commit()
    await db.refresh(lead)

    lead_out = LeadOut.model_validate(lead)
    if lead.company:
        lead_out.company_name = lead.company.name
        lead_out.company_country = lead.company.country
        lead_out.company_size_bucket = lead.company.size_bucket
    return lead_out


@router.patch("/{lead_id}/status", response_model=LeadOut)
async def update_status(
    lead_id: uuid.UUID,
    body: LeadStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually override a lead's pipeline status."""
    if body.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(sorted(VALID_STATUSES))}",
        )

    result = await db.execute(
        select(Lead).options(selectinload(Lead.company)).where(Lead.id == lead_id)
    )
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead.status = body.status
    await db.commit()
    await db.refresh(lead)

    lead_out = LeadOut.model_validate(lead)
    if lead.company:
        lead_out.company_name = lead.company.name
        lead_out.company_country = lead.company.country
        lead_out.company_size_bucket = lead.company.size_bucket
    return lead_out
