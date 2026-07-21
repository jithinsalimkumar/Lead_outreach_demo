import os
import time
import json
import requests
import logging
import urllib.parse
from datetime import datetime, timedelta
from dotenv import load_dotenv
from config import BASE_URL, DATASET_IDS, DAYS_BACK, PAUSE_BETWEEN_REQUESTS, WAIT_BEFORE_FETCH, FETCH_RETRY_WAIT, FETCH_MAX_RETRIES, LIMIT_PER_INPUT, INDEED_DOMAINS

# Set up logging for this module
logger = logging.getLogger(__name__)

load_dotenv()
API_TOKEN = os.getenv("BRIGHT_DATA_TOKEN")

# Validate API token immediately on import so we fail fast
if not API_TOKEN:
    raise ValueError("BRIGHT_DATA_TOKEN is not set in the .env file. Please provide a valid API token.")

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Map full country names to ISO country codes for the Bright Data API
COUNTRY_CODES = {
    "United States": "US",
    "United Kingdom": "GB",
    "Canada": "CA",
}

def build_search_url(platform, job_title, country):
    """Builds the appropriate search URL for each platform, scoped to DAYS_BACK recency."""
    country_code = COUNTRY_CODES.get(country, country)
    
    # URL encode the job title and location
    encoded_title = urllib.parse.quote(job_title)
    encoded_location = urllib.parse.quote(country)
    
    if platform == "linkedin":
        # LinkedIn's "posted within" filter (f_TPR) takes a value like "r604800"
        # where the number is seconds. DAYS_BACK * 86400 gives us that value,
        # so DAYS_BACK now actually controls how recent results are.
        seconds_back = DAYS_BACK * 86400
        url = (
            f"https://www.linkedin.com/jobs/search/?keywords={encoded_title}"
            f"&location={encoded_location}&f_TPR=r{seconds_back}"
        )
    elif platform == "indeed":
        # Indeed is split across country-specific domains — indeed.com only
        # serves US listings, so UK/Canada need indeed.co.uk / indeed.ca.
        # "fromage" (days) is Indeed's native "posted within last N days" filter.
        domain = INDEED_DOMAINS.get(country, "www.indeed.com")
        url = (
            f"https://{domain}/jobs?q={encoded_title}"
            f"&l={encoded_location}&fromage={DAYS_BACK}"
        )
    else:
        raise ValueError(f"Unsupported platform: {platform}")
    
    return url

def trigger_scrape(platform, job_title, country):
    """
    Triggers the Bright Data Dataset scraping job and returns the snapshot ID.
    
    Uses 'discover_new' mode with URL-based discovery for both platforms.
    """
    dataset_id = DATASET_IDS.get(platform)
    if not dataset_id:
        logger.error(f"  ❌ Unknown platform: {platform}")
        return None

    url = f"{BASE_URL}/trigger"

    # Use discover_new mode with URL-based discovery
    params = {
        "dataset_id": dataset_id,
        "type": "discover_new",
        "discover_by": "url",
        "format": "json",
        "uncompressed_webhook": "true",
        "limit_per_input": str(LIMIT_PER_INPUT),   # ← controlled from config.py
        "include_errors": "true"
    }

    # Build the search URL for the platform
    search_url = build_search_url(platform, job_title, country)
    
    # Send the URL as input
    payload = [{
        "url": search_url
    }]

    try:
        logger.info(f"  📡 Sending request to: {search_url}")
        response = requests.post(url, headers=HEADERS, params=params, json=payload, timeout=30)
        response.raise_for_status() 
        
        response_json = response.json()
        snapshot_id = response_json.get("snapshot_id")
        
        if snapshot_id:
            logger.info(f"  ✅ Triggered {platform} | '{job_title}' | {country} → Snapshot: {snapshot_id}")
            return snapshot_id
        else:
            logger.error(f"  ❌ API returned success but no snapshot_id was found: {response_json}")
            return None

    except requests.exceptions.Timeout:
        logger.error(f"  ❌ Timeout occurred while triggering {platform} for '{job_title}' in {country}.")
    except requests.exceptions.RequestException as e:
        logger.error(f"  ❌ Network/API error triggering {platform}: {e}")
        if e.response is not None:
            logger.error(f"  ❌ Response content: {e.response.text}")
    except ValueError as e:
        logger.error(f"  ❌ Failed to parse JSON response from Bright Data API: {e}")
        
    return None

def wait_for_snapshot_ready(snapshot_id, max_retries=FETCH_MAX_RETRIES, wait_seconds=FETCH_RETRY_WAIT):
    """
    Polls the Bright Data /progress/ endpoint until the snapshot is ready.
    
    Returns True if the snapshot is ready, False if it failed or timed out.
    """
    progress_url = f"{BASE_URL}/progress/{snapshot_id}"
    current_wait = wait_seconds

    for attempt in range(max_retries):
        logger.info(f"  ⏳ Checking snapshot status... attempt {attempt + 1}/{max_retries}")
        try:
            response = requests.get(progress_url, headers=HEADERS, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                
                if status == "ready":
                    logger.info(f"  ✅ Snapshot is ready for download!")
                    return True
                elif status in ("running", "pending", "scheduled", "building", "processing"):
                    logger.info(f"  🔄 Snapshot status: '{status}'. Waiting {current_wait}s...")
                    time.sleep(current_wait)
                    current_wait = min(current_wait * 2, 300)
                    continue
                elif status == "failed":
                    error_msg = data.get("error", "Unknown error")
                    logger.error(f"  ❌ Snapshot collection failed: {error_msg}")
                    return False
                else:
                    logger.warning(f"  ⚠️ Unknown snapshot status: '{status}'. Full response: {data}. Retrying...")
                    time.sleep(current_wait)
                    current_wait = min(current_wait * 2, 300)
                    continue
            else:
                logger.warning(f"  ⚠️ Progress check returned HTTP {response.status_code}: {response.text}. Retrying...")
                time.sleep(current_wait)
                current_wait = min(current_wait * 2, 300)
                
        except requests.exceptions.Timeout:
            logger.warning(f"  ⚠️ Timeout checking progress. Retrying after {current_wait}s...")
            time.sleep(current_wait)
            current_wait = min(current_wait * 2, 300)
        except requests.exceptions.RequestException as e:
            logger.warning(f"  ⚠️ Network error checking progress: {e}. Retrying after {current_wait}s...")
            time.sleep(current_wait)
            current_wait = min(current_wait * 2, 300)
        except ValueError as e:
            logger.error(f"  ❌ Failed to parse progress JSON: {e}")
            return False

    logger.warning("  ⚠️ Max retries reached waiting for snapshot to be ready.")
    return False

def download_snapshot(snapshot_id, max_download_retries=3):
    """
    Downloads the actual snapshot data once it's confirmed ready.
    
    Uses format=json query parameter as required by Bright Data API.
    """
    url = f"{BASE_URL}/snapshot/{snapshot_id}"
    params = {"format": "json"}
    
    for attempt in range(max_download_retries):
        try:
            logger.info(f"  ⬇️ Downloading snapshot data... attempt {attempt + 1}/{max_download_retries}")
            
            response = requests.get(
                url, headers=HEADERS, params=params,
                timeout=(30, 300), stream=True
            )
            
            if response.status_code == 200:
                # Read the full content using streaming to avoid IncompleteRead
                content = b""
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        content += chunk
                
                text = content.decode("utf-8").strip()
                
                if not text:
                    logger.warning("  ⚠️ Snapshot download returned empty response body.")
                    time.sleep(15)
                    continue
                
                data = json.loads(text)
                
                if isinstance(data, dict) and "error" in data:
                    logger.error(f"  ❌ API returned an error in download: {data}")
                    return []
                
                # Handle both list and dict responses
                if isinstance(data, list):
                    if len(data) == 0:
                        logger.warning("  ⚠️ Snapshot returned 0 records.")
                    else:
                        logger.info(f"  ✅ Downloaded {len(data)} records")
                    return data
                elif isinstance(data, dict):
                    # Sometimes data is wrapped in a dict with a 'data' or 'results' key
                    if "data" in data:
                        results = data["data"]
                        logger.info(f"  ✅ Downloaded {len(results)} records")
                        return results
                    elif "results" in data:
                        results = data["results"]
                        logger.info(f"  ✅ Downloaded {len(results)} records")
                        return results
                    else:
                        # Single record returned as dict
                        logger.info(f"  ✅ Downloaded 1 record")
                        return [data]
                else:
                    logger.error(f"  ❌ Unexpected data format: {type(data)}")
                    return []
                    
            elif response.status_code == 202:
                logger.warning("  ⚠️ Snapshot still not ready during download (HTTP 202). Skipping.")
                return []
            else:
                logger.error(f"  ❌ Download failed (HTTP {response.status_code}): {response.text}")
                return []
                
        except requests.exceptions.Timeout:
            logger.warning(f"  ⚠️ Timeout downloading snapshot {snapshot_id}. Retrying after 15s...")
            time.sleep(15)
        except requests.exceptions.RequestException as e:
            logger.warning(f"  ⚠️ Network error downloading snapshot {snapshot_id}: {e}. Retrying after 15s...")
            time.sleep(15)
        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f"  ❌ Failed to parse downloaded JSON for snapshot {snapshot_id}: {e}")
            return []
    
    logger.error(f"  ❌ Failed to download snapshot {snapshot_id} after {max_download_retries} attempts.")
    return []

def fetch_results(snapshot_id):
    """
    Two-step fetch process:
    1. Poll /progress/{snapshot_id} until status is 'ready'
    2. Download results from /snapshot/{snapshot_id}
    """
    is_ready = wait_for_snapshot_ready(snapshot_id)
    
    if not is_ready:
        logger.warning(f"  ⚠️ Snapshot {snapshot_id} never became ready. Skipping download.")
        return []
    
    return download_snapshot(snapshot_id)

def scrape_all(job_titles, countries):
    """Main loop to trigger and fetch jobs across all titles and countries. Yields results incrementally."""
    platforms = list(DATASET_IDS.keys())
    total = len(platforms) * len(job_titles) * len(countries)
    count = 0

    for platform in platforms:
        for job_title in job_titles:
            for country in countries:
                count += 1
                logger.info(f"\n[{count}/{total}] Platform: {platform.upper()} | Title: '{job_title}' | Country: {country}")

                snapshot_id = trigger_scrape(platform, job_title, country)

                if snapshot_id:
                    logger.info(f"  ⏳ Waiting {WAIT_BEFORE_FETCH}s before first status check...")
                    time.sleep(WAIT_BEFORE_FETCH)
                    results = fetch_results(snapshot_id)

                    for r in results:
                        if isinstance(r, dict):
                            r["source_platform"] = platform
                            r["search_title"]    = job_title
                            r["search_country"]  = country

                    chunk = [r for r in results if isinstance(r, dict)]
                    yield chunk
                else:
                    logger.warning(f"  ⚠️ Failed to get snapshot_id for {platform} | {job_title} | {country}")

                logger.info(f"  ⏳ Pausing {PAUSE_BETWEEN_REQUESTS}s before next trigger...")
                time.sleep(PAUSE_BETWEEN_REQUESTS)