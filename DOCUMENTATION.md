# Enterprise Job Scraper & Resume Intelligence Platform — Complete Documentation

## 1. System Architecture

The system is built on modern asynchronous Python (3.10+), FastAPI, React 18, and SQLite/PostgreSQL with the following modular layers:

### Core Modules:
1. **`ats_clients/` — Direct ATS JSON Ingestion**:
   - `GreenhouseClient`: Queries `boards-api.greenhouse.io`.
   - `LeverClient`: Queries `api.lever.co`.
   - `AshbyClient`: Queries `api.ashbyhq.com`.
   - `SmartRecruitersClient`: Queries `api.smartrecruiters.com`.
   - `WorkdayClient`: Queries `/wday/cxs/{tenant}/{site}/jobs`.
   - `HtmlFallbackClient`: Asynchronous polite HTML scraper with rate limiting.

2. **`scoring/` — Resume Intelligence & AI Matcher**:
   - `taxonomy.py`: Curated 150+ skill ontology.
   - `extractor.py`: TF-IDF prominence-weighted keyword extraction.
   - `matcher.py`: 0–100 match score and skill gap computation.
   - `bullet_generator.py`: Anthropic Claude tailored resume bullet point generator.

3. **`backend/` — Persistence & REST API**:
   - `models.py`: SQLAlchemy schema for companies, jobs, scrape_runs, filters, users, and exports.
   - `api.py` & `routers/`: Modular FastAPI endpoints for companies, jobs, filters, runs, and export downloads.
   - `auth.py`: JWT bearer token security with bcrypt hashing.
   - `retention.py`: Automated retention policy for daily scrape history.
   - `telemetry.py`: Sentry SDK error tracking & Healthchecks.io ping.

4. **`frontend/` — Single Page Dashboard**:
   - React 18 + Vite + TypeScript.
   - Dark glassmorphic UI system.
   - Live views for Overview, Companies, Dynamic Filters, Jobs, Scrape Runs, and Exports.

5. **`notifier/` — Daily Digest Delivery**:
   - `digest.py`: Telegram MarkdownV2 notifier and SMTP email fallback summarizing top match leads.

---

## 2. Running & Managing the System

### Automated Setup:
```bash
./setup.sh
```

### Starting the Services:
- **Backend API**: `source venv/bin/activate && uvicorn backend.api:app --reload --port 8000`
- **Frontend Dashboard**: `cd frontend && npm run dev`
- **Docker Compose**: `docker-compose up --build -d`

---

## 3. Database Schema Overview

```sql
-- Target Companies Table
CREATE TABLE companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    career_url TEXT NOT NULL,
    portal_type TEXT DEFAULT 'generic',
    ats TEXT DEFAULT 'html_fallback',
    ats_token TEXT,
    ats_id TEXT,
    location_filter JSON,
    company_type TEXT DEFAULT 'Tech',
    active BOOLEAN DEFAULT 1,
    last_scraped_at DATETIME,
    job_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Scraped & Scored Jobs Table
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT UNIQUE NOT NULL,
    company_name TEXT NOT NULL,
    company_type TEXT,
    title TEXT NOT NULL,
    match_score INTEGER DEFAULT 0,
    experience_range TEXT,
    location TEXT,
    top_jd_keywords JSON,
    missing_from_resume JSON,
    suggested_bullets TEXT,
    posted_date TEXT,
    apply_link TEXT,
    portal_url TEXT,
    description TEXT,
    stack_match BOOLEAN DEFAULT 0,
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. Test Suite Execution

Run all 30 unit tests:
```bash
python -m unittest discover tests
```
