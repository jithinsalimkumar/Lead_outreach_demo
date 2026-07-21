"""Pydantic schemas for dashboard stats endpoint."""

from pydantic import BaseModel


class LeadsByStatus(BaseModel):
    """Count of leads at each pipeline stage"""
    new: int = 0
    filtered: int = 0
    scraping_contacts: int = 0
    contacts_found: int = 0
    enriching: int = 0
    enriched: int = 0
    queued_for_outreach: int = 0
    sent: int = 0
    replied: int = 0
    bounced: int = 0
    unsubscribed: int = 0


class CampaignPerformanceSummary(BaseModel):
    """Aggregate campaign performance across all campaigns"""
    total_sends: int = 0
    total_opened: int = 0
    total_clicked: int = 0
    total_replied: int = 0
    total_bounced: int = 0
    # Percentages (0-100) — only meaningful if total_sends > 0
    open_rate: float = 0.0
    click_rate: float = 0.0
    reply_rate: float = 0.0
    bounce_rate: float = 0.0


class DashboardStats(BaseModel):
    """GET /api/dashboard/stats — response"""
    leads_by_status: LeadsByStatus
    leads_discovered_this_week: int = 0
    total_leads: int = 0
    total_companies: int = 0
    campaign_performance: CampaignPerformanceSummary
