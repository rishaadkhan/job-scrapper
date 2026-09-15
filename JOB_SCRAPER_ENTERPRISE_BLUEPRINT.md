# Job Scraper → Enterprise-Grade Product: Diagnosis & Execution Blueprint

> Companion doc to `CODEBASE_ANALYSIS_AND_IMPROVEMENT_SPEC.md`. That doc describes the *intended* architecture and known flaws. This doc is grounded in your actual `High_Conversion_Job_Leads_2026-09-12.xlsx` output — 9 rows, 422 companies scraped — and turns the gap between "intended" and "actual" into a phased build plan with session-sized prompts for Antigravity.

---

## 1. What Your Real Output Is Actually Telling You

I parsed the attached sheet directly. Every issue below is from a real row, not a hypothetical.

### 1.1 The role filter is not filtering roles
`is_backend_role()` let these through as "backend, 0–3 yrs" leads:
- **Systems Sales Engineer** (Nutanix)
- **Solutions Engineer, Workvivo (APJ)** (Zoom)
- **Revenue Event Marketing Lead** (Shopify)
- **Creative Ops & Studio Manager** (Paddle)

This confirms the doc's Bug #1 — `BACKEND_KEYWORDS` is imported but never checked, so anything that isn't `senior/lead/manager/architect/...` passes by default. Sales, marketing, and ops roles are leaking straight into your leads sheet.

### 1.2 The location filter is filtering on the wrong string
Rows tagged `Location: India` have job descriptions that plainly say:
- Nutanix row → **Vancouver, British Columbia**
- Zoom row → job title itself says **Singapore**
- Shopify row → **Remote - APAC, Singapore, Hong Kong**
- Paddle row → **Toronto, UK**
- Thought Machine rows (x2) → **Portugal, Lisbon**
- Remitly row → **Seattle, WA**

Every single non-India example is because the scraper is matching `India` against the *career portal search URL* (`career_url?location=India`), not the job's actual scraped location. The URL is templated with `India` regardless of what the site actually returns — so `is_valid_location()` is effectively a no-op. This is a more serious bug than what's documented; it means **none of your 9 leads are reliably India-based.**

### 1.3 Deduplication is broken by design, not just slow
"Data Engineer - Spark" at Chargebee appears **twice**, once under `Chargebee` and once under `Chargebee India`, ~20 minutes apart. Two compounding bugs:
- `companies.json` has near-duplicate entries (`Chargebee` / `Chargebee India`, likely `Nutanix` / `Nutanix India` too) that scrape the same listings twice.
- The `Job ID` field is the **full LinkedIn URL including `refId`/`trackingId` query params**, which are unique per page load. `state_manager`'s `seen_jobs` key is built from this URL, so the same job looks "new" every run and dedup silently fails.

### 1.4 Job titles are corrupted by missing whitespace on scrape
- `Revenue Event Marketing LeadRemote - APAC, Singapore, Hong Kong`
- `Application  Security Engineer Portugal, Lisbon`
- `Software EngineerPortugal, Lisbon`

Title and location DOM nodes are being concatenated without a separator on Ashby-based boards. This also explains why `is_valid_location` sometimes "works" — it's accidentally matching leftover location text stuck to the title.

### 1.5 The job description column is mostly not a job description
- Two Ashby-based postings returned **`"You need to enable JavaScript to run this app."`** — the exact SPA failure mode in doc §4, Flaw #2, happening live.
- One Remitly row returned **`"Page not found"`** — a dead link was scraped and stored as a valid lead instead of being discarded.
- The one row with real content (Chargebee, via LinkedIn) is full of UI chrome: `Apply`, `Save`, `Report this job`, `Over 200 applicants`, `Use AI to assess how you fit` — not clean JD text, and it's truncated mid-sentence at the 5000-char cap.

### 1.6 An undocumented data source is in play
Two of your nine rows have `Job ID` / `Official Apply Link` pointing at `in.linkedin.com`, not a company career page. Nothing in the architecture doc mentions LinkedIn as a source. Two things follow from this:
- If this is intentional (a fallback when a career page yields nothing), it needs to be an explicit, documented pipeline step — right now it looks like an unmanaged code path.
- **LinkedIn's Terms of Service explicitly prohibit automated scraping of the site.** This is worth resolving deliberately before you build more on top of it, especially if there's any future where this becomes a product other people run — see §4.

### 1.7 Net yield
422 companies → 9 rows → of those, roughly **0 are clean, verifiably-India, verifiably-backend, non-duplicate leads** once you correct for 1.1–1.4. The pipeline currently produces work for you to manually re-filter, which is the opposite of its purpose.

### 1.8 What's structurally missing (not a bug, a gap)
- No relevance/match score against your actual resume.
- No keyword-frequency or "what this JD emphasizes" analysis.
- No resume bullet suggestions.
- No `Posted Date` (always `None` — never populated, so you can't tell a live posting from a stale one).
- No visual usability: no freeze panes, no hyperlink formatting, no conditional highlighting for strong matches — every run produces a flat data dump you have to work to read.

---

## 2. Distribution Decision: Web App, Not a Browser Extension

You asked directly, so a direct answer:

**Build this as a web application (dashboard + backend API), not a browser extension.** Keep the scraping/scoring as a scheduled backend job (what you already have via GitHub Actions, or a small always-on worker later).

Why an extension is the wrong primary vehicle here:
- Your core value is **unattended, scheduled scraping across 400+ sites**. That's a server-side/cron workload. A browser extension only runs in a browser the user has open, can't reliably wake itself on a schedule (Manifest V3 service workers are event-driven and get suspended), and can't scrape sites the user isn't actively visiting.
- The frontend you're describing — manage companies, edit filters, browse/download/delete extracts, auth — is exactly a dashboard-over-REST-API shape. That's a standard SPA + backend, not extension territory.
- Distribution and iteration are simpler for a web app: no browser store review cycles, no per-browser manifest differences, instant updates, and a much more natural path to a subscription SaaS if you productize.
- Chrome extensions also generally require broad host permissions to be useful, which is a harder sell for user trust than a web app that only ever talks to your own backend.

Where a browser extension *could* earn a place — later, as a companion, not the core product — is a "quick-apply assistant" that reads your dashboard's tailored bullets and autofills an application form while you're on a specific job page. That's a nice-to-have for Phase 5+, not the foundation.

**Recommended shape:** Python backend (FastAPI) + scheduled worker for scraping/scoring + a small React (or plain HTML/Tailwind) dashboard, backed by a real database instead of committing Excel files to git.

---

## 3. Target Architecture (Enterprise-Lite, Right-Sized for a Solo-Founder Tool)

```
                    ┌────────────────────────────┐
                    │   Scheduler (cron / GH      │
                    │   Actions / worker queue)    │
                    └──────────────┬───────────────┘
                                   ▼
                    ┌────────────────────────────┐
                    │   Ingestion Layer            │
                    │   ATS API clients            │
                    │   (Greenhouse, Lever, Ashby,│
                    │   SmartRecruiters, Workday   │
                    │   CXS) + Playwright fallback │
                    │   pool for pure-SPA sites    │
                    └──────────────┬───────────────┘
                                   ▼
                    ┌────────────────────────────┐
                    │   Normalization &            │
                    │   Filtering Layer            │
                    │   - role match (positive)    │
                    │   - true location extraction │
                    │   - experience parsing        │
                    │   - stable job_id derivation  │
                    └──────────────┬───────────────┘
                                   ▼
                    ┌────────────────────────────┐
                    │   Relevance & Resume         │
                    │   Intelligence Layer         │
                    │   - keyword frequency / TF-IDF│
                    │   - match score vs. resume   │
                    │   - tailored bullet suggestions│
                    └──────────────┬───────────────┘
                                   ▼
                    ┌────────────────────────────┐
                    │   Persistence Layer          │
                    │   SQLite → Postgres/Supabase │
                    │   (companies, jobs, runs,    │
                    │   filters, users)             │
                    └──────────────┬───────────────┘
                         ▼                    ▼
           ┌────────────────────┐   ┌────────────────────┐
           │  Export Service     │   │  Backend API        │
           │  (xlsx generation,  │   │  (FastAPI, auth,     │
           │  retention/purge)   │   │  CRUD, RBAC)          │
           └────────────────────┘   └──────────┬───────────┘
                                                ▼
                                    ┌────────────────────┐
                                    │  Web Dashboard        │
                                    │  (companies, filters,  │
                                    │  extracts, downloads)  │
                                    └────────────────────┘
```

Cross-cutting concerns to bake in from Phase 0 onward: structured logging, centralized exception handling with typed error categories (network, parsing, rate-limit, auth), retries with exponential backoff, secrets via environment/GitHub Secrets (never hardcoded), and input validation (Pydantic models) at every boundary.

---

## 4. Redesigned Excel Output — Target Schema

| Column | Notes |
|---|---|
| Company Name | deduped against canonical company list |
| Company Type | unchanged |
| Job Title | cleaned — title/location split fixed |
| **Match Score** | new — 0–100, resume vs. JD keyword overlap |
| Experience Range | unchanged, parser hardened |
| Location (parsed) | new logic — from actual JD/ATS field, not URL |
| **Top JD Keywords** | new — top 8–10 frequent/emphasized skills & tools |
| **Missing From Resume** | new — keywords in JD not found in your resume |
| **Suggested Bullet Edits** | new — 2–3 tailored bullet rewrites per job |
| Job ID | stable, tracking-param-stripped or hash-derived |
| Posted Date | actually populated from ATS metadata where available |
| Official Apply Link | unchanged |
| Career Portal URL | unchanged |
| Full Job Description | clean text, no UI chrome, no truncation mid-sentence |
| Scraped Timestamp | unchanged |

Formatting: frozen header row, hyperlinked URLs, conditional formatting on `Match Score` (e.g. green ≥ 70), auto-filter enabled, column widths sane.

---

## 5. Security, Compliance & Legal Notes (don't skip this)

- **LinkedIn sourcing**: resolve deliberately. Either remove it entirely and rely on ATS APIs + official career pages, or, if you keep it, treat it as a known ToS risk you're consciously accepting for personal use only — don't carry it into anything you distribute to other users.
- **Secrets**: any API keys (Anthropic, cloud storage, Telegram bot tokens) go in environment variables / GitHub Actions secrets, never in `companies.json` or committed files.
- **Auth**: even for a single-user tool, don't skip real auth (hashed passwords or OAuth, signed sessions/JWT) if the dashboard will ever be reachable outside `localhost` — you're literally about to expose "delete my extracts" and "edit my scrape targets" over HTTP.
- **Rate limiting & backoff**: per-domain concurrency caps and exponential backoff on 429/5xx, so you don't get IP-banned from career sites you actually care about.
- **Retention**: auto-purge > 14 days should be a scheduled job with a dry-run/log mode first, not an unconditional delete on day one.
- **If this becomes a product**: each ATS's own terms (Greenhouse, Lever, Ashby, SmartRecruiters, Workday) generally tolerate their own public JSON endpoints far better than scraping third-party sites like LinkedIn — lean entirely on official APIs before onboarding other users.

---

## 6. Phase-Wise Roadmap

Each phase below is sized to be **one focused Antigravity session** — enough context and scope to make real progress, not so much that the agent drowns in ambiguity. Paste the prompt as-is, with both this file and `CODEBASE_ANALYSIS_AND_IMPROVEMENT_SPEC.md` attached/referenced, and your actual repo open.

### Phase 0 — Stop the Bleeding (correctness fixes, no architecture change)
**Goal:** the pipeline stops producing false leads, without touching the overall design yet.

```
Context: I'm attaching CODEBASE_ANALYSIS_AND_IMPROVEMENT_SPEC.md (architecture) and
JOB_SCRAPER_ENTERPRISE_BLUEPRINT.md (diagnosis section 1) for this repo. Section 1
lists concrete bugs found in a real output file — use it as your bug list, not just
the abstract description in the architecture doc.

Task: Fix these five correctness bugs in the existing codebase WITHOUT changing the
overall architecture (no async, no ATS APIs yet — that's a later phase):

1. filters.py — is_backend_role() must positively require a BACKEND_KEYWORDS match
   in the title/JD, not just the absence of EXCLUDE_KEYWORDS.
2. filters.py — is_valid_location() must validate against the actual scraped job
   location field (from JD text or ATS metadata), never against the career_url
   query string. Add a disqualifying-location check (e.g. reject if the only
   location signal found is a known non-India city/country).
3. state_manager.py / scraper.py — derive a stable job_id: for LinkedIn/tracked
   URLs, strip all query parameters before dedup; add a fallback stable ID via a
   hash of (company + normalized title + first 500 chars of JD) when no clean ID
   exists. Write a unit test proving two scrapes of the same job with different
   tracking params dedupe to one entry.
4. scraper.py — fix title/location concatenation: ensure whitespace/separator
   between DOM text nodes when building job_title, and don't let scraped location
   text leak into the title field.
5. main.py / scraper.py — before accepting a job listing, validate the fetched
   page isn't a dead link or SPA shell: reject descriptions that are empty, under
   ~50 chars, contain "Page not found", or contain "enable JavaScript" — log these
   as skipped-with-reason rather than silently dropping them.

Also: deduplicate companies.json — merge near-duplicate entries like "Chargebee" /
"Chargebee India" into one canonical entry with a location_filter list, instead of
two separate company records.

Deliverable: updated filters.py, scraper.py, state_manager.py, companies.json, plus
a short tests/ file covering each fix, and a CHANGELOG entry summarizing what changed
and why (cite the specific bad row from the sample output as justification per fix).
Do not modify exporter.py or the Excel schema in this session.
```

### Phase 1 — ATS-Native Ingestion Engine
```
Context: attaching CODEBASE_ANALYSIS_AND_IMPROVEMENT_SPEC.md §4 (Flaw #2/#3) and
§6 (target companies.json schema). Phase 0 fixes are already merged.

Task: Replace HTML scraping with direct ATS JSON APIs for the four platforms with
public APIs, and add a Workday CXS client:
- Greenhouse: https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true
- Lever: https://api.lever.co/v0/postings/{company}?mode=json
- Ashby: https://api.ashbyhq.com/posting-api/job-board/{organization}
- SmartRecruiters: https://api.smartrecruiters.com/v1/companies/{company}/postings
- Workday: POST to /wday/cxs/{tenant}/{site}/jobs (inspect a real Workday board's
  network requests to confirm the payload shape before implementing)

Upgrade companies.json to the schema in the architecture doc §6 (add `ats`,
`ats_token`/`ats_id` fields) and migrate at least the top 100 companies by likely
ATS platform. For companies without a known public API, keep the existing HTML
fallback but mark them `ats: "html_fallback"` so we know which yield is
API-sourced (reliable) vs scraped (best-effort).

Refactor the ingestion loop to asyncio + httpx.AsyncClient with a concurrency
semaphore (max 10 concurrent) and per-domain rate limiting + exponential backoff
retry on 429/5xx. Keep state_manager's dedup/persistence logic intact and
compatible.

Explicitly remove the LinkedIn scraping code path (see blueprint §1.6 / §5) —
replace any LinkedIn-sourced fallback with either a real company career-page
fallback or an explicit "no listing found" skip, and log which companies had zero
sources available so we know where to add manual coverage.

Deliverable: an ats_clients/ module (one file per platform), updated main.py using
async orchestration, updated companies.json, and a before/after yield comparison
(companies with 0 jobs found, before vs after) logged to console at end of run.
```

### Phase 2 — Relevance Scoring & Resume Intelligence
```
Context: attaching JOB_SCRAPER_ENTERPRISE_BLUEPRINT.md §4 (target Excel schema).
Phases 0–1 are merged; job descriptions are now clean, API-sourced text.

Task: Add a scoring/intelligence module that runs after filtering, before export:

1. Keyword extraction: build a curated backend-engineering skills taxonomy
   (languages, frameworks, cloud, databases, practices) plus a general
   frequency/TF-IDF pass over the JD text, and output the top 8-10 emphasized
   keywords per job.
2. Resume input: accept a resume as a local text/markdown file (config-driven
   path, not hardcoded) containing my skills/experience. Extract my current
   keyword set from it once per run.
3. Match Score: compute a 0-100 score per job from keyword overlap
   (resume keywords ∩ JD keywords, weighted by JD emphasis/frequency).
4. Missing-from-resume: list JD keywords with no resume match.
5. Suggested bullet edits: for jobs scoring above a configurable threshold, call
   the Anthropic API (model configurable, key from environment variable) with the
   resume text + JD text to generate 2-3 tailored bullet-point rewrites
   emphasizing the missing/matched keywords. Handle API failures gracefully
   (skip suggestion, log, continue the run — never crash the whole pipeline over
   one failed LLM call).

Update exporter.py to the schema in blueprint §4: add Match Score, Top JD
Keywords, Missing From Resume, Suggested Bullet Edits columns, freeze the header
row, autofilter, hyperlink the URL columns, and conditional-format Match Score
(e.g. green >= 70, yellow 40-69, red < 40).

Deliverable: a scoring/ module, updated exporter.py, a sample resume.md format
documented in README, and a run against real scraped output showing the new
columns populated.
```

### Phase 3 — Backend Service Layer & Storage Migration
```
Context: attaching CODEBASE_ANALYSIS_AND_IMPROVEMENT_SPEC.md §4 Flaw #5 (git
bloat from committed Excel binaries) and blueprint §3 (target architecture) and
§5 (security notes). Phases 0-2 are merged.

Task: Migrate persistence off git-committed files onto a real database, and stand
up a backend API:

1. Replace scraper_state.json + git-committed xlsx files with SQLite (design for
   an easy swap to Postgres/Supabase later) — tables: companies, jobs, scrape_runs,
   filters, users. Write a one-time migration script that imports existing
   scraper_state.json history into the new schema.
2. Build a FastAPI service exposing: GET/POST/PUT/DELETE /companies,
   GET/PUT /filters, GET /jobs (with query params: date range, min match score,
   company), GET /runs, POST /export (triggers xlsx generation from DB, returns a
   download link), DELETE /exports/{id}.
3. Add JWT-based auth (single admin user is fine for now, but design the users
   table and auth middleware so it's not a rewrite to add more users later).
4. Add centralized exception handling (typed exceptions: ScrapeError,
   ParseError, RateLimitError, AuthError), structured JSON logging, and Pydantic
   request/response validation on every endpoint.
5. Move all secrets (Anthropic API key, DB credentials, JWT secret) to
   environment variables with a documented .env.example — never committed.

Deliverable: backend/ FastAPI app, migration script, updated GitHub Actions
workflow to call the scraper against the new DB instead of committing files,
and API docs (FastAPI's auto-generated OpenAPI is sufficient).
```

### Phase 4 — Web Dashboard
```
Context: attaching blueprint §2 (why web app, not extension) and §3
(architecture). Phase 3's backend API is live and documented via OpenAPI.

Task: Build a web dashboard (React + a simple component library, or plain
HTML/Tailwind if you want to keep it lighter) that consumes the Phase 3 API:

1. Login page (JWT auth against the backend).
2. Companies view: list/add/edit/deactivate companies, edit their ATS
   type/token, see dedup warnings for near-identical names.
3. Filters view: edit backend keyword lists, exclude keywords, experience
   range, and location rules — without redeploying code.
4. Extracts view: list past daily runs with row counts and average match
   score, download any extract as xlsx, delete an extract.
5. Retention: a scheduled backend job that auto-deletes extracts older than a
   configurable retention window (default 14 days), with a dry-run mode and a
   log of what was deleted and when.
6. Basic RBAC scaffold even if there's only one role today (admin) — so adding
   a "viewer" role later doesn't require restructuring auth.

Deliverable: frontend/ app talking to the Phase 3 API, deployed locally via a
documented `npm run dev` (or equivalent), plus a short README covering how to
run the full stack (backend + scheduler + frontend) locally.
```

### Phase 5 — Productization & Distribution
```
Context: attaching blueprint §2 (distribution decision), §5 (compliance notes).
Phases 0-4 are complete and working for personal use.

Task: Prepare the tool for possible distribution beyond yourself:

1. Containerize the backend + scheduler (Dockerfile + docker-compose for
   local/staging), and document a deployment target (e.g. Railway/Render/Fly.io
   or a small VPS) with CI/CD via GitHub Actions (build, test, deploy on merge
   to main).
2. Add a daily digest notifier (Telegram bot or email) summarizing top N
   matches above a score threshold, sent after each scrape run.
3. Add observability: error tracking (e.g. Sentry) for both the scraper and API,
   and a simple uptime/heartbeat check on the scheduled job so a silent failure
   doesn't go unnoticed for days.
4. Run a compliance pass: confirm every active data source is either an official
   ATS API or a company's own career page (no LinkedIn or other ToS-restricted
   sources), and document this in a SOURCES.md.
5. If pursuing multi-tenant SaaS later: sketch (don't fully build yet) what
   changes — per-user resume storage & isolation, a companies/filters template
   vs. per-user overrides, and a billing hook (e.g. Stripe) — as a design doc,
   not code, so Phase 6 has a clear starting point.

Deliverable: Dockerfile, docker-compose.yml, deploy workflow, notifier module,
SOURCES.md, and a short MULTI_TENANT_DESIGN.md sketch for future work.
```

---

## 7. Suggested Sequencing

Run Phase 0 first regardless of anything else — every later phase inherits its bugs otherwise. Phases 1–2 can be combined into a slightly longer session if you're comfortable with a bigger scope; Phases 3–4 are naturally sequential (no frontend without an API). Phase 5 is the only phase that's genuinely optional if you decide to keep this as a personal tool.
