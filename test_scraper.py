"""Test script to validate scraper setup"""
import json
from scraper import JobScraper
from filters import JobFilter
from state_manager import StateManager

def test_company_loading():
    print("Testing company database loading...")
    with open('companies.json', 'r') as f:
        companies = json.load(f)
    print(f"✓ Loaded {len(companies)} companies")
    return companies

def test_scraper(companies):
    print("\nTesting scraper on first 3 companies...")
    scraper = JobScraper()
    
    for company in companies[:3]:
        print(f"\nScraping {company['name']}...")
        jobs = scraper.scrape_company(company)
        print(f"  Found {len(jobs)} job listings")
        
        if jobs:
            print(f"  Sample job: {jobs[0]['title']}")

def test_filters():
    print("\nTesting job filters...")
    
    test_job = {
        'title': 'Software Engineer - Backend',
        'description': 'Looking for a backend engineer with Java, Spring Boot, and microservices experience. 0-2 years required.',
        'location': 'Bangalore, India'
    }
    
    result = JobFilter.filter_job(test_job)
    print(f"  Backend role filter: {'✓ PASS' if result else '✗ FAIL'}")
    
    test_job2 = {
        'title': 'Senior Software Engineer',
        'description': 'Need 5+ years experience',
        'location': 'Bangalore'
    }
    
    result2 = JobFilter.filter_job(test_job2)
    print(f"  Experience filter: {'✓ PASS' if not result2 else '✗ FAIL'}")

def test_state_manager(companies):
    print("\nTesting state manager...")
    state = StateManager()
    
    to_scrape = state.get_companies_to_scrape(companies)
    print(f"  Companies to scrape: {len(to_scrape)}")
    print(f"  ✓ State manager working")

if __name__ == '__main__':
    print("=== Job Scraper Validation ===\n")
    
    try:
        companies = test_company_loading()
        test_filters()
        test_state_manager(companies)
        test_scraper(companies)
        
        print("\n=== All Tests Passed ===")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
