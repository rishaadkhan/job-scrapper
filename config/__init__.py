"""
Configuration constants and settings for the Enterprise Job Scraper.
Provides backward-compatible constants alongside the new Pydantic Settings system.
"""
import os
from .settings import Settings, get_settings, settings, log_startup_capabilities

# Scraping Configuration
COMPANIES_PER_RUN = 999999
ROTATION_DAYS = 1
REQUEST_TIMEOUT = 15
RATE_LIMIT_DELAY = 1

# Target Criteria
TARGET_LOCATIONS = [
    "bangalore", "bengaluru", "hyderabad", "pune", "chennai",
    "delhi", "ncr", "gurgaon", "gurugram", "noida", "mumbai", "navi mumbai",
    "kolkata", "ahmedabad", "remote", "india"
]

BACKEND_KEYWORDS = [
    "software engineer", "backend engineer", "sde", "platform engineer",
    "full stack", "fullstack", "software developer", "backend developer"
]

EXCLUDE_KEYWORDS = [
    "senior",
    "staff",
    "principal",
    "lead",
    "manager",
    "architect",
    "intern",
    "qa engineer",
    "quality assurance",
    "support engineer",
    "test engineer",
    "sdet",
]

TECH_STACK_KEYWORDS = [
    "java", "spring", "spring boot", "microservices", "rest api",
    "sql", "mysql", "postgresql", "redis", "docker", "kubernetes",
    "aws", "azure", "gcp", "cloud", "backend", "api", "python", "golang"
]

# Dynamic settings resolved from environment / .env via Settings
_active_settings = settings or (get_settings() if os.getenv("DATABASE_URL") else None)

RESUME_FILE = _active_settings.RESUME_FILE if _active_settings else os.getenv("RESUME_FILE", "resume.md")
OPENROUTER_API_KEY = _active_settings.OPENROUTER_API_KEY if _active_settings else os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL_PRIORITY = _active_settings.OPENROUTER_MODEL_PRIORITY if _active_settings else [
    m.strip() for m in os.getenv("OPENROUTER_MODEL_PRIORITY", "anthropic/claude-3.5-sonnet,openai/gpt-4o-mini").split(",") if m.strip()
]
ANTHROPIC_API_KEY = _active_settings.ANTHROPIC_API_KEY if _active_settings else os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = _active_settings.ANTHROPIC_MODEL if _active_settings else os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
LLM_SUGGESTION_THRESHOLD = _active_settings.LLM_SUGGESTION_THRESHOLD if _active_settings else int(os.getenv("LLM_SUGGESTION_THRESHOLD", "60"))
OUTPUT_DIR = _active_settings.OUTPUT_DIR if _active_settings else os.getenv("OUTPUT_DIR", "output")


STATE_FILE = "scraper_state.json"
EXCEL_FILENAME_TEMPLATE = "High_Conversion_Job_Leads_{date}.xlsx"

# Target Excel Columns (Blueprint §4)
EXCEL_COLUMNS = [
    "Company Name",
    "Company Type",
    "Job Title",
    "Match Score",
    "Experience Range",
    "Location",
    "Top JD Keywords",
    "Missing From Resume",
    "Suggested Bullet Edits",
    "Job ID",
    "Posted Date",
    "Official Apply Link",
    "Career Portal URL",
    "Full Job Description",
    "Scraped Timestamp"
]

# User Agent
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

__all__ = [
    "Settings",
    "get_settings",
    "settings",
    "log_startup_capabilities",
    "COMPANIES_PER_RUN",
    "ROTATION_DAYS",
    "REQUEST_TIMEOUT",
    "RATE_LIMIT_DELAY",
    "TARGET_LOCATIONS",
    "BACKEND_KEYWORDS",
    "EXCLUDE_KEYWORDS",
    "TECH_STACK_KEYWORDS",
    "RESUME_FILE",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_MODEL",
    "LLM_SUGGESTION_THRESHOLD",
    "OUTPUT_DIR",
    "STATE_FILE",
    "EXCEL_FILENAME_TEMPLATE",
    "EXCEL_COLUMNS",
    "USER_AGENT"
]
