"""
Dashboard router — aggregate stats for the dashboard overview.

Returns counts for the lead pipeline, campaign performance, and
weekly discovery metrics.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.campaign import CampaignSend
from app.models.company import Company
from app.models.lead import Lead
from app.models.user import User
from app.schemas.dashboard import CampaignPerformanceSummary, DashboardStats, LeadsByStatus

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get aggregate dashboard statistics.

    This endpoint runs several aggregate queries to build the dashboard overview:
    1. Count of leads at each pipeline stage
    2. Total leads discovered in the last 7 days
    3. Total leads and companies
    4. Campaign performance summary (opens/clicks/replies/bounces as counts and rates)
    """
    # --- Leads by status ---
    status_counts = {}
    all_statuses = [
        "new", "filtered", "scraping_contacts", "contacts_found", "enriching",
        "enriched", "queued_for_outreach", "sent", "replied", "bounced", "unsubscribed",
    ]
    for s in all_statuses:
        count_result = await db.execute(
            select(func.count(Lead.id)).where(Lead.status == s)
        )
        status_counts[s] = count_result.scalar()

    leads_by_status = LeadsByStatus(**status_counts)

    # --- Total leads and companies ---
    total_leads = (await db.execute(select(func.count(Lead.id)))).scalar()
    total_companies = (await db.execute(select(func.count(Company.id)))).scalar()

    # --- Leads discovered this week ---
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    weekly_count = (
        await db.execute(
            select(func.count(Lead.id)).where(Lead.created_at >= one_week_ago)
        )
    ).scalar()

    # --- Campaign performance summary ---
    campaign_stats = await db.execute(
        select(
            func.count(CampaignSend.id).label("total"),
            func.count(CampaignSend.id).filter(CampaignSend.opened == True).label("opened"),
            func.count(CampaignSend.id).filter(CampaignSend.clicked == True).label("clicked"),
            func.count(CampaignSend.id).filter(CampaignSend.replied == True).label("replied"),
            func.count(CampaignSend.id).filter(CampaignSend.bounced == True).label("bounced"),
        )
    )
    cs = campaign_stats.one()

    # Calculate rates (avoid division by zero)
    total_sends = cs.total or 0
    campaign_performance = CampaignPerformanceSummary(
        total_sends=total_sends,
        total_opened=cs.opened,
        total_clicked=cs.clicked,
        total_replied=cs.replied,
        total_bounced=cs.bounced,
        open_rate=round((cs.opened / total_sends * 100), 1) if total_sends > 0 else 0,
        click_rate=round((cs.clicked / total_sends * 100), 1) if total_sends > 0 else 0,
        reply_rate=round((cs.replied / total_sends * 100), 1) if total_sends > 0 else 0,
        bounce_rate=round((cs.bounced / total_sends * 100), 1) if total_sends > 0 else 0,
    )

    return DashboardStats(
        leads_by_status=leads_by_status,
        leads_discovered_this_week=weekly_count,
        total_leads=total_leads,
        total_companies=total_companies,
        campaign_performance=campaign_performance,
    )
