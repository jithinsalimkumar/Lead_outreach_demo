"""
Seed script — populates the database with realistic test data.

Run this after migrations to see the dashboard and tables populated:
    docker-compose exec backend python -m app.seed

Creates:
  - 2 users (admin + member)
  - 10 companies across US/UK/CA
  - 15 job postings
  - 20 leads at various pipeline stages
  - Enrichment data for leads past the enrichment stage
  - 3 campaigns with sends
  - A few suppression entries
  - 1 email template
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.database import async_session_factory
from app.models import (
    Campaign,
    CampaignSend,
    Company,
    EmailTemplate,
    EnrichmentData,
    JobPosting,
    Lead,
    Suppression,
    User,
)
from app.services.auth import hash_password


async def seed():
    """Main seed function — creates all test data."""
    print("WARNING: This is a local dev seed script.")
    confirm = input("Type 'yes' to proceed with inserting dummy data: ")
    if confirm.lower() != 'yes':
        print("Aborting seed script.")
        return

    async with async_session_factory() as db:
        # Check if data already exists (idempotent)
        existing = await db.execute(select(User).limit(1))
        if existing.scalar_one_or_none():
            print("Database already seeded — skipping. Drop tables first to re-seed.")
            return

        print("Seeding database with test data...")
        now = datetime.now(timezone.utc)

        # ===========================
        # USERS
        # ===========================
        admin_user = User(
            id=uuid.uuid4(),
            email="admin@team.com",
            hashed_password=hash_password("admin123"),
            role="admin",
        )
        member_user = User(
            id=uuid.uuid4(),
            email="member@team.com",
            hashed_password=hash_password("member123"),
            role="member",
        )
        db.add_all([admin_user, member_user])
        print("  ✓ Created 2 users (admin@team.com / member@team.com)")

        # ===========================
        # EMAIL TEMPLATE
        # ===========================
        template = EmailTemplate(
            id=uuid.uuid4(),
            name="Cold Outreach v1",
            subject="Quick question about your email marketing",
            body_html="<p>Hi {{first_name}},</p><p>I noticed your team is hiring for email marketing roles...</p>",
            created_by=admin_user.id,
        )
        db.add(template)
        print("  ✓ Created 1 email template")

        # ===========================
        # COMPANIES
        # ===========================
        companies_data = [
            {"name": "Acme Marketing Co", "domain": "acmemarketing.com", "country": "US", "employees": 150, "size": "small"},
            {"name": "BrightWave Digital", "domain": "brightwavedigital.com", "country": "US", "employees": 350, "size": "large"},
            {"name": "CloudReach Solutions", "domain": "cloudreachsolutions.co.uk", "country": "UK", "employees": 85, "size": "small"},
            {"name": "DataDriven Agency", "domain": "datadrivenagency.com", "country": "US", "employees": 220, "size": "large"},
            {"name": "Engage Digital Ltd", "domain": "engagedigital.co.uk", "country": "UK", "employees": 45, "size": "small"},
            {"name": "FunnelPro Marketing", "domain": "funnelpro.ca", "country": "CA", "employees": 120, "size": "small"},
            {"name": "GrowthLab Inc", "domain": "growthlab.com", "country": "US", "employees": 500, "size": "large"},
            {"name": "HyperTarget Media", "domain": "hypertarget.ca", "country": "CA", "employees": 75, "size": "small"},
            {"name": "InboxPeak Agency", "domain": "inboxpeak.com", "country": "US", "employees": 30, "size": "small"},
            {"name": "JetStream Digital", "domain": "jetstreamdigital.co.uk", "country": "UK", "employees": 280, "size": "large"},
        ]

        companies = []
        for c in companies_data:
            company = Company(
                id=uuid.uuid4(),
                name=c["name"],
                domain=c["domain"],
                country=c["country"],
                employee_size_estimate=c["employees"],
                size_bucket=c["size"],
                source_job_url=f"https://indeed.com/jobs?q={c['name'].replace(' ', '+')}",
                created_at=now - timedelta(days=len(companies) * 2),
            )
            companies.append(company)
            db.add(company)
        print(f"  ✓ Created {len(companies)} companies")

        # ===========================
        # JOB POSTINGS
        # ===========================
        job_postings_data = [
            (0, "Email Marketing Manager", "email_marketer", "indeed", "New York, NY"),
            (0, "Senior Email Specialist", "email_marketer", "linkedin", "Remote"),
            (1, "Digital Marketing Director", "digital_marketer", "linkedin", "San Francisco, CA"),
            (2, "Marketing Coordinator", "general_marketer", "indeed", "London, UK"),
            (3, "Email Campaign Strategist", "email_marketer", "indeed", "Chicago, IL"),
            (3, "Digital Marketing Manager", "digital_marketer", "linkedin", "Austin, TX"),
            (4, "Marketing Executive", "general_marketer", "indeed", "Manchester, UK"),
            (5, "Email Marketing Specialist", "email_marketer", "linkedin", "Toronto, CA"),
            (6, "VP of Digital Marketing", "digital_marketer", "linkedin", "New York, NY"),
            (6, "Email Agency Partner Manager", "email_agency", "indeed", "Boston, MA"),
            (7, "Marketing Manager", "general_marketer", "indeed", "Vancouver, CA"),
            (8, "Email Deliverability Specialist", "email_marketer", "linkedin", "Remote"),
            (8, "Lifecycle Marketing Manager", "email_marketer", "indeed", "Remote"),
            (9, "Digital Marketing Lead", "digital_marketer", "linkedin", "Edinburgh, UK"),
            (9, "Email Marketing Agency Lead", "email_agency", "indeed", "London, UK"),
        ]

        job_postings = []
        for comp_idx, title, tier, portal, location in job_postings_data:
            jp = JobPosting(
                id=uuid.uuid4(),
                company_id=companies[comp_idx].id,
                title=title,
                tier_signal=tier,
                portal=portal,
                url=f"https://{portal}.com/jobs/{uuid.uuid4().hex[:8]}",
                location=location,
                scraped_at=now - timedelta(days=comp_idx * 2, hours=comp_idx),
            )
            job_postings.append(jp)
            db.add(jp)
        print(f"  ✓ Created {len(job_postings)} job postings")

        # ===========================
        # LEADS (decision-makers)
        # ===========================
        leads_data = [
            # (company_idx, name, title, status, is_excluded)
            (0, "Sarah Johnson", "VP of Marketing", "enriched", False),
            (0, "Mike Chen", "Head of Email Marketing", "sent", False),
            (1, "Emma Williams", "CMO", "replied", False),
            (1, "David Brown", "Director of Digital", "enriched", False),
            (2, "James Wilson", "Marketing Manager", "contacts_found", False),
            (2, "Sophie Taylor", "HR Manager", "filtered", True),  # excluded: HR
            (3, "Alex Martinez", "VP Growth", "queued_for_outreach", False),
            (3, "Jennifer Lee", "Email Marketing Lead", "sent", False),
            (4, "Oliver Davies", "Marketing Director", "new", False),
            (5, "Rachel Nguyen", "Head of Marketing", "enriching", False),
            (5, "Tom Patterson", "Recruiter", "filtered", True),  # excluded: recruiter
            (6, "Amanda Foster", "CRO", "bounced", False),
            (6, "Robert Kim", "SVP Marketing", "enriched", False),
            (7, "Lisa Tremblay", "Marketing Manager", "scraping_contacts", False),
            (7, "Chris Anderson", "Digital Director", "new", False),
            (8, "Jessica Hayes", "Founder & CEO", "sent", False),
            (8, "Mark Robinson", "Head of Growth", "enriched", False),
            (9, "Daniel Evans", "Marketing Director", "unsubscribed", False),
            (9, "Hannah Wright", "VP Marketing & Comms", "queued_for_outreach", False),
            (0, "Kevin Zhang", "Content Marketing Manager", "new", False),
        ]

        leads = []
        for comp_idx, name, title, lead_status, excluded in leads_data:
            lead = Lead(
                id=uuid.uuid4(),
                company_id=companies[comp_idx].id,
                full_name=name,
                job_title=title,
                linkedin_url=f"https://linkedin.com/in/{name.lower().replace(' ', '-')}",
                is_excluded=excluded,
                status=lead_status,
                created_at=now - timedelta(days=len(leads), hours=len(leads) * 3),
            )
            leads.append(lead)
            db.add(lead)
        print(f"  ✓ Created {len(leads)} leads")

        # ===========================
        # ENRICHMENT DATA
        # ===========================
        # Add enrichment for leads that are past the enrichment stage
        enriched_statuses = {"enriched", "queued_for_outreach", "sent", "replied", "bounced", "unsubscribed"}
        enrichment_records = []
        for lead in leads:
            if lead.status in enriched_statuses:
                first_name = lead.full_name.split()[0].lower()
                last_name = lead.full_name.split()[-1].lower()
                # Find company domain for email generation
                company = next(c for c in companies if c.id == lead.company_id)

                enrichment = EnrichmentData(
                    id=uuid.uuid4(),
                    lead_id=lead.id,
                    email=f"{first_name}.{last_name}@{company.domain}",
                    phone=f"+1-555-{str(uuid.uuid4().int)[:3]}-{str(uuid.uuid4().int)[:4]}",
                    verification_status="verified" if lead.status in {"sent", "replied", "enriched", "queued_for_outreach"} else "unverified",
                    provider="prospeo" if len(enrichment_records) % 2 == 0 else "vibe_prospecting",
                    score=85 + (len(enrichment_records) * 3) % 15,  # Scores between 85-99
                    raw_response={"source": "seed_data", "confidence": "high"},
                    created_at=now - timedelta(days=len(enrichment_records)),
                )
                enrichment_records.append(enrichment)
                db.add(enrichment)
        print(f"  ✓ Created {len(enrichment_records)} enrichment records")

        # ===========================
        # CAMPAIGNS
        # ===========================
        campaign1 = Campaign(
            id=uuid.uuid4(),
            name="US Email Marketers - Q1 2024",
            template_id=template.id,
            sending_account="outreach@team.com",
            daily_limit=30,
            country_scope=["US"],
            created_by=admin_user.id,
            created_at=now - timedelta(days=14),
        )
        campaign2 = Campaign(
            id=uuid.uuid4(),
            name="UK Decision Makers",
            template_id=template.id,
            sending_account="hello@team.com",
            daily_limit=20,
            country_scope=["UK"],
            created_by=admin_user.id,
            created_at=now - timedelta(days=7),
        )
        campaign3 = Campaign(
            id=uuid.uuid4(),
            name="North America Full Sweep",
            template_id=None,
            sending_account="outreach@team.com",
            daily_limit=50,
            country_scope=["US", "CA"],
            created_by=member_user.id,
            created_at=now - timedelta(days=3),
        )
        db.add_all([campaign1, campaign2, campaign3])
        print("  ✓ Created 3 campaigns")

        # ===========================
        # CAMPAIGN SENDS
        # ===========================
        # Add sends for leads that are in "sent", "replied", "bounced" status
        sends_data = []

        # Campaign 1 sends (US leads)
        for lead in leads:
            if lead.status in {"sent", "replied", "bounced"} and lead.full_name in {
                "Mike Chen", "Jessica Hayes"
            }:
                send = CampaignSend(
                    id=uuid.uuid4(),
                    lead_id=lead.id,
                    campaign_id=campaign1.id,
                    sequence_step=1,
                    sent_at=now - timedelta(days=10),
                    opened=True,
                    clicked=lead.full_name == "Mike Chen",
                    replied=False,
                    bounced=False,
                )
                sends_data.append(send)
                db.add(send)

                # Add follow-up for Mike Chen
                if lead.full_name == "Mike Chen":
                    send2 = CampaignSend(
                        id=uuid.uuid4(),
                        lead_id=lead.id,
                        campaign_id=campaign1.id,
                        sequence_step=2,
                        sent_at=now - timedelta(days=5),
                        opened=True,
                        clicked=True,
                        replied=False,
                        bounced=False,
                    )
                    sends_data.append(send2)
                    db.add(send2)

        # Emma Williams replied (Campaign 1)
        for lead in leads:
            if lead.full_name == "Emma Williams":
                send = CampaignSend(
                    id=uuid.uuid4(),
                    lead_id=lead.id,
                    campaign_id=campaign1.id,
                    sequence_step=1,
                    sent_at=now - timedelta(days=12),
                    opened=True,
                    clicked=True,
                    replied=True,
                    bounced=False,
                )
                sends_data.append(send)
                db.add(send)

        # Amanda Foster bounced (Campaign 3)
        for lead in leads:
            if lead.full_name == "Amanda Foster":
                send = CampaignSend(
                    id=uuid.uuid4(),
                    lead_id=lead.id,
                    campaign_id=campaign3.id,
                    sequence_step=1,
                    sent_at=now - timedelta(days=2),
                    opened=False,
                    clicked=False,
                    replied=False,
                    bounced=True,
                )
                sends_data.append(send)
                db.add(send)

        # Jennifer Lee sent (Campaign 1)
        for lead in leads:
            if lead.full_name == "Jennifer Lee":
                send = CampaignSend(
                    id=uuid.uuid4(),
                    lead_id=lead.id,
                    campaign_id=campaign1.id,
                    sequence_step=1,
                    sent_at=now - timedelta(days=8),
                    opened=True,
                    clicked=False,
                    replied=False,
                    bounced=False,
                )
                sends_data.append(send)
                db.add(send)

        # Daniel Evans - Campaign 2 (UK) - unsubscribed
        for lead in leads:
            if lead.full_name == "Daniel Evans":
                send = CampaignSend(
                    id=uuid.uuid4(),
                    lead_id=lead.id,
                    campaign_id=campaign2.id,
                    sequence_step=1,
                    sent_at=now - timedelta(days=5),
                    opened=True,
                    clicked=False,
                    replied=False,
                    bounced=False,
                )
                sends_data.append(send)
                db.add(send)

        print(f"  ✓ Created {len(sends_data)} campaign sends")

        # ===========================
        # SUPPRESSION LIST
        # ===========================
        suppressions = [
            Suppression(email_or_domain="bounce@badserver.com", reason="bounced", country="US"),
            Suppression(email_or_domain="noreply.example.com", reason="manual", country=None),
            Suppression(email_or_domain="angry@company.co.uk", reason="complained", country="UK"),
            Suppression(email_or_domain="daniel.evans@jetstreamdigital.co.uk", reason="unsubscribed", country="UK"),
        ]
        for s in suppressions:
            s.id = uuid.uuid4()
            db.add(s)
        print(f"  ✓ Created {len(suppressions)} suppression entries")

        # Commit all data
        await db.commit()
        print("\n✅ Database seeded successfully!")
        print("   Login credentials:")
        print("   Admin:  admin@team.com  / admin123")
        print("   Member: member@team.com / member123")


if __name__ == "__main__":
    asyncio.run(seed())
