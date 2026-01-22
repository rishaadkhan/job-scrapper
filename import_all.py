"""Master script to import all company expansion files"""
import json
import csv
import glob

def import_all_expansions():
    """Import all expansion CSV files"""
    
    # Load existing companies
    try:
        with open('companies.json', 'r') as f:
            companies = json.load(f)
    except FileNotFoundError:
        companies = []
    
    print(f"Starting with {len(companies)} companies\n")
    
    existing_names = {c['name'].lower() for c in companies}
    
    # Find all expansion CSV files
    csv_files = glob.glob('companies_expansion_part*.csv')
    
    if not csv_files:
        print("No expansion files found!")
        print("Looking for: companies_expansion_part*.csv")
        return
    
    total_new = 0
    total_duplicates = 0
    
    # Import each CSV file
    for csv_file in sorted(csv_files):
        print(f"Importing {csv_file}...")
        
        new_count = 0
        dup_count = 0
        
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row['name'].strip()
                if name.lower() not in existing_names:
                    companies.append({
                        'name': name,
                        'type': row['type'].strip(),
                        'career_url': row['career_url'].strip()
                    })
                    existing_names.add(name.lower())
                    new_count += 1
                else:
                    dup_count += 1
        
        print(f"  ✓ Added {new_count} companies, skipped {dup_count} duplicates\n")
        total_new += new_count
        total_duplicates += dup_count
    
    # Save updated list
    with open('companies.json', 'w') as f:
        json.dump(companies, f, indent=2)
    
    print("="*60)
    print("✓ IMPORT COMPLETE!")
    print("="*60)
    print(f"New companies added: {total_new}")
    print(f"Duplicates skipped: {total_duplicates}")
    print(f"Total companies: {len(companies)}")
    print("="*60)

if __name__ == '__main__':
    import_all_expansions()
