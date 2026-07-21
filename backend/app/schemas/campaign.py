"""Pydantic schemas for campaign endpoints."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CampaignCreate(BaseModel):
    """POST /api/campaigns — request body"""
    name: str
    template_id: Optional[uuid.UUID] = None
    sending_account: Optional[str] = None
    daily_limit: int = 50
    country_scope: Optional[list[str]] = None


class CampaignOut(BaseModel):
    """Campaign data returned in list API responses"""
    id: uuid.UUID
    name: str
    template_id: Optional[uuid.UUID] = None
    sending_account: Optional[str] = None
    daily_limit: int
    country_scope: Optional[list[str]] = None
    created_by: Optional[uuid.UUID] = None
    created_at: datetime
    # Aggregated performance metrics
    total_sends: int = 0
    total_opened: int = 0
    total_clicked: int = 0
    total_replied: int = 0
    total_bounced: int = 0

    model_config = {"from_attributes": True}


class CampaignDetailOut(CampaignOut):
    """Campaign detail with individual lead send data"""
    leads: list["CampaignLeadOut"] = []

    model_config = {"from_attributes": True}


class CampaignLeadOut(BaseModel):
    """Lead info within a campaign context"""
    lead_id: uuid.UUID
    full_name: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[str] = None
    sends: list["CampaignSendSimple"] = []

    model_config = {"from_attributes": True}


class CampaignSendSimple(BaseModel):
    """Simplified send data for campaign detail view"""
    id: uuid.UUID
    sequence_step: int
    sent_at: Optional[datetime] = None
    opened: bool
    clicked: bool
    replied: bool
    bounced: bool

    model_config = {"from_attributes": True}


class CampaignAddLeads(BaseModel):
    """POST /api/campaigns/{id}/leads — request body"""
    lead_ids: list[uuid.UUID]
