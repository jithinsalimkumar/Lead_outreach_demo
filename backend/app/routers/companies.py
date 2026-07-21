"""
Companies router — list and detail views for discovered companies.

Companies are created by the scraping pipeline (not manually via API).
This router provides read-only access with filtering.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user
from app.models.company import Company
from app.models.lead import Lead
from app.models.user import User
from app.schemas.company import CompanyDetailOut, CompanyOut

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("", response_model=dict)
async def list_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    country: str | None = Query(None, description="Filter by country: US, UK, CA"),
    size_bucket: str | None = Query(None, description="Filter by size: small, large"),
    has_leads: bool | None = Query(None, description="Filter to companies that have leads"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List companies with optional filters and pagination."""
    # Build the base query
    query = select(Company)
    count_query = select(func.count(Company.id))

    # Apply filters
    if country:
        query = query.where(Company.country == country)
        count_query = count_query.where(Company.country == country)
    if size_bucket:
        query = query.where(Company.size_bucket == size_bucket)
        count_query = count_query.where(Company.size_bucket == size_bucket)
    if has_leads is True:
        # Only companies that have at least one lead
        query = query.where(Company.id.in_(select(Lead.company_id).distinct()))
        count_query = count_query.where(Company.id.in_(select(Lead.company_id).distinct()))

    # Get total count
    total = (await db.execute(count_query)).scalar()

    # Paginate and fetch
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Company.created_at.desc()).offset(offset).limit(page_size)
    )
    companies = result.scalars().all()

    return {
        "items": [CompanyOut.model_validate(c) for c in companies],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
    }


@router.get("/{company_id}", response_model=CompanyDetailOut)
async def get_company(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single company with its job postings and lead count."""
    result = await db.execute(
        select(Company)
        .options(selectinload(Company.job_postings))
        .where(Company.id == company_id)
    )
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Count leads for this company
    lead_count_result = await db.execute(
        select(func.count(Lead.id)).where(Lead.company_id == company_id)
    )
    lead_count = lead_count_result.scalar()

    # Build response — we need to manually construct since lead_count
    # isn't a model attribute
    response = CompanyDetailOut.model_validate(company)
    response.lead_count = lead_count
    return response
