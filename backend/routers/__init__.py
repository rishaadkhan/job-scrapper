"""Expose all router instances from the routers package"""
from backend.routers.auth import router as auth_router
from backend.routers.companies import router as companies_router
from backend.routers.filters import router as filters_router
from backend.routers.jobs import router as jobs_router
from backend.routers.runs import router as runs_router
from backend.routers.exports import router as exports_router

__all__ = [
    "auth_router",
    "companies_router",
    "filters_router",
    "jobs_router",
    "runs_router",
    "exports_router"
]
