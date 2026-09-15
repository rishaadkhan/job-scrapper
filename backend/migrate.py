"""Migration script: Imports companies.json, scraper_state.json history, and defaults into SQLite"""
import json
import os
import asyncio
import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import init_db, AsyncSessionLocal
from backend.models import Company, Job, FilterConfig, User, ExportRecord
from backend.auth import get_password_hash
from backend.config import ADMIN_EMAIL, ADMIN_PASSWORD, OUTPUT_DIR, utc_now
from config import (
    TARGET_LOCATIONS, BACKEND_KEYWORDS, EXCLUDE_KEYWORDS,
    TECH_STACK_KEYWORDS, LLM_SUGGESTION_THRESHOLD
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("migration")


async def migrate_data():
    """Idempotently seed and migrate existing file state to the database."""
    logger.info("Initializing database schema...")
    await init_db()

    async with AsyncSessionLocal() as session:
        # 1. Seed or verify Admin User
        stmt = select(User).where(User.email == ADMIN_EMAIL.lower())
        existing_admin = (await session.execute(stmt)).scalar_one_or_none()
        if not existing_admin:
            logger.info(f"Creating default admin user: {ADMIN_EMAIL}")
            admin_user = User(
                email=ADMIN_EMAIL.lower(),
                hashed_password=get_password_hash(ADMIN_PASSWORD),
                role="admin",
                is_active=True,
                created_at=utc_now()
            )
            session.add(admin_user)
        else:
            logger.info(f"Admin user {ADMIN_EMAIL} already exists.")

        # 2. Seed default FilterConfig
        stmt = select(FilterConfig).where(FilterConfig.name == "default")
        existing_filter = (await session.execute(stmt)).scalar_one_or_none()
        if not existing_filter:
            logger.info("Seeding default FilterConfig...")
            filter_config = FilterConfig(
                name="default",
                is_active=True,
                target_locations=TARGET_LOCATIONS,
                backend_keywords=BACKEND_KEYWORDS,
                exclude_keywords=EXCLUDE_KEYWORDS,
                tech_stack_keywords=TECH_STACK_KEYWORDS,
                min_experience=0,
                max_experience=3,
                llm_suggestion_threshold=LLM_SUGGESTION_THRESHOLD,
                updated_at=utc_now()
            )
            session.add(filter_config)

        # 3. Load scraper_state.json metadata
        state_data = {"companies": {}, "seen_jobs": {}}
        if os.path.exists("scraper_state.json"):
            try:
                with open("scraper_state.json", "r") as f:
                    state_data = json.load(f)
                logger.info(f"Loaded scraper_state.json with {len(state_data.get('companies', {}))} company records and {len(state_data.get('seen_jobs', {}))} seen jobs.")
            except Exception as e:
                logger.warning(f"Could not read scraper_state.json: {e}")

        # 4. Migrate companies.json
        if os.path.exists("companies.json"):
            with open("companies.json", "r") as f:
                companies_list = json.load(f)

            logger.info(f"Migrating {len(companies_list)} companies from companies.json...")
            comp_state_map = state_data.get("companies", {})
            added_companies = 0
            updated_companies = 0

            for c in companies_list:
                comp_name = c.get("name", "").strip()
                if not comp_name:
                    continue

                stmt = select(Company).where(Company.name.ilike(comp_name))
                existing_c = (await session.execute(stmt)).scalar_one_or_none()

                # Check state metadata for last_scraped
                last_scraped_dt = None
                job_count = 0
                if comp_name in comp_state_map:
                    meta = comp_state_map[comp_name]
                    try:
                        last_scraped_dt = datetime.fromisoformat(meta.get("last_scraped"))
                    except Exception:
                        pass
                    job_count = meta.get("job_count", 0)

                if not existing_c:
                    new_c = Company(
                        name=comp_name,
                        career_url=c.get("career_url", ""),
                        portal_type=c.get("portal_type", "generic"),
                        ats=c.get("ats", "html_fallback"),
                        ats_token=c.get("ats_token"),
                        ats_id=c.get("ats_id"),
                        location_filter=c.get("location_filter", []),
                        company_type=c.get("type", "Tech"),
                        active=True,
                        last_scraped_at=last_scraped_dt,
                        job_count=job_count,
                        created_at=utc_now()
                    )
                    session.add(new_c)
                    added_companies += 1
                else:
                    # Update fields if missing
                    existing_c.career_url = c.get("career_url", existing_c.career_url)
                    existing_c.ats = c.get("ats", existing_c.ats)
                    existing_c.ats_token = c.get("ats_token", existing_c.ats_token)
                    existing_c.ats_id = c.get("ats_id", existing_c.ats_id)
                    existing_c.location_filter = c.get("location_filter", existing_c.location_filter)
                    if last_scraped_dt and not existing_c.last_scraped_at:
                        existing_c.last_scraped_at = last_scraped_dt
                        existing_c.job_count = job_count
                    updated_companies += 1

            logger.info(f"Companies migration complete: {added_companies} added, {updated_companies} existing/updated.")

        # 5. Migrate seen_jobs from scraper_state.json
        seen_jobs = state_data.get("seen_jobs", {})
        logger.info(f"Migrating {len(seen_jobs)} seen jobs history into DB...")
        added_jobs = 0
        for job_key, job_meta in seen_jobs.items():
            stmt = select(Job).where(Job.job_id == job_key)
            existing_j = (await session.execute(stmt)).scalar_one_or_none()
            if not existing_j:
                first_seen = None
                try:
                    first_seen = datetime.fromisoformat(job_meta.get("first_seen"))
                except Exception:
                    first_seen = utc_now()

                job_record = Job(
                    job_id=job_key,
                    company_name=job_meta.get("company", "Unknown"),
                    title="Historical Lead",
                    match_score=50,
                    location="India",
                    scraped_at=first_seen,
                    created_at=first_seen or utc_now()
                )
                session.add(job_record)
                added_jobs += 1

        logger.info(f"Seen jobs migration complete: {added_jobs} historical job records created.")

        # 6. Index existing output xlsx files
        if os.path.exists(OUTPUT_DIR):
            for fname in os.listdir(OUTPUT_DIR):
                if fname.endswith(".xlsx"):
                    fpath = os.path.join(OUTPUT_DIR, fname)
                    stmt = select(ExportRecord).where(ExportRecord.filename == fname)
                    existing_exp = (await session.execute(stmt)).scalar_one_or_none()
                    if not existing_exp:
                        stat = os.stat(fpath)
                        session.add(ExportRecord(
                            filename=fname,
                            filepath=fpath,
                            row_count=0,
                            avg_match_score=0.0,
                            created_at=datetime.fromtimestamp(stat.st_mtime)
                        ))

        await session.commit()
        logger.info("Database migration successfully finished!")


def main():
    asyncio.run(migrate_data())


if __name__ == "__main__":
    main()
