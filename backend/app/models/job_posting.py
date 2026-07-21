"""
Job Posting model — individual job listings scraped from Indeed/LinkedIn.

Each posting is linked to a company and carries a tier_signal that
indicates what type of marketer role was advertised.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class JobPosting(Base):
    __tablename__ = "job_postings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    tier_signal: Mapped[str] = mapped_column(
        Enum(
            "email_marketer",
            "digital_marketer",
            "general_marketer",
            "email_agency",
            name="tier_signal",
        ),
        nullable=False,
    )
    portal: Mapped[str] = mapped_column(
        Enum("indeed", "linkedin", name="job_portal"),
        nullable=False,
    )
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationship back to the parent company
    company = relationship("Company", back_populates="job_postings")

    def __repr__(self) -> str:
        return f"<JobPosting {self.title} @ {self.company_id}>"
