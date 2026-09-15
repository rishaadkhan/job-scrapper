# Automated Test Suite Verification Report

## 🧪 Test Execution Summary

- **Total Test Cases**: 30
- **Passing Tests**: 30 (100%)
- **Failing / Errors**: 0 (0%)
- **Execution Time**: ~0.16 seconds
- **Test Framework**: Python Standard Library `unittest` / `pytest`

---

## 📋 Detailed Test Module Breakdown

### 1. `tests/test_ats_clients.py` (5 Tests)
- `test_greenhouse_parsing`: Verifies parsing of Greenhouse public board JSON payloads into normalized job schemas.
- `test_lever_parsing`: Verifies parsing of Lever JSON postings with category and commitment data.
- `test_ashby_parsing`: Verifies parsing of Ashby job board postings.
- `test_smartrecruiters_parsing`: Verifies parsing of SmartRecruiters postings and section breakdown.
- `test_workday_payload`: Verifies payload shape and response parsing for Workday CXS candidate endpoints.

### 2. `tests/test_scoring.py` (6 Tests)
- `test_taxonomy_matching`: Verifies extraction of canonical skills against the 150+ skill ontology.
- `test_prominence_weighting`: Verifies title and requirements section boosting in TF-IDF keyword extraction.
- `test_resume_matcher_score`: Verifies 0–100 candidate score calculation based on resume keyword intersection.
- `test_missing_skills_identification`: Verifies accurate reporting of required technologies absent from resume.
- `test_claude_bullet_generator`: Verifies prompt construction and Anthropic Claude response handling (with mock fallback).
- `test_threshold_triggering`: Ensures bullet generation is triggered only for scores meeting `LLM_SUGGESTION_THRESHOLD`.

### 3. `tests/test_backend_api.py` (11 Tests)
- `test_jwt_login_success_and_failure`: Validates authentication and JWT token generation.
- `test_companies_crud`: Validates `GET`, `POST`, `PUT`, `DELETE` operations on `/companies`.
- `test_duplicate_company_warning`: Validates fuzzy deduplication alerts on company creation.
- `test_filters_dynamic_update`: Validates dynamic configuration updates on `/filters`.
- `test_jobs_query_and_pagination`: Validates job queries with score, location, and company filtering.
- `test_runs_telemetry_endpoint`: Validates ingestion of run metrics on `/runs`.
- `test_export_generation_and_delete`: Validates on-demand Excel spreadsheet generation and deletion.
- `test_retention_policy_worker`: Validates auto-deletion of scrape runs older than retention window.

### 4. `tests/test_fixes.py` (8 Tests)
- `test_backend_role_positive_match`: Ensures non-engineering titles without backend keywords are rejected.
- `test_india_location_validation`: Ensures foreign cities are disqualified and India tech hubs are accepted.
- `test_experience_years_parsing`: Ensures candidates with >3 years experience requirements are filtered out.
- `test_tracking_stripped_job_id`: Ensures URLs with tracking query parameters produce identical stable job IDs.
- `test_openpyxl_15_column_schema`: Verifies all 15 columns, auto-filters, frozen panes, and conditional formatting.

---

## 🏃 Command to Run Test Suite
```bash
source venv/bin/activate
python -m unittest discover tests
```
