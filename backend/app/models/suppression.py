"""
Suppression List model — emails/domains that should never receive outreach.

Entries are added when:
  - An email bounces (automated)
  - A recipient complains or unsubscribes (automated via webhook)
  - A team member manually adds an entry
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Suppression(Base):
    __tablename__ = "suppression_list"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email_or_domain: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(
        Enum("bounced", "complained", "unsubscribed", "manual", name="suppression_reason"),
        nullable=False,
    )
    country: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<Suppression {self.email_or_domain} ({self.reason})>"
