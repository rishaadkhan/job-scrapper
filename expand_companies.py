"""
Company Expansion Utility
Adds new companies to companies.json with automatic ATS detection,
schema validation, atomic writes, and automatic synchronization to SQLite (jobscraper.db).
"""
import os
import re
import json
import sqlite3
import argparse
from datetime import datetime
from typing import Dict, Any, List, Tuple
from urllib.parse import urlparse

# Default target locations for India engineering roles
DEFAULT_LOCATIONS = [
    "India",
    "Bengaluru",
    "Bangalore",
    "Hyderabad",
    "Pune",
    "Chennai",
    "Delhi",
    "Noida",
    "Gurgaon",
    "Gurugram",
    "Mumbai",
    "Remote"
]

# Additional curated companies with ATS metadata
ADDITIONAL_COMPANIES: List[Dict[str, Any]] = [
    # Tier-1 GCCs & Big Tech
    {
        "name": "Stripe India",
        "type": "Tier-1 GCC",
        "career_url": "https://stripe.com/jobs/search?location=India",
        "ats": "html_fallback"
    },
    {
        "name": "Databricks",
        "type": "Tier-1 GCC",
        "career_url": "https://boards.greenhouse.io/databricks",
        "ats": "greenhouse",
        "ats_token": "databricks"
    },
    {
        "name": "Snowflake",
        "type": "Tier-1 GCC",
        "career_url": "https://careers.snowflake.com/us/en/search-results?location=India",
        "ats": "workday",
        "ats_token": "snowflake",
        "ats_id": "Snowflake_Careers"
    },
    {
        "name": "Confluent",
        "type": "Tier-1 GCC",
        "career_url": "https://boards.greenhouse.io/confluent",
        "ats": "greenhouse",
        "ats_token": "confluent"
    },
    {
        "name": "MongoDB",
        "type": "Tier-1 GCC",
        "career_url": "https://boards.greenhouse.io/mongodb",
        "ats": "greenhouse",
        "ats_token": "mongodb"
    },
    {
        "name": "Elastic",
        "type": "Tier-1 GCC",
        "career_url": "https://boards.greenhouse.io/elastic",
        "ats": "greenhouse",
        "ats_token": "elastic"
    },
    {
        "name": "Twilio",
        "type": "Tier-1 GCC",
        "career_url": "https://boards.greenhouse.io/twilio",
        "ats": "greenhouse",
        "ats_token": "twilio"
    },
    {
        "name": "Okta",
        "type": "Tier-1 GCC",
        "career_url": "https://boards.greenhouse.io/okta",
        "ats": "greenhouse",
        "ats_token": "okta"
    },
    {
        "name": "Cloudflare",
        "type": "Tier-1 GCC",
        "career_url": "https://boards.greenhouse.io/cloudflare",
        "ats": "greenhouse",
        "ats_token": "cloudflare"
    },
    {
        "name": "Figma",
        "type": "Tier-1 GCC",
        "career_url": "https://boards.greenhouse.io/figma",
        "ats": "greenhouse",
        "ats_token": "figma"
    },
    {
        "name": "Notion",
        "type": "Tier-1 GCC",
        "career_url": "https://jobs.lever.co/notion",
        "ats": "lever",
        "ats_token": "notion"
    },
    {
        "name": "Canva",
        "type": "Tier-1 GCC",
        "career_url": "https://jobs.lever.co/canva",
        "ats": "lever",
        "ats_token": "canva"
    },
    {
        "name": "Grammarly",
        "type": "Tier-1 GCC",
        "career_url": "https://jobs.lever.co/grammarly",
        "ats": "lever",
        "ats_token": "grammarly"
    },
    {
        "name": "Ramp",
        "type": "Unicorn",
        "career_url": "https://jobs.ashbyhq.com/ramp",
        "ats": "ashby",
        "ats_token": "ramp"
    },
    {
        "name": "Vercel",
        "type": "Unicorn",
        "career_url": "https://jobs.ashbyhq.com/vercel",
        "ats": "ashby",
        "ats_token": "vercel"
    },
    {
        "name": "Linear",
        "type": "Unicorn",
        "career_url": "https://jobs.ashbyhq.com/linear",
        "ats": "ashby",
        "ats_token": "linear"
    },
    {
        "name": "Postman",
        "type": "Unicorn",
        "career_url": "https://jobs.lever.co/postman",
        "ats": "lever",
        "ats_token": "postman"
    },
    {
        "name": "Zepto",
        "type": "Unicorn",
        "career_url": "https://boards.greenhouse.io/zepto",
        "ats": "greenhouse",
        "ats_token": "zepto"
    },
    {
        "name": "Dream11",
        "type": "Unicorn",
        "career_url": "https://boards.greenhouse.io/dream11",
        "ats": "greenhouse",
        "ats_token": "dream11"
    },
    {
        "name": "InMobi",
        "type": "Unicorn",
        "career_url": "https://jobs.lever.co/inmobi",
        "ats": "lever",
        "ats_token": "inmobi"
    },
    {
        "name": "Urban Company",
        "type": "Unicorn",
        "career_url": "https://jobs.lever.co/urbancompany",
        "ats": "lever",
        "ats_token": "urbancompany"
    },
    {
        "name": "Coinbase India",
        "type": "Tier-1 GCC",
        "career_url": "https://boards.greenhouse.io/coinbase",
        "ats": "greenhouse",
        "ats_token": "coinbase"
    },
    {
        "name": "Rubrik India",
        "type": "Tier-1 GCC",
        "career_url": "https://boards.greenhouse.io/rubrik",
        "ats": "greenhouse",
        "ats_token": "rubrik"
    },
    {
        "name": "Cohesity India",
        "type": "Tier-1 GCC",
        "career_url": "https://boards.greenhouse.io/cohesity",
        "ats": "greenhouse",
        "ats_token": "cohesity"
    },
    {
        "name": "GitLab",
        "type": "Tier-1 GCC",
        "career_url": "https://boards.greenhouse.io/gitlab",
        "ats": "greenhouse",
        "ats_token": "gitlab"
    },
    {
        "name": "PagerDuty",
        "type": "Tier-1 GCC",
        "career_url": "https://boards.greenhouse.io/pagerduty",
        "ats": "greenhouse",
        "ats_token": "pagerduty"
    }
]


def detect_ats(url: str) -> Tuple[str, str, str]:
    """
    Analyzes a career URL and detects the underlying ATS platform and tokens.
    Returns (ats_platform, ats_token, ats_id).
    """
    if not url:
        return "html_fallback", "", ""

    url_str = url.strip()

    # 1. Greenhouse
    gh_match = re.search(r'(?:boards|job-boards|boards-api)\.greenhouse\.io/(?:v1/boards/)?([a-zA-Z0-9_\-]+)', url_str, re.I)
    if gh_match:
        token = gh_match.group(1).split('/')[0].split('?')[0]
        return "greenhouse", token, ""

    # 2. Lever
    lever_match = re.search(r'(?:jobs|api)\.lever\.co/(?:v0/postings/)?([a-zA-Z0-9_\-]+)', url_str, re.I)
    if lever_match:
        token = lever_match.group(1).split('/')[0].split('?')[0]
        return "lever", token, ""

    # 3. Ashby
    ashby_match = re.search(r'(?:jobs|api)\.ashbyhq\.com/(?:posting-api/job-board/)?([a-zA-Z0-9_\-]+)', url_str, re.I)
    if ashby_match:
        token = ashby_match.group(1).split('/')[0].split('?')[0]
        return "ashby", token, ""

    # 4. SmartRecruiters
    sr_match = re.search(r'(?:jobs|api)\.smartrecruiters\.com/(?:v1/companies/)?([a-zA-Z0-9_\-]+)', url_str, re.I)
    if sr_match:
        token = sr_match.group(1).split('/')[0].split('?')[0]
        return "smartrecruiters", token, ""

    # 5. Workday CXS
    wd_match = re.search(r'([a-zA-Z0-9_\-]+)\.(?:wd\d+|myworkdayjobs)\.com/(?:[a-zA-Z_\-]+/)?([a-zA-Z0-9_\-]+)', url_str, re.I)
    if wd_match:
        tenant = wd_match.group(1)
        site = wd_match.group(2).split('?')[0]
        return "workday", tenant, site

    return "html_fallback", "", ""


def normalize_company(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures a company dictionary conforms to the full schema."""
    name = entry.get("name", "").strip()
    c_type = entry.get("type", "Tech").strip()
    career_url = entry.get("career_url", "").strip()
    
    # Detect ATS if not provided or set to html_fallback
    ats = entry.get("ats", "")
    ats_token = entry.get("ats_token", "")
    ats_id = entry.get("ats_id", "")
    
    if not ats or (ats == "html_fallback" and not ats_token):
        detected_ats, detected_token, detected_id = detect_ats(career_url)
        if detected_ats != "html_fallback":
            ats = detected_ats
            ats_token = detected_token
            ats_id = detected_id
        elif not ats:
            ats = "html_fallback"

    locations = entry.get("location_filter")
    if not locations or not isinstance(locations, list):
        locations = list(DEFAULT_LOCATIONS)

    active = entry.get("active", True)

    return {
        "name": name,
        "type": c_type,
        "career_url": career_url,
        "location_filter": locations,
        "ats": ats,
        "ats_token": ats_token or None,
        "ats_id": ats_id or None,
        "active": active
    }


def sync_to_sqlite(companies: List[Dict[str, Any]], db_path: str = "jobscraper.db") -> int:
    """Syncs company records to SQLite database if present."""
    if not os.path.exists(db_path):
        return 0

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Ensure table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                career_url TEXT NOT NULL,
                portal_type TEXT DEFAULT 'generic',
                ats TEXT DEFAULT 'html_fallback',
                ats_token TEXT,
                ats_id TEXT,
                location_filter JSON,
                company_type TEXT DEFAULT 'Tech',
                active BOOLEAN DEFAULT 1,
                last_scraped_at DATETIME,
                job_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        upsert_count = 0
        for comp in companies:
            cursor.execute("""
                INSERT INTO companies (name, career_url, portal_type, ats, ats_token, ats_id, location_filter, company_type, active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    career_url=excluded.career_url,
                    ats=excluded.ats,
                    ats_token=excluded.ats_token,
                    ats_id=excluded.ats_id,
                    company_type=excluded.company_type,
                    active=excluded.active,
                    updated_at=excluded.updated_at
            """, (
                comp["name"],
                comp["career_url"],
                "generic",
                comp["ats"],
                comp.get("ats_token"),
                comp.get("ats_id"),
                json.dumps(comp.get("location_filter", DEFAULT_LOCATIONS)),
                comp.get("type", "Tech"),
                1 if comp.get("active", True) else 0,
                now_str,
                now_str
            ))
            upsert_count += 1
            
        conn.commit()
        conn.close()
        return upsert_count
    except Exception as e:
        print(f"Warning: Failed to sync with SQLite: {e}")
        return 0


def expand_companies(companies_file: str = "companies.json", new_entries: List[Dict[str, Any]] = None, sync_db: bool = True):
    """Adds new companies to companies.json with deduplication, atomic write, and DB sync."""
    if new_entries is None:
        new_entries = ADDITIONAL_COMPANIES

    # 1. Load existing companies
    if os.path.exists(companies_file):
        with open(companies_file, "r", encoding="utf-8") as f:
            existing_companies = json.load(f)
    else:
        existing_companies = []

    print(f"Loaded {len(existing_companies)} existing companies from {companies_file}")

    existing_names = {c["name"].strip().lower(): i for i, c in enumerate(existing_companies)}
    added_count = 0
    updated_count = 0

    # 2. Process new entries
    for raw in new_entries:
        norm = normalize_company(raw)
        name_key = norm["name"].strip().lower()

        if name_key in existing_names:
            idx = existing_names[name_key]
            # If the new entry has richer ATS info, upgrade existing
            curr = existing_companies[idx]
            if curr.get("ats") == "html_fallback" and norm["ats"] != "html_fallback":
                curr["ats"] = norm["ats"]
                curr["ats_token"] = norm["ats_token"]
                curr["ats_id"] = norm["ats_id"]
                updated_count += 1
        else:
            existing_companies.append(norm)
            existing_names[name_key] = len(existing_companies) - 1
            added_count += 1

    # 3. Atomic write to companies.json
    tmp_file = f"{companies_file}.tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(existing_companies, f, indent=2, ensure_ascii=False)
    os.replace(tmp_file, companies_file)

    print(f"✓ Updated {companies_file}: Added {added_count} new, upgraded {updated_count} existing.")
    print(f"Total companies in database: {len(existing_companies)}")

    # 4. Sync to SQLite
    if sync_db and os.path.exists("jobscraper.db"):
        synced = sync_to_sqlite(existing_companies)
        print(f"✓ Synchronized {synced} companies to SQLite database (jobscraper.db).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Expand and normalize target companies database.")
    parser.add_argument("--file", default="companies.json", help="Path to companies.json")
    parser.add_argument("--no-db-sync", action="store_true", help="Skip syncing to SQLite database")
    args = parser.parse_args()

    expand_companies(companies_file=args.file, sync_db=not args.no_db_sync)
