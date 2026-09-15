# Changelog

All notable changes to the Job Scraper project are documented in this file.

---

## [Phase 3 - Backend Service Layer & SQLite Database Persistence] - 2026-09-12

This release migrates persistence off git-committed Excel binaries and `scraper_state.json` onto a real database (SQLite with `aiosqlite` and SQLAlchemy 2.0 async, easily swappable for Postgres/Supabase), stands up a production-grade FastAPI REST API with JWT authentication and RBAC, implements on-demand Excel export generation, scheduled retention purging, and updates GitHub Actions workflows to prevent git binary bloat.

### 1. Database Schema & Migration (`backend/models.py`, `backend/database.py`, `backend/migrate.py`)
- Created SQLAlchemy 2.0 async models for 6 core entities:
  - `Company`: Name, career URL, ATS configuration (type, token, id), location filters, active status, scrape timestamps, and job counts.
  - `Job`: Stable job ID, title, company, match score, experience, location, keywords, LLM bullet rewrites, apply links, and scrape timestamp.
  - `ScrapeRun`: Telemetry logs (started_at, duration, raw jobs ingested, valid leads yielded, company counts, average match score, status).
  - `FilterConfig`: Dynamically editable keyword taxonomies, experience bounds, target locations, and LLM score thresholds.
  - `User`: Email, bcrypt-hashed password, RBAC role (`admin`, `viewer`), active status, and login timestamps.
  - `ExportRecord`: Generated spreadsheet metadata, download links, row counts, and deletion status.
- Implemented idempotent migration script `backend/migrate.py` that imports existing `scraper_state.json` history, 397 companies from `companies.json`, seeds default filters, and initializes the admin account.

### 2. FastAPI REST Service & Routers (`backend/api.py`, `backend/routers/`)
- Implemented modular FastAPI application with structured JSON logging and OpenAPI documentation (`/docs`, `/redoc`):
  - **Auth (`/auth`)**: JWT-based login with bcrypt password verification, current user profile (`/auth/me`), and user registration.
  - **Companies (`/companies`)**: Full CRUD (`GET`, `POST`, `PUT`, `DELETE`), ATS filtering, search, and near-duplicate company name alerts.
  - **Filters (`/filters`)**: `GET` and `PUT` for dynamically tuning backend keywords, locations, and experience constraints without redeploying code.
  - **Jobs (`/jobs`)**: Filterable paginated job search by score, company, location, date range, plus aggregate stats (`/jobs/stats`).
  - **Runs (`/runs`)**: Historical scrape telemetry inspection and async background run triggering (`POST /runs/trigger`).
  - **Exports (`/exports`)**: On-demand 15-column Excel sheet generation (`POST /exports`), binary download streaming (`GET /exports/{id}/download`), and file deletion (`DELETE /exports/{id}`).

### 3. Security, RBAC & Centralized Error Handling (`backend/auth.py`, `backend/exceptions.py`)
- Direct `bcrypt` password hashing and signed JWT validation.
- Role-Based Access Control (`require_admin` dependency guard) restricting company/filter mutations and deletions to administrators.
- Typed exception hierarchy (`AppBaseException`, `NotFoundError`, `AuthError`, `ForbiddenError`, `ConflictError`, `ValidationError`, `RateLimitError`, `ScrapeError`, `ParseError`) with structured RFC-compliant JSON responses.
- Environment-driven configuration with `.env.example` documenting all secret keys (`JWT_SECRET`, `ADMIN_PASSWORD`, `DATABASE_URL`, etc.).

### 4. Scheduled Export Retention & Cleanups (`backend/retention.py`)
- Built export retention cleaner with configurable window (default 14 days).
- Supports CLI execution with `--dry-run` flag and detailed logging of purged spreadsheets.

### 5. Scraper Pipeline Synchronization & CI/CD (`main.py`, `.github/workflows/scraper.yml`)
- Updated `main.py` to synchronize scraped leads, company timestamps, and run metrics directly into SQLite.
- Updated `.github/workflows/scraper.yml` to run database migration, execute the scraper, purge old files, and upload daily reports via GitHub Actions Artifacts instead of committing `.xlsx` binaries to git.

### 6. Automated Test Suite (`tests/test_backend_api.py`)
- Added 9 comprehensive async integration tests covering all REST endpoints, JWT authentication, RBAC restrictions, export generation, downloads, and retention purge (39 total tests passing across repository).

---

## [Phase 2 - Relevance Scoring & Resume Intelligence] - 2026-09-12

- Indexed 150+ backend engineering technologies across 6 key domains (`scoring/taxonomy.py`).
- Implemented weighted TF-IDF keyword extraction and 0–100 candidate resume alignment scoring (`scoring/extractor.py`, `scoring/matcher.py`).
- Integrated Anthropic Claude API for high-scoring lead bullet point generation (`scoring/bullet_generator.py`).
- Upgraded `exporter.py` to 15-column schema with conditional styling, frozen panes, and auto-filters.

---

## [Phase 1 - ATS-Native Ingestion Engine] - 2026-09-12

- Replaced HTML scraping with native JSON APIs (Greenhouse, Lever, Ashby, SmartRecruiters, Workday CXS).
- Refactored `main.py` to `asyncio` + `httpx.AsyncClient` with semaphore concurrency and rate limiting.
- Deprecated all LinkedIn scraping code paths per ToS guidelines.
- Migrated `companies.json` to structured ATS schemas (397 companies).

---

## [Phase 0 - Core Correctness & Reliability Fixes] - 2026-09-12

- Enforced positive `BACKEND_KEYWORDS` role matching in `filters.py`.
- Enforced strict location validation and non-India disqualification.
- Implemented tracking-param-stripped URL deduplication and SHA-256 fallback job ID.
- Separated title and location DOM nodes with whitespace.
- Rejected SPA JavaScript shells and 404 dead links.
- Deduplicated `companies.json` catalog from 422 to 397 entries.
