"""
Master Script: Import All Expansion CSV Files
Finds all companies_expansion_part*.csv files and imports them with ATS detection,
deduplication, atomic JSON updates, and SQLite database synchronization.
"""
import glob
import os
from import_csv import import_companies_from_csv


def import_all_expansions(pattern: str = "companies_expansion_part*.csv", sync_db: bool = True):
    """Imports all matching CSV expansion files into companies.json and SQLite."""
    csv_files = sorted(glob.glob(pattern))
    if not csv_files:
        print(f"No expansion files found matching '{pattern}'.")
        return

    print(f"Found {len(csv_files)} expansion file(s) to process:\n" + "\n".join(f"  - {f}" for f in csv_files))
    print("=" * 60)

    total_added = 0
    total_updated = 0
    total_skipped = 0

    for csv_file in csv_files:
        print(f"\nProcessing {csv_file}...")
        res = import_companies_from_csv(csv_file, sync_db=False)
        total_added += res["added"]
        total_updated += res["updated"]
        total_skipped += res["duplicates"]

    # Final DB sync if requested
    if sync_db and os.path.exists("jobscraper.db"):
        import json
        from expand_companies import sync_to_sqlite
        with open("companies.json", "r", encoding="utf-8") as f:
            companies = json.load(f)
        synced = sync_to_sqlite(companies)
        print(f"\n✓ Synchronized {synced} total companies to SQLite database (jobscraper.db).")

    print("\n" + "=" * 60)
    print("🎉 ALL EXPANSION IMPORTS COMPLETE!")
    print("=" * 60)
    print(f"Total new companies added : {total_added}")
    print(f"Total existing upgraded   : {total_updated}")
    print(f"Total duplicates skipped  : {total_skipped}")
    print("=" * 60)


if __name__ == "__main__":
    import_all_expansions()
