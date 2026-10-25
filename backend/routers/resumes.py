"""Resume management endpoints: upload, list, retrieve, and delete candidate LaTeX templates"""
import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Request, UploadFile, File, Form, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import User
from backend.auth import get_current_user
from backend.schemas import ResumeResponse, ResumeListResponse
from backend.crud import (
    create_resume, get_resumes, get_resume_by_id, delete_resume
)
from backend.latex_validator import validate_latex_source
from backend.exceptions import NotFoundError, ValidationError

logger = logging.getLogger("jobscraper.resumes")

router = APIRouter(prefix="/resumes", tags=["Resumes"])


@router.post("", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload and validate a LaTeX resume template.
    
    Accepts:
    1. JSON body: { "label": "...", "latex_source": "...", "is_master": bool }
    2. Multipart form data: 'file' upload (.tex) or 'latex_source' field, plus 'label' and 'is_master'
    3. Raw text body with optional query parameters ?label=...&is_master=...
    
    Validation:
    - Balanced \\begin{...} and \\end{...} environments
    - At least one '%-- AI:EDITABLE START --%' marker
    Rejects broken source with clear structured error.
    """
    content_type = request.headers.get("content-type", "")
    latex_source = ""
    label = ""
    is_master = False

    if "multipart/form-data" in content_type:
        form = await request.form()
        label_val = form.get("label")
        if label_val:
            label = str(label_val).strip()

        is_master_val = form.get("is_master", "false")
        is_master = str(is_master_val).lower() in ("true", "1", "yes", "t")

        file_obj = form.get("file")
        if file_obj and hasattr(file_obj, "read"):
            content_bytes = await file_obj.read()
            latex_source = content_bytes.decode("utf-8", errors="replace")
            if not label and hasattr(file_obj, "filename") and file_obj.filename:
                label = file_obj.filename.replace(".tex", "").replace("_", " ").title()
        
        if not latex_source and form.get("latex_source"):
            latex_source = str(form.get("latex_source"))

    elif "application/json" in content_type:
        try:
            body = await request.json()
        except Exception as exc:
            raise ValidationError(message=f"Invalid JSON payload: {exc}")

        latex_source = body.get("latex_source", "")
        label = body.get("label", "")
        is_master = bool(body.get("is_master", False))

    else:
        # Fallback: Raw text body
        raw_bytes = await request.body()
        latex_source = raw_bytes.decode("utf-8", errors="replace")
        label = request.query_params.get("label", "Untitled Resume")
        is_master = request.query_params.get("is_master", "false").lower() in ("true", "1", "yes")

    if not label or not label.strip():
        label = "Master Resume" if is_master else "Untitled Resume"

    # Strict LaTeX validation — rejects invalid source with clear message
    validate_latex_source(latex_source)

    resume = await create_resume(
        db=db,
        user_id=current_user.id,
        label=label.strip(),
        latex_source=latex_source,
        is_master=is_master
    )
    logger.info(f"Successfully uploaded resume id={resume.id} ('{resume.label}') for user {current_user.email}")
    return ResumeResponse.model_validate(resume)


@router.get("", response_model=ResumeListResponse)
async def list_resumes(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all resumes uploaded by the current user."""
    items, total = await get_resumes(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size
    )
    return ResumeListResponse(
        items=[ResumeResponse.model_validate(r) for r in items],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve a specific resume and its LaTeX source."""
    resume = await get_resume_by_id(db, resume_id=resume_id, user_id=current_user.id)
    if not resume:
        raise NotFoundError(message=f"Resume with ID {resume_id} not found")
    return ResumeResponse.model_validate(resume)


@router.delete("/{resume_id}")
async def delete_resume_endpoint(
    resume_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Permanently delete a resume record."""
    deleted = await delete_resume(db, resume_id=resume_id, user_id=current_user.id)
    if not deleted:
        raise NotFoundError(message=f"Resume with ID {resume_id} not found")

    # If linked to R2 storage object, attempt cleanup
    if deleted.pdf_url:
        try:
            from storage.r2_client import delete_pdf
            # Key can be extracted from URL if standard format
            key = deleted.pdf_url.split("/")[-1]
            delete_pdf(key)
        except Exception as e:
            logger.warning(f"Could not delete R2 object for resume {resume_id}: {e}")

    logger.info(f"Deleted resume id={resume_id} for user {current_user.email}")
    return {"message": f"Resume {resume_id} successfully deleted", "id": resume_id}
