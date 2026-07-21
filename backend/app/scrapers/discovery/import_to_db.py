import asyncio
import os
import uuid
import pandas as pd
from datetime import datetime, timezone
import sys

# Add the backend folder to sys.path so we can import from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from sqlalchemy import select
from app.database import async_session_factory
from app.models.company import Company
from app.models.job_posting import JobPosting

async def import_csv_to_db():
    csv_path = os.path.join(os.path.dirname(__file__), "output", "leads.csv")
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        print("CSV is empty.")
        return

    print(f"Loaded {len(df)} rows from CSV.")
    
    async with async_session_factory() as db:
        new_companies = 0
        new_jobs = 0

        for index, row in df.iterrows():
            company_domain = str(row['company_domain']).strip().lower()
            if not company_domain or company_domain == 'nan':
                continue
                
            company_name = str(row['company_name']).strip()
            
            # Map country
            country = "US"
            if "uk" in str(row['search_country']).lower() or "united kingdom" in str(row['search_country']).lower():
                country = "UK"
            elif "ca" in str(row['search_country']).lower() or "canada" in str(row['search_country']).lower():
                country = "CA"
            
            # Map size
            size_bucket = "small"
            emp_size_raw = str(row.get('employee_size', ''))
            emp_size = None
            if emp_size_raw and emp_size_raw != 'N/A' and emp_size_raw != 'nan':
                if '1000' in emp_size_raw or '500' in emp_size_raw:
                    size_bucket = "large"
                # very crude parsing just for demonstration
                try:
                    parts = emp_size_raw.replace('+', '').replace(',', '').split('-')
                    emp_size = int(parts[-1].strip())
                    if emp_size >= 200:
                        size_bucket = "large"
                except:
                    pass

            # Check if company exists
            result = await db.execute(select(Company).where(Company.domain == company_domain))
            company = result.scalar_one_or_none()
            
            if not company:
                company = Company(
                    id=uuid.uuid4(),
                    name=company_name,
                    domain=company_domain,
                    country=country,
                    employee_size_estimate=emp_size,
                    size_bucket=size_bucket,
                    source_job_url=str(row['job_url']) if not pd.isna(row['job_url']) else None,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(company)
                new_companies += 1
                await db.flush() # get the ID for job posting

            # Map tier signal based on search_title
            tier_signal = "general_marketer"
            st = str(row['search_title']).lower()
            if "email" in st:
                tier_signal = "email_marketer"
            elif "digital" in st:
                tier_signal = "digital_marketer"
            elif "agency" in st:
                tier_signal = "email_agency"

            # Map portal
            portal = "linkedin"
            if "indeed" in str(row['platform']).lower():
                portal = "indeed"

            # Check if job posting exists (prevent duplicates by URL)
            job_url = str(row['job_url'])
            if job_url and job_url != 'nan':
                job_result = await db.execute(select(JobPosting).where(JobPosting.url == job_url))
                existing_job = job_result.scalar_one_or_none()
                
                if not existing_job:
                    job = JobPosting(
                        id=uuid.uuid4(),
                        company_id=company.id,
                        title=str(row['job_title']),
                        tier_signal=tier_signal,
                        portal=portal,
                        url=job_url,
                        location=str(row['job_location']) if not pd.isna(row['job_location']) else None,
                        scraped_at=datetime.now(timezone.utc)
                    )
                    db.add(job)
                    new_jobs += 1

        await db.commit()
        print(f"Successfully imported {new_companies} new companies and {new_jobs} new job postings.")

if __name__ == "__main__":
    asyncio.run(import_csv_to_db())
