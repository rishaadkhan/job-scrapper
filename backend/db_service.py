"""Database integration service for ingestion pipeline and batch scraper jobs"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import AsyncSessionLocal
from backend.models import Company, Job, ScrapeRun, FilterConfig, ExportRecord
from backend.crud import create_or_update_job, create_export_record
from backend.config import utc_now

logger = logging.getLogger("jobscraper.db_service")


async def db_load_active_companies() -> List[Dict[str, Any]]:
    """Load active company targets from the database. Returns dicts compatible with ATS clients."""
    async with AsyncSessionLocal() as db:
        stmt = select(Company).where(Company.active == True).order_by(Company.name.asc())
        result = await db.execute(stmt)
        companies = result.scalars().all()
        return [
            {
                "name": c.name,
                "career_url": c.career_url,
                "portal_type": c.portal_type,
                "ats": c.ats,
                "ats_token": c.ats_token,
                "ats_id": c.ats_id,
                "location_filter": c.location_filter or [],
                "type": c.company_type or "Tech"
            }
            for c in companies
        ]


async def db_load_seen_job_ids() -> set:
    """Load set of all previously seen job_ids for fast O(1) in-memory deduplication."""
    async with AsyncSessionLocal() as db:
        stmt = select(Job.job_id)
        result = await db.execute(stmt)
        return set(result.scalars().all())


async def db_save_scrape_results(
    valid_jobs: List[Dict[str, Any]],
    company_stats: List[Dict[str, Any]],
    start_time_dt: datetime,
    duration_sec: float,
    export_filepath: Optional[str] = None
) -> Optional[int]:
    """
    Persist all valid leads, update company scrape timestamps,
    log the scrape run telemetry, and register the generated export.
    """
    async with AsyncSessionLocal() as db:
        try:
            # 1. Insert/Update Scored Jobs
            for j in valid_jobs:
                await create_or_update_job(db, j)

            # 2. Update company scrape timestamps and counts
            for stat in company_stats:
                comp_name = stat.get("company")
                valid_count = stat.get("valid_count", 0)
                if comp_name:
                    stmt = update(Company).where(Company.name.ilike(comp_name)).values(
                        last_scraped_at=utc_now(),
                        job_count=valid_count,
                        updated_at=utc_now()
                    )
                    await db.execute(stmt)

            # 3. Calculate metrics for ScrapeRun
            total_raw = sum(s.get("raw_count", 0) for s in company_stats)
            total_valid = len(valid_jobs)
            companies_with_jobs = sum(1 for s in company_stats if s.get("raw_count", 0) > 0)
            companies_zero = len(company_stats) - companies_with_jobs
            avg_score = (
                round(sum(j.get("match_score", 0) for j in valid_jobs) / total_valid, 2)
                if total_valid > 0 else 0.0
            )

            run = ScrapeRun(
                started_at=start_time_dt,
                completed_at=utc_now(),
                duration_sec=round(duration_sec, 2),
                total_companies=len(company_stats),
                companies_with_jobs=companies_with_jobs,
                companies_zero_jobs=companies_zero,
                total_raw_jobs=total_raw,
                total_valid_leads=total_valid,
                avg_match_score=avg_score,
                status="completed"
            )
            db.add(run)
            await db.flush()

            # 4. If an Excel file was generated, record it in exports
            if export_filepath:
                import os
                filename = os.path.basename(export_filepath)
                exp = ExportRecord(
                    filename=filename,
                    filepath=export_filepath,
                    row_count=total_valid,
                    avg_match_score=avg_score,
                    created_at=utc_now()
                )
                db.add(exp)

            await db.commit()
            logger.info(f"Database sync complete: ScrapeRun #{run.id} logged with {total_valid} leads.")
            return run.id
        except Exception as e:
            await db.rollback()
            logger.error(f"Error persisting scrape results to database: {e}", exc_info=True)
            return None
