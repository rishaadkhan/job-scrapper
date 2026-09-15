"""Job listing and analytics endpoints: Filtered queries, score tiers, and job details"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import User
from backend.schemas import JobResponse, JobListResponse, JobStatsResponse
from backend.auth import get_current_user
from backend.crud import get_jobs, get_job_by_id, get_job_stats
from backend.exceptions import NotFoundError

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Items per page"),
    company: Optional[str] = Query(None, description="Filter by company name"),
    min_score: Optional[int] = Query(None, ge=0, le=100, description="Minimum Match Score (0-100)"),
    max_score: Optional[int] = Query(None, ge=0, le=100, description="Maximum Match Score (0-100)"),
    location: Optional[str] = Query(None, description="Filter by location keyword"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD or ISO)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD or ISO)"),
    search: Optional[str] = Query(None, description="Search term across title, company, description"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """Retrieve job leads with multidimensional filtering (match score, company, location, date)."""
    jobs, total = await get_jobs(
        db=db,
        page=page,
        page_size=page_size,
        company=company,
        min_score=min_score,
        max_score=max_score,
        location=location,
        date_from=date_from,
        date_to=date_to,
        search=search
    )
    return JobListResponse(
        items=[JobResponse.model_validate(j) for j in jobs],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/stats", response_model=JobStatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """Fetch aggregate metrics: total leads, score tier distribution, and company count."""
    stats = await get_job_stats(db)
    return JobStatsResponse(**stats)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """Retrieve full details of a specific scored job posting."""
    job = await get_job_by_id(db, job_id)
    if not job:
        raise NotFoundError(message=f"Job with ID {job_id} not found")
    return JobResponse.model_validate(job)
