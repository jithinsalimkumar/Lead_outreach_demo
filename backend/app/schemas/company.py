"""Pydantic schemas for company endpoints."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class JobPostingOut(BaseModel):
    """Job posting data nested within company responses"""
    id: uuid.UUID
    title: str
    tier_signal: str
    portal: str
    url: str
    location: Optional[str] = None
    scraped_at: datetime

    model_config = {"from_attributes": True}


class CompanyOut(BaseModel):
    """Company data returned in list/detail API responses"""
    id: uuid.UUID
    name: str
    domain: str
    country: str
    employee_size_estimate: Optional[int] = None
    size_bucket: str
    source_job_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CompanyDetailOut(CompanyOut):
    """Company detail with nested job postings and lead count"""
    job_postings: list[JobPostingOut] = []
    lead_count: int = 0

    model_config = {"from_attributes": True}
