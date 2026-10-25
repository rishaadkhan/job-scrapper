"""SQLAlchemy ORM models for companies, jobs, runs, filters, users, and exports"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime, JSON, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.config import utc_now


class Company(Base):
    """Company career portal tracking and ATS configuration"""
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    career_url = Column(Text, nullable=False)
    portal_type = Column(String(50), default="generic")
    ats = Column(String(50), default="html_fallback", index=True)
    ats_token = Column(String(255), nullable=True)
    ats_id = Column(String(255), nullable=True)
    location_filter = Column(JSON, default=list)
    company_type = Column(String(100), default="Tech")
    active = Column(Boolean, default=True, index=True)
    last_scraped_at = Column(DateTime, nullable=True)
    job_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class Job(Base):
    """Scraped and scored job postings with full metadata"""
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(255), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    company_type = Column(String(100), nullable=True)
    title = Column(String(255), nullable=False, index=True)
    match_score = Column(Integer, default=0, index=True)
    experience_range = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    top_jd_keywords = Column(JSON, default=list)
    missing_from_resume = Column(JSON, default=list)
    suggested_bullets = Column(Text, nullable=True)
    posted_date = Column(String(100), nullable=True)
    apply_link = Column(Text, nullable=True)
    portal_url = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    stack_match = Column(Boolean, default=False)
    scraped_at = Column(DateTime, default=utc_now, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)


    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")


class ScrapeRun(Base):
    """Telemetry and execution logs for automated scrape runs"""
    __tablename__ = "scrape_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    started_at = Column(DateTime, default=utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_sec = Column(Float, default=0.0)
    total_companies = Column(Integer, default=0)
    companies_with_jobs = Column(Integer, default=0)
    companies_zero_jobs = Column(Integer, default=0)
    total_raw_jobs = Column(Integer, default=0)
    total_valid_leads = Column(Integer, default=0)
    avg_match_score = Column(Float, default=0.0)
    status = Column(String(50), default="completed", index=True)  # 'running', 'completed', 'failed'
    error_log = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class FilterConfig(Base):
    """Dynamic filtering and keyword rules stored in database"""
    __tablename__ = "filters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, default="default")
    is_active = Column(Boolean, default=True)
    target_locations = Column(JSON, default=list)
    backend_keywords = Column(JSON, default=list)
    exclude_keywords = Column(JSON, default=list)
    tech_stack_keywords = Column(JSON, default=list)
    min_experience = Column(Integer, default=0)
    max_experience = Column(Integer, default=3)
    llm_suggestion_threshold = Column(Integer, default=60)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class User(Base):
    """Authentication and RBAC user model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="admin", nullable=False)  # 'admin', 'viewer'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    last_login_at = Column(DateTime, nullable=True)

    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")


class ExportRecord(Base):
    """Generated Excel extract tracking and download management"""
    __tablename__ = "exports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(Text, nullable=False)
    row_count = Column(Integer, default=0)
    avg_match_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    deleted_at = Column(DateTime, nullable=True)


class Resume(Base):
    """Candidate LaTeX resume templates, versions, and compiled references"""
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    label = Column(String(255), nullable=False)
    latex_source = Column(Text, nullable=False)
    is_master = Column(Boolean, default=False, nullable=False, index=True)
    pdf_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="resumes")
    applications = relationship("Application", back_populates="resume")


class Application(Base):
    """Job application tracker linking candidate resumes to scraped job leads"""
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(50), default="not_applied", nullable=False, index=True)
    applied_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    resume = relationship("Resume", back_populates="applications")


class LLMCall(Base):
    """Observability log tracking LLM attempts, fallbacks, and latencies across models"""
    __tablename__ = "llm_calls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_used = Column(String(255), nullable=False, index=True)
    success = Column(Boolean, default=True, nullable=False, index=True)
    latency_ms = Column(Float, default=0.0, nullable=False)
    purpose = Column(String(255), default="bullet_generation", nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

