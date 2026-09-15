"""Company management API endpoints: List, Create, Edit, Deactivate, and Dedup alerts"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import User
from backend.schemas import (
    CompanyResponse, CompanyCreate, CompanyUpdate, CompanyListResponse
)
from backend.auth import get_current_user, require_admin
from backend.crud import (
    get_companies, get_company_by_id, create_company, update_company, delete_company
)
from backend.exceptions import NotFoundError

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get("", response_model=CompanyListResponse)
async def list_companies(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Items per page"),
    search: Optional[str] = Query(None, description="Search company name, ATS, or career URL"),
    ats: Optional[str] = Query(None, description="Filter by ATS platform (greenhouse, lever, ashby, etc.)"),
    active_only: bool = Query(True, description="Filter only active companies"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """List companies with pagination, ATS filtering, search, and near-duplicate name alerts."""
    items, total, warnings = await get_companies(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        ats=ats,
        active_only=active_only
    )
    return CompanyListResponse(
        items=[CompanyResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        dedup_warnings=warnings
    )


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """Retrieve details of a specific company by ID."""
    comp = await get_company_by_id(db, company_id)
    if not comp:
        raise NotFoundError(message=f"Company with ID {company_id} not found")
    return CompanyResponse.model_validate(comp)


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def add_company(
    comp_in: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
):
    """Register a new company and ATS target configuration (Admin only)."""
    comp = await create_company(db, comp_in)
    return CompanyResponse.model_validate(comp)


@router.put("/{company_id}", response_model=CompanyResponse)
async def edit_company(
    company_id: int,
    comp_in: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
):
    """Update ATS metadata, location filters, or active status for a company (Admin only)."""
    comp = await update_company(db, company_id, comp_in)
    return CompanyResponse.model_validate(comp)


@router.delete("/{company_id}")
async def remove_company(
    company_id: int,
    hard: bool = Query(False, description="Set true to permanently delete instead of deactivating"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
):
    """Deactivate or permanently remove a company from the scraping catalog (Admin only)."""
    await delete_company(db, company_id, hard=hard)
    return {"message": f"Company {company_id} successfully {'deleted' if hard else 'deactivated'}"}
