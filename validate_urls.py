"""
Async Company URL & ATS Endpoint Validator
Validates accessibility of career portal URLs and direct public ATS API endpoints
using httpx with bounded concurrency, SSL validation, and non-blocking I/O.
"""
import asyncio
import json
import os
import argparse
from typing import Dict, Any, Tuple, List
import httpx

from config import REQUEST_TIMEOUT, USER_AGENT
from expand_companies import detect_ats


async def validate_company_url(client: httpx.AsyncClient, company: Dict[str, Any], semaphore: asyncio.Semaphore) -> Tuple[str, str, int, str]:
    """
    Checks if a company's career URL or ATS API endpoint is responsive.
    Returns (name, status_text, status_code, details).
    """
    name = company.get("name", "Unknown")
    career_url = company.get("career_url", "")
    ats = company.get("ats", "html_fallback")
    ats_token = company.get("ats_token", "")
    ats_id = company.get("ats_id", "")

    if not career_url:
        return name, "NO_URL", 0, "No URL specified"

    # Determine endpoint to test: if ATS client exists, test ATS API directly
    test_url = career_url
    if ats == "greenhouse" and ats_token:
        test_url = f"https://boards-api.greenhouse.io/v1/boards/{ats_token}/jobs"
    elif ats == "lever" and ats_token:
        test_url = f"https://api.lever.co/v0/postings/{ats_token}?limit=1"
    elif ats == "ashby" and ats_token:
        test_url = f"https://api.ashbyhq.com/posting-api/job-board/{ats_token}"
    elif ats == "smartrecruiters" and ats_token:
        test_url = f"https://api.smartrecruiters.com/v1/companies/{ats_token}/postings?limit=1"

    async with semaphore:
        try:
            headers = {"User-Agent": USER_AGENT}
            response = await client.get(test_url, headers=headers, timeout=REQUEST_TIMEOUT, follow_redirects=True)
            code = response.status_code

            if code == 200:
                return name, "OK", code, f"[{ats}] OK"
            elif code in (301, 302, 307, 308):
                return name, "REDIRECT", code, f"[{ats}] Redirect ({code})"
            elif code == 404:
                return name, "NOT_FOUND", code, f"[{ats}] 404 Not Found"
            elif code == 403:
                return name, "FORBIDDEN", code, f"[{ats}] 403 Forbidden (Cloudflare/Bot protection)"
            else:
                return name, "ERROR", code, f"[{ats}] HTTP {code}"
        except httpx.TimeoutException:
            return name, "TIMEOUT", 0, f"[{ats}] Request timed out"
        except httpx.RequestError as e:
            return name, "FAILED", 0, f"[{ats}] Network error: {type(e).__name__}"


async def validate_all_companies(companies_file: str = "companies.json", max_concurrency: int = 15, limit: int = None):
    """Asynchronously validates all company endpoints."""
    if not os.path.exists(companies_file):
        print(f"Error: {companies_file} not found.")
        return

    with open(companies_file, "r", encoding="utf-8") as f:
        companies = json.load(f)

    if limit:
        companies = companies[:limit]

    print(f"Validating {len(companies)} companies using async client (concurrency: {max_concurrency})...\n")

    semaphore = asyncio.Semaphore(max_concurrency)
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)

    async with httpx.AsyncClient(limits=limits, timeout=REQUEST_TIMEOUT) as client:
        tasks = [validate_company_url(client, comp, semaphore) for comp in companies]
        results = await asyncio.gather(*tasks)

    summary = {
        "OK": [],
        "REDIRECT": [],
        "NOT_FOUND": [],
        "FORBIDDEN": [],
        "TIMEOUT": [],
        "FAILED": [],
        "ERROR": []
    }

    for name, status, code, details in results:
        if status in summary:
            summary[status].append((name, code, details))
        else:
            summary["ERROR"].append((name, code, details))

    total = len(companies)
    ok_count = len(summary["OK"]) + len(summary["REDIRECT"])

    print("=" * 60)
    print("VALIDATION SUMMARY REPORT")
    print("=" * 60)
    print(f"✓ Healthy (200 / Redirects) : {ok_count}/{total} ({ok_count/total*100:.1f}%)")
    print(f"✗ 404 Not Found             : {len(summary['NOT_FOUND'])}")
    print(f"🛡️  403 Cloudflare/Protected  : {len(summary['FORBIDDEN'])}")
    print(f"⏱️  Timeouts                 : {len(summary['TIMEOUT'])}")
    print(f"⚠️  Network Failures         : {len(summary['FAILED'])}")
    print("=" * 60)

    if summary["NOT_FOUND"]:
        print(f"\nTop 5 404 Endpoints to Review:")
        for name, code, det in summary["NOT_FOUND"][:5]:
            print(f"  - {name}: {det}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate company career URLs and ATS APIs.")
    parser.add_argument("--file", default="companies.json", help="Path to companies.json")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of companies to check")
    parser.add_argument("--concurrency", type=int, default=15, help="Async concurrency limit")
    args = parser.parse_args()

    asyncio.run(validate_all_companies(companies_file=args.file, max_concurrency=args.concurrency, limit=args.limit))
