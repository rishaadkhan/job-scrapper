# Enterprise Company Management & Ingestion Guide

This comprehensive guide explains how to add, manage, and verify target companies in the **Enterprise Job Scraper & Resume Intelligence Engine**.

---

## 🎯 Target Company Schema Specification

Each company in `companies.json` and the SQLite database (`jobscraper.db`) conforms to the following schema:

```json
{
  "name": "Databricks",
  "type": "Tier-1 GCC",
  "career_url": "https://boards.greenhouse.io/databricks",
  "ats": "greenhouse",
  "ats_token": "databricks",
  "ats_id": null,
  "location_filter": [
    "India",
    "Bengaluru",
    "Bangalore",
    "Hyderabad",
    "Pune",
    "Mumbai",
    "Remote"
  ],
  "active": true
}
```

### Schema Field Definitions:
| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Unique company name (e.g. `"Stripe"`, `"Razorpay"`) |
| `type` | string | Yes | Category (`"Tier-1 GCC"`, `"Unicorn"`, `"High-Paying Startup"`, `"MNC"`) |
| `career_url` | string | Yes | Canonical career portal URL |
| `ats` | string | Yes | ATS platform: `"greenhouse"`, `"lever"`, `"ashby"`, `"smartrecruiters"`, `"workday"`, or `"html_fallback"` |
| `ats_token` | string | Optional | ATS board token, organization slug, or company ID |
| `ats_id` | string | Optional | Workday career site ID (e.g. `"Snowflake_Careers"`) |
| `location_filter` | list[str] | Optional | Allowed India cities and location keywords |
| `active` | boolean | Optional | Whether this company should be included in daily scrape runs (default: `true`) |

---

## 🚀 5 Ways to Add & Manage Companies

---

### Method 1: Via Modern React Web Dashboard (Recommended for UI)

1. Open the Web Dashboard at [http://localhost:5173](http://localhost:5173) (or `npm run dev` in `frontend/`).
2. Log in with admin credentials (`admin@jobscraper.io` / `admin123`).
3. Navigate to the **Companies** view in the sidebar.
4. Click **+ Add Company** button in the top right.
5. Fill in the company details:
   - **Company Name**: e.g., `Ramp`
   - **Category**: `Unicorn`
   - **Career Portal URL**: `https://jobs.ashbyhq.com/ramp`
   - **ATS Platform**: Select `ashby` (or let it auto-detect)
   - **ATS Token**: `ramp`
6. The dashboard will automatically perform real-time **duplicate name detection** to alert you if a similar company already exists.
7. Click **Save Company**. The company is instantly saved to the database.

---

### Method 2: Via FastAPI REST API (Recommended for Automation)

Interactive Swagger UI is available at [http://localhost:8000/docs](http://localhost:8000/docs).

#### cURL Example:
```bash
# 1. Obtain JWT Bearer Token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@jobscraper.io&password=admin123" | jq -r .access_token)

# 2. Add Company via POST /companies
curl -X POST http://localhost:8000/companies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Postman",
    "company_type": "Unicorn",
    "career_url": "https://jobs.lever.co/postman",
    "ats": "lever",
    "ats_token": "postman",
    "active": true
  }'
```

---

### Method 3: Via CSV Bulk Import (`import_csv.py`)

You can create or export a CSV file and import hundreds of companies in bulk with automated ATS detection and deduplication.

#### Step 1: Create your CSV file (`my_companies.csv`):
```csv
name,type,career_url,ats,ats_token
Databricks,Tier-1 GCC,https://boards.greenhouse.io/databricks,greenhouse,databricks
Postman,Unicorn,https://jobs.lever.co/postman,lever,postman
Linear,Unicorn,https://jobs.ashbyhq.com/linear,ashby,linear
CRED,Unicorn,https://careers.cred.club/,html_fallback,
```

*(Note: If `ats` and `ats_token` columns are omitted, `import_csv.py` will automatically inspect the URL and detect the ATS platform).*

#### Step 2: Run the import command:
```bash
python import_csv.py my_companies.csv
```

This will automatically:
- Deduplicate against existing companies.
- Validate and normalize schemas.
- Atomically update `companies.json`.
- Synchronize all records to SQLite (`jobscraper.db`).

---

### Method 4: Via Python Expansion Script (`expand_companies.py`)

1. Open `expand_companies.py`.
2. Add your target entries to the `ADDITIONAL_COMPANIES` list:
```python
ADDITIONAL_COMPANIES = [
    {
        "name": "Vercel",
        "type": "Unicorn",
        "career_url": "https://jobs.ashbyhq.com/vercel",
        "ats": "ashby",
        "ats_token": "vercel"
    }
]
```
3. Run the script:
```bash
python expand_companies.py
```

---

### Method 5: Direct JSON Editing (`companies.json`)

You can edit `companies.json` directly with any standard text editor.
After editing, validate JSON integrity and sync to the database:
```bash
# Validate JSON syntax
python -c "import json; json.load(open('companies.json')); print('✓ Valid JSON')"

# Sync to SQLite
python -m backend.migrate
```

---

## 🔍 How to Identify ATS Platforms and Tokens

| ATS Platform | Example Career URL | Detected `ats` | `ats_token` | `ats_id` |
|---|---|---|---|---|
| **Greenhouse** | `https://boards.greenhouse.io/stripe` | `greenhouse` | `stripe` | `null` |
| **Lever** | `https://jobs.lever.co/postman` | `lever` | `postman` | `null` |
| **Ashby** | `https://jobs.ashbyhq.com/ramp` | `ashby` | `ramp` | `null` |
| **SmartRecruiters**| `https://jobs.smartrecruiters.com/Uber` | `smartrecruiters` | `Uber` | `null` |
| **Workday** | `https://snowflake.wd5.myworkdayjobs.com/Snowflake_Careers` | `workday` | `snowflake` | `Snowflake_Careers` |
| **Custom Portal** | `https://company.com/careers` | `html_fallback` | `null` | `null` |

---

## 🧪 Validating Company URLs and ATS Endpoints

After adding new companies, run the asynchronous URL validator to verify that all endpoints are responsive and healthy:

```bash
python validate_urls.py
```

To validate a quick sample (e.g., first 20 companies):
```bash
python validate_urls.py --limit 20
```

---

## 📊 Summary of Current Database

- **Total Companies Tracked**: 590+
- **Direct ATS Ingestion**: Greenhouse, Lever, Ashby, SmartRecruiters, Workday CXS
- **Fallback Support**: Async HTML parser with rate limiting and exponential backoff
