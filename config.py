"""Configuration constants for job scraper"""
import os
from datetime import datetime

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

# Resume & Scoring Configuration
RESUME_FILE = os.getenv("RESUME_FILE", "resume.md")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
LLM_SUGGESTION_THRESHOLD = int(os.getenv("LLM_SUGGESTION_THRESHOLD", "60"))

# Output Configuration
OUTPUT_DIR = "output"
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
