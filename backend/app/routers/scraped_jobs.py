"""
Scraped Jobs router — listing and exporting raw job postings.

Provides a raw view of all job postings joined with their companies,
before any lead generation or enrichment takes place.
"""

import csv
import io
from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func, select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.deps import get_current_user
from app.models.company import Company
from app.models.job_posting import JobPosting
from app.models.user import User

router = APIRouter(prefix="/api/scraped-jobs", tags=["scraped-jobs"])


class ScrapedJobOut(BaseModel):
    id: str
    company_name: str
    company_domain: str
    country: str
    job_title: str
    tier_signal: str
    job_url: str
    portal: str
    location: Optional[str] = None
    scraped_at: datetime

    model_config = {"from_attributes": True}


def build_query(
    country: str | None = None,
    portal: str | None = None,
    tier_signal: str | None = None,
    search: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
):
    """Helper to build the base query with filters."""
    query = select(JobPosting, Company).outerjoin(Company, JobPosting.company_id == Company.id)

    if country:
        query = query.where(Company.country == country)
    if portal:
        query = query.where(JobPosting.portal == portal)
    if tier_signal:
        query = query.where(JobPosting.tier_signal == tier_signal)
    if date_from:
        # Cast scraped_at to date for comparison
        query = query.where(func.date(JobPosting.scraped_at) >= date_from)
    if date_to:
        query = query.where(func.date(JobPosting.scraped_at) <= date_to)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Company.name.ilike(search_term),
                JobPosting.title.ilike(search_term),
            )
        )
        
    return query


@router.get("", response_model=dict)
async def list_scraped_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    country: str | None = Query(None),
    portal: str | None = Query(None),
    tier_signal: str | None = Query(None),
    search: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List scraped jobs with filtering and pagination."""
    base_query = build_query(country, portal, tier_signal, search, date_from, date_to)
    
    # Get total count
    count_query = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Paginate and fetch
    offset = (page - 1) * page_size
    query = base_query.order_by(JobPosting.scraped_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    
    # Process results
    items = []
    for job, company in result.all():
        items.append(
            ScrapedJobOut(
                id=str(job.id),
                company_name=company.name if company else "Unknown",
                company_domain=company.domain if company else "",
                country=company.country if company else "US",
                job_title=job.title,
                tier_signal=job.tier_signal,
                job_url=job.url,
                portal=job.portal,
                location=job.location,
                scraped_at=job.scraped_at,
            )
        )

    return {
        "items": [item.model_dump() for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size) if total > 0 else 1,
    }


@router.get("/export")
async def export_scraped_jobs(
    country: str | None = Query(None),
    portal: str | None = Query(None),
    tier_signal: str | None = Query(None),
    search: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export filtered scraped jobs as a CSV."""
    query = build_query(country, portal, tier_signal, search, date_from, date_to).order_by(JobPosting.scraped_at.desc())
    result = await db.execute(query)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "company_name", "company_domain", "country", "job_title", 
        "tier_signal", "job_url", "portal", "location", "scraped_at"
    ])
    
    for job, company in result.all():
        writer.writerow([
            company.name if company else "Unknown",
            company.domain if company else "",
            company.country if company else "US",
            job.title,
            job.tier_signal,
            job.url,
            job.portal,
            job.location or "",
            job.scraped_at.isoformat() if job.scraped_at else ""
        ])
        
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=scraped_jobs.csv"}
    )
