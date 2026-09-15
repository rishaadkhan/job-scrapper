"""
CSV Company Import Utility
Imports companies from CSV files into companies.json and jobscraper.db,
with automatic ATS platform detection, deduplication, schema validation, and atomic writes.
"""
import os
import csv
import sys
import json
import argparse
from typing import Dict, Any, List
from expand_companies import detect_ats, normalize_company, sync_to_sqlite, DEFAULT_LOCATIONS


def import_companies_from_csv(csv_path: str, companies_file: str = "companies.json", sync_db: bool = True) -> Dict[str, int]:
    """
    Reads a CSV file and merges its companies into companies.json and SQLite.
    Supports CSV formats with columns:
    - name,type,career_url
    - name,type,career_url,ats,ats_token,ats_id
    """
    if not os.path.exists(csv_path):
        print(f"Error: CSV file '{csv_path}' not found.")
        return {"added": 0, "updated": 0, "duplicates": 0, "total": 0}

    # 1. Load existing companies
    if os.path.exists(companies_file):
        with open(companies_file, "r", encoding="utf-8") as f:
            companies = json.load(f)
    else:
        companies = []

    existing_names = {c["name"].strip().lower(): idx for idx, c in enumerate(companies)}
    added = 0
    updated = 0
    duplicates = 0

    # 2. Read CSV entries
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            print("Error: Empty CSV or invalid header.")
            return {"added": 0, "updated": 0, "duplicates": 0, "total": len(companies)}

        # Normalize field names to lowercase
        header_map = {k.strip().lower(): k for k in reader.fieldnames if k}

        for row in reader:
            name = (row.get(header_map.get("name", "")) or "").strip()
            if not name:
                continue

            c_type = (row.get(header_map.get("type", "")) or "Tech").strip()
            career_url = (row.get(header_map.get("career_url", "")) or row.get(header_map.get("url", "")) or "").strip()
            ats = (row.get(header_map.get("ats", "")) or "").strip()
            ats_token = (row.get(header_map.get("ats_token", "")) or "").strip()
            ats_id = (row.get(header_map.get("ats_id", "")) or "").strip()

            entry = {
                "name": name,
                "type": c_type,
                "career_url": career_url,
                "ats": ats,
                "ats_token": ats_token,
                "ats_id": ats_id
            }

            norm = normalize_company(entry)
            name_key = norm["name"].strip().lower()

            if name_key in existing_names:
                idx = existing_names[name_key]
                curr = companies[idx]
                # Upgrade ATS details if current has html_fallback and new entry has specific ATS
                if curr.get("ats") == "html_fallback" and norm["ats"] != "html_fallback":
                    curr["ats"] = norm["ats"]
                    curr["ats_token"] = norm["ats_token"]
                    curr["ats_id"] = norm["ats_id"]
                    updated += 1
                else:
                    duplicates += 1
            else:
                companies.append(norm)
                existing_names[name_key] = len(companies) - 1
                added += 1

    # 3. Atomic write
    tmp_file = f"{companies_file}.tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(companies, f, indent=2, ensure_ascii=False)
    os.replace(tmp_file, companies_file)

    print(f"✓ Imported '{csv_path}': Added {added} new, updated {updated}, skipped {duplicates} existing.")
    print(f"Total companies in database: {len(companies)}")

    # 4. Sync to DB
    if sync_db and os.path.exists("jobscraper.db"):
        synced = sync_to_sqlite(companies)
        print(f"✓ Synchronized {synced} companies to SQLite database (jobscraper.db).")

    return {"added": added, "updated": updated, "duplicates": duplicates, "total": len(companies)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import companies from CSV into job scraper database.")
    parser.add_argument("csv_file", help="Path to CSV file to import")
    parser.add_argument("--file", default="companies.json", help="Path to companies.json")
    parser.add_argument("--no-db-sync", action="store_true", help="Skip syncing to SQLite database")
    args = parser.parse_args()

    import_companies_from_csv(args.csv_file, companies_file=args.file, sync_db=not args.no_db_sync)
