"""Scrape run history and trigger endpoints: Telemetry inspection and run orchestration"""
import asyncio
from fastapi import APIRouter, Depends, Query, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db, AsyncSessionLocal
from backend.models import User
from backend.schemas import ScrapeRunListResponse, ScrapeRunResponse, ScrapeTriggerResponse
from backend.auth import get_current_user, require_admin
from backend.crud import get_scrape_runs, create_scrape_run, update_scrape_run

router = APIRouter(prefix="/runs", tags=["Scrape Runs"])


async def run_scraper_task(run_id: int):
    """Background task to execute the ingestion engine and persist telemetry to DB."""
    try:
        from main import async_main
        # Run the existing async engine
        await async_main()

        async with AsyncSessionLocal() as session:
            await update_scrape_run(session, run_id, {
                "status": "completed",
                "completed_at": None  # will use default or updated timestamp
            })
    except Exception as e:
        async with AsyncSessionLocal() as session:
            await update_scrape_run(session, run_id, {
                "status": "failed",
                "error_log": str(e)
            })


@router.get("", response_model=ScrapeRunListResponse)
async def list_runs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """Retrieve history of automated or manual scrape runs with yields and performance telemetry."""
    runs, total = await get_scrape_runs(db, page=page, page_size=page_size)
    return ScrapeRunListResponse(
        items=[ScrapeRunResponse.model_validate(r) for r in runs],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/trigger", response_model=ScrapeTriggerResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_run(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
):
    """Manually launch a full scraping, filtering, and scoring run in the background (Admin only)."""
    run = await create_scrape_run(db, status="running")
    background_tasks.add_task(run_scraper_task, run.id)
    return ScrapeTriggerResponse(
        message="Scrape run successfully initiated in the background",
        run_id=run.id,
        status="running"
    )
