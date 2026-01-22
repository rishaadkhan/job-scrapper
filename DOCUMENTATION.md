# Production Job Scraper - Complete Documentation

## System Architecture

### Core Components

1. **main.py** - Orchestrator
   - Coordinates all components
   - Manages scraping workflow
   - Handles error recovery

2. **scraper.py** - Multi-portal scraping engine
   - Greenhouse.io support
   - Lever.co support
   - Workday support
   - Generic HTML parsing fallback
   - Rate limiting & retry logic

3. **filters.py** - Intelligent job filtering
   - Location validation (India cities only)
   - Role type detection (backend-focused)
   - Experience extraction (0-3 years)
   - Tech stack validation (Java, Spring, Cloud, etc.)

4. **state_manager.py** - State persistence
   - Company rotation tracking
   - Job deduplication
   - Scraping history
   - Auto-cleanup of old records

5. **exporter.py** - Excel generation
   - Structured output format
   - Proper column ordering
   - Date-stamped filenames

6. **config.py** - Centralized configuration
   - All constants in one place
   - Easy customization

## Quick Start

### Option 1: Automated Setup
```bash
./setup.sh
source venv/bin/activate
python main.py
```

### Option 2: Manual Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Configuration Guide

### Adjusting Scraping Volume
Edit `config.py`:
```python
COMPANIES_PER_RUN = 120  # Companies per execution
ROTATION_DAYS = 8        # Days before re-scraping
```

### Customizing Filters

**Target Locations:**
```python
TARGET_LOCATIONS = [
    "bangalore", "hyderabad", "pune", "chennai",
    "delhi", "mumbai", "remote", "india"
]
```

**Backend Keywords:**
```python
BACKEND_KEYWORDS = [
    "software engineer", "backend engineer", "sde",
    "platform engineer", "full stack"
]
```

**Tech Stack:**
```python
TECH_STACK_KEYWORDS = [
    "java", "spring boot", "microservices",
    "rest api", "sql", "redis", "docker", "cloud"
]
```

## Expanding Company Database

### Method 1: Edit companies.json directly
```json
{
  "name": "Company Name",
  "type": "Tier-1 GCC|Unicorn|Series B-D",
  "career_url": "https://company.com/careers"
}
```

### Method 2: Use expansion script
1. Edit `expand_companies.py`
2. Add companies to `ADDITIONAL_COMPANIES` list
3. Run: `python expand_companies.py`

### Current Database Stats
- Total companies: 155+
- Tier-1 GCCs: 35+
- Unicorns: 60+
- Series B-D: 60+

**Target: 1000+ companies**
To reach this, continue adding:
- More product GCCs (Shopify, Slack, Zoom, etc.)
- Indian SaaS companies
- Series A-B startups
- Regional unicorns

## Deployment Options

### 1. Local Cron (macOS/Linux)
```bash
# Edit crontab
crontab -e

# Run daily at 9 AM
0 9 * * * cd /path/to/jobscrap && /path/to/venv/bin/python main.py >> logs/scraper.log 2>&1
```

### 2. GitHub Actions (Recommended)
- Already configured in `.github/workflows/scraper.yml`
- Runs daily at 3 AM UTC (8:30 AM IST)
- Automatically uploads Excel files as artifacts
- Commits state file back to repo

**Setup:**
1. Push code to GitHub
2. Enable Actions in repository settings
3. Workflow runs automatically

**Manual trigger:**
- Go to Actions tab
- Select "Daily Job Scraper"
- Click "Run workflow"

### 3. AWS Lambda (Advanced)
```python
# Create Lambda function with:
# - Runtime: Python 3.10
# - Timeout: 15 minutes
# - Memory: 512 MB
# - EventBridge trigger: cron(0 3 * * ? *)
# - S3 bucket for output storage
```

### 4. Docker Container
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## Output Format

### Excel File Structure
**Filename:** `High_Conversion_Job_Leads_YYYY-MM-DD.xlsx`

**Columns:**
1. Company Name - Official company name
2. Company Type - Tier-1 GCC / Unicorn / Series B-D
3. Job Title - Exact job title from portal
4. Experience Range - Extracted (e.g., "0-2 years")
5. Location - City/cities in India
6. Job ID - Unique identifier from portal
7. Posted Date - When job was posted (if available)
8. Official Apply Link - Direct application URL
9. Career Portal URL - Company career page
10. Full Job Description - Complete JD text
11. Scraped Timestamp - When data was collected

## State Management

### scraper_state.json Structure
```json
{
  "companies": {
    "Google India": {
      "last_scraped": "2024-01-15T09:30:00",
      "job_count": 12
    }
  },
  "seen_jobs": {
    "Google India_12345": {
      "company": "Google India",
      "first_seen": "2024-01-15T09:30:00"
    }
  }
}
```

### Rotation Logic
- Companies not scraped in last 8 days are prioritized
- ~120 companies scraped per run
- Full rotation cycle: ~10-12 days for 155 companies
- Scales automatically as database grows

### Deduplication
- Job IDs tracked in state file
- Prevents duplicate entries
- Auto-cleans jobs older than 30 days

## Filtering Logic Deep Dive

### 1. Location Filter
```python
# Matches any of these in location string
["bangalore", "bengaluru", "hyderabad", "pune", 
 "chennai", "delhi", "ncr", "mumbai", "remote", "india"]
```

### 2. Role Type Filter
**Included:**
- Software Engineer
- Backend Engineer
- SDE (I, II)
- Platform Engineer
- Full Stack (if backend-heavy)

**Excluded:**
- Senior/Staff/Principal roles
- Internships
- QA/Test Engineer
- Frontend-only roles
- DevOps-only roles
- Support Engineer

### 3. Experience Filter
**Accepts:**
- "0-2 years", "0-3 years", "1-3 years"
- "Freshers", "Fresh graduates"
- "Entry level"
- No experience mentioned

**Rejects:**
- "4+ years", "5+ years"
- "Minimum 4 years"
- "At least 5 years"

### 4. Tech Stack Filter
**Requires at least 2 matches from:**
- java, spring, spring boot
- microservices, rest api
- sql, mysql, postgresql
- redis, docker, kubernetes
- aws, azure, gcp, cloud
- backend, api

## Troubleshooting

### Issue: No jobs found
**Causes:**
- Career pages changed structure
- Rate limiting
- Network issues

**Solutions:**
1. Check if URLs are accessible
2. Increase `RATE_LIMIT_DELAY` in config.py
3. Add logging to see which companies fail
4. Consider adding Playwright for JS-heavy sites

### Issue: Too many/few results
**Adjust filters in config.py:**
- Relax tech stack requirement (change `>= 2` to `>= 1`)
- Add more backend keywords
- Expand location list

### Issue: Duplicates appearing
**Check:**
- State file is being saved properly
- Job ID extraction is working
- State file isn't being deleted between runs

### Issue: Script crashes
**Common causes:**
- Missing dependencies: `pip install -r requirements.txt`
- Network timeout: Increase `REQUEST_TIMEOUT`
- Memory issues: Reduce `COMPANIES_PER_RUN`

## Performance Optimization

### Current Performance
- ~120 companies per run
- ~2 seconds per company (rate limiting)
- Total runtime: ~4-5 minutes
- Expected output: 20-50 valid jobs per run

### Scaling Up
To scrape more companies faster:

1. **Parallel Processing:**
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    results = executor.map(scraper.scrape_company, companies)
```

2. **Reduce Rate Limiting:**
```python
RATE_LIMIT_DELAY = 1  # Faster but riskier
```

3. **Increase Companies Per Run:**
```python
COMPANIES_PER_RUN = 200
```

## Monitoring & Logging

### Add Logging
```python
import logging

logging.basicConfig(
    filename='scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

### Track Metrics
- Companies scraped
- Jobs found vs. filtered
- Success/failure rate
- Average jobs per company
- Runtime per company

## Legal & Ethical Considerations

### Compliance
✓ Respects robots.txt
✓ Rate limiting implemented
✓ Only public career pages
✓ No authentication bypass
✓ No personal data collection

### Best Practices
- Don't scrape too aggressively
- Honor rate limits
- Check terms of service
- Use data responsibly
- Don't resell scraped data

## Future Enhancements

### Phase 2 Features
1. **Email Notifications**
   - Daily digest of new jobs
   - Alert for specific companies

2. **Advanced Filtering**
   - Salary range extraction
   - Remote vs. office detection
   - Tech stack scoring

3. **Job Matching**
   - Resume parsing
   - Skill matching
   - Personalized recommendations

4. **Analytics Dashboard**
   - Hiring trends
   - Company activity
   - Location insights

5. **API Integration**
   - Greenhouse API
   - Lever API
   - Workday API

## Support & Contribution

### Adding New Portal Types
Extend `scraper.py`:
```python
def _scrape_custom_portal(self, response, company):
    # Add custom parsing logic
    pass
```

### Reporting Issues
Include:
- Error message
- Company name
- Career URL
- Python version
- OS version

## Maintenance Schedule

### Daily
- Check scraper runs successfully
- Verify Excel output quality
- Monitor state file size

### Weekly
- Review filtered jobs
- Update company list
- Check for broken URLs

### Monthly
- Expand company database
- Update dependencies
- Review and optimize filters
- Clean up old state data

## Success Metrics

### Quality Indicators
- 80%+ of scraped jobs are relevant
- <5% duplicate rate
- 90%+ of companies successfully scraped
- <10% false positives in filters

### Volume Targets
- 20-50 valid jobs per day (current database)
- 100-200 jobs per day (1000+ companies)
- 500+ jobs per week
- 2000+ jobs per month

---

**Version:** 1.0
**Last Updated:** 2024
**Maintainer:** Backend Engineering Team
