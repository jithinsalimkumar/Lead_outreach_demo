import pandas as pd
import os
import re
import logging
import urllib.parse
from config import OUTPUT_FILE, EXCLUDE_TITLE_KEYWORDS, DAYS_BACK

# Set up logging for this module
logger = logging.getLogger(__name__)

def clean_url(url):
    """Normalize the company domain/URL by removing protocol, www., and trailing slashes."""
    if not url or not isinstance(url, str):
        return ""
    
    url = url.strip().lower()
    
    # Remove http:// or https://
    if url.startswith('http://'):
        url = url[len('http://'):]
    elif url.startswith('https://'):
        url = url[len('https://'):]
        
    # Remove www.
    if url.startswith('www.'):
        url = url[len('www.'):]
        
    # Remove trailing slash or paths to get just the base domain
    url = url.split('/')[0]
    
    return url

def normalize_company_name(name):
    """Normalize company name for better deduplication."""
    if not name or not isinstance(name, str):
        return ""
    name = name.lower().strip()
    # Remove common corporate suffixes that cause duplicates
    name = re.sub(r'\b(inc|llc|ltd|limited|corp|corporation)\b\.?', '', name)
    # Remove multiple spaces
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def debug_record_fields(record, platform):
    """
    Logs ALL field keys returned by Bright Data for the first record
    of each platform so you can see exactly what fields are available.
    This is only logged once per platform per run.
    """
    if not hasattr(debug_record_fields, "_logged"):
        debug_record_fields._logged = set()
    if platform not in debug_record_fields._logged:
        debug_record_fields._logged.add(platform)
        logger.info(f"\n🔍 DEBUG — All fields returned by Bright Data for [{platform}]:")
        for key, val in record.items():
            logger.info(f"    {key}: {repr(val)[:120]}")
        logger.info("─" * 60)


# ── Known field names Bright Data uses for employee/company size ──────────────
# Jobs dataset (LinkedIn + Indeed) — these fields often NOT present in job records
# Company dataset fields — present only if you hit the company endpoint separately
_EMPLOYEE_FIELD_CANDIDATES = [
    # Top-level flat fields (jobs dataset, varies by schema version)
    "company_size",
    "company_employee_count",
    "employee_count",
    "employees",
    "num_employees",
    "company_size_range",
    "company_employees",
    "employees_in_linkedin",
    "linkedin_employees",
    # LinkedIn-specific top-level
    "job_company_size",
    "companySize",
    "company_staff_count",
    "staff_count",
    # Indeed-specific
    "company_size_text",
    "details_size",        # Glassdoor-style field sometimes mixed in
]

# ── Known nested paths — e.g. record["company_info"]["size"] ─────────────────
_EMPLOYEE_NESTED_PATHS = [
    ("company_info",     "size"),
    ("company_info",     "employee_count"),
    ("company_info",     "employees"),
    ("company_details",  "size"),
    ("company_details",  "employees"),
    ("key_info",         "company_size"),   # GitHub sample shows this path
    ("metrics",          "linkedin_employees"),
]

# ── Regex to extract size from free-text description ─────────────────────────
# Matches patterns like: "51-200 employees", "10,001+ employees", "1 to 10 employees"
_EMPLOYEE_REGEX = re.compile(
    r'\b(\d[\d,]*(?:\+|\s*[-–to]+\s*\d[\d,]*)?)\s*employees?\b',
    re.IGNORECASE
)

# Standard LinkedIn bracket ranges for normalisation
_LINKEDIN_SIZE_BRACKETS = [
    "1-10", "11-50", "51-200", "201-500",
    "501-1000", "1001-5000", "5001-10000", "10001+"
]


def normalise_size_value(raw: str) -> str:
    """
    Cleans up raw size strings into a consistent format.
    Examples:
      "51-200 employees"  → "51-200"
      "51 to 200"         → "51-200"
      "10,001+ employees" → "10001+"
      "Large"             → "Large"   (kept as-is if unrecognised)
    """
    val = raw.strip()
    val = re.sub(r'\s*employees?\b', '', val, flags=re.IGNORECASE).strip()
    val = re.sub(r',', '', val)           # remove thousands separator
    val = re.sub(r'\s+to\s+', '-', val)  # "51 to 200" → "51-200"
    val = re.sub(r'\s*–\s*', '-', val)   # en-dash → hyphen
    val = re.sub(r'\s+', '', val)         # remove any remaining spaces
    return val if val else "N/A"


def extract_employee_size(record):
    """
    Extracts company employee size from a Bright Data job record.

    WHY THIS IS HARD:
    The Bright Data Jobs dataset (LinkedIn + Indeed) does NOT reliably
    include company size — that field lives in the Company dataset.
    However, some records do carry it in various field names or nested
    objects depending on the schema version. This function tries every
    known location before falling back to regex extraction from the
    job description text.

    Strategy (in order of priority):
    1. Check all known top-level field name variants
    2. Check known nested object paths (e.g. company_info.size)
    3. Scan the job description / summary text with regex
    4. Return "N/A" if nothing found

    Returns a normalised string like "51-200", "1-10", "10001+" or "N/A".
    """

    # ── Step 1: Top-level flat fields ────────────────────────────────────────
    for field in _EMPLOYEE_FIELD_CANDIDATES:
        val = record.get(field)
        if val and str(val).strip() not in ("", "0", "None", "null"):
            return normalise_size_value(str(val))

    # ── Step 2: Nested object paths ──────────────────────────────────────────
    for parent_key, child_key in _EMPLOYEE_NESTED_PATHS:
        parent = record.get(parent_key)
        if isinstance(parent, dict):
            val = parent.get(child_key)
            if val and str(val).strip() not in ("", "0", "None", "null"):
                return normalise_size_value(str(val))

    # ── Step 3: Parse from job description / summary text ────────────────────
    # Indeed and LinkedIn often mention company size in the job description.
    # e.g. "We are a 51-200 employee company..." or "Company size: 51-200 employees"
    description_fields = [
        "description", "description_text", "job_description",
        "summary", "job_summary", "overview", "about",
    ]
    for field in description_fields:
        text = record.get(field, "")
        if text and isinstance(text, str):
            match = _EMPLOYEE_REGEX.search(text)
            if match:
                raw = match.group(0)
                return normalise_size_value(raw)

    return "N/A"


def normalize_record(record, platform):
    """Standardize field names from Bright Data API responses."""

    # Log all fields from the first record per platform — helps debug missing fields
    debug_record_fields(record, platform)

    job_title    = record.get("title") or record.get("job_title", "")
    company_name = record.get("company") or record.get("company_name", "")
    job_location = record.get("location") or record.get("job_location", "")
    url          = record.get("url") or record.get("job_url", "")
    
    if platform == "linkedin":
        company_url = record.get("company_url") or record.get("company_website", "")
        return {
            "job_title":      job_title,
            "company_name":   company_name,
            "company_domain": clean_url(company_url),
            "job_location":   job_location,
            "job_url":        url,
            "date_posted":    record.get("posted_at") or record.get("posted_date", ""),
            "seniority":      record.get("seniority_level") or record.get("job_seniority_level", ""),
            "employment_type":record.get("employment_type", ""),
            "employee_size":  extract_employee_size(record),   # ← new column
            "platform":       "LinkedIn"
        }
    elif platform == "indeed":
        company_url = record.get("company_url", "")
        return {
            "job_title":      job_title,
            "company_name":   company_name,
            "company_domain": clean_url(company_url),
            "job_location":   job_location,
            "job_url":        url,
            "date_posted":    record.get("posted_at") or record.get("date_posted_parsed") or record.get("date_posted", ""),
            "seniority":      "",
            "employment_type":record.get("job_type", ""),
            "employee_size":  extract_employee_size(record),   # ← new column
            "platform":       "Indeed"
        }
    return {}

def clean_and_filter(raw_results):
    """Processes, cleans, and deduplicates the raw scraped leads."""
    normalized = []

    for record in raw_results:
        platform = record.get("source_platform", "")
        clean = normalize_record(record, platform)
        clean["search_title"]   = record.get("search_title", "")
        clean["search_country"] = record.get("search_country", "")
        normalized.append(clean)

    df = pd.DataFrame(normalized)

    if df.empty:
        logger.warning("⚠️ No data to process.")
        return df

    logger.info(f"\n📊 Raw records: {len(df)}")

    # Remove empty companies
    df = df[df["company_name"].str.strip() != ""]
    logger.info(f"✅ After removing empty companies: {len(df)}")

    # Filter out excluded HR/Recruiter keywords
    pattern = "|".join([re.escape(k.lower()) for k in EXCLUDE_TITLE_KEYWORDS])
    df = df[~df["job_title"].str.lower().str.contains(pattern, na=False)]
    logger.info(f"✅ After excluding HR/Recruiter titles: {len(df)}")

    # Improve deduplication by adding normalized columns temporarily
    df['_norm_title'] = df['job_title'].astype(str).str.lower().str.strip()
    df['_norm_company'] = df['company_name'].apply(normalize_company_name)
    df['_norm_location'] = df['job_location'].astype(str).str.lower().str.strip()

    df = df.drop_duplicates(subset=["_norm_title", "_norm_company", "_norm_location"])
    logger.info(f"✅ After enhanced deduplication: {len(df)}")

    # Drop temporary columns
    df = df.drop(columns=['_norm_title', '_norm_company', '_norm_location'])

    # Safety-net recency filter: the LinkedIn/Indeed URL params already restrict
    # results to the last DAYS_BACK days, but if a record's date_posted can be
    # parsed and turns out to be older than that window, drop it too. Records
    # whose date can't be parsed are kept rather than discarded.
    before = len(df)
    parsed_dates = pd.to_datetime(df["date_posted"], errors="coerce", utc=True)
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=DAYS_BACK)
    df = df[parsed_dates.isna() | (parsed_dates >= cutoff)]
    logger.info(f"✅ After recency filter (last {DAYS_BACK} days): {len(df)} (removed {before - len(df)})")

    df = df.reset_index(drop=True)
    return df

def save_to_csv(df):
    """Saves the final DataFrame to the output CSV file."""
    os.makedirs("output", exist_ok=True)
    try:
        df.to_csv(OUTPUT_FILE, index=False)
        logger.info(f"\n💾 Saved {len(df)} leads to: {OUTPUT_FILE}")
    except PermissionError:
        logger.error(f"\n❌ Permission Denied: Could not save to {OUTPUT_FILE}.")
        logger.error("Please close the file if it is open in Excel or another program.")
        logger.error("The script will continue collecting leads in memory and try to save again on the next pass.")