"""Main orchestrator for job scraping system"""
import json
from datetime import datetime
from scraper import JobScraper
from filters import JobFilter
from state_manager import StateManager
from exporter import ExcelExporter

def load_companies():
    with open('companies.json', 'r') as f:
        return json.load(f)

def main():
    print("=== Job Scraper Started ===")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Initialize components
    state_manager = StateManager()
    scraper = JobScraper()
    exporter = ExcelExporter()
    
    # Load and select companies
    all_companies = load_companies()
    companies_to_scrape = state_manager.get_companies_to_scrape(all_companies)
    
    print(f"Total companies in database: {len(all_companies)}")
    print(f"Companies to scrape today: {len(companies_to_scrape)}\n")
    
    all_jobs = []
    
    for idx, company in enumerate(companies_to_scrape, 1):
        print(f"[{idx}/{len(companies_to_scrape)}] Scraping {company['name']}...")
        
        jobs = scraper.scrape_company(company)
        print(f"  Found {len(jobs)} job listings")
        
        valid_jobs = []
        for job in jobs:
            # Fetch full description
            if job['link']:
                job['description'] = scraper.fetch_job_description(job['link'])
            
            # Apply filters
            if JobFilter.filter_job(job):
                job_id = f"{company['name']}_{job['job_id']}"
                
                if not state_manager.is_job_seen(job_id):
                    job['scraped_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    valid_jobs.append(job)
                    state_manager.mark_job_seen(job_id, company['name'])
        
        print(f"  Valid backend jobs: {len(valid_jobs)}")
        all_jobs.extend(valid_jobs)
        
        state_manager.mark_company_scraped(company['name'], len(valid_jobs))
    
    # Cleanup old job records
    state_manager.cleanup_old_jobs()
    state_manager.save_state()
    
    print(f"\n=== Scraping Complete ===")
    print(f"Total valid jobs found: {len(all_jobs)}")
    
    # Export to Excel
    if all_jobs:
        filepath = exporter.export_jobs(all_jobs)
        print(f"\nExcel file generated: {filepath}")
    else:
        print("\nNo jobs to export")

if __name__ == '__main__':
    main()
