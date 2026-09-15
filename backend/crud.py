"""Database CRUD operations for companies, jobs, filters, runs, users, and exports"""
import re
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, update, delete, func, or_, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Company, Job, ScrapeRun, FilterConfig, User, ExportRecord
from backend.schemas import (
    CompanyCreate, CompanyUpdate, FilterConfigUpdate, JobCreate, UserCreate
)
from backend.exceptions import NotFoundError, ConflictError
from backend.config import utc_now


# --- Company Operations ---

async def get_companies(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 50,
    search: Optional[str] = None,
    ats: Optional[str] = None,
    active_only: bool = True
) -> Tuple[List[Company], int, List[str]]:
    """Fetch paginated companies with search, ATS filters, and near-duplicate detection."""
    stmt = select(Company)
    count_stmt = select(func.count(Company.id))

    filters = []
    if active_only:
        filters.append(Company.active == True)
    if ats:
        filters.append(Company.ats == ats)
    if search:
        search_pattern = f"%{search.strip()}%"
        filters.append(or_(
            Company.name.ilike(search_pattern),
            Company.career_url.ilike(search_pattern),
            Company.ats.ilike(search_pattern)
        ))

    if filters:
        stmt = stmt.where(and_(*filters))
        count_stmt = count_stmt.where(and_(*filters))

    # Order by name
    stmt = stmt.order_by(Company.name.asc()).offset((page - 1) * page_size).limit(page_size)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    result = await db.execute(stmt)
    items = list(result.scalars().all())

    # Detect near-duplicate name warnings across the returned or whole set
    dedup_warnings = []
    seen_bases = {}
    for comp in items:
        # Strip common qualifiers like 'India', 'Inc', 'Pvt', 'Labs'
        base = re.sub(r'\b(india|inc|pvt|ltd|labs|technologies|corporation)\b', '', comp.name, flags=re.IGNORECASE).strip().lower()
        if base in seen_bases:
            dedup_warnings.append(f"Near-duplicate detected: '{comp.name}' is very similar to '{seen_bases[base]}'")
        else:
            seen_bases[base] = comp.name

    return items, total, dedup_warnings


async def get_company_by_id(db: AsyncSession, company_id: int) -> Optional[Company]:
    stmt = select(Company).where(Company.id == company_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_company_by_name(db: AsyncSession, name: str) -> Optional[Company]:
    stmt = select(Company).where(Company.name.ilike(name.strip()))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_company(db: AsyncSession, comp_in: CompanyCreate) -> Company:
    existing = await get_company_by_name(db, comp_in.name)
    if existing:
        raise ConflictError(message=f"Company with name '{comp_in.name}' already exists")

    company = Company(
        name=comp_in.name,
        career_url=comp_in.career_url,
        portal_type=comp_in.portal_type,
        ats=comp_in.ats,
        ats_token=comp_in.ats_token,
        ats_id=comp_in.ats_id,
        location_filter=comp_in.location_filter,
        company_type=comp_in.company_type,
        active=comp_in.active
    )
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return company


async def update_company(db: AsyncSession, company_id: int, comp_in: CompanyUpdate) -> Company:
    company = await get_company_by_id(db, company_id)
    if not company:
        raise NotFoundError(message=f"Company with ID {company_id} not found")

    update_data = comp_in.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] != company.name:
        existing = await get_company_by_name(db, update_data["name"])
        if existing and existing.id != company.id:
            raise ConflictError(message=f"Another company already has name '{update_data['name']}'")

    for field, value in update_data.items():
        setattr(company, field, value)

    company.updated_at = utc_now()
    await db.commit()
    await db.refresh(company)
    return company


async def delete_company(db: AsyncSession, company_id: int, hard: bool = False) -> bool:
    company = await get_company_by_id(db, company_id)
    if not company:
        raise NotFoundError(message=f"Company with ID {company_id} not found")

    if hard:
        await db.delete(company)
    else:
        company.active = False
        company.updated_at = utc_now()

    await db.commit()
    return True


# --- Filter Operations ---

async def get_active_filters(db: AsyncSession) -> FilterConfig:
    """Retrieve current active filtering rules or initialize default if none exists."""
    stmt = select(FilterConfig).where(FilterConfig.is_active == True).limit(1)
    result = await db.execute(stmt)
    filters = result.scalar_one_or_none()

    if not filters:
        # Create default from config defaults
        from config import TARGET_LOCATIONS, BACKEND_KEYWORDS, EXCLUDE_KEYWORDS, TECH_STACK_KEYWORDS, LLM_SUGGESTION_THRESHOLD
        filters = FilterConfig(
            name="default",
            is_active=True,
            target_locations=TARGET_LOCATIONS,
            backend_keywords=BACKEND_KEYWORDS,
            exclude_keywords=EXCLUDE_KEYWORDS,
            tech_stack_keywords=TECH_STACK_KEYWORDS,
            min_experience=0,
            max_experience=3,
            llm_suggestion_threshold=LLM_SUGGESTION_THRESHOLD
        )
        db.add(filters)
        await db.commit()
        await db.refresh(filters)

    return filters


async def update_active_filters(db: AsyncSession, filter_in: FilterConfigUpdate) -> FilterConfig:
    filters = await get_active_filters(db)
    update_data = filter_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(filters, field, value)

    filters.updated_at = utc_now()
    await db.commit()
    await db.refresh(filters)
    return filters


# --- Job Operations ---

async def get_jobs(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 50,
    company: Optional[str] = None,
    min_score: Optional[int] = None,
    max_score: Optional[int] = None,
    location: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None
) -> Tuple[List[Job], int]:
    """Retrieve scored job leads with rich filtering and pagination."""
    stmt = select(Job)
    count_stmt = select(func.count(Job.id))

    clauses = []
    if company:
        clauses.append(Job.company_name.ilike(f"%{company.strip()}%"))
    if min_score is not None:
        clauses.append(Job.match_score >= min_score)
    if max_score is not None:
        clauses.append(Job.match_score <= max_score)
    if location:
        clauses.append(Job.location.ilike(f"%{location.strip()}%"))
    if search:
        s = f"%{search.strip()}%"
        clauses.append(or_(
            Job.title.ilike(s),
            Job.company_name.ilike(s),
            Job.description.ilike(s)
        ))
    if date_from:
        try:
            df = datetime.fromisoformat(date_from)
            clauses.append(Job.scraped_at >= df)
        except Exception:
            pass
    if date_to:
        try:
            dt = datetime.fromisoformat(date_to)
            clauses.append(Job.scraped_at <= dt)
        except Exception:
            pass

    if clauses:
        stmt = stmt.where(and_(*clauses))
        count_stmt = count_stmt.where(and_(*clauses))

    # Order by match_score descending, then scraped_at descending
    stmt = stmt.order_by(desc(Job.match_score), desc(Job.scraped_at)).offset((page - 1) * page_size).limit(page_size)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    result = await db.execute(stmt)
    jobs = list(result.scalars().all())

    return jobs, total


async def get_job_by_id(db: AsyncSession, job_pk: int) -> Optional[Job]:
    stmt = select(Job).where(Job.id == job_pk)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_job_by_job_id(db: AsyncSession, job_id_str: str) -> Optional[Job]:
    stmt = select(Job).where(Job.job_id == job_id_str)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_or_update_job(db: AsyncSession, job_data: dict) -> Job:
    """Insert or update a job record based on stable job_id."""
    job_id = job_data["job_id"]
    existing = await get_job_by_job_id(db, job_id)

    if existing:
        for k, v in job_data.items():
            if hasattr(existing, k) and k not in ("id", "created_at"):
                setattr(existing, k, v)
        await db.commit()
        await db.refresh(existing)
        return existing
    else:
        job = Job(
            job_id=job_id,
            company_name=job_data.get("company_name", job_data.get("company", "")),
            company_type=job_data.get("company_type"),
            title=job_data.get("title", ""),
            match_score=job_data.get("match_score", 0),
            experience_range=job_data.get("experience_range"),
            location=job_data.get("location"),
            top_jd_keywords=job_data.get("top_jd_keywords", []),
            missing_from_resume=job_data.get("missing_from_resume", []),
            suggested_bullets=job_data.get("suggested_bullets"),
            posted_date=job_data.get("posted_date"),
            apply_link=job_data.get("apply_link", job_data.get("link")),
            portal_url=job_data.get("portal_url"),
            description=job_data.get("description"),
            stack_match=job_data.get("stack_match", False),
            scraped_at=utc_now()
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job


async def get_job_stats(db: AsyncSession) -> dict:
    """Compute aggregate analytics for dashboard overview."""
    total = (await db.execute(select(func.count(Job.id)))).scalar_one()
    high = (await db.execute(select(func.count(Job.id)).where(Job.match_score >= 70))).scalar_one()
    mid = (await db.execute(select(func.count(Job.id)).where(and_(Job.match_score >= 40, Job.match_score < 70)))).scalar_one()
    low = (await db.execute(select(func.count(Job.id)).where(Job.match_score < 40))).scalar_one()
    companies = (await db.execute(select(func.count(func.distinct(Job.company_name))))).scalar_one()

    return {
        "total_leads": total,
        "high_match_count": high,
        "mid_match_count": mid,
        "low_match_count": low,
        "companies_represented": companies,
        "top_demanded_skills": {}
    }


# --- Scrape Run Operations ---

async def get_scrape_runs(db: AsyncSession, page: int = 1, page_size: int = 20) -> Tuple[List[ScrapeRun], int]:
    stmt = select(ScrapeRun).order_by(desc(ScrapeRun.started_at)).offset((page - 1) * page_size).limit(page_size)
    count_stmt = select(func.count(ScrapeRun.id))

    total = (await db.execute(count_stmt)).scalar_one()
    items = list((await db.execute(stmt)).scalars().all())
    return items, total


async def create_scrape_run(db: AsyncSession, status: str = "running") -> ScrapeRun:
    run = ScrapeRun(status=status, started_at=utc_now())
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run


async def update_scrape_run(db: AsyncSession, run_id: int, updates: dict) -> ScrapeRun:
    stmt = select(ScrapeRun).where(ScrapeRun.id == run_id)
    run = (await db.execute(stmt)).scalar_one_or_none()
    if not run:
        raise NotFoundError(message=f"ScrapeRun {run_id} not found")

    for k, v in updates.items():
        if hasattr(run, k):
            setattr(run, k, v)

    await db.commit()
    await db.refresh(run)
    return run


# --- User Operations ---

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    stmt = select(User).where(User.email == email.strip().lower())
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    existing = await get_user_by_email(db, user_in.email)
    if existing:
        raise ConflictError(message=f"User with email '{user_in.email}' already exists")

    from backend.auth import get_password_hash
    user = User(
        email=user_in.email.strip().lower(),
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role,
        is_active=user_in.is_active
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user_last_login(db: AsyncSession, user_id: int) -> None:
    stmt = update(User).where(User.id == user_id).values(last_login_at=utc_now())
    await db.execute(stmt)
    await db.commit()


# --- Export Operations ---

async def get_exports(db: AsyncSession) -> List[ExportRecord]:
    stmt = select(ExportRecord).where(ExportRecord.deleted_at.is_(None)).order_by(desc(ExportRecord.created_at))
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_export_by_id(db: AsyncSession, export_id: int) -> Optional[ExportRecord]:
    stmt = select(ExportRecord).where(and_(ExportRecord.id == export_id, ExportRecord.deleted_at.is_(None)))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_export_record(
    db: AsyncSession,
    filename: str,
    filepath: str,
    row_count: int,
    avg_match_score: float
) -> ExportRecord:
    record = ExportRecord(
        filename=filename,
        filepath=filepath,
        row_count=row_count,
        avg_match_score=avg_match_score,
        created_at=utc_now()
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def delete_export_record(db: AsyncSession, export_id: int) -> bool:
    record = await get_export_by_id(db, export_id)
    if not record:
        raise NotFoundError(message=f"Export record {export_id} not found")

    record.deleted_at = utc_now()
    await db.commit()
    return True
