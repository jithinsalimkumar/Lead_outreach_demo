"""
Enrichment Data model — contact details found for a lead.

Each lead can have multiple enrichment records (from different providers
or retries). The best record is typically the one with the highest score
and a "verified" verification_status.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EnrichmentData(Base):
    __tablename__ = "enrichment_data"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    verification_status: Mapped[str] = mapped_column(
        Enum("verified", "unverified", "invalid", name="verification_status"),
        nullable=False,
        default="unverified",
    )
    provider: Mapped[str] = mapped_column(
        Enum("prospeo", "vibe_prospecting", name="enrichment_provider"),
        nullable=False,
    )
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # raw_response stores the full JSON response from the enrichment API
    # for debugging and auditing purposes
    raw_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationship back to the lead
    lead = relationship("Lead", back_populates="enrichment_data")

    def __repr__(self) -> str:
        return f"<EnrichmentData {self.email} ({self.verification_status})>"
