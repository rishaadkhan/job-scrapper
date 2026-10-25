"""
Centralized Application Settings & Environment Configuration.
Separates REQUIRED variables (fail-fast at startup) from OPTIONAL variables (graceful degradation).
"""
import os
import logging
from typing import Optional, List, Dict, Any, Union
from pydantic import Field, field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("jobscraper.config")


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and optional .env file.
    
    Required variables:
        - DATABASE_URL: Database connection string (SQLite or PostgreSQL)
        - JWT_SECRET: Secret key for signing authentication tokens
        
    Optional variables (gracefully degrade when absent):
        - ANTHROPIC_API_KEY: LLM resume bullet suggestions
        - TELEGRAM_BOT_TOKEN & TELEGRAM_CHAT_ID: Telegram daily digest
        - SMTP_USER & SMTP_PASSWORD: Email daily digest fallback
        - SENTRY_DSN: Sentry error monitoring
        - HEARTBEAT_URL: healthchecks.io uptime monitoring ping
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # =========================================================================
    # 1. REQUIRED CONFIGURATION (App fails fast at startup if missing/empty)
    # =========================================================================
    DATABASE_URL: str = Field(
        ...,
        description="Database connection URL. Required for data persistence and state tracking."
    )
    JWT_SECRET: str = Field(
        ...,
        description="Secret key for JWT token signing. Required for secure API authentication."
    )

    # =========================================================================
    # 2. OPTIONAL INTEGRATIONS (Graceful degradation — app runs without them)
    # =========================================================================
    
    # ── OpenRouter LLM (Multi-Model Resume Tailoring) ─────────────────────
    OPENROUTER_API_KEY: Optional[str] = Field(
        default="",
        description="OpenRouter API key for LLM resume tailoring with model fallback. If omitted, bullet tailoring is disabled."
    )
    openrouter_model_priority_raw: Union[str, List[str]] = Field(
        default="anthropic/claude-3.5-sonnet,openai/gpt-4o-mini",
        alias="OPENROUTER_MODEL_PRIORITY",
        description="Comma-separated ordered list of OpenRouter model slugs to try in priority order"
    )

    @property
    def OPENROUTER_MODEL_PRIORITY(self) -> List[str]:
        val = self.openrouter_model_priority_raw
        if isinstance(val, str):
            return [m.strip() for m in val.split(",") if m.strip()]
        return list(val)

    # ── Legacy Anthropic Claude LLM (Fallback / Backward Compatibility) ──
    ANTHROPIC_API_KEY: Optional[str] = Field(
        default="",
        description="Anthropic API key for Claude resume bullet suggestions. If omitted, bullet generation is disabled."
    )
    ANTHROPIC_MODEL: str = Field(
        default="claude-3-5-sonnet-latest",
        description="Anthropic Claude model identifier"
    )
    LLM_SUGGESTION_THRESHOLD: int = Field(
        default=60,
        description="Minimum candidate match score (0-100) to trigger AI resume bullet generation"
    )
    RESUME_FILE: str = Field(
        default="resume.md",
        description="Path to candidate resume markdown file"
    )

    # ── Sandboxed LaTeX Compiler Service ─────────────────────────────────
    LATEX_COMPILER_URL: str = Field(
        default="http://localhost:8001",
        description="Internal HTTP URL for sandboxed Tectonic LaTeX compiler microservice"
    )

    # ── Cloudflare R2 (S3-Compatible) Object Storage ──────────────────────
    R2_ACCESS_KEY: Optional[str] = Field(
        default="",
        description="Cloudflare R2 access key ID"
    )
    R2_SECRET_KEY: Optional[str] = Field(
        default="",
        description="Cloudflare R2 secret access key"
    )
    R2_BUCKET: Optional[str] = Field(
        default="",
        description="Cloudflare R2 storage bucket name"
    )
    R2_ENDPOINT: Optional[str] = Field(
        default="",
        description="Cloudflare R2 endpoint URL (https://<account_id>.r2.cloudflarestorage.com)"
    )
    R2_PUBLIC_URL: Optional[str] = Field(
        default="",
        description="Optional public domain or CDN URL prefix for direct PDF downloads"
    )


    # ── Observability (Sentry & Heartbeat) ────────────────────────────────
    SENTRY_DSN: Optional[str] = Field(
        default="",
        description="Sentry project DSN for exception tracking. If omitted, Sentry is a no-op."
    )
    ENVIRONMENT: str = Field(
        default="production",
        description="Deployment environment tag ('production', 'staging', 'local')"
    )
    HEARTBEAT_URL: Optional[str] = Field(
        default="",
        description="Healthchecks.io heartbeat ping URL. If omitted, heartbeat pings are skipped."
    )

    # ── Daily Digest — Telegram ──────────────────────────────────────────
    TELEGRAM_BOT_TOKEN: Optional[str] = Field(
        default="",
        description="Telegram bot token from @BotFather. If omitted, Telegram digest is disabled."
    )
    TELEGRAM_CHAT_ID: Optional[str] = Field(
        default="",
        description="Telegram chat ID for daily digest delivery."
    )
    DIGEST_SCORE_THRESHOLD: int = Field(
        default=60,
        description="Minimum match score (0-100) to include in daily digest notification"
    )
    DIGEST_TOP_N: int = Field(
        default=10,
        description="Maximum number of top leads to include in daily digest"
    )

    # ── Daily Digest — SMTP Email Fallback ────────────────────────────────
    SMTP_HOST: str = Field(
        default="smtp.gmail.com",
        description="SMTP server host"
    )
    SMTP_PORT: int = Field(
        default=587,
        description="SMTP server port"
    )
    SMTP_USER: Optional[str] = Field(
        default="",
        description="SMTP username for email digest"
    )
    SMTP_PASSWORD: Optional[str] = Field(
        default="",
        description="SMTP password for email digest"
    )
    SMTP_TO: Optional[str] = Field(
        default="",
        description="Recipient email address for digest"
    )

    # ── Auth & Admin Defaults ─────────────────────────────────────────────
    ADMIN_EMAIL: str = Field(
        default="admin@jobscraper.io",
        description="Default administrator email for initial bootstrap"
    )
    ADMIN_PASSWORD: str = Field(
        default="admin123",
        description="Default administrator password for initial bootstrap"
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=1440,
        description="JWT access token lifetime in minutes (default: 24h)"
    )
    cors_origins_raw: Union[str, List[str]] = Field(
        default="http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173",
        alias="CORS_ORIGINS",
        description="Allowed CORS origins"
    )

    @property
    def CORS_ORIGINS(self) -> List[str]:
        val = self.cors_origins_raw
        if isinstance(val, str):
            return [o.strip() for o in val.split(",") if o.strip()]
        return list(val)

    # ── Storage & Retention ───────────────────────────────────────────────
    OUTPUT_DIR: str = Field(
        default="output",
        description="Directory for generated Excel spreadsheet reports"
    )
    RETENTION_DAYS: int = Field(
        default=14,
        description="Historical run retention window in days"
    )

    # =========================================================================
    # VALIDATORS
    # =========================================================================
    @field_validator("DATABASE_URL", "JWT_SECRET")
    @classmethod
    def validate_required_non_empty(cls, v: str, info: ValidationInfo) -> str:
        """Enforces that required variables are neither missing nor empty strings."""
        if not v or not v.strip():
            raise ValueError(
                f"REQUIRED environment variable '{info.field_name}' cannot be empty. "
                f"The application cannot start without a valid {info.field_name}."
            )
        return v.strip()

    @field_validator("DATABASE_URL")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        """Normalizes SQLite and PostgreSQL connection strings for async SQLAlchemy engines."""
        url = v.strip()
        if url.startswith("sqlite:///") and not url.startswith("sqlite+aiosqlite:///"):
            return url.replace("sqlite:///", "sqlite+aiosqlite:///")
        if url.startswith("postgres://") or url.startswith("postgresql://"):
            if not url.startswith("postgresql+asyncpg://"):
                return url.replace("postgres://", "postgresql+asyncpg://").replace("postgresql://", "postgresql+asyncpg://")
        return url

    # =========================================================================
    # CAPABILITY PROPERTIES
    # =========================================================================
    @property
    def is_openrouter_enabled(self) -> bool:
        """True if OpenRouter API key is configured."""
        return bool(self.OPENROUTER_API_KEY and self.OPENROUTER_API_KEY.strip())

    @property
    def is_bullet_generation_enabled(self) -> bool:
        """True if OpenRouter or Anthropic API key is configured."""
        return bool(
            (self.OPENROUTER_API_KEY and self.OPENROUTER_API_KEY.strip()) or
            (self.ANTHROPIC_API_KEY and self.ANTHROPIC_API_KEY.strip())
        )

    @property
    def is_r2_storage_enabled(self) -> bool:
        """True if Cloudflare R2 credentials, bucket, and endpoint are configured."""
        return bool(
            self.R2_ACCESS_KEY and self.R2_ACCESS_KEY.strip() and
            self.R2_SECRET_KEY and self.R2_SECRET_KEY.strip() and
            self.R2_BUCKET and self.R2_BUCKET.strip() and
            self.R2_ENDPOINT and self.R2_ENDPOINT.strip()
        )

    @property
    def is_telegram_digest_enabled(self) -> bool:
        """True if Telegram bot token and chat ID are configured."""
        return bool(
            self.TELEGRAM_BOT_TOKEN and self.TELEGRAM_BOT_TOKEN.strip() and
            self.TELEGRAM_CHAT_ID and self.TELEGRAM_CHAT_ID.strip()
        )

    @property
    def is_smtp_digest_enabled(self) -> bool:
        """True if SMTP credentials and recipient are configured."""
        return bool(
            self.SMTP_USER and self.SMTP_USER.strip() and
            self.SMTP_PASSWORD and self.SMTP_PASSWORD.strip() and
            (self.SMTP_TO and self.SMTP_TO.strip() or os.getenv("DIGEST_EMAIL_TO"))
        )

    @property
    def is_sentry_enabled(self) -> bool:
        """True if Sentry DSN is configured."""
        return bool(self.SENTRY_DSN and self.SENTRY_DSN.strip())

    @property
    def is_heartbeat_enabled(self) -> bool:
        """True if heartbeat ping URL is configured."""
        return bool(self.HEARTBEAT_URL and self.HEARTBEAT_URL.strip())


def get_settings() -> Settings:
    """
    Factory function returning the application Settings instance.
    Fails fast with a clear, readable diagnostic message if any REQUIRED variable is missing.
    """
    try:
        return Settings()
    except Exception as exc:
        msg = f"\n[CRITICAL CONFIGURATION ERROR] Failed to load required settings:\n{exc}\n"
        logger.critical(msg)
        raise SystemExit(msg) from exc


# Module-level singleton
try:
    settings = Settings()
except Exception:
    # If environment is not yet initialized during import (e.g. before test setup),
    # fallback to None; callers should use get_settings() or initialize env
    settings = None  # type: ignore


def log_startup_capabilities(custom_settings: Optional[Settings] = None, custom_logger: Optional[logging.Logger] = None) -> List[str]:
    """
    Logs a clear summary of which optional features are ACTIVE vs DISABLED at scraper startup.
    Returns the list of capability status lines.
    """
    cfg = custom_settings or settings
    if cfg is None:
        cfg = get_settings()

    lines = []

    # 1. Resume tailoring (OpenRouter / Anthropic)
    if cfg.is_openrouter_enabled:
        lines.append(f"Resume bullet suggestions: ENABLED (Resume tailoring: ENABLED - OpenRouter models: {', '.join(cfg.OPENROUTER_MODEL_PRIORITY)})")
    elif cfg.ANTHROPIC_API_KEY and cfg.ANTHROPIC_API_KEY.strip():
        lines.append(f"Resume bullet suggestions: ENABLED (Resume tailoring: ENABLED - Legacy Anthropic: {cfg.ANTHROPIC_MODEL})")
    else:
        lines.append("Resume bullet suggestions: DISABLED (Resume tailoring: DISABLED)")


    # 2. Cloudflare R2 object storage
    if cfg.is_r2_storage_enabled:
        lines.append(f"Cloudflare R2 PDF storage: ENABLED (Bucket: {cfg.R2_BUCKET})")
    else:
        lines.append("Cloudflare R2 PDF storage: DISABLED (R2 credentials/bucket not set)")

    # 3. Telegram digest
    if cfg.is_telegram_digest_enabled:
        lines.append("Telegram digest: ENABLED")
    else:
        reason = "TELEGRAM_BOT_TOKEN not set" if not cfg.TELEGRAM_BOT_TOKEN else "TELEGRAM_CHAT_ID not set"
        lines.append(f"Telegram digest: DISABLED ({reason})")

    # 4. SMTP email digest
    if cfg.is_smtp_digest_enabled:
        lines.append("SMTP email digest: ENABLED")
    else:
        lines.append("SMTP email digest: DISABLED (SMTP credentials/recipient not set)")

    # 5. Sentry error tracking
    if cfg.is_sentry_enabled:
        lines.append("Sentry error tracking: ENABLED")
    else:
        lines.append("Sentry error tracking: DISABLED (SENTRY_DSN not set)")

    # 6. Heartbeat monitoring
    if cfg.is_heartbeat_enabled:
        lines.append("Heartbeat monitoring: ENABLED")
    else:
        lines.append("Heartbeat monitoring: DISABLED (HEARTBEAT_URL not set)")


    log_fn = custom_logger.info if custom_logger else print
    for line in lines:
        log_fn(f"  • {line}")

    return lines
