"""Scrape run history and trigger endpoints: Telemetry inspection and run orchestration"""
import asyncio
import logging
from fastapi import APIRouter, Depends, Query, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db, AsyncSessionLocal
from backend.models import User
from backend.schemas import ScrapeRunListResponse, ScrapeRunResponse, ScrapeTriggerResponse
from backend.auth import get_current_user, require_admin
from backend.crud import get_scrape_runs, get_active_scrape_run, create_scrape_run, update_scrape_run
from backend.exceptions import ConflictError
from backend.config import utc_now

logger = logging.getLogger("jobscraper.backend.runs")

router = APIRouter(prefix="/runs", tags=["Scrape Runs"])


async def run_scraper_task(run_id: int):
    """Background task to execute the ingestion engine and persist telemetry to DB."""
    try:
        from main import async_main
        # Execute scraping pipeline passing the tracking run_id
        await async_main(run_id=run_id)
    except Exception as e:
        logger.error(f"Background scraper run #{run_id} failed: {e}", exc_info=True)
        try:
            async with AsyncSessionLocal() as session:
                await update_scrape_run(session, run_id, {
                    "status": "failed",
                    "error_log": str(e),
                    "completed_at": utc_now()
                })
        except Exception as inner_e:
            logger.error(f"Failed to record failure status for run #{run_id}: {inner_e}")


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
    active_run = await get_active_scrape_run(db)
    if active_run:
        raise ConflictError(message=f"Scrape run #{active_run.id} is already in progress. Please wait for it to finish.")

    run = await create_scrape_run(db, status="running")
    background_tasks.add_task(run_scraper_task, run.id)
    return ScrapeTriggerResponse(
        message="Scrape run successfully initiated in the background",
        run_id=run.id,
        status="running"
    )
