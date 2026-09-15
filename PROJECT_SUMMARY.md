# Project Summary: Enterprise Job Scraper & Intelligence Engine

## 🎯 Executive Summary
An enterprise-grade, privacy-first platform that extracts and analyzes early-career backend engineering job opportunities across 590+ Tier-1 GCCs, Unicorns, and high-growth startups in India.

---

## 🏆 Key Milestones & Capabilities Delivered

| Phase | Milestone | Core Capabilities |
|---|---|---|
| **Phase 0** | **Correctness & Hygiene** | Positive backend keyword filter (`filters.py`), India location filter, tracking-stripped SHA-256 stable job IDs, 15-column OpenPyXL Excel schema. |
| **Phase 1** | **Direct ATS Ingestion** | Dedicated JSON clients for Greenhouse, Lever, Ashby, SmartRecruiters, Workday CXS + HTML fallback. Zero third-party scraping. |
| **Phase 2** | **AI Scoring & Intelligence** | Curated 150+ backend skills taxonomy, TF-IDF prominence ranking, 0–100 match score, missing skills gap analysis, Anthropic Claude resume bullet generator. |
| **Phase 3** | **Persistence & REST API** | SQLite/PostgreSQL schema, FastAPI backend with OpenAPI Swagger `/docs`, JWT auth, CRUD routers, automated retention cleanup job. |
| **Phase 4** | **React Web Dashboard** | Modern React 18 + Vite + TypeScript single-page app with Companies management, Dynamic Filters tuning, Jobs explorer, and Run metrics. |
| **Phase 5** | **Distribution & Observability** | Multi-stage Docker container, docker-compose orchestration, GitHub Actions CI/CD, Fly.io deployment, Sentry telemetry, Healthchecks.io heartbeat, Telegram/Email daily digest alerts, and ToS compliance audit (`SOURCES.md`). |

---

## 📈 Quality & Reliability Highlights
- **100% Automated Unit Test Pass Rate** (30 tests covering ATS parsing, scoring, REST API, filters, and persistence).
- **Sub-15s Async Execution** across hundreds of target companies with bounded concurrency (`asyncio.Semaphore(10)`).
- **Full ToS Compliance** — only official public ATS JSON endpoints or corporate career pages are queried.
