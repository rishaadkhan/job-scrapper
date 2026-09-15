"""Backend environment and application configuration"""
import os
from datetime import datetime, timezone, timedelta
from typing import List


def utc_now() -> datetime:
    """Return timezone-naive UTC datetime compatible across SQLAlchemy and Pydantic."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///jobscraper.db")
# If DATABASE_URL starts with sqlite:///, normalize to sqlite+aiosqlite:/// for async engine
if DATABASE_URL.startswith("sqlite:///") and not DATABASE_URL.startswith("sqlite+aiosqlite:///"):
    DATABASE_URL = DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
elif DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://"):
    if not DATABASE_URL.startswith("postgresql+asyncpg://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://").replace("postgresql://", "postgresql+asyncpg://")

# JWT & Authentication
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-jobscraper-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours

# Default Admin Credentials
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@jobscraper.io")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# LLM & Resume
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
LLM_SUGGESTION_THRESHOLD = int(os.getenv("LLM_SUGGESTION_THRESHOLD", "60"))
RESUME_FILE = os.getenv("RESUME_FILE", "resume.md")

# Storage & Retention
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "14"))

# ── Observability (Phase 5) ───────────────────────────────────────────────────
# Sentry DSN — obtain from sentry.io project settings; leave blank to disable
SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
# Deployment environment tag sent to Sentry ("production", "staging", "local")
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
# Heartbeat URL — healthchecks.io ping URL; leave blank to disable
HEARTBEAT_URL: str = os.getenv("HEARTBEAT_URL", "")

# ── Digest Notifications (Phase 5) ───────────────────────────────────────────
# Telegram
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
DIGEST_SCORE_THRESHOLD: int = int(os.getenv("DIGEST_SCORE_THRESHOLD", "60"))
DIGEST_TOP_N: int = int(os.getenv("DIGEST_TOP_N", "10"))
# SMTP email fallback
SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER: str = os.getenv("SMTP_USER", "")
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
SMTP_TO: str = os.getenv("SMTP_TO", "")

# CORS — restrict in production; keep wildcard off by default
_CORS_RAW: str = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
)
CORS_ORIGINS: List[str] = [o.strip() for o in _CORS_RAW.split(",") if o.strip()]

