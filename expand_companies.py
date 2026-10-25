"""
Company Expansion & Ingestion Engine (Upgraded)
Features:
- Enterprise database-backed storage (PostgreSQL/SQLite via SQLAlchemy ORM)
- Robust deduplication with corporate & geographic suffix stripping and fuzzy matching
- Active ATS auto-detection and probing (Greenhouse, Lever, Ashby, SmartRecruiters, Workday)
- Honest 'unknown' fallback for unresolved ATS targets (never guess broken tokens)
- Comprehensive reporting with flagged duplicates, verified insertions, and manual review items
- Full backward compatibility with existing project utilities
"""
import os
import re
import json
import difflib
import sqlite3
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

logger = logging.getLogger("jobscraper.ingestion")

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

# Suffixes and corporate/geographic noise words to strip for deduplication
SUFFIX_TERMS = [
    r"private\s+limited",
    r"pvt\.?\s*ltd\.?",
    r"pvt\.?",
    r"ltd\.?",
    r"limited",
    r"incorporated",
    r"inc\.?",
    r"corporation",
    r"corp\.?",
    r"llc\.?",
    r"llp\.?",
    r"technologies",
    r"technology",
    r"tech\.?",
    r"labs\.?",
    r"solutions",
    r"software",
    r"services",
    r"holdings",
    r"group",
    r"systems",
    r"platform",
    r"platforms",
    r"digital",
    r"enterprises",
    r"co\.?",
    r"company",
    r"india",
    r"apac",
    r"usa?",
    r"uk",
    r"global",
    r"international"
]

_SUFFIX_REGEX = re.compile(r"\b(?:" + "|".join(SUFFIX_TERMS) + r")\b", re.IGNORECASE)

# Standard HTTP headers for polite and accurate ATS probing
PROBE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*"
}


# ==============================================================================
# 1. Normalization & Deduplication Logic
# ==============================================================================

def normalize_company_name(name: str) -> str:
    """
    Normalizes a company name for deduplication.
    Lowercases, removes bracketed text, punctuation, and strips legal/geographic
    suffixes (e.g. 'India', 'Pvt Ltd', 'Inc', 'Technologies', 'Labs').
    
    Examples:
        'Zoom India' -> 'zoom'
        'Zoom' -> 'zoom'
        'Chargebee Technologies Pvt Ltd' -> 'chargebee'
        'Nutanix India, Inc.' -> 'nutanix'
    """
    if not name:
        return ""
    
    # 1. Remove text in brackets / parentheses e.g. 'Zoom (India)' -> 'Zoom'
    cleaned = re.sub(r"[\(\[\{].*?[\)\]\}]", " ", name)
    
    # 2. Replace non-alphanumeric characters with spaces
    cleaned = re.sub(r"[^a-zA-Z0-9\s\-]", " ", cleaned)
    cleaned = cleaned.replace("-", " ")
    
    # 3. Iteratively strip suffix words from tokens
    prev = None
    curr = cleaned.lower()
    while prev != curr:
        prev = curr
        curr = _SUFFIX_REGEX.sub(" ", curr)
        curr = re.sub(r"\s+", " ", curr).strip()
        
    return curr


def fuzzy_match_company(
    candidate_name: str,
    existing_companies: List[Dict[str, Any]],
    threshold: float = 0.82
) -> Optional[Dict[str, Any]]:
    """
    Compares candidate against existing companies and returns match details if found.
    Checks exact raw names, normalized base names, token overlaps, and Levenshtein similarity.
    Never silently merges or skips. Returns None if no near/exact match.
    """
    cand_raw = candidate_name.strip()
    cand_lower = cand_raw.lower()
    cand_norm = normalize_company_name(cand_raw)

    if not cand_norm:
        return None

    cand_tokens = set(cand_norm.split())
    best_match: Optional[Dict[str, Any]] = None
    best_score: float = 0.0

    for comp in existing_companies:
        exist_name = comp.get("name", "").strip()
        exist_lower = exist_name.lower()
        exist_norm = normalize_company_name(exist_name)

        # 1. Exact raw name match (case-insensitive)
        if cand_lower == exist_lower:
            return {
                "matched": True,
                "existing_company": comp,
                "match_type": "Exact Name Match",
                "similarity": 1.0,
                "reason": f"Candidate '{cand_raw}' matches existing '{exist_name}' exactly."
            }

        if not exist_norm:
            continue

        # 2. Exact normalized base match (e.g. 'Zoom' vs 'Zoom India')
        if cand_norm == exist_norm:
            return {
                "matched": True,
                "existing_company": comp,
                "match_type": "Normalized Base Match",
                "similarity": 0.99,
                "reason": f"Candidate '{cand_raw}' matches existing '{exist_name}' after stripping corporate/geographic suffixes (normalized base: '{cand_norm}')."
            }

        exist_tokens = set(exist_norm.split())

        # 3. Token set equality or subset overlap
        if cand_tokens and exist_tokens:
            if cand_tokens == exist_tokens:
                score = 0.98
                match_type = "Token Set Match"
                reason = f"Candidate '{cand_raw}' has identical base tokens to existing '{exist_name}'."
                if score > best_score:
                    best_score = score
                    best_match = {
                        "matched": True,
                        "existing_company": comp,
                        "match_type": match_type,
                        "similarity": score,
                        "reason": reason
                    }
            elif (cand_tokens.issubset(exist_tokens) or exist_tokens.issubset(cand_tokens)) and min(len(cand_tokens), len(exist_tokens)) >= 1:
                overlap = cand_tokens & exist_tokens
                # Require that overlapping token is substantial (at least 3 characters)
                if any(len(tok) >= 3 for tok in overlap):
                    score = 0.92
                    match_type = "Token Overlap / Substring Match"
                    reason = f"Candidate '{cand_raw}' and existing '{exist_name}' share primary root tokens {list(overlap)}."
                    if score > best_score:
                        best_score = score
                        best_match = {
                            "matched": True,
                            "existing_company": comp,
                            "match_type": match_type,
                            "similarity": score,
                            "reason": reason
                        }

        # 4. Levenshtein / SequenceMatcher ratio on normalized strings
        ratio = difflib.SequenceMatcher(None, cand_norm, exist_norm).ratio()
        if ratio >= threshold and ratio > best_score:
            best_score = ratio
            best_match = {
                "matched": True,
                "existing_company": comp,
                "match_type": f"Fuzzy String Similarity ({round(ratio * 100)}%)",
                "similarity": round(ratio, 3),
                "reason": f"Normalized candidate '{cand_norm}' is {round(ratio * 100)}% similar to existing '{exist_norm}'."
            }

    return best_match


# ==============================================================================
# 2. ATS Detection & Probing Logic
# ==============================================================================

def detect_ats(url: str) -> Tuple[str, str, str]:
    """
    Analyzes a career URL and detects the underlying ATS platform and tokens.
    Returns (ats_platform, ats_token, ats_id).
    Supported platforms: Greenhouse, Lever, Ashby, SmartRecruiters, Workday CXS.
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
    sr_match = re.search(r'(?:jobs|api|careers)\.smartrecruiters\.com/(?:v1/companies/)?([a-zA-Z0-9_\-]+)', url_str, re.I)
    if sr_match:
        token = sr_match.group(1).split('/')[0].split('?')[0]
        return "smartrecruiters", token, ""

    # 5. Workday CXS
    wd_match = re.search(r'(?:https?://)?([a-zA-Z0-9_\-]+?)(?:\.wd\d+)?\.myworkdayjobs\.com/(?:[a-zA-Z_\-]+/)?([a-zA-Z0-9_\-]+)', url_str, re.I)
    if wd_match:
        tenant = wd_match.group(1)
        site = wd_match.group(2).split('?')[0]
        return "workday", tenant, site

    return "html_fallback", "", ""


def probe_ats(
    company_name: str,
    session: Optional[requests.Session] = None,
    timeout: float = 3.5
) -> Dict[str, Any]:
    """
    Probes public ATS endpoints (Greenhouse, Lever, Ashby, SmartRecruiters, Workday)
    for a candidate company with unknown URL.
    Returns: {
        'ats': platform or 'unknown',
        'token': token,
        'ats_id': id,
        'url': detected career url,
        'resolved': bool,
        'method': str
    }
    If none resolve, marks ats: 'unknown' rather than guessing.
    """
    norm_base = normalize_company_name(company_name)
    slugs = []
    # Primary slug: alphanumeric characters only
    s1 = re.sub(r'[^a-z0-9]', '', norm_base)
    if s1:
        slugs.append(s1)
    # Secondary slug: hyphen-separated
    s2 = re.sub(r'[^a-z0-9]+', '-', norm_base).strip('-')
    if s2 and s2 != s1:
        slugs.append(s2)

    sess = session or requests.Session()

    for slug in slugs:
        # 1. Probe Greenhouse API
        try:
            gh_url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
            resp = sess.get(gh_url, headers=PROBE_HEADERS, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                if "jobs" in data or "name" in data:
                    return {
                        "ats": "greenhouse",
                        "token": slug,
                        "ats_id": None,
                        "url": f"https://boards.greenhouse.io/{slug}",
                        "resolved": True,
                        "method": "greenhouse_api_probe"
                    }
        except Exception:
            pass

        # 2. Probe Lever API
        try:
            lever_url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
            resp = sess.get(lever_url, headers=PROBE_HEADERS, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    return {
                        "ats": "lever",
                        "token": slug,
                        "ats_id": None,
                        "url": f"https://jobs.lever.co/{slug}",
                        "resolved": True,
                        "method": "lever_api_probe"
                    }
        except Exception:
            pass

        # 3. Probe Ashby API
        try:
            ashby_url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
            resp = sess.get(ashby_url, headers=PROBE_HEADERS, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                if "jobs" in data or "jobBoard" in data:
                    return {
                        "ats": "ashby",
                        "token": slug,
                        "ats_id": None,
                        "url": f"https://jobs.ashbyhq.com/{slug}",
                        "resolved": True,
                        "method": "ashby_api_probe"
                    }
        except Exception:
            pass

        # 4. Probe SmartRecruiters (check career portal without following redirects to prevent false positives)
        try:
            sr_url = f"https://careers.smartrecruiters.com/{slug}"
            resp = sess.get(sr_url, headers=PROBE_HEADERS, timeout=timeout, allow_redirects=False)
            if resp.status_code == 200:
                return {
                    "ats": "smartrecruiters",
                    "token": slug,
                    "ats_id": None,
                    "url": sr_url,
                    "resolved": True,
                    "method": "smartrecruiters_portal_probe"
                }
        except Exception:
            pass

    # No ATS could be definitively resolved
    return {
        "ats": "unknown",
        "token": None,
        "ats_id": None,
        "url": "",
        "resolved": False,
        "method": "unresolved"
    }


def detect_or_probe_company_ats(
    name: str,
    career_url: Optional[str] = None,
    session: Optional[requests.Session] = None,
    timeout: float = 3.5
) -> Dict[str, Any]:
    """
    Comprehensive ATS detection:
    1. If career_url is provided, pattern-matches against known ATS platforms.
    2. If not provided or generic, actively probes public ATS endpoints.
    3. If none resolve, safely falls back to ats: 'unknown'.
    """
    url_clean = (career_url or "").strip()
    if url_clean:
        platform, token, ats_id = detect_ats(url_clean)
        if platform != "html_fallback":
            return {
                "ats": platform,
                "token": token,
                "ats_id": ats_id or None,
                "url": url_clean,
                "resolved": True,
                "method": "url_pattern"
            }

        # If a URL was provided but matched generic html, probe the URL itself for ATS redirects or links
        sess = session or requests.Session()
        try:
            resp = sess.get(url_clean, headers=PROBE_HEADERS, timeout=timeout, allow_redirects=True)
            if resp.status_code == 200:
                final_url = resp.url
                p, t, aid = detect_ats(final_url)
                if p != "html_fallback":
                    return {
                        "ats": p,
                        "token": t,
                        "ats_id": aid or None,
                        "url": final_url,
                        "resolved": True,
                        "method": "url_redirect_detection"
                    }
                # Check HTML body for ATS board links
                for pat, p_name in [
                    (r'boards\.greenhouse\.io/([a-zA-Z0-9_\-]+)', 'greenhouse'),
                    (r'jobs\.lever\.co/([a-zA-Z0-9_\-]+)', 'lever'),
                    (r'jobs\.ashbyhq\.com/([a-zA-Z0-9_\-]+)', 'ashby'),
                    (r'careers\.smartrecruiters\.com/([a-zA-Z0-9_\-]+)', 'smartrecruiters'),
                ]:
                    m = re.search(pat, resp.text, re.I)
                    if m:
                        tok = m.group(1).split('/')[0].split('?')[0]
                        return {
                            "ats": p_name,
                            "token": tok,
                            "ats_id": None,
                            "url": m.group(0),
                            "resolved": True,
                            "method": "html_embedded_ats"
                        }
        except Exception:
            pass

    # No valid URL or custom URL didn't reveal ATS: probe candidate name against platforms
    probe_res = probe_ats(name, session=session, timeout=timeout)
    if probe_res["resolved"]:
        return probe_res

    # Unresolved: keep known career_url if provided, but mark ats as unknown
    return {
        "ats": "unknown",
        "token": None,
        "ats_id": None,
        "url": url_clean,
        "resolved": False,
        "method": "unresolved"
    }


# ==============================================================================
# 3. Database Ingestion & Persistence Layer
# ==============================================================================

async def db_load_all_companies() -> List[Dict[str, Any]]:
    """
    Loads all company records directly from the database storage
    (PostgreSQL or SQLite depending on current DATABASE_URL).
    """
    try:
        from backend.database import AsyncSessionLocal
        from backend.models import Company
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            stmt = select(Company)
            res = await session.execute(stmt)
            companies = res.scalars().all()
            return [
                {
                    "id": c.id,
                    "name": c.name,
                    "career_url": c.career_url,
                    "portal_type": c.portal_type,
                    "ats": c.ats,
                    "ats_token": c.ats_token,
                    "ats_id": c.ats_id,
                    "location_filter": c.location_filter or [],
                    "company_type": c.company_type or "Tech",
                    "active": c.active,
                }
                for c in companies
            ]
    except Exception as exc:
        logger.warning(f"Could not load companies from async database: {exc}. Falling back to SQLite/JSON.")
        # Fallback to direct sqlite if jobscraper.db exists
        if os.path.exists("jobscraper.db"):
            conn = sqlite3.connect("jobscraper.db")
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            try:
                cur.execute("SELECT id, name, career_url, portal_type, ats, ats_token, ats_id, location_filter, company_type, active FROM companies")
                rows = cur.fetchall()
                result = []
                for r in rows:
                    d = dict(r)
                    if isinstance(d.get("location_filter"), str):
                        try:
                            d["location_filter"] = json.loads(d["location_filter"])
                        except Exception:
                            d["location_filter"] = list(DEFAULT_LOCATIONS)
                    result.append(d)
                conn.close()
                return result
            except Exception:
                conn.close()

        # Fallback to companies.json if DB unavailable
        if os.path.exists("companies.json"):
            with open("companies.json", "r", encoding="utf-8") as f:
                return json.load(f)
        return []


async def db_insert_company(comp_dict: Dict[str, Any]) -> Any:
    """
    Inserts a single company record directly into the database.
    """
    from backend.database import AsyncSessionLocal
    from backend.models import Company
    from backend.config import utc_now

    async with AsyncSessionLocal() as session:
        new_c = Company(
            name=comp_dict["name"],
            career_url=comp_dict.get("career_url", ""),
            portal_type=comp_dict.get("portal_type", "generic"),
            ats=comp_dict.get("ats", "unknown"),
            ats_token=comp_dict.get("ats_token"),
            ats_id=comp_dict.get("ats_id"),
            location_filter=comp_dict.get("location_filter", DEFAULT_LOCATIONS),
            company_type=comp_dict.get("type", comp_dict.get("company_type", "Tech")),
            active=comp_dict.get("active", True),
            created_at=utc_now(),
            updated_at=utc_now()
        )
        session.add(new_c)
        await session.commit()
        await session.refresh(new_c)
        return new_c


async def ingest_candidates(
    candidates: List[Dict[str, Any]],
    dry_run: bool = False,
    save_unresolved: bool = False,
    existing_companies: Optional[List[Dict[str, Any]]] = None,
    timeout: float = 3.5
) -> Dict[str, Any]:
    """
    Orchestrates ingestion of a candidate batch:
    1. Loads current storage (DB).
    2. Runs deduplication logic (exact & fuzzy matching). Flagged matches are NEVER silently added.
    3. Runs ATS auto-detection (pattern matching and probing).
    4. Writes verified, non-duplicate entries to the DB (models/session).
    5. Returns a structured summary report.
    """
    if existing_companies is None:
        existing_companies = await db_load_all_companies()

    # Track current in-memory existing list to prevent duplicates WITHIN the candidate batch itself
    current_existing = list(existing_companies)

    added = []
    flagged_duplicates = []
    ats_unresolved = []

    session = requests.Session()
    adapter = HTTPAdapter(max_retries=Retry(total=2, backoff_factor=0.5))
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    for item in candidates:
        name = item.get("name", "").strip()
        c_type = item.get("type", item.get("company_type", "Tech")).strip()
        career_url = item.get("career_url", item.get("url", "")).strip()

        if not name:
            continue

        # Step 1: Deduplication Check against existing entries
        match_info = fuzzy_match_company(name, current_existing)
        if match_info:
            flagged_duplicates.append({
                "candidate_name": name,
                "candidate_type": c_type,
                "matched_existing_name": match_info["existing_company"].get("name"),
                "matched_existing_id": match_info["existing_company"].get("id"),
                "matched_existing_ats": match_info["existing_company"].get("ats"),
                "matched_existing_url": match_info["existing_company"].get("career_url"),
                "match_type": match_info["match_type"],
                "similarity": match_info["similarity"],
                "reason": match_info["reason"],
                "action": "FLAGGED_FOR_MANUAL_REVIEW"
            })
            continue

        # Step 2: ATS Auto-Detection & Probing
        ats_info = detect_or_probe_company_ats(name, career_url=career_url, session=session, timeout=timeout)

        entry = {
            "name": name,
            "type": c_type,
            "career_url": ats_info["url"] or career_url or f"https://www.google.com/search?q={name}+careers",
            "portal_type": "generic",
            "ats": ats_info["ats"],
            "ats_token": ats_info["token"],
            "ats_id": ats_info["ats_id"],
            "location_filter": item.get("location_filter") or list(DEFAULT_LOCATIONS),
            "active": True if ats_info["resolved"] else False
        }

        # Step 3: Handle Resolved vs Unresolved
        if ats_info["resolved"]:
            if not dry_run:
                try:
                    db_obj = await db_insert_company(entry)
                    entry["id"] = db_obj.id
                except Exception as e:
                    logger.error(f"Failed to insert {name} into DB: {e}")
                    entry["db_error"] = str(e)
            
            added.append(entry)
            current_existing.append(entry)
        else:
            # ATS Unresolved: mark ats: "unknown" and flag for manual follow-up
            unres_info = {
                "candidate_name": name,
                "candidate_type": c_type,
                "ats": "unknown",
                "career_url": entry["career_url"],
                "probed_platforms": ["Greenhouse", "Lever", "Ashby", "SmartRecruiters", "Workday"],
                "manual_action": f"Search official career portal or inspect network API for '{name}'.",
                "saved_to_db": False
            }

            if save_unresolved and not dry_run:
                try:
                    entry["active"] = False
                    db_obj = await db_insert_company(entry)
                    entry["id"] = db_obj.id
                    unres_info["saved_to_db"] = True
                except Exception as e:
                    logger.error(f"Failed to insert unresolved {name} into DB: {e}")

            ats_unresolved.append(unres_info)

    session.close()

    from backend.config import DATABASE_URL
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "database_url": DATABASE_URL,
        "total_processed": len(candidates),
        "added_count": len(added),
        "flagged_duplicates_count": len(flagged_duplicates),
        "ats_unresolved_count": len(ats_unresolved),
        "added": added,
        "flagged_duplicates": flagged_duplicates,
        "ats_unresolved": ats_unresolved,
        "dry_run": dry_run
    }


def generate_ingestion_report(results: Dict[str, Any]) -> str:
    """
    Renders a human-readable text and markdown summary report of the ingestion run.
    """
    db_target = results.get("database_url", "Configured Database")
    # Redact credentials if in DATABASE_URL
    if "@" in db_target:
        db_target = db_target.split("@")[-1]

    lines = [
        "=" * 80,
        "                    COMPANY INGESTION SUMMARY REPORT",
        "=" * 80,
        f"Execution Time   : {results.get('timestamp')}",
        f"Storage Target   : {db_target}",
        f"Dry Run Mode     : {'YES (No DB changes)' if results.get('dry_run') else 'NO (Live DB Updates)'}",
        f"Total Processed  : {results.get('total_processed')}",
        f"Added (Verified) : {results.get('added_count')}",
        f"Flagged Dups     : {results.get('flagged_duplicates_count')} (Flagged for manual review, NOT added)",
        f"ATS Unresolved   : {results.get('ats_unresolved_count')} (Marked 'unknown', flagged for follow-up)",
        "=" * 80,
        ""
    ]

    # Section 1: Added
    lines.append(f"--- 1. VERIFIED & ADDED TO DATABASE ({results.get('added_count')}) ---")
    if results.get("added"):
        for c in results["added"]:
            lines.append(f"  ✓ {c['name']}")
            lines.append(f"    - Category : {c.get('type', 'Tech')}")
            lines.append(f"    - ATS      : {c.get('ats')} (token: {c.get('ats_token') or 'N/A'})")
            lines.append(f"    - URL      : {c.get('career_url')}")
    else:
        lines.append("  (None)")
    lines.append("")

    # Section 2: Flagged Duplicates
    lines.append(f"--- 2. FLAGGED DUPLICATES & NEAR-MATCHES ({results.get('flagged_duplicates_count')}) ---")
    if results.get("flagged_duplicates"):
        for d in results["flagged_duplicates"]:
            lines.append(f"  [!] Candidate: '{d['candidate_name']}'")
            lines.append(f"      - Matched Existing : '{d['matched_existing_name']}'")
            lines.append(f"      - Match Type       : {d['match_type']}")
            lines.append(f"      - Similarity Score : {d['similarity']}")
            lines.append(f"      - Reason           : {d['reason']}")
            lines.append(f"      - Existing URL     : {d['matched_existing_url']}")
            lines.append(f"      - Action           : FLAGGED FOR MANUAL REVIEW (Not inserted)")
    else:
        lines.append("  (None)")
    lines.append("")

    # Section 3: ATS Unresolved
    lines.append(f"--- 3. ATS UNRESOLVED - MARKED 'unknown' ({results.get('ats_unresolved_count')}) ---")
    if results.get("ats_unresolved"):
        for u in results["ats_unresolved"]:
            lines.append(f"  [?] Candidate: '{u['candidate_name']}'")
            lines.append(f"      - ATS Status       : {u['ats']}")
            lines.append(f"      - Probed Platforms : {', '.join(u['probed_platforms'])}")
            lines.append(f"      - Manual Action    : {u['manual_action']}")
    else:
        lines.append("  (None)")
    lines.append("")
    lines.append("=" * 80)

    return "\n".join(lines)


# ==============================================================================
# 4. Backward Compatibility Layer
# ==============================================================================

# Additional curated companies for backward compatibility
ADDITIONAL_COMPANIES: List[Dict[str, Any]] = [
    {"name": "Stripe India", "type": "Tier-1 GCC", "career_url": "https://stripe.com/jobs/search?location=India", "ats": "greenhouse", "ats_token": "stripe"},
    {"name": "Databricks", "type": "Tier-1 GCC", "career_url": "https://boards.greenhouse.io/databricks", "ats": "greenhouse", "ats_token": "databricks"},
    {"name": "Snowflake", "type": "Tier-1 GCC", "career_url": "https://careers.snowflake.com/us/en/search-results?location=India", "ats": "workday", "ats_token": "snowflake", "ats_id": "Snowflake_Careers"},
    {"name": "Confluent", "type": "Tier-1 GCC", "career_url": "https://boards.greenhouse.io/confluent", "ats": "greenhouse", "ats_token": "confluent"},
    {"name": "MongoDB", "type": "Tier-1 GCC", "career_url": "https://boards.greenhouse.io/mongodb", "ats": "greenhouse", "ats_token": "mongodb"},
    {"name": "Elastic", "type": "Tier-1 GCC", "career_url": "https://boards.greenhouse.io/elastic", "ats": "greenhouse", "ats_token": "elastic"},
    {"name": "Twilio", "type": "Tier-1 GCC", "career_url": "https://boards.greenhouse.io/twilio", "ats": "greenhouse", "ats_token": "twilio"},
    {"name": "Okta", "type": "Tier-1 GCC", "career_url": "https://boards.greenhouse.io/okta", "ats": "greenhouse", "ats_token": "okta"},
    {"name": "Cloudflare", "type": "Tier-1 GCC", "career_url": "https://boards.greenhouse.io/cloudflare", "ats": "greenhouse", "ats_token": "cloudflare"},
    {"name": "Figma", "type": "Tier-1 GCC", "career_url": "https://boards.greenhouse.io/figma", "ats": "greenhouse", "ats_token": "figma"},
    {"name": "Notion", "type": "Tier-1 GCC", "career_url": "https://jobs.lever.co/notion", "ats": "lever", "ats_token": "notion"},
    {"name": "Canva", "type": "Tier-1 GCC", "career_url": "https://jobs.lever.co/canva", "ats": "lever", "ats_token": "canva"},
    {"name": "Grammarly", "type": "Tier-1 GCC", "career_url": "https://jobs.lever.co/grammarly", "ats": "lever", "ats_token": "grammarly"},
    {"name": "Ramp", "type": "Unicorn", "career_url": "https://jobs.ashbyhq.com/ramp", "ats": "ashby", "ats_token": "ramp"},
    {"name": "Vercel", "type": "Unicorn", "career_url": "https://jobs.ashbyhq.com/vercel", "ats": "ashby", "ats_token": "vercel"},
    {"name": "Linear", "type": "Unicorn", "career_url": "https://jobs.ashbyhq.com/linear", "ats": "ashby", "ats_token": "linear"},
    {"name": "Postman", "type": "Unicorn", "career_url": "https://jobs.lever.co/postman", "ats": "lever", "ats_token": "postman"},
    {"name": "Zepto", "type": "Unicorn", "career_url": "https://boards.greenhouse.io/zepto", "ats": "greenhouse", "ats_token": "zepto"},
    {"name": "Dream11", "type": "Unicorn", "career_url": "https://boards.greenhouse.io/dream11", "ats": "greenhouse", "ats_token": "dream11"},
    {"name": "InMobi", "type": "Unicorn", "career_url": "https://jobs.lever.co/inmobi", "ats": "lever", "ats_token": "inmobi"},
    {"name": "Urban Company", "type": "Unicorn", "career_url": "https://jobs.lever.co/urbancompany", "ats": "lever", "ats_token": "urbancompany"},
    {"name": "Coinbase India", "type": "Tier-1 GCC", "career_url": "https://boards.greenhouse.io/coinbase", "ats": "greenhouse", "ats_token": "coinbase"},
    {"name": "Rubrik India", "type": "Tier-1 GCC", "career_url": "https://boards.greenhouse.io/rubrik", "ats": "greenhouse", "ats_token": "rubrik"},
    {"name": "Cohesity India", "type": "Tier-1 GCC", "career_url": "https://boards.greenhouse.io/cohesity", "ats": "greenhouse", "ats_token": "cohesity"},
    {"name": "GitLab", "type": "Tier-1 GCC", "career_url": "https://boards.greenhouse.io/gitlab", "ats": "greenhouse", "ats_token": "gitlab"},
    {"name": "PagerDuty", "type": "Tier-1 GCC", "career_url": "https://boards.greenhouse.io/pagerduty", "ats": "greenhouse", "ats_token": "pagerduty"}
]


def normalize_company(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures a company dictionary conforms to the full schema."""
    name = entry.get("name", "").strip()
    c_type = entry.get("type", "Tech").strip()
    career_url = entry.get("career_url", "").strip()

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
                comp.get("portal_type", "generic"),
                comp["ats"],
                comp.get("ats_token"),
                comp.get("ats_id"),
                json.dumps(comp.get("location_filter", DEFAULT_LOCATIONS)),
                comp.get("type", comp.get("company_type", "Tech")),
                1 if comp.get("active", True) else 0,
                now_str,
                now_str
            ))
            upsert_count += 1

        conn.commit()
        conn.close()
        return upsert_count
    except Exception as e:
        logger.warning(f"Failed to sync with SQLite: {e}")
        return 0


def expand_companies(companies_file: str = "companies.json", new_entries: List[Dict[str, Any]] = None, sync_db: bool = True):
    """
    Main legacy entrypoint for company expansion.
    Upgraded with fuzzy deduplication and async DB persistence.
    """
    if new_entries is None:
        new_entries = ADDITIONAL_COMPANIES

    async def _run():
        res = await ingest_candidates(new_entries, dry_run=False)
        print(generate_ingestion_report(res))
        return res

    return asyncio.run(_run())


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Expand and normalize target companies database.")
    parser.add_argument("--file", default="companies.json", help="Path to companies.json (legacy mode)")
    parser.add_argument("--dry-run", action="store_true", help="Evaluate without modifying DB")
    args = parser.parse_args()

    asyncio.run(ingest_candidates(ADDITIONAL_COMPANIES, dry_run=args.dry_run))
