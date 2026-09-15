"""Pydantic schemas for request and response validation"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from backend.config import utc_now


# --- Auth & User Schemas ---
class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str


class UserBase(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    role: str = "admin"
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# --- Company Schemas ---
class CompanyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    career_url: str = Field(..., min_length=5)
    portal_type: str = "generic"
    ats: str = "html_fallback"
    ats_token: Optional[str] = None
    ats_id: Optional[str] = None
    location_filter: List[str] = Field(default_factory=list)
    company_type: str = "Tech"
    active: bool = True


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    career_url: Optional[str] = None
    portal_type: Optional[str] = None
    ats: Optional[str] = None
    ats_token: Optional[str] = None
    ats_id: Optional[str] = None
    location_filter: Optional[List[str]] = None
    company_type: Optional[str] = None
    active: Optional[bool] = None


class CompanyResponse(CompanyBase):
    id: int
    last_scraped_at: Optional[datetime] = None
    job_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyListResponse(BaseModel):
    items: List[CompanyResponse]
    total: int
    page: int
    page_size: int
    dedup_warnings: List[str] = Field(default_factory=list)


# --- Job Schemas ---
class JobBase(BaseModel):
    job_id: str
    company_name: str
    company_type: Optional[str] = None
    title: str
    match_score: int = 0
    experience_range: Optional[str] = None
    location: Optional[str] = None
    top_jd_keywords: List[str] = Field(default_factory=list)
    missing_from_resume: List[str] = Field(default_factory=list)
    suggested_bullets: Optional[str] = None
    posted_date: Optional[str] = None
    apply_link: Optional[str] = None
    portal_url: Optional[str] = None
    description: Optional[str] = None
    stack_match: bool = False
    scraped_at: datetime = Field(default_factory=utc_now)


class JobCreate(JobBase):
    pass


class JobResponse(JobBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobListResponse(BaseModel):
    items: List[JobResponse]
    total: int
    page: int
    page_size: int


class JobStatsResponse(BaseModel):
    total_leads: int
    high_match_count: int  # score >= 70
    mid_match_count: int   # score 40-69
    low_match_count: int   # score < 40
    companies_represented: int
    top_demanded_skills: Dict[str, int] = Field(default_factory=dict)


# --- Filter Schemas ---
class FilterConfigBase(BaseModel):
    name: str = "default"
    is_active: bool = True
    target_locations: List[str] = Field(default_factory=list)
    backend_keywords: List[str] = Field(default_factory=list)
    exclude_keywords: List[str] = Field(default_factory=list)
    tech_stack_keywords: List[str] = Field(default_factory=list)
    min_experience: int = 0
    max_experience: int = 3
    llm_suggestion_threshold: int = 60


class FilterConfigUpdate(BaseModel):
    target_locations: Optional[List[str]] = None
    backend_keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    tech_stack_keywords: Optional[List[str]] = None
    min_experience: Optional[int] = None
    max_experience: Optional[int] = None
    llm_suggestion_threshold: Optional[int] = None


class FilterConfigResponse(FilterConfigBase):
    id: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Scrape Run Schemas ---
class ScrapeRunResponse(BaseModel):
    id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_sec: float = 0.0
    total_companies: int = 0
    companies_with_jobs: int = 0
    companies_zero_jobs: int = 0
    total_raw_jobs: int = 0
    total_valid_leads: int = 0
    avg_match_score: float = 0.0
    status: str
    error_log: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScrapeRunListResponse(BaseModel):
    items: List[ScrapeRunResponse]
    total: int
    page: int
    page_size: int


class ScrapeTriggerResponse(BaseModel):
    message: str
    run_id: int
    status: str


# --- Export Schemas ---
class ExportRequest(BaseModel):
    min_score: Optional[int] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    company: Optional[str] = None
    limit: Optional[int] = 1000


class ExportResponse(BaseModel):
    id: int
    filename: str
    row_count: int
    avg_match_score: float
    download_url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExportListResponse(BaseModel):
    items: List[ExportResponse]
    total: int


# --- Standard Error Response ---
class ErrorResponse(BaseModel):
    error: str
    error_code: str
    detail: str
    timestamp: datetime = Field(default_factory=utc_now)
    details: Optional[Dict[str, Any]] = None
