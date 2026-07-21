"""
Lead model — decision-makers at discovered companies.

A lead represents a person (e.g. VP of Marketing) at a company who might
be the right contact for outreach. Leads progress through a multi-stage
pipeline from discovery to outreach.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# All possible lead statuses, representing the pipeline stages:
#   new → filtered → scraping_contacts → contacts_found → enriching →
#   enriched → queued_for_outreach → sent → replied / bounced / unsubscribed
LEAD_STATUS_ENUM = Enum(
    "new",
    "filtered",
    "scraping_contacts",
    "contacts_found",
    "enriching",
    "enriched",
    "queued_for_outreach",
    "sent",
    "replied",
    "bounced",
    "unsubscribed",
    name="lead_status",
)


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(String(500), nullable=False)
    job_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    is_excluded: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        LEAD_STATUS_ENUM,
        nullable=False,
        default="new",
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    company = relationship("Company", back_populates="leads")
    enrichment_data = relationship(
        "EnrichmentData", back_populates="lead", lazy="selectin"
    )
    campaign_sends = relationship(
        "CampaignSend", back_populates="lead", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Lead {self.full_name} ({self.status})>"
