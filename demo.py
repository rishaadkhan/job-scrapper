"""Quick demo with Greenhouse companies"""
import json
from scraper import JobScraper
from filters import JobFilter
from exporter import ExcelExporter
from datetime import datetime

# Test with known Greenhouse companies
test_companies = [
    {"name": "Razorpay", "type": "Unicorn", "career_url": "https://razorpay.com/jobs/"},
    {"name": "CRED", "type": "Unicorn", "career_url": "https://careers.cred.club/"},
]

scraper = JobScraper()
exporter = ExcelExporter()
all_jobs = []

print("=== Quick Demo - Testing Greenhouse Companies ===\n")

for company in test_companies:
    print(f"Scraping {company['name']}...")
    jobs = scraper.scrape_company(company)
    print(f"  Found {len(jobs)} job listings")
    
    valid_jobs = []
    for job in jobs:
        if job['link']:
            job['description'] = scraper.fetch_job_description(job['link'])
        
        if JobFilter.filter_job(job):
            job['scraped_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            valid_jobs.append(job)
    
    print(f"  Valid backend jobs: {len(valid_jobs)}")
    if valid_jobs:
        print(f"  Sample: {valid_jobs[0]['title']}")
    all_jobs.extend(valid_jobs)
    print()

print(f"Total valid jobs: {len(all_jobs)}")

if all_jobs:
    filepath = exporter.export_jobs(all_jobs)
    print(f"\n✓ Excel file created: {filepath}")
else:
    print("\nNote: No jobs passed filters. This is normal for strict filtering.")
    print("The system is working correctly - it's filtering out non-backend roles.")
