"""Export and spreadsheet download endpoints: On-demand Excel generation and file serving"""
import os
from typing import Optional
from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import User
from backend.schemas import ExportRequest, ExportResponse, ExportListResponse
from backend.auth import get_current_user, require_admin
from backend.crud import (
    get_jobs, create_export_record, get_exports, get_export_by_id, delete_export_record
)
from backend.exceptions import NotFoundError, ValidationError
from exporter import ExcelExporter

router = APIRouter(prefix="/exports", tags=["Exports"])


@router.post("", response_model=ExportResponse, status_code=status.HTTP_201_CREATED)
async def generate_export(
    export_req: ExportRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """Generate a 15-column formatted Excel file from filtered DB jobs and create a download link."""
    jobs, total = await get_jobs(
        db=db,
        page=1,
        page_size=export_req.limit or 1000,
        company=export_req.company,
        min_score=export_req.min_score,
        date_from=export_req.date_from,
        date_to=export_req.date_to
    )

    if not jobs:
        raise ValidationError(message="No job leads match the specified criteria to export")

    # Convert ORM jobs to dictionary payload expected by ExcelExporter
    job_dicts = []
    total_score = 0
    for j in jobs:
        score = j.match_score or 0
        total_score += score
        job_dicts.append({
            "company": j.company_name,
            "company_type": j.company_type or "Tech",
            "title": j.title,
            "match_score": score,
            "experience_range": j.experience_range or "0-3 years",
            "location": j.location or "India",
            "top_jd_keywords": j.top_jd_keywords or [],
            "missing_from_resume": j.missing_from_resume or [],
            "suggested_bullets": j.suggested_bullets or "",
            "job_id": j.job_id,
            "posted_date": j.posted_date or "",
            "link": j.apply_link or "",
            "portal_url": j.portal_url or "",
            "description": j.description or "",
            "scraped_at": j.scraped_at.strftime("%Y-%m-%d %H:%M:%S") if j.scraped_at else ""
        })

    exporter = ExcelExporter()
    filepath = exporter.export_jobs(job_dicts)
    filename = os.path.basename(filepath)
    avg_score = round(total_score / len(jobs), 2) if jobs else 0.0

    record = await create_export_record(
        db=db,
        filename=filename,
        filepath=filepath,
        row_count=len(jobs),
        avg_match_score=avg_score
    )

    return ExportResponse(
        id=record.id,
        filename=record.filename,
        row_count=record.row_count,
        avg_match_score=record.avg_match_score,
        download_url=f"/exports/{record.id}/download",
        created_at=record.created_at
    )


@router.get("", response_model=ExportListResponse)
async def list_exports(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """List all available generated Excel exports with row counts and average match scores."""
    records = await get_exports(db)
    items = [
        ExportResponse(
            id=r.id,
            filename=r.filename,
            row_count=r.row_count,
            avg_match_score=r.avg_match_score,
            download_url=f"/exports/{r.id}/download",
            created_at=r.created_at
        )
        for r in records
    ]
    return ExportListResponse(items=items, total=len(items))


@router.get("/{export_id}/download")
async def download_export(
    export_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """Download the requested Excel spreadsheet file as a binary attachment."""
    record = await get_export_by_id(db, export_id)
    if not record or not os.path.exists(record.filepath):
        raise NotFoundError(message=f"Export spreadsheet {export_id} not found on server")

    return FileResponse(
        path=record.filepath,
        filename=record.filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.delete("/{export_id}")
async def delete_export(
    export_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
):
    """Delete an export record and remove its generated spreadsheet file (Admin only)."""
    record = await get_export_by_id(db, export_id)
    if not record:
        raise NotFoundError(message=f"Export spreadsheet {export_id} not found")

    if os.path.exists(record.filepath):
        try:
            os.remove(record.filepath)
        except OSError:
            pass

    await delete_export_record(db, export_id)
    return {"message": f"Export {export_id} successfully deleted"}
