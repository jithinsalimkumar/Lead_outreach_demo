"""Initial schema - all tables

Revision ID: 001
Revises: None
Create Date: 2024-01-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Enum types ---
    user_role = postgresql.ENUM("admin", "member", name="user_role", create_type=False)
    user_role.create(op.get_bind(), checkfirst=True)

    country_code = postgresql.ENUM("US", "UK", "CA", name="country_code", create_type=False)
    country_code.create(op.get_bind(), checkfirst=True)

    size_bucket = postgresql.ENUM("small", "large", name="size_bucket", create_type=False)
    size_bucket.create(op.get_bind(), checkfirst=True)

    tier_signal = postgresql.ENUM(
        "email_marketer", "digital_marketer", "general_marketer", "email_agency",
        name="tier_signal", create_type=False,
    )
    tier_signal.create(op.get_bind(), checkfirst=True)

    job_portal = postgresql.ENUM("indeed", "linkedin", name="job_portal", create_type=False)
    job_portal.create(op.get_bind(), checkfirst=True)

    lead_status = postgresql.ENUM(
        "new", "filtered", "scraping_contacts", "contacts_found", "enriching",
        "enriched", "queued_for_outreach", "sent", "replied", "bounced", "unsubscribed",
        name="lead_status", create_type=False,
    )
    lead_status.create(op.get_bind(), checkfirst=True)

    verification_status = postgresql.ENUM(
        "verified", "unverified", "invalid",
        name="verification_status", create_type=False,
    )
    verification_status.create(op.get_bind(), checkfirst=True)

    enrichment_provider = postgresql.ENUM(
        "prospeo", "vibe_prospecting",
        name="enrichment_provider", create_type=False,
    )
    enrichment_provider.create(op.get_bind(), checkfirst=True)

    suppression_reason = postgresql.ENUM(
        "bounced", "complained", "unsubscribed", "manual",
        name="suppression_reason", create_type=False,
    )
    suppression_reason.create(op.get_bind(), checkfirst=True)

    # --- Users table ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False, server_default="member"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Email Templates table ---
    op.create_table(
        "email_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("body_html", sa.Text(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Companies table ---
    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("domain", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("country", country_code, nullable=False, index=True),
        sa.Column("employee_size_estimate", sa.Integer(), nullable=True),
        sa.Column("size_bucket", size_bucket, nullable=False, server_default="small", index=True),
        sa.Column("source_job_url", sa.String(2000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Job Postings table ---
    op.create_table(
        "job_postings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("tier_signal", tier_signal, nullable=False),
        sa.Column("portal", job_portal, nullable=False),
        sa.Column("url", sa.String(2000), nullable=False),
        sa.Column("location", sa.String(500), nullable=True),
        sa.Column("scraped_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Leads table ---
    op.create_table(
        "leads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("full_name", sa.String(500), nullable=False),
        sa.Column("job_title", sa.String(500), nullable=True),
        sa.Column("linkedin_url", sa.String(2000), nullable=True),
        sa.Column("is_excluded", sa.Boolean(), nullable=False, server_default="false", index=True),
        sa.Column("status", lead_status, nullable=False, server_default="new", index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Enrichment Data table ---
    op.create_table(
        "enrichment_data",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("verification_status", verification_status, nullable=False, server_default="unverified"),
        sa.Column("provider", enrichment_provider, nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("raw_response", postgresql.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Campaigns table ---
    op.create_table(
        "campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("email_templates.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sending_account", sa.String(255), nullable=True),
        sa.Column("daily_limit", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("country_scope", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Campaign Sends table ---
    op.create_table(
        "campaign_sends",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("sequence_step", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("opened", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("clicked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("replied", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("bounced", sa.Boolean(), nullable=False, server_default="false"),
        sa.CheckConstraint("sequence_step >= 1 AND sequence_step <= 3", name="valid_step"),
        sa.UniqueConstraint("lead_id", "campaign_id", "sequence_step", name="unique_send"),
    )

    # --- Suppression List table ---
    op.create_table(
        "suppression_list",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email_or_domain", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("reason", suppression_reason, nullable=False),
        sa.Column("country", sa.String(10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Settings table ---
    op.create_table(
        "settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("encrypted_value", sa.Text(), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    # Drop tables in reverse order (respects FK dependencies)
    op.drop_table("settings")
    op.drop_table("suppression_list")
    op.drop_table("campaign_sends")
    op.drop_table("campaigns")
    op.drop_table("enrichment_data")
    op.drop_table("leads")
    op.drop_table("job_postings")
    op.drop_table("companies")
    op.drop_table("email_templates")
    op.drop_table("users")

    # Drop enum types
    for enum_name in [
        "suppression_reason", "enrichment_provider", "verification_status",
        "lead_status", "job_portal", "tier_signal", "size_bucket",
        "country_code", "user_role",
    ]:
        postgresql.ENUM(name=enum_name).drop(op.get_bind(), checkfirst=True)
