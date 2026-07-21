"""Pydantic schemas for lead endpoints."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.company import CompanyOut, JobPostingOut
from app.schemas.enrichment import EnrichmentOut


class LeadOut(BaseModel):
    """Lead data returned in list API responses"""
    id: uuid.UUID
    company_id: uuid.UUID
    full_name: str
    job_title: Optional[str] = None
    linkedin_url: Optional[str] = None
    is_excluded: bool
    status: str
    created_at: datetime
    # Flattened company info for the table view
    company_name: Optional[str] = None
    company_country: Optional[str] = None
    company_size_bucket: Optional[str] = None
    # Best enrichment score for filtering/display
    best_score: Optional[int] = None

    model_config = {"from_attributes": True}


class CampaignSendOut(BaseModel):
    """Campaign send data for lead detail view"""
    id: uuid.UUID
    campaign_id: uuid.UUID
    campaign_name: Optional[str] = None
    sequence_step: int
    sent_at: Optional[datetime] = None
    opened: bool
    clicked: bool
    replied: bool
    bounced: bool

    model_config = {"from_attributes": True}


class LeadDetailOut(BaseModel):
    """Full lead detail with company, enrichment, and send history"""
    id: uuid.UUID
    full_name: str
    job_title: Optional[str] = None
    linkedin_url: Optional[str] = None
    is_excluded: bool
    status: str
    created_at: datetime
    company: Optional[CompanyOut] = None
    job_postings: list[JobPostingOut] = []
    enrichment_data: list[EnrichmentOut] = []
    campaign_sends: list[CampaignSendOut] = []

    model_config = {"from_attributes": True}


class LeadStatusUpdate(BaseModel):
    """PATCH /api/leads/{id}/status — request body"""
    status: str


class LeadExcludeUpdate(BaseModel):
    """PATCH /api/leads/{id}/exclude — request body"""
    is_excluded: bool
