"""Import companies from CSV file"""
import json
import csv
import sys

def import_from_csv(csv_file):
    """Import companies from CSV file"""
    
    # Load existing companies
    try:
        with open('companies.json', 'r') as f:
            companies = json.load(f)
    except FileNotFoundError:
        companies = []
    
    existing_names = {c['name'].lower() for c in companies}
    
    # Read CSV and add new companies
    new_companies = []
    duplicates = 0
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['name'].strip()
            if name.lower() not in existing_names:
                new_companies.append({
                    'name': name,
                    'type': row['type'].strip(),
                    'career_url': row['career_url'].strip()
                })
                existing_names.add(name.lower())
            else:
                duplicates += 1
    
    # Add new companies
    companies.extend(new_companies)
    
    # Save updated list
    with open('companies.json', 'w') as f:
        json.dump(companies, f, indent=2)
    
    print(f"✓ Import complete!")
    print(f"  - New companies added: {len(new_companies)}")
    print(f"  - Duplicates skipped: {duplicates}")
    print(f"  - Total companies: {len(companies)}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python import_csv.py <csv_file>")
        print("\nCSV format:")
        print("name,type,career_url")
        print("Company Name,Tier-1 GCC,https://...")
        sys.exit(1)
    
    import_from_csv(sys.argv[1])
