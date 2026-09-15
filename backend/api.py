"""Main FastAPI application entry point with centralized error handling, structured logging, and OpenAPI docs"""
import time
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from backend.config import CORS_ORIGINS, utc_now
from backend.database import init_db
from backend.exceptions import AppBaseException
from backend.schemas import ErrorResponse
from backend.telemetry import init_sentry
from backend.routers import (
    auth_router, companies_router, filters_router,
    jobs_router, runs_router, exports_router
)

# Configure structured logging
logger = logging.getLogger("jobscraper.api")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle events."""
    logger.info("Starting up Job Scraper Enterprise API service...")
    init_sentry()
    await init_db()
    yield
    logger.info("Shutting down Job Scraper Enterprise API service...")


app = FastAPI(
    title="Job Scraper Enterprise API",
    description="Production REST API service for ATS-native job scraping, candidate resume scoring, company management, and automated leads export.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Structured Request/Response Logging Middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)

    log_payload = {
        "timestamp": utc_now().isoformat(),
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "duration_ms": duration_ms,
        "client_ip": request.client.host if request.client else None
    }
    logger.info(json.dumps(log_payload))
    return response


# --- Centralized Exception Handlers ---

@app.exception_handler(AppBaseException)
async def app_exception_handler(request: Request, exc: AppBaseException):
    """Handle all typed application domain exceptions."""
    logger.warning(f"Domain exception on {request.method} {request.url.path}: {exc.error_code} - {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code.replace("_", " ").title(),
            "error_code": exc.error_code,
            "detail": exc.message,
            "timestamp": utc_now().isoformat(),
            "details": exc.details
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic request schema validation errors."""
    errors = exc.errors()
    logger.warning(f"Validation error on {request.method} {request.url.path}: {errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "error_code": "VALIDATION_ERROR",
            "detail": "Invalid request payload or query parameters",
            "timestamp": utc_now().isoformat(),
            "details": {"validation_errors": errors}
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all unhandled exception handler to prevent leaking stack traces."""
    logger.error(f"Unhandled server error on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "error_code": "INTERNAL_SERVER_ERROR",
            "detail": "An unexpected error occurred while processing the request",
            "timestamp": utc_now().isoformat(),
            "details": {}
        }
    )


# --- Health & Root Endpoints ---

@app.get("/", tags=["General"])
async def root():
    return {
        "service": "Job Scraper Enterprise API",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs",
        "timestamp": utc_now().isoformat()
    }


@app.get("/health", tags=["General"])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": utc_now().isoformat()
    }


# --- Mount Sub-Routers ---
app.include_router(auth_router)
app.include_router(companies_router)
app.include_router(filters_router)
app.include_router(jobs_router)
app.include_router(runs_router)
app.include_router(exports_router)
