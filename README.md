# Enterprise Job Scraper & Resume Intelligence Engine

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An enterprise-grade, privacy-first, automated job extraction and AI resume match intelligence engine targeting early-career backend engineering roles (0–3 years experience, India locations) across **390+ curated Tier-1 GCCs, Unicorns, and high-growth tech companies**.

Built with direct public ATS API ingestion (Greenhouse, Lever, Ashby, SmartRecruiters, Workday), an async concurrency engine, a 0–100 candidate match scoring algorithm, Anthropic Claude resume bullet generation, SQLite persistence, a FastAPI REST service, a modern React/Vite dashboard, Docker containerization, Sentry error monitoring, and Telegram/Email daily digests.

---

## 🏗️ System Architecture

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
           └──────────────────────────┘
```

---

## ✨ Key Features & Highlights

### 1. 🚀 Direct Public ATS Ingestion (100% ToS Compliant)
- **Greenhouse API (`boards-api.greenhouse.io`)**: Ingests structured JSON job feeds with clean descriptions.
- **Lever API (`api.lever.co`)**: Fetches exact post metadata and requirement blocks.
- **Ashby API (`api.ashbyhq.com`)**: Directly queries job boards, bypassing single-page JavaScript rendering.
- **SmartRecruiters API (`api.smartrecruiters.com`)**: Parses structured posting sections and location metadata.
- **Workday CXS API (`/wday/cxs/{tenant}/{site}/jobs`)**: Queries Workday candidate service endpoints directly.
- **Polite HTML Fallback**: Asynchronous, rate-limited parser for custom company portals.
- **Zero Third-Party Scraping**: Strict ToS compliance (no scraping of LinkedIn, Indeed, Glassdoor, or Naukri).

### 2. ⚡ High-Throughput Async Engine
- **Async Concurrency**: Powered by `asyncio` and `httpx.AsyncClient` with connection pooling.
- **Bounded Concurrency**: Uses `asyncio.Semaphore(10)` to prevent host networking saturation.
- **Domain Rate Limiting**: Exponential backoff with random jitter on HTTP 429 / 5xx responses.
- **Stable Tracking-Stripped Job IDs**: Generates stable SHA-256 job keys that strip tracking parameters (`utm_source`, `gh_jid`, `lever-origin`) for exact deduplication.

### 3. 🎯 AI Resume Intelligence & Match Scoring (`scoring/`)
- **Backend Engineering Skills Taxonomy**: Curated dictionary of 150+ skills spanning Languages, Frameworks, Databases & Caching, Cloud & DevOps, Distributed Systems, and Architecture.
- **TF-IDF Keyword Prominence**: Ranks job requirements based on term frequency and section prominence (Title > Requirements > Overview).
- **0–100 Match Score Algorithm**: Computes candidate alignment based on skills overlap and requirement weighting.
- **Skills Gap Analysis**: Identifies critical technology keywords present in the job posting but missing from your candidate resume.
- **Anthropic Claude Bullet Generator**: Generates 2–3 tailored resume achievement bullets for high-scoring roles (Score ≥ threshold) via `claude-3-5-sonnet-latest`.

### 4. 🗄️ Database Persistence & REST API (`backend/`)
- **SQLite Database (`jobscraper.db`)**: Stores target companies, extracted jobs, daily run metrics, filter configs, and users.
- **FastAPI REST Service**: Exposes documented endpoints (`/docs`) for programmatic management.
- **JWT Authentication**: Secure token-based authentication with password hashing (`passlib`/`bcrypt`).
- **Automated Retention Cleanup**: Scheduled job to automatically purge historical runs older than `RETENTION_DAYS` (default 14 days) with dry-run support.

### 5. 💻 Modern React Web Dashboard (`frontend/`)
- **React 18 + Vite + TypeScript**: Premium, fast administrative interface.
- **Companies View**: Add, edit, activate/deactivate companies, update ATS tokens, and detect duplicate company names.
- **Filters View**: Dynamically tune backend experience ranges, backend keywords, exclude keywords, and allowed locations without redeploying code.
- **Jobs & Scrape Runs View**: Search jobs by score, date range, location, and company; inspect daily run telemetry; download styled Excel spreadsheets.
- **Exports View**: Download or remove historical daily lead spreadsheets.

### 6. 🔔 Observability & Daily Digest Notifiers (`notifier/` & `telemetry.py`)
- **Telegram & Email Digest Notifiers**: Sends a daily summary message highlighting top match leads above a configurable threshold.
- **Sentry Integration**: Automatic error tracking for both FastAPI API requests and scraper executions (`SENTRY_DSN`).
- **Heartbeat Ping**: Ping integration for [healthchecks.io](https://healthchecks.io) (`HEARTBEAT_URL`) to monitor daily job completion.

### 7. 🐳 Containerization & CI/CD
- **Multi-Stage Dockerfile**: Slim Python 3.11 image with non-root security context.
- **Docker Compose Stack**: Defines `api`, `scheduler`, and `frontend` services with volume persistence.
- **GitHub Actions CI/CD**: Automated unit test execution and Fly.io production deployment on merge to `main`.

---

## 🚀 Quick Start (Local Setup)

### Automated One-Step Setup

The project includes an automated setup script that checks prerequisites, sets up the virtual environment, installs Python and Node dependencies, initializes the database, and runs unit tests.

Run the setup script:
```bash
./setup.sh
```

---

### Manual Setup Step-by-Step

#### 1. Clone & Setup Virtual Environment
```bash
cd jobscrap
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 2. Configure Environment Variables
Copy the example environment configuration file:
```bash
cp .env.example .env
```
*(Optionally add your `ANTHROPIC_API_KEY`, `TELEGRAM_BOT_TOKEN`, or `SENTRY_DSN` in `.env`)*

#### 3. Initialize Database
Migrate historical state and company data into SQLite:
```bash
python -m backend.migrate
```

#### 4. Setup Frontend Dashboard
```bash
cd frontend
npm install
cd ..
```

---

## 🏃 Running the Application

### Option 1: Run with Docker Compose (Recommended for Full Stack)

Launch the API, Web Dashboard, and database using Docker:
```bash
docker-compose up --build -d
```
- **Web Dashboard**: [http://localhost:5173](http://localhost:5173)
- **FastAPI Backend API**: [http://localhost:8000](http://localhost:8000)
- **API Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

Trigger a scrape run inside Docker:
```bash
docker-compose run --rm scheduler
```

---

### Option 2: Run Locally Component by Component

#### 1. Run Scraper Pipeline (CLI Mode)
Executes a full async scrape, scores leads against `resume.md`, updates the database, and generates an Excel spreadsheet in `output/`:
```bash
source venv/bin/activate
python main.py
```

#### 2. Run FastAPI Backend API
Starts the REST API service on port 8000:
```bash
source venv/bin/activate
uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload
```

#### 3. Run React Web Dashboard
Starts the Vite dev server on port 5173:
```bash
cd frontend
npm run dev
```

**Default Admin Credentials for Web Dashboard:**
- **Email**: `admin@jobscraper.io`
- **Password**: `admin123`

---

## 📄 Candidate Resume Configuration (`resume.md`)

Place your resume details in `resume.md` in the project root directory (or point `RESUME_FILE` in `.env` to your custom path):

```markdown
# Candidate Name — Backend Engineer
Email: candidate@example.com | Location: Bengaluru, India | GitHub: github.com/candidate

## Technical Skills
- Languages: Python, Java, Go, SQL
- Frameworks: FastAPI, Django, Spring Boot, Express
- Databases & Caching: PostgreSQL, Redis, MySQL, MongoDB
- Cloud & Infrastructure: AWS, Docker, Kubernetes, GitHub Actions, Terraform
- Architecture & Practices: Microservices, REST APIs, Distributed Systems, Unit Testing, CI/CD
```

---

## 🛠️ Environment Variables Configuration (`.env`)

| Variable | Default Value | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./jobscraper.db` | SQLite or PostgreSQL database connection string |
| `JWT_SECRET` | `dev-secret-key-change-in-production` | Secret key for JWT token signing |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | JWT token lifespan (minutes) |
| `RESUME_FILE` | `resume.md` | Path to candidate resume markdown file |
| `ANTHROPIC_API_KEY` | *Optional* | Anthropic API key for AI resume bullet generation |
| `ANTHROPIC_MODEL` | `claude-3-5-sonnet-latest` | Claude model for bullet points |
| `LLM_SUGGESTION_THRESHOLD` | `60` | Minimum match score to trigger Claude bullet generation |
| `TELEGRAM_BOT_TOKEN` | *Optional* | Telegram Bot API token for daily digest |
| `TELEGRAM_CHAT_ID` | *Optional* | Telegram chat ID to receive daily digest |
| `SMTP_SERVER` | *Optional* | SMTP host for email daily digest fallback |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USER` / `SMTP_PASSWORD` | *Optional* | Credentials for SMTP email sender |
| `SENTRY_DSN` | *Optional* | Sentry project DSN for error monitoring |
| `HEARTBEAT_URL` | *Optional* | Healthchecks.io ping URL for job telemetry heartbeat |
| `RETENTION_DAYS` | `14` | Days of scrape history to retain in database |

---

## 🧪 Running Automated Unit Tests

The repository includes a comprehensive 30-test automated unit testing suite:

```bash
source venv/bin/activate
python -m unittest discover tests
```

### Test Suite Coverage:
- **`tests/test_ats_clients.py`**: Tests JSON parsing across Greenhouse, Lever, Ashby, Workday, and SmartRecruiters ATS clients.
- **`tests/test_scoring.py`**: Validates skills taxonomy extraction, TF-IDF scoring algorithm, and candidate resume matching.
- **`tests/test_backend_api.py`**: Tests FastAPI routes, JWT authentication, company CRUD, job queries, and filter updates.
- **`tests/test_fixes.py`**: Ensures correctness of location filtering, role matching, job ID deduplication, and openpyxl formatting.

---

## 📊 Formatted Excel Output (15 Columns)

Every scrape run outputs a formatted, styled spreadsheet to `output/High_Conversion_Job_Leads_YYYY-MM-DD.xlsx`:

| # | Column Header | Description |
|---|---|---|
| 1 | Company Name | Deduplicated target company name |
| 2 | Company Type | Category (Tier-1 GCC, Unicorn, Startup, Big MNC) |
| 3 | Job Title | Whitespace-cleaned job title |
| 4 | **Match Score** | **0–100 alignment score with color coding (Green ≥70, Yellow 40–69, Red <40)** |
| 5 | Experience Range | Parsed experience requirement (e.g. `0-2 years`) |
| 6 | Location | Verified job location (India cities only) |
| 7 | **Top JD Keywords** | **Top 8–10 backend technical keywords in the JD** |
| 8 | **Missing From Resume** | **Required JD keywords absent from candidate resume** |
| 9 | **Suggested Bullet Edits** | **2–3 AI-tailored resume bullets generated via Claude** |
| 10 | Job ID | Stable tracking-stripped unique identifier |
| 11 | Posted Date | Official ATS publication timestamp |
| 12 | Official Apply Link | Direct hyperlinked application URL |
| 13 | Career Portal URL | Hyperlinked main corporate career portal |
| 14 | Full Job Description | Plain-text job description without boilerplate |
| 15 | Scraped Timestamp | ISO execution timestamp |

---

## 📁 Repository Structure

```
jobscrap/
├── .github/workflows/        # CI/CD pipeline definitions (ci.yml, scraper.yml)
├── ats_clients/              # Direct ATS JSON API integrations (Greenhouse, Lever, Ashby, Workday, SmartRecruiters)
├── backend/                  # FastAPI REST Service, SQLAlchemy Models, Auth, CRUD & Migration
│   ├── routers/              # Modular API routes (auth, companies, filters, jobs, runs, exports)
│   ├── api.py                # FastAPI app initialization & OpenAPI setup
│   ├── auth.py               # Password hashing & JWT token verification
│   ├── database.py           # SQLAlchemy database session & engine configuration
│   ├── migrate.py            # Historical JSON to SQLite migration script
│   └── telemetry.py          # Sentry error monitoring & Healthchecks.io ping
├── frontend/                 # React 18 + Vite + TypeScript Web Dashboard
│   ├── src/
│   │   ├── pages/            # Admin pages (Login, Overview, Companies, Filters, Jobs, Runs, Exports)
│   │   ├── components/       # UI components (Sidebar, Modals, Badges)
│   │   ├── api/client.ts     # Axios API client with JWT interceptor
│   │   └── contexts/         # React Auth Context
│   ├── Dockerfile.frontend   # Nginx production Docker image
│   └── nginx.conf            # Reverse proxy configuration
├── notifier/                 # Telegram & Email daily digest notification engines
├── scoring/                  # Backend skills taxonomy, TF-IDF extractor, Matcher & LLM Bullet Generator
├── tests/                    # Automated unit test suite (30 test cases)
├── companies.json            # Curated target list of 390+ companies with ATS metadata
├── config.py                 # Central system parameters, regex rules, and thresholds
├── Dockerfile                # Multi-stage production container build
├── docker-compose.yml        # Multi-container local/staging orchestration
├── exporter.py               # OpenPyXL spreadsheet exporter with conditional formatting
├── filters.py                # Business logic filters (role, location, experience)
├── fly.toml                  # Fly.io cloud deployment manifest
├── main.py                   # Async pipeline orchestrator with telemetry summary
├── requirements.txt          # Python dependencies
├── resume.md                 # Markdown resume input file
├── scraper.py                # Async HTTP client, rate limiter, and job ID derivation
├── setup.sh                  # Automated local setup script for macOS/Linux
├── SOURCES.md                # Compliance & ToS data sourcing documentation
└── MULTI_TENANT_DESIGN.md    # Multi-tenant SaaS architecture reference design
```

---

## 🔒 Security & Compliance

- **ToS Compliance**: All job data is gathered exclusively via public ATS JSON endpoints or official company career portals. No protected networks or ToS-restricted aggregator platforms are accessed (documented in [`SOURCES.md`](file:///Users/rishaadkhan/DevelopmentCoding/jobscrap/SOURCES.md)).
- **Zero Hardcoded Secrets**: Secrets and tokens are strictly configured via environment variables or `.env`.
- **SSRF & Network Defense**: Protocol validation restricted strictly to `http://` and `https://` with bounded timeouts.
- **Input Sanitization**: ReDoS-safe regex patterns and strict path handling prevent directory traversal.

---

## 📜 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
