"""
Quick Interactive Demo of the Enterprise Job Scraper & Intelligence Engine
Scrapes real public ATS endpoints (Greenhouse/Lever), applies backend filters,
scores alignment against candidate resume, and generates a formatted Excel export.
"""
import asyncio
from datetime import datetime
import httpx
from ats_clients import fetch_company_jobs
from config import REQUEST_TIMEOUT, RESUME_FILE
from exporter import ExcelExporter
from filters import JobFilter
from scraper import validate_job_page
from scoring import JobScorer

# Curated test companies with public ATS endpoints
DEMO_COMPANIES = [
    {
        "name": "Razorpay",
        "type": "Unicorn",
        "career_url": "https://boards.greenhouse.io/razorpay",
        "ats": "greenhouse",
        "ats_token": "razorpay"
    },
    {
        "name": "Databricks",
        "type": "Tier-1 GCC",
        "career_url": "https://boards.greenhouse.io/databricks",
        "ats": "greenhouse",
        "ats_token": "databricks"
    },
    {
        "name": "Postman",
        "type": "Unicorn",
        "career_url": "https://jobs.lever.co/postman",
        "ats": "lever",
        "ats_token": "postman"
    }
]


async def run_demo():
    print("============================================================")
    print("      ENTERPRISE JOB SCRAPER & SCORING ENGINE DEMO          ")
    print("============================================================\n")
    print(f"Target Companies: {', '.join(c['name'] for c in DEMO_COMPANIES)}")
    print(f"Resume Source   : {RESUME_FILE}\n")

    scorer = JobScorer(resume_path=RESUME_FILE)
    exporter = ExcelExporter()
    valid_jobs = []

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        for comp in DEMO_COMPANIES:
            name = comp["name"]
            ats = comp.get("ats", "html_fallback")
            print(f"Fetching job listings for {name} ({ats})...")

            raw_jobs = await fetch_company_jobs(comp, client)
            print(f"  → Found {len(raw_jobs)} total postings.")

            for job in raw_jobs:
                desc = job.get("description", "")
                is_valid_page, _ = validate_job_page(desc)
                if not is_valid_page:
                    continue

                if JobFilter.filter_job(job, comp):
                    print(f"  ✓ Qualified lead: '{job.get('title')}' in {job.get('location', 'India')}")
                    scored = await scorer.score_and_enrich_job(job, client)
                    scored["scraped_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"    • Match Score     : {scored.get('match_score')}/100")
                    print(f"    • Top Skills      : {', '.join(scored.get('top_jd_keywords', [])[:4])}")
                    if scored.get("missing_from_resume"):
                        print(f"    • Missing Skills  : {', '.join(scored.get('missing_from_resume', [])[:3])}")
                    valid_jobs.append(scored)

    print("\n" + "=" * 60)
    print(f"DEMO RESULTS: {len(valid_jobs)} qualified backend leads found.")
    print("=" * 60)

    if valid_jobs:
        out_path = exporter.export_jobs(valid_jobs)
        print(f"✓ Formatted Excel spreadsheet generated at:\n  {out_path}")
    else:
        print("Note: No jobs matched the strict early-career (0-3 yrs) backend filter today.")
        print("The filtering rules are working as intended to prevent unqualified leads.")


if __name__ == "__main__":
    asyncio.run(run_demo())
