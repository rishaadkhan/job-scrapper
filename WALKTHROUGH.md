# Enterprise Job Scraper & Resume Intelligence Engine — Full System Walkthrough

This document provides an end-to-end technical walkthrough of the **Enterprise Job Scraper & Resume Intelligence Engine**, detailing all system architecture components, business logic workflows, data schemas, API routes, user interfaces, and verification procedures across **Phases 0 through 5**.

---

## 📐 1. System Architecture Overview

```
                               ┌─────────────────────────────────────────┐
                               │       Direct ATS Public JSON APIs       │
                               │ Greenhouse | Lever | Ashby | Workday    │
                               └────────────────────┬────────────────────┘
                                                    │
                                                    ▼
 ┌──────────────────────┐              ┌──────────────────────────┐             ┌─────────────────────┐
 │  Resume Input File   │─────────────►│ Async Python Orchestrator│────────────►│  Curated Taxonomy   │
 │    (`resume.md`)     │              │  (httpx + Semaphore 10)  │             │   (150+ Skills)     │
 └──────────────────────┘              └────────────┬─────────────┘             └─────────────────────┘
                                                    │
                                                    ▼
                                       ┌──────────────────────────┐
                                       │ Resume Intelligence & AI │
                                       │ Match Score + Claude LLM │
                                       └────────────┬─────────────┘
                                                    │
                                                    ▼
                                       ┌──────────────────────────┐
                                       │   SQLite Database &      │
                                       │   Formatted OpenPyXL     │
                                       └────────────┬─────────────┘
                                                    │
                         ┌──────────────────────────┴──────────────────────────┐
                         ▼                                                     ▼
           ┌──────────────────────────┐                          ┌──────────────────────────┐
           │   FastAPI REST API       │                          │ Telegram / Email Digest  │
           │ (JWT Auth, CORS, RBAC)   │                          │   (Daily High Matches)   │
           └────────────┬─────────────┘                          └──────────────────────────┘
                        │
                        ▼
           ┌──────────────────────────┐
           │ React / Vite Web App     │
           │ (Companies, Jobs, Runs)  │
           └────────────┬─────────────┘
```

---

## 🛠️ 2. Phase-by-Phase Technical Capabilities

### Phase 0: Core Correctness & Data Hygiene
- **Backend Role Matching (`filters.py`)**: `is_backend_role()` positively requires at least one match in `BACKEND_KEYWORDS` in the job title or description, preventing non-engineering roles from passing through.
- **Strict Location Validation (`filters.py`)**: `is_valid_location()` strictly validates the scraped job location field against allowed India cities (Bengaluru, Hyderabad, Gurgaon, Pune, Mumbai, Remote India), rejecting non-India cities (e.g. London, San Francisco, Singapore).
- **Stable Tracking-Stripped Job IDs (`state_manager.py`)**: Derives unique job keys by stripping tracking parameters (`utm_source`, `gh_jid`, `lever-origin`) from URLs, generating a deterministic SHA-256 fallback hash.
- **15-Column OpenPyXL Exporter (`exporter.py`)**: Generates formatted spreadsheets with auto-filters, frozen header rows, clickable hyperlinks, and conditional HSL color coding (Green ≥70, Yellow 40–69, Red <40).

### Phase 1: Direct ATS Ingestion & Company Migration
- **5 Dedicated ATS Public JSON Clients (`ats_clients/`)**:
  - `GreenhouseClient`: Consumes `boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true`.
  - `LeverClient`: Consumes `api.lever.co/v0/postings/{company}?mode=json`.
  - `AshbyClient`: Consumes `api.ashbyhq.com/posting-api/job-board/{organization}`.
  - `SmartRecruitersClient`: Consumes `api.smartrecruiters.com/v1/companies/{company}/postings`.
  - `WorkdayClient`: Posts to `/wday/cxs/{tenant}/{site}/jobs`.
  - `HtmlFallbackClient`: Asynchronous HTML fallback for custom career portals.
- **Company Target List (`companies.json`)**: Migrated 390+ target companies with structured ATS metadata (`ats`, `ats_token`, `ats_id`).

### Phase 2: AI Resume Intelligence & Match Scoring
- **Curated Skills Taxonomy (`scoring/taxonomy.py`)**: Indexed dictionary of 150+ backend engineering skills spanning Languages, Frameworks, Databases, Cloud & DevOps, Distributed Systems, and Microservices Architecture.
- **TF-IDF Prominence Extractor (`scoring/extractor.py`)**: Extracts top 8–10 keywords per job based on term frequency and section weighting (Title > Requirements > Overview).
- **Candidate Matcher (`scoring/matcher.py`)**: Scores job alignment (0–100) based on candidate resume keyword overlap and requirement weights; lists missing skill gaps.
- **Claude LLM Bullet Generator (`scoring/bullet_generator.py`)**: Generates 2–3 tailored resume achievement bullet points via `claude-3-5-sonnet-latest` for jobs scoring above `LLM_SUGGESTION_THRESHOLD` (default 60).

### Phase 3: SQLite Persistence & FastAPI REST API
- **SQLAlchemy Schema (`backend/models.py`)**: Tables for `companies`, `jobs`, `scrape_runs`, `filters`, and `users`.
- **Migration Script (`backend/migrate.py`)**: Imports historical JSON state and target companies into SQLite database (`jobscraper.db`).
- **FastAPI REST Service (`backend/api.py` & `backend/routers/`)**:
  - `POST /auth/login` — OAuth2 Password Request Form, returns JWT bearer token.
  - `GET/POST/PUT/DELETE /companies` — CRUD for target companies with deduplication warnings.
  - `GET/PUT /filters` — Dynamic configuration for backend keywords, exclude keywords, experience ranges, and allowed locations.
  - `GET /jobs` — Query filtered jobs with pagination, minimum match score, company, and location parameters.
  - `GET /runs` — Inspect past scrape run metrics (duration, total scraped, qualified leads).
  - `POST /export` & `DELETE /exports/{id}` — Generate dynamic Excel spreadsheets and manage historical downloads.
- **Automated Retention Cleanup (`backend/retention.py`)**: Scheduled job that purges historical runs older than `RETENTION_DAYS` (default 14 days) with dry-run support.

### Phase 4: Modern React Web Dashboard
- **Single-Page Application (`frontend/`)**: Vite + React 18 + TypeScript + Tailwind-style Dark Glassmorphic Design System.
- **Interactive Views**:
  - **Overview**: System metrics, total tracked companies, active listings, average match score, recent scrape runs.
  - **Companies**: Interactive table with ATS token editing, status toggling (active/inactive), search, and name deduplication warning badges.
  - **Filters**: Live editor for backend keywords, excluded keywords, allowed experience range, and allowed locations.
  - **Jobs**: High-conversion leads grid with expandable drawer displaying full job descriptions, match scores, top keywords, missing resume skills, and AI-generated resume bullet points.
  - **Runs & Exports**: Detailed run log execution metrics and one-click Excel download options.

### Phase 5: Distribution Readiness & Observability
- **Multi-Stage Docker Container (`Dockerfile`)**: Optimized Python 3.11 build with non-root user `appuser` and built-in healthchecks.
- **Docker Compose Stack (`docker-compose.yml`)**: Multi-container stack orchestrating `api` (port 8000), `frontend` Nginx (port 5173), and `scheduler`.
- **Fly.io Deployment Config (`fly.toml`)**: Cloud deployment definition with automated persistent volume mounting (`/data`).
- **CI/CD Pipeline (`.github/workflows/ci.yml`)**: GitHub Actions workflow running automated unit tests on every push/PR and deploying to Fly.io on main branch merges.
- **Daily Digest Notifiers (`notifier/digest.py`)**: Telegram MarkdownV2 notifier and SMTP email fallback summarizing top high-match job leads daily.
- **Telemetry & Observability (`backend/telemetry.py`)**: Sentry SDK exception monitoring and Healthchecks.io heartbeat ping integration.
- **Compliance Audit (`SOURCES.md`)**: Complete legal and ToS compliance audit documenting 100% public API data sources and zero third-party scraping.
- **Multi-Tenant SaaS Reference Architecture (`MULTI_TENANT_DESIGN.md`)**: Strategic design for multi-tenant SaaS scaling (Postgres RLS, Stripe integration, user resume upload management).

---

## 🚀 3. Local Setup & Quick Start

### 1. One-Command Setup Script
Run the automated setup script to set up Python virtual environment, install backend and frontend dependencies, initialize the database, and execute the test suite:
```bash
./setup.sh
```

### 2. Running via Docker Compose
To launch the full stack in containers:
```bash
docker-compose up --build -d
```
Access points:
- **Web Dashboard**: `http://localhost:5173`
- **FastAPI REST API**: `http://localhost:8000`
- **OpenAPI Swagger Docs**: `http://localhost:8000/docs`

### 3. Running Components Separately
- **Run Scraper Pipeline (CLI)**:
  ```bash
  source venv/bin/activate
  python main.py
  ```
- **Run FastAPI Service**:
  ```bash
  source venv/bin/activate
  uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload
  ```
- **Run Web Dashboard**:
  ```bash
  cd frontend
  npm run dev
  ```

**Default Admin Credentials:**
- **Email**: `admin@jobscraper.io`
- **Password**: `admin123`

---

## 🧪 4. Automated Testing & Verification

The suite includes 30 unit tests with 100% pass rate:
```bash
source venv/bin/activate
python -m unittest discover tests
```

### Summary of Passing Tests:
1. `test_ats_clients.py` — Verifies JSON payload extraction across Greenhouse, Lever, Ashby, Workday, and SmartRecruiters APIs.
2. `test_scoring.py` — Tests skills taxonomy extraction, TF-IDF scoring algorithm, and candidate resume matching.
3. `test_backend_api.py` — Tests JWT login authentication, FastAPI CRUD endpoints, filter updates, and export generation.
4. `test_fixes.py` — Validates role matching, India location filter enforcement, tracking-stripped job deduplication, and OpenPyXL column formatting.

---

## 📄 5. Compliance & Security Verification

- **Data Sourcing**: All data ingestion relies strictly on public ATS JSON feeds or company career sites (documented in [`SOURCES.md`](file:///Users/rishaadkhan/DevelopmentCoding/jobscrap/SOURCES.md)).
- **Zero Credentials Leakage**: Credentials and keys are configured via environment variables with `.env.example` guidance.
- **Network Safety**: Bounded HTTP timeouts and protocol checks protect network security.
