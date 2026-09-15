# Job Scraper: Comprehensive Codebase Analysis & LLM Improvement Blueprint

> **Document Version:** 1.0.0  
> **Target Audience:** AI Engineering Models (Claude 3.7 / GPT-4o / Gemini 2.5), Engineering Leads, and System Architects  
> **Purpose:** Full-context system architecture, technical debt analysis, critical bug identification, and actionable execution roadmap for modernizing and scaling the job scraping ecosystem.

---

## 1. Executive System Overview

The **Job Scraper** is an automated Python-based data extraction pipeline designed to find early-career backend engineering job opportunities (0–3 years experience) in India across Tier-1 GCCs, Unicorns, and high-growth startups. 

It runs as a scheduled daily job via **GitHub Actions** (at 03:00 UTC / 08:30 IST), parsing career pages, filtering listings against experience, role, and location criteria, deduplicating records over a rolling 30-day window, and outputting an Excel report (`.xlsx`) committed directly back to the GitHub repository.

### Key Metrics
- **Company Catalog:** 422 curated companies (`companies.json`)
  - Tier-1 GCCs: 214
  - High-Paying Startups: 93
  - Unicorns: 57
  - Big MNCs: 45
  - Series B-D: 13
- **Scraping Engine:** Synchronous HTTP (`requests` + `BeautifulSoup4`) with heuristic portal dispatching.
- **Output Artifacts:** Daily Excel spreadsheets saved in `output/` and state tracking in `scraper_state.json`.

---

## 2. Architecture & Workflow Diagram

```
                              [ GitHub Actions (Daily Cron 03:00 UTC) ]
                                                │
                                                ▼
                                         [ main.py ]
                                                │
                 ┌──────────────────────────────┴──────────────────────────────┐
                 ▼                                                             ▼
        [ companies.json ]                                            [ state_manager.py ]
      (422 Target Companies)                                       (Loads scraper_state.json)
                 │                                                             │
                 ▼                                                             │
         [ scraper.py ]  ◄─────────────── Loop over companies ─────────────────┘
                 │
                 ├──► Greenhouse (_scrape_greenhouse via HTML)
                 ├──► Lever (_scrape_lever via HTML)
                 ├──► Workday (_scrape_workday via HTML)
                 └──► Generic (_scrape_generic regex fallback)
                 │
                 ▼
        (Raw Job Listings)
                 │
                 ▼
        [ Detail Scraping ] ──► fetch_job_description(job['link'])
                 │
                 ▼
         [ filters.py ] (JobFilter)
                 ├── 1. Location Validation (is_valid_location)
                 ├── 2. Role Exclusion Filter (is_backend_role)
                 ├── 3. Experience Validation (is_valid_experience)
                 └── 4. Metadata Attachment (extract_experience, stack_match)
                 │
                 ▼
        (Deduplication & State Update)
                 │ (Checks & marks `company_jobid` in state_manager)
                 ▼
         [ exporter.py ] (ExcelExporter via openpyxl)
                 │
                 ▼
  [ output/High_Conversion_Job_Leads_YYYY-MM-DD.xlsx ]
                 │
                 ▼
  [ Git Auto-Commit & Push back to main ]
```

---

## 3. Detailed Component Breakdown

### 3.1 Orchestrator: `main.py`
- **Role:** Main controller script.
- **Workflow:**
  1. Instantiates `StateManager`, `JobScraper`, and `ExcelExporter`.
  2. Reads `companies.json` and queries `state_manager.get_companies_to_scrape()`.
  3. Iterates through each company sequentially:
     - Scrapes listings via `JobScraper.scrape_company()`.
     - Fetches individual job description via HTTP for each listing.
     - Runs `JobFilter.filter_job()`.
     - Checks `state_manager.is_job_seen(job_id)`.
     - Appends valid jobs and updates state.
  4. Triggers `state_manager.cleanup_old_jobs(days=30)` and `state_manager.save_state()`.
  5. Exports results to `output/High_Conversion_Job_Leads_YYYY-MM-DD.xlsx`.

### 3.2 Scraping Engine: `scraper.py`
- **Role:** HTTP client and HTML parser.
- **Handlers:**
  - `_scrape_greenhouse`: HTML parsing of `div.opening`.
  - `_scrape_lever`: HTML parsing of `div.posting`.
  - `_scrape_workday`: Naive HTML parsing of `li.css-1q2dra3`.
  - `_scrape_generic`: Regex match on elements with classes containing `job|position|opening|career`.
  - `fetch_job_description`: Downloads individual job page, strips scripts/styles/nav/footers, and extracts text container (max 5000 characters).

### 3.3 Filtering Engine: `filters.py`
- **Role:** Business logic for qualifying job listings.
- **Rules:**
  - `is_valid_location`: Substring matching against `TARGET_LOCATIONS` (e.g., "bangalore", "hyderabad", "pune", "delhi", "remote", "india").
  - `is_backend_role`: Checks against `EXCLUDE_KEYWORDS` (e.g., senior, lead, manager, architect, intern, qa engineer, sdet).
  - `is_valid_experience`: Rejects jobs where patterns like `4+ years` or `minimum 4 years` occur.
  - `extract_experience`: Regular expression extractor for ranges (`0-3 years`, etc.).
  - `has_relevant_tech_stack`: Soft signal boolean for Java/Spring/SQL/Docker/Cloud keywords.

### 3.4 State & Deduplication: `state_manager.py`
- **Role:** Persists scraping history and deduplicates jobs across runs.
- **Data Structure (`scraper_state.json`):**
  ```json
  {
    "companies": {
      "Company Name": {
        "last_scraped": "2026-09-12T03:00:00.000000",
        "job_count": 2
      }
    },
    "seen_jobs": {
      "CompanyName_JobID": {
        "company": "CompanyName",
        "first_seen": "2026-09-12T03:00:00.000000"
      }
    }
  }
  ```
- **Retention:** Automatically purges records older than 30 days via `cleanup_old_jobs(days=30)`.

### 3.5 Exporter: `exporter.py`
- **Role:** Writes filtered jobs to structured Excel files via `openpyxl`.
- **Columns (11 Fields):** `Company Name`, `Company Type`, `Job Title`, `Experience Range`, `Location`, `Job ID`, `Posted Date`, `Official Apply Link`, `Career Portal URL`, `Full Job Description`, `Scraped Timestamp`.

### 3.6 Automation & Auxiliary Scripts
- `.github/workflows/scraper.yml`: GitHub Actions cron (daily at 3 AM UTC), sets up Python 3.10, runs `main.py`, commits output files and state JSON.
- `validate_urls.py`: Multithreaded URL checker (`ThreadPoolExecutor`) testing status codes of career links.
- `expand_companies.py` & `import_all.py`: Ingestion utilities for batch importing companies from CSV.
- `email_excel.py`, `upload_to_gdrive.py`, `upload_to_s3.py`: Optional notification/storage export scripts.

---

## 4. Critical Flaws, Vulnerabilities & Limitations

The codebase has several major bottlenecks and bugs that limit its yield and reliability:

### 🚨 Critical Bug #1: `BACKEND_KEYWORDS` is Never Checked
In `filters.py`, `BACKEND_KEYWORDS` is imported from `config.py` but is **never referenced** inside `is_backend_role()`.
- **Current Behavior:** As long as a job title does not contain "senior", "lead", "architect", "intern", etc., it passes as a backend role.
- **Impact:** Non-engineering roles (HR, Sales, Product, Legal, Finance) bypass the filter if they appear on generic career pages.

### 🚨 Critical Flaw #2: Failure on Modern JS/SPA Portals
Over 60% of companies in `companies.json` use JavaScript Single Page Applications (React, Angular, Vue, Workday, Taleo, iCIMS, Google Careers, Microsoft Careers, Apple Jobs):
- `requests.get()` only fetches the bare HTML shell (e.g. `<div id="root"></div>`), returning **0 jobs**.
- Workday's client-side dynamic rendering fails against `_scrape_workday` because job cards are loaded asynchronously via POST requests to `/wday/cxs/{tenant}/{site}/jobs`.

### 🚨 Critical Flaw #3: Missing Direct ATS JSON APIs
Platforms like Greenhouse, Lever, Ashby, and SmartRecruiters offer public, high-speed, rate-limit-friendly JSON APIs that return 100% structured data without HTML scraping:
- **Greenhouse API:** `https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true`
- **Lever API:** `https://api.lever.co/v0/postings/{company}?mode=json`
- **Ashby API:** `https://api.ashbyhq.com/posting-api/job-board/{organization}`
- **SmartRecruiters API:** `https://api.smartrecruiters.com/v1/companies/{company}/postings`
The current scraper uses brittle HTML parsing instead of these reliable APIs.

### 🚨 Performance Bottleneck #4: Synchronous Sequential Execution & Rate Limiting
- Scraping 422 companies sequentially with `RATE_LIMIT_DELAY = 2` seconds per request + 1 request per job description takes an extensive amount of time and risks hitting GitHub Action run timeouts.
- Needs asynchronous I/O (`asyncio` + `httpx`/`aiohttp`) or worker pools with controlled per-domain concurrency.

### 🚨 Repository Bloat #5: Committing Excel Binaries to Git
- The repository currently commits `.xlsx` binary files daily into the git tree (`output/High_Conversion_Job_Leads_*.xlsx`).
- There are already over 100 binary Excel files in git history, which permanently inflates repository clone size and creates merge conflict risks.

---

## 5. Prioritized Improvement Roadmap

Here is the structured 4-phase transformation plan for any LLM model or engineering team working on this project:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: CORE ENGINE & ATS API INTEGRATIONS (High Priority)                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Fix `filters.py`: Enforce positive `BACKEND_KEYWORDS` matching in title. │
│ 2. Implement ATS API Clients:                                               │
│    - Greenhouse JSON API (`boards-api.greenhouse.io`)                       │
│    - Lever JSON API (`api.lever.co`)                                        │
│    - Ashby API (`api.ashbyhq.com`)                                          │
│    - SmartRecruiters API (`api.smartrecruiters.com`)                        │
│    - Workday CXS JSON Endpoint client                                       │
│ 3. Add explicit `ats_type` and `ats_id` fields to `companies.json`.         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: ASYNC CONCURRENCY & RESILIENCE                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Refactor engine to `asyncio` + `httpx` for high-throughput crawling.     │
│ 2. Implement domain-level rate limiters and exponential backoff retry logic.│
│ 3. Add optional Headless Browser (`Playwright` / `Camoufox`) worker fallback│
│    for tough SPA portals (Google, Amazon, Meta, Apple).                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: INTELLIGENT FILTERING & LLM EXTRACTION                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Advanced Experience Parser (distinguish minimum vs maximum vs total exp).│
│ 2. Tech Stack Scoring & Salary/Remote extraction.                           │
│ 3. Optional local/fast LLM classification step (e.g. Gemini Flash / Ollama) │
│    for ambiguous job descriptions.                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 4: STORAGE, NOTIFICATIONS & DELIVERY DECOUPLING                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Migrate storage from Git commits to SQLite / Supabase / PostgreSQL.      │
│ 2. Auto-upload Excel to Google Drive / AWS S3 / Cloudflare R2.              │
│ 3. Instant Alerting: Telegram Bot / Discord Webhook / Slack integration.    │
│ 4. Build a lightweight Web UI / Dashboard (Streamlit, FastHTML, or Next.js).│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Target Data Schema for `companies.json`

To enable clean API dispatching, the company schema should be upgraded:

```json
[
  {
    "name": "Stripe",
    "type": "Tier-1 GCC",
    "ats": "greenhouse",
    "ats_token": "stripe",
    "career_url": "https://stripe.com/jobs",
    "location_filter": ["India", "Remote - India", "Bengaluru"]
  },
  {
    "name": "Netflix",
    "type": "Tier-1 GCC",
    "ats": "custom_api",
    "api_url": "https://jobs.netflix.com/api/search?location=India",
    "career_url": "https://jobs.netflix.com"
  }
]
```

---

## 7. Instructions for Future LLM Prompts

When prompting an LLM model to work on this repository, provide this document along with one of the following prompt templates:

### Prompt Template 1: Fix Core Filtering & Add Greenhouse/Lever APIs
> *"You are working on the job scraping system described in `CODEBASE_ANALYSIS_AND_IMPROVEMENT_SPEC.md`. Refactor `scraper.py` and `filters.py` to: (1) Enforce strict backend role keyword matching in `filters.py`, (2) Replace the HTML scrapers for Greenhouse and Lever with direct calls to their public JSON APIs, and (3) Add unit tests validating these changes."*

### Prompt Template 2: Convert Scraper to Async (`httpx` + `asyncio`)
> *"Read `CODEBASE_ANALYSIS_AND_IMPROVEMENT_SPEC.md`. Refactor the core pipeline (`main.py` and `scraper.py`) to use `asyncio` and `httpx.AsyncClient` with a concurrency semaphore (max 10 concurrent requests) and per-host rate limiting, keeping full state persistence and deduplication intact."*

### Prompt Template 3: Integrate Telegram / Discord / Cloud Storage Export
> *"Based on `CODEBASE_ANALYSIS_AND_IMPROVEMENT_SPEC.md`, create an automated alert dispatcher module that takes the daily exported jobs, formats a markdown digest of high-match leads, and sends them via a Telegram bot / Discord webhook, while uploading the `.xlsx` file to Google Drive or AWS S3."*
