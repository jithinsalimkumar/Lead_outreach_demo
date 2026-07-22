# config.py
# ─────────────────────────────────────────────────────────────
# Module 1 — Hiring Signal Discovery
# Configuration File (Option 3 — Credit Safe Settings)
#
# Total estimated usage: ~1,624 credits
# Remaining after run:   ~3,376 credits (saved for Module 2 & 3)
# Expected clean leads:  ~800 – 1,000 unique companies
# ─────────────────────────────────────────────────────────────

JOB_TITLES = [
    "Email Marketer",
    "Email Marketing Specialist",
    "Digital Marketer",
    "Marketing Manager"
]

COUNTRIES = [
    "United States",
    "United Kingdom",
    "Canada"
]

DATASET_IDS = {
    "linkedin": "gd_lpfll7v5hcqtkxl6l",
    "indeed":   "gd_l4dx9j9sscpvs7no2",
}

DAYS_BACK = 7  # Last one week
BASE_URL = "https://api.brightdata.com/datasets/v3"
OUTPUT_FILE = "output/leads.csv"

# Indeed uses separate country-specific domains — searching "www.indeed.com"
# with a UK/Canada location will not reliably return UK/Canada postings.
INDEED_DOMAINS = {
    "United States": "www.indeed.com",
    "United Kingdom": "www.indeed.co.uk",
    "Canada": "www.indeed.ca",
}

# ── Output size limit ─────────────────────────────────────────
# Max results returned per trigger call (per platform/title/country combo).
# Lower = fewer credits used. Set to 50 for demo / credit-safe runs.
LIMIT_PER_INPUT = 50

PAUSE_BETWEEN_REQUESTS = 5
WAIT_BEFORE_FETCH      = 60   # Wait 60s before first fetch (discover_new mode needs time)
FETCH_RETRY_WAIT       = 90   # Wait 90s between retry attempts
FETCH_MAX_RETRIES      = 10   # More retries since discover mode can take 2-5 minutes

EXCLUDE_TITLE_KEYWORDS = [
    "recruiter",
    "talent acquisition",
    "hr manager",
    "human resources",
    "people operations",
    "people partner",
    "hr business partner",
    "staffing",
    "headhunter"
]