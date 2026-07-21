"""
Company model — companies discovered through job posting scraping.

Each company is identified by its domain (unique). The size_bucket field
is derived from employee_size_estimate: small (<200) or large (200+).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    domain: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    country: Mapped[str] = mapped_column(
        Enum("US", "UK", "CA", name="country_code"),
        nullable=False,
        index=True,
    )
    employee_size_estimate: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    size_bucket: Mapped[str] = mapped_column(
        Enum("small", "large", name="size_bucket"),
        nullable=False,
        default="small",
        index=True,
    )
    source_job_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships — lazy="selectin" means related objects are loaded
    # in a single extra query (efficient for async)
    job_postings = relationship("JobPosting", back_populates="company", lazy="selectin")
    leads = relationship("Lead", back_populates="company", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Company {self.name} ({self.domain})>"
