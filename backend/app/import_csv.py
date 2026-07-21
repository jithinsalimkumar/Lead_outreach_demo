import asyncio
import csv
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.database import async_session_factory
from app.models.company import Company
from app.models.job_posting import JobPosting

# Mappings for enum conversions
TIER_MAPPING = {
    "Email Marketer": "email_marketer",
    "Digital Marketer": "digital_marketer",
    "General Marketer": "general_marketer",
    "Email Agency": "email_agency",
}

COUNTRY_MAPPING = {
    "United States": "US",
    "United Kingdom": "UK",
    "Canada": "CA",
}


async def import_data():
    csv_path = "app/scrapers/discovery/output/leads.csv"
    print(f"Reading from {csv_path}...")
    
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("No data found in CSV.")
        return

    now = datetime.now(timezone.utc)
    
    async with async_session_factory() as db:
        print("Connected to DB, inserting data...")
        
        # We will keep a local dictionary of companies inserted/found during this run
        # to avoid inserting duplicates. Key: domain
        company_cache = {}
        
        # Load existing companies to cache
        result = await db.execute(select(Company))
        for existing_c in result.scalars():
            company_cache[existing_c.domain] = existing_c.id

        new_companies = []
        new_jobs = []

        for idx, row in enumerate(rows):
            domain = row.get("company_domain", "").strip()
            name = row.get("company_name", "Unknown Company").strip()
            
            # Use name as fallback if domain is empty or generic
            if not domain or domain == 'linkedin.com':
                domain = name.lower().replace(" ", "") + ".com"
            
            country_str = row.get("search_country", "United States")
            country = COUNTRY_MAPPING.get(country_str, "US")
            
            # Handle Company
            if domain not in company_cache:
                comp_id = uuid.uuid4()
                company_cache[domain] = comp_id
                
                # Try to parse employee size (e.g. "1,001-5,000 employees" or "N/A")
                emp_str = row.get("employee_size", "")
                size_bucket = "small"
                emp_est = None
                if emp_str and emp_str != "N/A":
                    try:
                        # Extract first number
                        first_num_str = emp_str.split("-")[0].replace(",", "").split("+")[0].strip()
                        if first_num_str.isdigit():
                            emp_est = int(first_num_str)
                            if emp_est >= 200:
                                size_bucket = "large"
                    except Exception:
                        pass
                
                new_comp = Company(
                    id=comp_id,
                    name=name,
                    domain=domain,
                    country=country,
                    employee_size_estimate=emp_est,
                    size_bucket=size_bucket,
                    source_job_url=row.get("job_url", ""),
                    created_at=now
                )
                new_companies.append(new_comp)
                db.add(new_comp)
            else:
                comp_id = company_cache[domain]
            
            # Handle Job Posting
            platform_str = row.get("platform", "LinkedIn").lower()
            if platform_str not in ["linkedin", "indeed"]:
                platform_str = "linkedin"
                
            search_title = row.get("search_title", "Email Marketer")
            tier_signal = TIER_MAPPING.get(search_title, "email_marketer")
            
            job = JobPosting(
                id=uuid.uuid4(),
                company_id=comp_id,
                title=row.get("job_title", "Unknown Title"),
                tier_signal=tier_signal,
                portal=platform_str,
                url=row.get("job_url", ""),
                location=row.get("job_location", ""),
                scraped_at=now
            )
            new_jobs.append(job)
            db.add(job)

        await db.commit()
        print(f"Successfully inserted {len(new_companies)} new companies and {len(new_jobs)} new job postings.")


if __name__ == "__main__":
    asyncio.run(import_data())
