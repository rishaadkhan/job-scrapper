# Production Job Scraper - Backend Roles (0-3 Years, India)

## Overview
Automated job scraping system that extracts backend engineering roles from official company career portals in India.

## Features
- Scrapes 1000+ companies (Tier-1 GCCs, Unicorns, Series B-D startups)
- Multi-portal support (Greenhouse, Lever, Workday, custom portals)
- Smart rotation (scrapes ~120 companies per run, 8-day rotation cycle)
- Filters for backend roles, 0-3 years experience, India locations
- Tech stack validation (Java, Spring Boot, Microservices, Cloud, etc.)
- Deduplication and state management
- Daily Excel output

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup
```bash
# Clone or download the project
cd jobscrap

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Run Locally
```bash
python main.py
```

Output will be generated in `output/High_Conversion_Job_Leads_YYYY-MM-DD.xlsx`

### Run Daily with Cron (macOS/Linux)
```bash
# Edit crontab
crontab -e

# Add this line to run daily at 9 AM
0 9 * * * cd /Users/rishaadkhan/Documents/jobscrap && /Users/rishaadkhan/Documents/jobscrap/venv/bin/python main.py >> logs/scraper.log 2>&1
```

### Run with GitHub Actions

Create `.github/workflows/scraper.yml`:

```yaml
name: Daily Job Scraper

on:
  schedule:
    - cron: '0 3 * * *'  # Runs at 3 AM UTC daily
  workflow_dispatch:  # Manual trigger

jobs:
  scrape:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run scraper
      run: python main.py
    
    - name: Upload Excel
      uses: actions/upload-artifact@v3
      with:
        name: job-leads
        path: output/*.xlsx
```

## Configuration

Edit `config.py` to customize:
- `COMPANIES_PER_RUN`: Number of companies per execution (default: 120)
- `ROTATION_DAYS`: Days before re-scraping a company (default: 8)
- `TARGET_LOCATIONS`: India cities to target
- `TECH_STACK_KEYWORDS`: Required tech keywords

## File Structure
```
jobscrap/
├── main.py              # Orchestrator
├── scraper.py           # Core scraping engine
├── filters.py           # Job filtering logic
├── state_manager.py     # Rotation and deduplication
├── exporter.py          # Excel generation
├── config.py            # Configuration
├── companies.json       # Company database (1000+)
├── requirements.txt     # Dependencies
├── scraper_state.json   # Auto-generated state file
└── output/              # Excel files
```

## State Management
- `scraper_state.json` tracks:
  - Last scraped date per company
  - Seen job IDs (prevents duplicates)
  - Auto-cleans jobs older than 30 days

## Adding More Companies

Edit `companies.json`:
```json
{
  "name": "Company Name",
  "type": "Tier-1 GCC|Unicorn|Series B-D",
  "career_url": "https://company.com/careers"
}
```

## Troubleshooting

### No jobs found
- Check if company career pages are accessible
- Some portals use JavaScript rendering (consider adding Playwright/Selenium)

### Rate limiting
- Increase `RATE_LIMIT_DELAY` in `config.py`
- Reduce `COMPANIES_PER_RUN`

### Missing dependencies
```bash
pip install --upgrade -r requirements.txt
```

## Output Format
Excel columns:
1. Company Name
2. Company Type
3. Job Title
4. Experience Range
5. Location
6. Job ID
7. Posted Date
8. Official Apply Link
9. Career Portal URL
10. Full Job Description
11. Scraped Timestamp

## Notes
- Respects robots.txt and rate limits
- No job boards (LinkedIn, Indeed, Naukri)
- Only official company portals
- Backend-focused roles only
- 0-3 years experience filter
- India locations only
