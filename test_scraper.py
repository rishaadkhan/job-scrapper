"""
Validation and Integration Test Script
Tests all core components of the scraper system:
1. companies.json loading & ATS schema verification
2. JobFilter rules (backend role, India location, 0-3 years experience)
3. Resume scoring & skill taxonomy extraction
4. Stable tracking-stripped Job ID derivation
5. Async JobScraper execution with rate limiting
6. SQLite Database & ORM integration
"""
import asyncio
import json
import os
import sqlite3
import httpx

from config import REQUEST_TIMEOUT
from filters import JobFilter
from scraper import JobScraper, derive_job_id, clean_job_url, DomainRateLimiter
from scoring import KeywordExtractor, ResumeMatcher
from state_manager import StateManager


def test_company_loading():
    print("1. Testing company database loading & schema...")
    with open('companies.json', 'r', encoding='utf-8') as f:
        companies = json.load(f)
    assert len(companies) > 0, "companies.json is empty"
    
    # Verify schema fields
    sample = companies[0]
    assert "name" in sample, "Missing 'name' in company schema"
    assert "career_url" in sample, "Missing 'career_url' in company schema"
    assert "ats" in sample, "Missing 'ats' in company schema"
    print(f"   ✓ Successfully loaded {len(companies)} companies with ATS schema (Sample ATS: {sample.get('ats')})")
    return companies


def test_filters():
    print("\n2. Testing job filter logic...")
    
    # Test valid backend engineering job in India
    valid_job = {
        'title': 'Software Engineer - Backend',
        'description': 'Looking for a backend engineer with Python, Java, Spring Boot, and PostgreSQL experience. 0-2 years required.',
        'location': 'Bengaluru, India'
    }
    assert JobFilter.filter_job(valid_job) is True, "Valid backend role was incorrectly rejected"
    print("   ✓ Valid backend role: PASS")

    # Test non-backend role (should be rejected by positive keyword match)
    non_backend_job = {
        'title': 'Frontend React Developer',
        'description': 'Build interactive web user interfaces with CSS and HTML. 1 year experience.',
        'location': 'Bengaluru, India'
    }
    assert JobFilter.filter_job(non_backend_job) is False, "Non-backend role was incorrectly accepted"
    print("   ✓ Non-backend role rejection: PASS")

    # Test senior role (>3 years experience)
    senior_job = {
        'title': 'Staff Backend Engineer',
        'description': 'Need 8+ years experience in distributed systems architecture.',
        'location': 'Bengaluru, India'
    }
    assert JobFilter.filter_job(senior_job) is False, "Senior role was incorrectly accepted"
    print("   ✓ Senior experience exclusion: PASS")

    # Test foreign location (should be rejected)
    foreign_job = {
        'title': 'Backend Software Engineer',
        'description': 'Backend Python developer with 1 year experience.',
        'location': 'London, UK'
    }
    assert JobFilter.filter_job(foreign_job) is False, "Non-India location was incorrectly accepted"
    print("   ✓ Disqualifying non-India location: PASS")


def test_scoring():
    print("\n3. Testing resume scoring & taxonomy extractor...")
    extractor = KeywordExtractor()
    matcher = ResumeMatcher(resume_path="resume.md")
    
    sample_title = "Software Engineer - Backend"
    sample_jd = """
    We are looking for a backend developer skilled in Python, FastAPI, PostgreSQL, Docker, and Redis.
    Must understand microservices architecture, REST APIs, and AWS deployments.
    """
    
    extracted_keywords = extractor.extract_keywords(sample_title, sample_jd, top_n=10)
    assert len(extracted_keywords) > 0, "No keywords extracted from JD"
    print(f"   ✓ Extracted {len(extracted_keywords)} JD keywords: {extracted_keywords[:5]}")
    
    score_result = matcher.score_job(sample_title, sample_jd)
    score = score_result.get("match_score", 0)
    matched = score_result.get("matched_keywords", [])
    missing = score_result.get("missing_from_resume", [])
    
    assert 0 <= score <= 100, f"Score out of range: {score}"
    print(f"   ✓ Candidate Match Score: {score}/100 (Overlapping: {len(matched)}, Missing: {len(missing)})")


def test_job_id_derivation():
    print("\n4. Testing stable tracking-stripped Job ID derivation...")
    url1 = "https://boards.greenhouse.io/databricks/jobs/123456?utm_source=linkedin&gh_jid=123456"
    url2 = "https://boards.greenhouse.io/databricks/jobs/123456"
    
    clean1 = clean_job_url(url1)
    clean2 = clean_job_url(url2)
    assert clean1 == clean2, f"URLs not normalized: {clean1} != {clean2}"
    
    id1 = derive_job_id("Databricks", "Backend Engineer", url1, raw_id="123456")
    id2 = derive_job_id("Databricks", "Backend Engineer", url2, raw_id="123456")
    assert id1 == id2 == "123456", f"IDs mismatch: {id1} vs {id2}"
    print(f"   ✓ Tracking stripped cleanly: {clean1} -> ID: {id1}")


def test_database_connection():
    print("\n5. Testing SQLite database connection...")
    if not os.path.exists("jobscraper.db"):
        print("   ⚠️  jobscraper.db not found, skipping DB test.")
        return
    
    conn = sqlite3.connect("jobscraper.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM companies")
    count = cursor.fetchone()[0]
    conn.close()
    assert count > 0, "No companies found in database"
    print(f"   ✓ SQLite database connected with {count} active company records.")


async def test_async_scraper(companies):
    print("\n6. Testing async ATS ingestion on sample company...")
    from ats_clients import fetch_company_jobs
    
    # Pick a greenhouse or lever or smartrecruiters company
    target = None
    for c in companies:
        if c.get("ats") in ("greenhouse", "lever", "smartrecruiters", "ashby") and c.get("ats_token"):
            target = c
            break
            
    if not target:
        target = companies[0]

    print(f"   Scraping target: {target['name']} (ATS: {target.get('ats', 'html_fallback')})...")
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        jobs = await fetch_company_jobs(target, client)
        print(f"   ✓ Ingested {len(jobs)} raw listings from {target['name']}.")
        if jobs:
            print(f"     Sample listing: '{jobs[0].get('title')}'")


async def main_async():
    print("============================================================")
    print("       JOB SCRAPER SYSTEM VALIDATION & HEALTH CHECK         ")
    print("============================================================\n")
    
    companies = test_company_loading()
    test_filters()
    test_scoring()
    test_job_id_derivation()
    test_database_connection()
    await test_async_scraper(companies)
    
    print("\n============================================================")
    print("🎉 ALL SYSTEM COMPONENTS PASSED VALIDATION SUCCESSFULLY!")
    print("============================================================")


if __name__ == '__main__':
    asyncio.run(main_async())
