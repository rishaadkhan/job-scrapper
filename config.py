"""Configuration constants for job scraper"""
from datetime import datetime

# Scraping Configuration
COMPANIES_PER_RUN = 120
ROTATION_DAYS = 8
REQUEST_TIMEOUT = 15
RATE_LIMIT_DELAY = 2

# Target Criteria
TARGET_LOCATIONS = [
    "bangalore", "bengaluru", "hyderabad", "pune", "chennai", 
    "delhi", "ncr", "gurgaon", "noida", "mumbai", "navi mumbai",
    "remote", "india"
]

BACKEND_KEYWORDS = [
    "software engineer", "backend engineer", "sde", "platform engineer",
    "full stack", "fullstack", "software developer", "backend developer"
]

EXCLUDE_KEYWORDS = [
    "senior", "staff", "principal", "lead", "manager", "architect",
    "intern", "qa", "test", "support engineer"
]

TECH_STACK_KEYWORDS = [
    "java", "spring", "spring boot", "microservices", "rest api",
    "sql", "mysql", "postgresql", "redis", "docker", "kubernetes",
    "aws", "azure", "gcp", "cloud", "backend", "api"
]

# Output Configuration
OUTPUT_DIR = "output"
STATE_FILE = "scraper_state.json"
EXCEL_FILENAME_TEMPLATE = "High_Conversion_Job_Leads_{date}.xlsx"

# Excel Columns
EXCEL_COLUMNS = [
    "Company Name", "Company Type", "Job Title", "Experience Range",
    "Location", "Job ID", "Posted Date", "Official Apply Link",
    "Career Portal URL", "Full Job Description", "Scraped Timestamp"
]

# User Agent
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
