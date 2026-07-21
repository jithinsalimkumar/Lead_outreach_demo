"""
Campaign and CampaignSend models.

Campaign: A named outreach campaign targeting a set of leads.
CampaignSend: Tracks individual email sends within a campaign,
including engagement signals (open, click, reply, bounce).
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("email_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    sending_account: Mapped[str | None] = mapped_column(String(255), nullable=True)
    daily_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    # country_scope is an array of country codes this campaign targets
    # e.g. ["US", "UK"] — stored as a PostgreSQL ARRAY
    country_scope: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    creator = relationship("User")
    template = relationship("EmailTemplate")
    sends = relationship("CampaignSend", back_populates="campaign", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Campaign {self.name}>"


class CampaignSend(Base):
    __tablename__ = "campaign_sends"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # sequence_step: 1 = initial email, 2 = first follow-up, 3 = second follow-up
    sequence_step: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    opened: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    clicked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    replied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    bounced: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Constraints:
    # - sequence_step must be 1, 2, or 3
    # - each lead can only appear once per campaign per sequence step
    __table_args__ = (
        CheckConstraint("sequence_step >= 1 AND sequence_step <= 3", name="valid_step"),
        UniqueConstraint("lead_id", "campaign_id", "sequence_step", name="unique_send"),
    )

    # Relationships
    lead = relationship("Lead", back_populates="campaign_sends")
    campaign = relationship("Campaign", back_populates="sends")

    def __repr__(self) -> str:
        return f"<CampaignSend campaign={self.campaign_id} lead={self.lead_id} step={self.sequence_step}>"
