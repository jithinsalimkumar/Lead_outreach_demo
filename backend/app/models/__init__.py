"""
Models package — imports all models so Alembic can discover them.

When you add a new model file, import it here so that:
1. Alembic's autogenerate can detect its tables
2. Other modules can do: from app.models import User, Company, etc.
"""

from app.models.user import User
from app.models.company import Company
from app.models.job_posting import JobPosting
from app.models.lead import Lead
from app.models.enrichment import EnrichmentData
from app.models.campaign import Campaign, CampaignSend
from app.models.suppression import Suppression
from app.models.email_template import EmailTemplate
from app.models.setting import Setting

__all__ = [
    "User",
    "Company",
    "JobPosting",
    "Lead",
    "EnrichmentData",
    "Campaign",
    "CampaignSend",
    "Suppression",
    "EmailTemplate",
    "Setting",
]
