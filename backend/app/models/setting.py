"""
Setting model — key-value store for configuration like API keys.

Values are stored encrypted using Fernet symmetric encryption.
Only admins can read or update settings.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Setting(Base):
    __tablename__ = "settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # key is the setting name, e.g. "brightdata_api_key"
    key: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    # encrypted_value holds the Fernet-encrypted value
    encrypted_value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    updater = relationship("User")

    def __repr__(self) -> str:
        return f"<Setting {self.key}>"
