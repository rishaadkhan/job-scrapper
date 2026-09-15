"""Async orchestrator with native ATS JSON APIs, resume intelligence, match scoring, and database persistence"""
import asyncio
import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import httpx
from ats_clients import fetch_company_jobs
from filters import JobFilter
from state_manager import StateManager
from exporter import ExcelExporter
from scraper import DomainRateLimiter, validate_job_page
from scoring import JobScorer
from config import USER_AGENT, RESUME_FILE
from backend.telemetry import init_sentry, send_heartbeat

logger = logging.getLogger("jobscraper.main")
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

# Bootstrap Sentry as early as possible
init_sentry()

MAX_CONCURRENT_COMPANIES = 10


def load_companies() -> List[Dict[str, Any]]:
    with open('companies.json', 'r') as f:
        return json.load(f)


async def process_company(
    company: Dict[str, Any],
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    state_manager: StateManager,
    state_lock: asyncio.Lock,
    scorer: JobScorer,
    idx: int,
    total: int
) -> Dict[str, Any]:
    """Scrapes, validates, filters, and scores job listings for a single company under semaphore control."""
    ats_type = company.get('ats', 'html_fallback')
    company_name = company['name']

    async with semaphore:
        print(f"[{idx}/{total}] Scraping {company_name} (ATS: {ats_type})...")
        raw_jobs = await fetch_company_jobs(company, client)
        print(f"  [{company_name}] Found {len(raw_jobs)} raw listings")

        valid_jobs = []
        skipped_count = 0

        for job in raw_jobs:
            desc = job.get('description', '')

            # Validate page content (reject empty, 404, or SPA shells)
            is_valid_page, reason = validate_job_page(desc)
            if not is_valid_page:
                skipped_count += 1
                continue

            # Apply business filtering (location, positive backend role, experience)
            if JobFilter.filter_job(job, company):
                job_id = f"{company_name}_{job['job_id']}"

                async with state_lock:
                    is_seen = state_manager.is_job_seen(job_id)

                if not is_seen:
                    # Enrich with match score, top keywords, missing keywords, and LLM bullets
                    scored_job = await scorer.score_and_enrich_job(job, client)
                    scored_job['scraped_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    async with state_lock:
                        valid_jobs.append(scored_job)
                        state_manager.mark_job_seen(job_id, company_name)

                    print(f"  ✓ [{company_name}] '{job['title']}': Match Score {scored_job.get('match_score', 0)}/100")

        async with state_lock:
            state_manager.mark_company_scraped(company_name, len(valid_jobs))

        return {
            'company': company_name,
            'ats': ats_type,
            'raw_count': len(raw_jobs),
            'valid_count': len(valid_jobs),
            'skipped_count': skipped_count,
            'valid_jobs': valid_jobs
        }


def print_yield_comparison(stats: List[Dict[str, Any]], total_companies: int, duration_sec: float):
    """Prints a detailed yield comparison and telemetry report to console."""
    ats_breakdown: Dict[str, Dict[str, int]] = {}

    total_raw = 0
    total_valid = 0
    companies_with_jobs = 0
    companies_zero_jobs = 0

    for s in stats:
        ats = s['ats']
        if ats not in ats_breakdown:
            ats_breakdown[ats] = {
                'companies': 0,
                'companies_with_jobs': 0,
                'companies_zero': 0,
                'raw_jobs': 0,
                'valid_jobs': 0
            }

        ats_breakdown[ats]['companies'] += 1
        ats_breakdown[ats]['raw_jobs'] += s['raw_count']
        ats_breakdown[ats]['valid_jobs'] += s['valid_count']

        if s['raw_count'] > 0:
            ats_breakdown[ats]['companies_with_jobs'] += 1
            companies_with_jobs += 1
        else:
            ats_breakdown[ats]['companies_zero'] += 1
            companies_zero_jobs += 1

        total_raw += s['raw_count']
        total_valid += s['valid_count']

    print("\n" + "=" * 78)
    print("           JOB SCRAPER INGESTION ENGINE: YIELD & TELEMETRY REPORT")
    print("=" * 78)
    print(f"Total Companies Evaluated : {total_companies}")
    print(f"Total Pipeline Duration   : {duration_sec:.2f} seconds")
    print(f"Total Raw Listings Ingested: {total_raw}")
    print(f"Total Qualified Leads     : {total_valid}")
    print(f"Companies with >=1 Listing: {companies_with_jobs} ({(companies_with_jobs/total_companies*100):.1f}%)")
    print(f"Companies with 0 Listings : {companies_zero_jobs} ({(companies_zero_jobs/total_companies*100):.1f}%)")
    print("-" * 78)
    print(f"{'ATS Platform':<18} | {'Companies':<10} | {'With Jobs':<10} | {'Zero Jobs':<10} | {'Raw Jobs':<10} | {'Valid Leads':<10}")
    print("-" * 78)

    for ats, data in sorted(ats_breakdown.items(), key=lambda x: x[1]['companies'], reverse=True):
        print(f"{ats:<18} | {data['companies']:<10} | {data['companies_with_jobs']:<10} | {data['companies_zero']:<10} | {data['raw_jobs']:<10} | {data['valid_jobs']:<10}")

    print("=" * 78 + "\n")


async def async_main():
    start_time_mono = time.monotonic()
    start_time_dt = datetime.utcnow()
    print("=== Async Job Scraper Engine Started ===")
    print(f"Timestamp: {start_time_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Concurrency Limit: {MAX_CONCURRENT_COMPANIES} simultaneous workers")
    print(f"Resume Source    : {RESUME_FILE}\n")

    state_manager = StateManager()
    exporter = ExcelExporter()
    scorer = JobScorer(resume_path=RESUME_FILE)

    # Try loading from database if available, else fallback to companies.json
    all_companies = []
    try:
        from backend.db_service import db_load_active_companies
        all_companies = await db_load_active_companies()
    except Exception as exc:
        logger.debug(f"DB company load skipped, falling back to companies.json: {exc}")

    if not all_companies:
        all_companies = load_companies()

    companies_to_scrape = state_manager.get_companies_to_scrape(all_companies)

    print(f"Total companies in database: {len(all_companies)}")
    print(f"Candidate Skills Indexed   : {len(scorer.matcher.resume_keywords)} skills")
    print(f"Companies to scrape in this run: {len(companies_to_scrape)}\n")

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_COMPANIES)
    state_lock = asyncio.Lock()

    limits = httpx.Limits(max_connections=50, max_keepalive_connections=20)
    timeout = httpx.Timeout(20.0, connect=10.0)

    async with httpx.AsyncClient(limits=limits, timeout=timeout, headers={'User-Agent': USER_AGENT}, follow_redirects=True) as client:
        tasks = [
            process_company(
                company=company,
                client=client,
                semaphore=semaphore,
                state_manager=state_manager,
                state_lock=state_lock,
                scorer=scorer,
                idx=i,
                total=len(companies_to_scrape)
            )
            for i, company in enumerate(companies_to_scrape, 1)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=False)

    all_valid_jobs = []
    for r in results:
        all_valid_jobs.extend(r['valid_jobs'])

    # Cleanup state and save legacy JSON state
    state_manager.cleanup_old_jobs()
    state_manager.save_state()

    duration = time.monotonic() - start_time_mono

    # Output yield summary
    print_yield_comparison(results, len(companies_to_scrape), duration)

    # Export to Excel
    export_filepath = None
    if all_valid_jobs:
        export_filepath = exporter.export_jobs(all_valid_jobs)
        print(f"Excel report generated: {export_filepath}")
    else:
        print("No new jobs to export in this run.")

    # Persist run results, leads, and export to Database
    run_id: Optional[int] = None
    try:
        from backend.db_service import db_save_scrape_results
        run_id = await db_save_scrape_results(
            valid_jobs=all_valid_jobs,
            company_stats=results,
            start_time_dt=start_time_dt,
            duration_sec=duration,
            export_filepath=export_filepath
        )
    except Exception as exc:
        logger.warning(f"Could not sync scrape run to DB: {exc}")

    # Send daily digest notification (Telegram primary, SMTP fallback)
    try:
        from notifier.digest import send_daily_digest
        await send_daily_digest(valid_jobs=all_valid_jobs, run_id=run_id)
    except Exception as exc:
        logger.warning(f"Digest notification failed (non-fatal): {exc}")

    # Ping heartbeat URL to signal successful completion
    send_heartbeat()

    print("=== Job Scraping Complete ===")


def main():
    asyncio.run(async_main())


if __name__ == '__main__':
    main()
