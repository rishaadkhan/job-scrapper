"""
Backend environment and application configuration.
Unified with central Pydantic Settings system in config.settings.
"""
import os
from datetime import datetime, timezone
from typing import List
from config.settings import settings as _app_settings, get_settings


def utc_now() -> datetime:
    """Return timezone-naive UTC datetime compatible across SQLAlchemy and Pydantic."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# Resolve settings from central config
_cfg = _app_settings or (get_settings() if os.getenv("DATABASE_URL") else None)

# Database
DATABASE_URL: str = _cfg.DATABASE_URL if _cfg else os.getenv("DATABASE_URL", "sqlite+aiosqlite:///jobscraper.db")
if DATABASE_URL.startswith("sqlite:///") and not DATABASE_URL.startswith("sqlite+aiosqlite:///"):
    DATABASE_URL = DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
elif DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://"):
    if not DATABASE_URL.startswith("postgresql+asyncpg://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://").replace("postgresql://", "postgresql+asyncpg://")

# JWT & Authentication
JWT_SECRET: str = _cfg.JWT_SECRET if _cfg else os.getenv("JWT_SECRET", "super-secret-jobscraper-key-change-in-production")
JWT_ALGORITHM: str = _cfg.JWT_ALGORITHM if _cfg else os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = _cfg.ACCESS_TOKEN_EXPIRE_MINUTES if _cfg else int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# Default Admin Credentials
ADMIN_EMAIL: str = _cfg.ADMIN_EMAIL if _cfg else os.getenv("ADMIN_EMAIL", "admin@jobscraper.io")
ADMIN_PASSWORD: str = _cfg.ADMIN_PASSWORD if _cfg else os.getenv("ADMIN_PASSWORD", "admin123")

# LLM & Resume
OPENROUTER_API_KEY: str = _cfg.OPENROUTER_API_KEY if _cfg else os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL_PRIORITY: List[str] = _cfg.OPENROUTER_MODEL_PRIORITY if _cfg else [
    m.strip() for m in os.getenv("OPENROUTER_MODEL_PRIORITY", "anthropic/claude-3.5-sonnet,openai/gpt-4o-mini").split(",") if m.strip()
]
ANTHROPIC_API_KEY: str = _cfg.ANTHROPIC_API_KEY if _cfg else os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL: str = _cfg.ANTHROPIC_MODEL if _cfg else os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
LLM_SUGGESTION_THRESHOLD: int = _cfg.LLM_SUGGESTION_THRESHOLD if _cfg else int(os.getenv("LLM_SUGGESTION_THRESHOLD", "60"))
RESUME_FILE: str = _cfg.RESUME_FILE if _cfg else os.getenv("RESUME_FILE", "resume.md")

# LaTeX Compiler Microservice
LATEX_COMPILER_URL: str = _cfg.LATEX_COMPILER_URL if _cfg else os.getenv("LATEX_COMPILER_URL", "http://localhost:8001")

# Cloudflare R2 Storage
R2_ACCESS_KEY: str = _cfg.R2_ACCESS_KEY if _cfg else os.getenv("R2_ACCESS_KEY", "")
R2_SECRET_KEY: str = _cfg.R2_SECRET_KEY if _cfg else os.getenv("R2_SECRET_KEY", "")
R2_BUCKET: str = _cfg.R2_BUCKET if _cfg else os.getenv("R2_BUCKET", "")
R2_ENDPOINT: str = _cfg.R2_ENDPOINT if _cfg else os.getenv("R2_ENDPOINT", "")
R2_PUBLIC_URL: str = _cfg.R2_PUBLIC_URL if _cfg else os.getenv("R2_PUBLIC_URL", "")

# Storage & Retention
OUTPUT_DIR: str = _cfg.OUTPUT_DIR if _cfg else os.getenv("OUTPUT_DIR", "output")
RETENTION_DAYS: int = _cfg.RETENTION_DAYS if _cfg else int(os.getenv("RETENTION_DAYS", "14"))


# Observability
SENTRY_DSN: str = _cfg.SENTRY_DSN if _cfg else os.getenv("SENTRY_DSN", "")
ENVIRONMENT: str = _cfg.ENVIRONMENT if _cfg else os.getenv("ENVIRONMENT", "production")
HEARTBEAT_URL: str = _cfg.HEARTBEAT_URL if _cfg else os.getenv("HEARTBEAT_URL", "")

# Digest Notifications
TELEGRAM_BOT_TOKEN: str = _cfg.TELEGRAM_BOT_TOKEN if _cfg else os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = _cfg.TELEGRAM_CHAT_ID if _cfg else os.getenv("TELEGRAM_CHAT_ID", "")
DIGEST_SCORE_THRESHOLD: int = _cfg.DIGEST_SCORE_THRESHOLD if _cfg else int(os.getenv("DIGEST_SCORE_THRESHOLD", "60"))
DIGEST_TOP_N: int = _cfg.DIGEST_TOP_N if _cfg else int(os.getenv("DIGEST_TOP_N", "10"))
SMTP_HOST: str = _cfg.SMTP_HOST if _cfg else os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT: int = _cfg.SMTP_PORT if _cfg else int(os.getenv("SMTP_PORT", "587"))
SMTP_USER: str = _cfg.SMTP_USER if _cfg else os.getenv("SMTP_USER", "")
SMTP_PASSWORD: str = _cfg.SMTP_PASSWORD if _cfg else os.getenv("SMTP_PASSWORD", "")
SMTP_TO: str = _cfg.SMTP_TO if _cfg else os.getenv("SMTP_TO", "")

# CORS
CORS_ORIGINS: List[str] = _cfg.CORS_ORIGINS if _cfg else [
    "http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"
]
