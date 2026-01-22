"""Utility to validate company URLs are accessible"""
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def check_url(company):
    """Check if company career URL is accessible"""
    try:
        response = requests.head(company['career_url'], timeout=10, allow_redirects=True)
        status = response.status_code
        
        if status == 200:
            return company['name'], 'OK', status
        elif status in [301, 302, 307, 308]:
            return company['name'], 'REDIRECT', status
        else:
            return company['name'], 'ERROR', status
    except requests.exceptions.Timeout:
        return company['name'], 'TIMEOUT', None
    except requests.exceptions.RequestException as e:
        return company['name'], 'FAILED', str(e)[:50]

def validate_companies():
    """Validate all companies in database"""
    print("Loading companies...")
    with open('companies.json', 'r') as f:
        companies = json.load(f)
    
    print(f"Validating {len(companies)} companies...\n")
    
    results = {'ok': [], 'redirect': [], 'error': [], 'timeout': [], 'failed': []}
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_url, company): company for company in companies}
        
        for idx, future in enumerate(as_completed(futures), 1):
            name, status, code = future.result()
            
            if status == 'OK':
                results['ok'].append((name, code))
                print(f"[{idx}/{len(companies)}] ✓ {name}")
            elif status == 'REDIRECT':
                results['redirect'].append((name, code))
                print(f"[{idx}/{len(companies)}] ↪ {name} (redirect)")
            elif status == 'TIMEOUT':
                results['timeout'].append((name, code))
                print(f"[{idx}/{len(companies)}] ⏱ {name} (timeout)")
            elif status == 'ERROR':
                results['error'].append((name, code))
                print(f"[{idx}/{len(companies)}] ✗ {name} (HTTP {code})")
            else:
                results['failed'].append((name, code))
                print(f"[{idx}/{len(companies)}] ✗ {name} (failed)")
    
    # Summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    print(f"✓ OK:       {len(results['ok'])} ({len(results['ok'])/len(companies)*100:.1f}%)")
    print(f"↪ Redirect: {len(results['redirect'])} ({len(results['redirect'])/len(companies)*100:.1f}%)")
    print(f"⏱ Timeout:  {len(results['timeout'])} ({len(results['timeout'])/len(companies)*100:.1f}%)")
    print(f"✗ Error:    {len(results['error'])} ({len(results['error'])/len(companies)*100:.1f}%)")
    print(f"✗ Failed:   {len(results['failed'])} ({len(results['failed'])/len(companies)*100:.1f}%)")
    print("="*60)
    
    # Show problematic URLs
    if results['error'] or results['failed']:
        print("\nProblematic URLs:")
        for name, code in results['error'] + results['failed']:
            print(f"  - {name}: {code}")

if __name__ == '__main__':
    validate_companies()
