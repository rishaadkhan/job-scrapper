# Enterprise Job Scraper & Resume Intelligence Engine

## Overview
High-throughput automated job extraction and resume intelligence pipeline targeting early-career backend engineering roles (0–3 years experience, India locations) across 390+ curated Tier-1 GCCs, Unicorns, and high-growth startups.

---

## Key Features

### 🚀 Direct ATS JSON APIs
- **Greenhouse (`boards-api.greenhouse.io`)**: Ingests 100% structured data and clean descriptions directly via public JSON endpoints.
- **Lever (`api.lever.co`)**: Extracts structured postings with full category and commitment metadata.
- **Ashby (`api.ashbyhq.com`)**: Ingests direct posting payloads eliminating SPA JavaScript rendering failures.
- **SmartRecruiters (`api.smartrecruiters.com`)**: Ingests structured postings and section-by-section requirements.
- **Workday CXS (`/wday/cxs/{tenant}/{site}/jobs`)**: Queries Workday candidate services directly.
- **HTML Fallback**: Asynchronous, polite fallback for custom career portals.
- **Zero Third-Party Scraping**: Full compliance with ToS guidelines (no scraping of LinkedIn, Indeed, or Naukri).

### ⚡ Asynchronous Engine & Concurrency Control
- Refactored with `asyncio` and `httpx.AsyncClient` connection pooling.
- Bounded concurrency with `asyncio.Semaphore(10)`.
- Per-domain rate limiting (`DomainRateLimiter`) with exponential backoff and jitter on HTTP 429/5xx errors.

### 🎯 Resume Intelligence & Match Scoring (`scoring/`)
- **Curated Backend Taxonomy**: 150+ indexed backend engineering skills (Languages, Frameworks, Databases & Caching, Cloud & DevOps, Distributed Systems, Architecture).
- **Keyword Extraction & Prominence**: TF-IDF weighting with title and requirements section boosting.
- **0–100 Match Score**: Quantifies candidate-to-role alignment based on resume keyword intersection.
- **Missing Skills Identification**: Explicitly flags target technologies in the JD that are absent from your resume.
- **Anthropic Claude Bullet Generator**: Generates 2–3 high-impact, tailored resume bullet points for top-scoring leads using Claude (`claude-3-5-sonnet-latest`).

### 📊 Redesigned Excel Output (15-Column Schema)
- **Frozen Header Row**: Always visible column headers while scrolling.
- **Auto-Filter**: Instant filtering and sorting by Match Score, Company, Location, or Keywords.
- **Hyperlinked URLs**: Clickable apply links and career portal paths.
- **Conditional Color Formatting**:
  - 🟢 **Green (≥ 70)**: High alignment match
  - 🟡 **Yellow (40–69)**: Moderate alignment match
  - 🔴 **Red (< 40)**: Low alignment match

---

## Installation & Setup

### Prerequisites
- Python 3.10+
- virtualenv

### Setup
```bash
# Clone the repository
cd jobscrap

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Resume Configuration (`resume.md`)

Create or update your `resume.md` in the project root (or set `RESUME_FILE` in your environment):

```markdown
# John Doe — Backend Software Engineer
Email: john@example.com | Location: Bengaluru, India | GitHub: github.com/johndoe

## Technical Skills
- Languages: Java, Python, Go, SQL
- Frameworks: Spring Boot, FastAPI, Django, Express
- Databases & Caching: PostgreSQL, MySQL, Redis, Apache Kafka
- Cloud & Tools: AWS, Docker, Kubernetes, GitHub Actions, Linux
- Architecture: Microservices, REST APIs, Distributed Systems, Unit Testing
```

---

## Environment Variables (Optional)

Configure optional settings in your shell or `.env`:
```bash
export RESUME_FILE="resume.md"                       # Path to candidate resume
export ANTHROPIC_API_KEY="sk-ant-..."                # Anthropic API key for bullet generation
export ANTHROPIC_MODEL="claude-3-5-sonnet-latest"    # Model identifier
export LLM_SUGGESTION_THRESHOLD=60                   # Minimum match score to trigger bullet generation
```

---

## Running the Pipeline

### Execute Local Async Scrape
```bash
./venv/bin/python main.py
```

### Output Telemetry Report
```
==============================================================================
           JOB SCRAPER INGESTION ENGINE: YIELD & TELEMETRY REPORT
==============================================================================
Total Companies Evaluated : 397
Total Pipeline Duration   : 12.45 seconds
Total Raw Listings Ingested: 1,840
Total Qualified Leads     : 42
Companies with >=1 Listing: 118 (29.7%)
Companies with 0 Listings : 279 (70.3%)
------------------------------------------------------------------------------
ATS Platform       | Companies  | With Jobs  | Zero Jobs  | Raw Jobs   | Valid Leads
------------------------------------------------------------------------------
html_fallback      | 287        | 22         | 265        | 45         | 4         
greenhouse         | 52         | 52         | 0          | 1120       | 26        
workday            | 19         | 15         | 4          | 430        | 8         
smartrecruiters    | 17         | 17         | 0          | 145        | 3         
ashby              | 13         | 12         | 1          | 100        | 1         
==============================================================================
```

Output spreadsheet will be generated at:
`output/High_Conversion_Job_Leads_YYYY-MM-DD.xlsx`

---

## Running Unit Tests

Run the complete 30-test automated test suite:
```bash
./venv/bin/python -m unittest discover tests
```

---

## Excel Output Columns (15 Fields)

| # | Column Header | Description |
|---|---|---|
| 1 | Company Name | Clean, deduplicated company name |
| 2 | Company Type | Tier-1 GCC / Unicorn / High-Paying Startup / Big MNC |
| 3 | Job Title | Decoupled, whitespace-clean title |
| 4 | **Match Score** | **0–100 candidate alignment score with color coding** |
| 5 | Experience Range | Parsed experience requirement (e.g. `0-2 years`) |
| 6 | Location | Verified job location (India cities only) |
| 7 | **Top JD Keywords** | **Top 8–10 emphasized backend skills in the JD** |
| 8 | **Missing From Resume** | **Key required skills absent from candidate resume** |
| 9 | **Suggested Bullet Edits**| **2–3 AI-tailored resume bullets generated via Claude** |
| 10 | Job ID | Stable tracking-stripped ID or SHA-256 fallback |
| 11 | Posted Date | ATS publication date (where available) |
| 12 | Official Apply Link | Clickable hyperlinked direct application URL |
| 13 | Career Portal URL | Clickable hyperlinked main company portal |
| 14 | Full Job Description | Clean plain-text description (no SPA chrome) |
| 15 | Scraped Timestamp | ISO execution timestamp |

---

## Repository Structure
```
jobscrap/
├── ats_clients/             # Dedicated ATS JSON API clients (Greenhouse, Lever, Ashby, Workday, SmartRecruiters)
├── scoring/                 # Skills taxonomy, keyword extractor, resume matcher, and Claude bullet generator
├── tests/                   # Automated unit test suite (30 test cases)
├── output/                  # Formatted Excel output files (.xlsx)
├── companies.json           # Curated database of 397 target companies with ATS metadata
├── config.py                # System constants, column mappings, and thresholds
├── exporter.py              # OpenPyXL styled spreadsheet exporter
├── filters.py               # Pure business filters (role, location, experience)
├── main.py                  # Async orchestrator with semaphore concurrency and telemetry
├── scraper.py               # Rate limiting, backoff retries, and job ID derivation
├── state_manager.py         # Rolling 30-day state persistence and deduplication
├── resume.md                # Candidate resume input markdown file
└── requirements.txt         # Project dependencies
```
