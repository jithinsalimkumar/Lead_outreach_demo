import logging
import os
import pandas as pd
from config import JOB_TITLES, COUNTRIES, DATASET_IDS, OUTPUT_FILE
from bright_data import scrape_all
from processor import clean_and_filter, save_to_csv

# Configure logging for the entire pipeline
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)

def generate_summary_report(df, total_requests):
    """Generates a summary report of the scraping run."""
    summary_path = "output/summary.txt"
    
    if df.empty:
        report = "Lead Generation Summary Report\n================================\nNo leads were generated.\n"
        os.makedirs("output", exist_ok=True)
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info(f"📄 Summary report saved to {summary_path}")
        return

    # Lead breakdown by platform
    linkedin_count = len(df[df['platform'] == 'LinkedIn'])
    indeed_count = len(df[df['platform'] == 'Indeed'])

    # Top 10 companies by job posting count
    top_companies = df['company_name'].value_counts().head(10)

    # Lead breakdown by country
    country_breakdown = df['search_country'].value_counts()

    # Total credits estimated (API triggers + fetch attempts)
    # Using a placeholder estimate of ~10 credits per operation
    estimated_credits = total_requests * 10

    report_lines = [
        "Lead Generation Summary Report",
        "================================",
        f"Total Leads Found: {len(df)}",
        "",
        "Breakdown by Platform:",
        f"  - LinkedIn: {linkedin_count}",
        f"  - Indeed: {indeed_count}",
        "",
        "Breakdown by Country:"
    ]
    for country, count in country_breakdown.items():
        report_lines.append(f"  - {country}: {count}")

    report_lines.extend([
        "",
        "Top 10 Companies by Job Posting Count:"
    ])
    for company, count in top_companies.items():
        report_lines.append(f"  - {company}: {count} postings")

    report_lines.extend([
        "",
        f"Estimated Credits Used: ~{estimated_credits}",
        "================================"
    ])

    report = "\n".join(report_lines)
    
    os.makedirs("output", exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(report)
        
    logger.info(f"📄 Summary report saved to {summary_path}")

def validate_output():
    """Validates that the output file exists and has the correct format."""
    if not os.path.exists(OUTPUT_FILE):
        logger.error(f"❌ VALIDATION FAILED: {OUTPUT_FILE} was not created!")
        return False
        
    try:
        df = pd.read_csv(OUTPUT_FILE)
    except Exception as e:
        logger.error(f"❌ VALIDATION FAILED: Cannot read {OUTPUT_FILE}: {e}")
        return False
        
    if df.empty:
        logger.warning(f"⚠️ VALIDATION WARNING: {OUTPUT_FILE} is empty!")
        return False
        
    required_columns = {
        "job_title", "company_name", "company_domain", "job_location",
        "job_url", "date_posted", "seniority", "employment_type",
        "employee_size", "platform", "search_title", "search_country"
    }
    
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        logger.error(f"❌ VALIDATION FAILED: Missing required columns: {missing_columns}")
        return False
        
    logger.info("✅ VALIDATION SUCCESS: Output file is properly formatted and populated.")
    return True

def run_module1():
    logger.info("=" * 60)
    logger.info("   MODULE 1 — HIRING SIGNAL DISCOVERY")
    logger.info("=" * 60)

    logger.info(f"🔍 Searching for {len(JOB_TITLES)} job titles")
    logger.info(f"🌍 Across {len(COUNTRIES)} countries")
    logger.info("📡 On LinkedIn + Indeed")

    # Perform the scraping and save incrementally
    raw_results_accumulated = []
    clean_leads = pd.DataFrame()
    
    for chunk in scrape_all(JOB_TITLES, COUNTRIES):
        if chunk:
            raw_results_accumulated.extend(chunk)
            
            # Clean and deduplicate the accumulated leads
            clean_leads = clean_and_filter(raw_results_accumulated)
            
            # Save outputs incrementally
            save_to_csv(clean_leads)
            logger.info(f"💾 Incrementally saved {len(clean_leads)} clean leads to CSV.")
            
    logger.info(f"\n📥 Total raw records collected across all runs: {len(raw_results_accumulated)}")
    
    # Task 4: Generate summary report
    # Calculate estimated number of API interactions made
    total_requests = len(JOB_TITLES) * len(COUNTRIES) * len(DATASET_IDS) * 2
    generate_summary_report(clean_leads, total_requests)
    
    # Task 5: Validation step
    validate_output()

    logger.info("=" * 60)
    logger.info("   MODULE 1 COMPLETE")
    logger.info("=" * 60)
    logger.info(f"✅ Total clean leads found: {len(clean_leads)}")
    logger.info(f"📁 Output: {OUTPUT_FILE}")
    logger.info("🔗 Next: Pass leads.csv to Module 2")
    logger.info("=" * 60)

    return clean_leads

if __name__ == "__main__":
    run_module1()