"""Scrape run history and trigger endpoints: Telemetry inspection and run orchestration"""
import os
import asyncio
import logging
from fastapi import APIRouter, Depends, Query, BackgroundTasks, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db, AsyncSessionLocal
from backend.models import User
from backend.schemas import (
    ScrapeRunListResponse, ScrapeRunResponse, ScrapeTriggerResponse,
    BulkActionRequest, BulkActionResponse
)
from backend.auth import get_current_user, require_admin
from backend.crud import (
    get_scrape_runs, get_active_scrape_run, create_scrape_run, update_scrape_run,
    get_scrape_run_by_id, get_scrape_runs_by_ids, delete_scrape_run, delete_scrape_runs_bulk
)
from backend.exceptions import ConflictError, NotFoundError
from backend.config import utc_now
from exporter import ExcelExporter

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


@router.post("/bulk-download")
async def bulk_download_runs(
    req: BulkActionRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """Generate and download a formatted Excel report for selected scrape runs."""
    runs = await get_scrape_runs_by_ids(db, req.ids)
    if not runs:
        raise NotFoundError(message="No matching scrape runs found for export")

    run_payloads = [
        {
            "id": r.id,
            "started_at": r.started_at.strftime("%Y-%m-%d %H:%M:%S") if r.started_at else "",
            "completed_at": r.completed_at.strftime("%Y-%m-%d %H:%M:%S") if r.completed_at else "",
            "status": r.status,
            "duration_sec": r.duration_sec,
            "total_companies": r.total_companies,
            "companies_with_jobs": r.companies_with_jobs,
            "companies_zero_jobs": r.companies_zero_jobs,
            "total_raw_jobs": r.total_raw_jobs,
            "total_valid_leads": r.total_valid_leads,
            "avg_match_score": r.avg_match_score,
            "error_log": r.error_log or ""
        }
        for r in runs
    ]

    exporter = ExcelExporter()
    prefix = f"scrape_run_{runs[0].id}_report" if len(runs) == 1 else "scrape_runs_report"
    filepath = exporter.export_scrape_runs(run_payloads, filename_prefix=prefix)
    filename = os.path.basename(filepath)

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/{run_id}/download")
async def download_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """Download a formatted Excel report for a single scrape run."""
    run = await get_scrape_run_by_id(db, run_id)
    if not run:
        raise NotFoundError(message=f"Scrape run #{run_id} not found")

    run_payload = {
        "id": run.id,
        "started_at": run.started_at.strftime("%Y-%m-%d %H:%M:%S") if run.started_at else "",
        "completed_at": run.completed_at.strftime("%Y-%m-%d %H:%M:%S") if run.completed_at else "",
        "status": run.status,
        "duration_sec": run.duration_sec,
        "total_companies": run.total_companies,
        "companies_with_jobs": run.companies_with_jobs,
        "companies_zero_jobs": run.companies_zero_jobs,
        "total_raw_jobs": run.total_raw_jobs,
        "total_valid_leads": run.total_valid_leads,
        "avg_match_score": run.avg_match_score,
        "error_log": run.error_log or ""
    }

    exporter = ExcelExporter()
    filepath = exporter.export_scrape_runs([run_payload], filename_prefix=f"scrape_run_{run.id}_report")
    filename = os.path.basename(filepath)

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.post("/bulk-delete", response_model=BulkActionResponse)
async def bulk_delete_runs(
    req: BulkActionRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """Delete multiple scrape runs from history. Cannot delete running jobs."""
    deleted_count = await delete_scrape_runs_bulk(db, req.ids)
    return BulkActionResponse(
        message=f"Successfully deleted {deleted_count} scrape run(s)",
        affected_count=deleted_count
    )


@router.delete("/{run_id}")
async def delete_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """Delete a single scrape run from history."""
    await delete_scrape_run(db, run_id)
    return {"message": f"Scrape run #{run_id} successfully deleted"}
