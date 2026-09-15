# 🚀 Quick Start Guide: Enterprise Job Scraper & Intelligence Platform

## ✅ System Overview
An automated, privacy-first pipeline that ingests public ATS job postings (Greenhouse, Lever, Ashby, SmartRecruiters, Workday), filters for early-career backend engineering roles in India (0–3 years), scores leads against your candidate resume (`resume.md`), and presents them via an interactive React Web Dashboard, REST API, formatted Excel spreadsheets, and daily Telegram/Email digest alerts.

---

## ⚡ 1-Step Setup

```bash
./setup.sh
```

The setup script handles:
1. Python virtual environment creation & dependency installation.
2. Initial `.env` configuration from `.env.example`.
3. Database creation & historical migration (`jobscraper.db`).
4. Frontend Node package installation (`frontend/npm install`).
5. Automated test suite execution (30 tests).

---

## 🏃 Running the Application

### Option 1: Docker Compose (Full Stack)
```bash
docker-compose up --build -d
```
- **Web Dashboard**: [http://localhost:5173](http://localhost:5173) (Login: `admin@jobscraper.io` / `admin123`)
- **FastAPI Backend**: [http://localhost:8000](http://localhost:8000)
- **API Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### Option 2: Local CLI Mode
```bash
source venv/bin/activate
# Run Scraper Pipeline:
python main.py

# Run FastAPI API Server:
uvicorn backend.api:app --reload

# Run React Dashboard (in new terminal):
cd frontend && npm run dev
```

---

## 📚 Key Reference Documents

| Document | Purpose |
|---|---|
| [`README.md`](file:///Users/rishaadkhan/DevelopmentCoding/jobscrap/README.md) | Comprehensive system architecture & feature guide |
| [`WALKTHROUGH.md`](file:///Users/rishaadkhan/DevelopmentCoding/jobscrap/WALKTHROUGH.md) | End-to-end technical walkthrough across all phases |
| [`ADDING_COMPANIES_GUIDE.md`](file:///Users/rishaadkhan/DevelopmentCoding/jobscrap/ADDING_COMPANIES_GUIDE.md) | Guide to adding & managing target companies |
| [`FILTER_UPDATES.md`](file:///Users/rishaadkhan/DevelopmentCoding/jobscrap/FILTER_UPDATES.md) | Business logic & dynamic filter tuning |
| [`SOURCES.md`](file:///Users/rishaadkhan/DevelopmentCoding/jobscrap/SOURCES.md) | Data source compliance & ToS audit |
| [`MULTI_TENANT_DESIGN.md`](file:///Users/rishaadkhan/DevelopmentCoding/jobscrap/MULTI_TENANT_DESIGN.md) | SaaS scaling & multi-tenant reference architecture |
