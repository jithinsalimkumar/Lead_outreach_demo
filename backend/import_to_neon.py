"""
Script to import exported jobs CSV into your target database (Neon).

Usage:
  1. Set your Neon DATABASE_URL environment variable (or pass it in .env)
  2. Run: python import_to_neon.py
"""
import asyncio
import csv
import os
import sys
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from app.database import async_session_factory
from app.models import Company, JobPosting


async def import_to_neon():
    script_dir = os.path.dirname(__file__)
    csv_file = os.path.join(script_dir, "scraped_jobs_export.csv")
    if not os.path.exists(csv_file):
        csv_file = "scraped_jobs_export.csv"

    if not os.path.exists(csv_file):
        print(f"File '{csv_file}' not found. Please ensure 'scraped_jobs_export.csv' is in the backend folder.")
        return

    print(f"Reading records from {csv_file}...")
    with open(csv_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Loaded {len(rows)} records from CSV.")
    now = datetime.now(timezone.utc)

    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        from app.config import settings
        db_url = settings.DATABASE_URL

    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Use urlparse to remove unsupported asyncpg query parameters
    parsed = urlparse(db_url)
    query_params = parse_qs(parsed.query)
    query_params.pop("sslmode", None)
    query_params.pop("channel_binding", None)
    db_url = urlunparse(parsed._replace(query=urlencode(query_params, doseq=True)))

    engine = create_async_engine(db_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        company_cache = {}
        
        # Load existing companies
        result = await db.execute(select(Company))
        for existing in result.scalars():
            company_cache[existing.domain] = existing.id

        new_companies = 0
        new_jobs = 0

        for row in rows:
            domain = row.get("company_domain", "").strip().lower()
            name = row.get("company_name", "Unknown Company").strip()
            country = row.get("country", "US").strip()

            if not domain:
                domain = name.lower().replace(" ", "") + ".com"

            # Create Company if not exists
            if domain not in company_cache:
                comp_id = uuid.uuid4()
                company_cache[domain] = comp_id
                comp = Company(
                    id=comp_id,
                    name=name,
                    domain=domain,
                    country=country,
                    source_job_url=row.get("job_url", ""),
                    created_at=now,
                )
                db.add(comp)
                new_companies += 1
            else:
                comp_id = company_cache[domain]

            # Check if JobPosting URL already exists
            job_url = row.get("job_url", "").strip()
            job_exists = False
            if job_url:
                res = await db.execute(select(JobPosting).where(JobPosting.url == job_url))
                if res.scalar_one_or_none():
                    job_exists = True

            if not job_exists:
                jp = JobPosting(
                    id=uuid.uuid4(),
                    company_id=comp_id,
                    title=row.get("job_title", "Unknown Title"),
                    tier_signal=row.get("tier_signal", "general_marketer"),
                    portal=row.get("portal", "indeed"),
                    url=job_url,
                    location=row.get("location", ""),
                    scraped_at=now,
                )
                db.add(jp)
                new_jobs += 1

        await db.commit()
        print(f"✅ Successfully imported {new_companies} companies and {new_jobs} job postings to Neon!")


if __name__ == "__main__":
    asyncio.run(import_to_neon())
