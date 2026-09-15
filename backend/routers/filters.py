"""Filtering configuration API endpoints: Dynamic keyword and location rule management"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import User
from backend.schemas import FilterConfigResponse, FilterConfigUpdate
from backend.auth import get_current_user, require_admin
from backend.crud import get_active_filters, update_active_filters

router = APIRouter(prefix="/filters", tags=["Filters"])


@router.get("", response_model=FilterConfigResponse)
async def get_filter_rules(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """Retrieve the currently active filtering rules, backend keywords, and experience constraints."""
    filters = await get_active_filters(db)
    return FilterConfigResponse.model_validate(filters)


@router.put("", response_model=FilterConfigResponse)
async def update_filter_rules(
    filter_in: FilterConfigUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
):
    """Dynamically update target keywords, locations, or experience bounds without redeploying code (Admin only)."""
    updated = await update_active_filters(db, filter_in)
    return FilterConfigResponse.model_validate(updated)
