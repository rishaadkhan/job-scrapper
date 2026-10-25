#!/usr/bin/env python3
"""
Management CLI Interface for Job Scraper Enterprise
Provides administrative commands for company ingestion, database synchronization,
and pipeline maintenance.

Usage:
    python manage.py add-companies --input candidates.txt
    python manage.py add-companies "Ramp" "Zoom" --type "Unicorn"
    python manage.py list-companies --search "Stripe"
    python manage.py stats
"""
import os
import sys
import csv
import json
import asyncio
import argparse
from typing import List, Dict, Any, Optional

from expand_companies import (
    ingest_candidates,
    generate_ingestion_report,
    db_load_all_companies,
    DEFAULT_LOCATIONS
)


def parse_input_file(filepath: str, default_type: str = "Tech") -> List[Dict[str, Any]]:
    """
    Parses a candidates file supporting multiple formats:
    1. Plain text list (one company name per line)
    2. Markdown / Category headers (e.g. '# Tier-1 GCC', '## Unicorn') which group subsequent companies
    3. Markdown bullet points ('- Company Name', '* Company Name')
    4. CSV file with headers (name, type, career_url)
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input file not found: {filepath}")

    candidates: List[Dict[str, Any]] = []

    # Check if CSV
    is_csv = False
    with open(filepath, "r", encoding="utf-8-sig") as f:
        first_line = f.readline()
        if "," in first_line and any(h in first_line.lower() for h in ["name", "company", "career_url"]):
            is_csv = True

    if is_csv:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            header_map = {k.strip().lower(): k for k in (reader.fieldnames or []) if k}
            for row in reader:
                name = (row.get(header_map.get("name", "")) or row.get(header_map.get("company", "")) or "").strip()
                if not name:
                    continue
                c_type = (row.get(header_map.get("type", "")) or default_type).strip()
                url = (row.get(header_map.get("career_url", "")) or row.get(header_map.get("url", "")) or "").strip()
                candidates.append({
                    "name": name,
                    "type": c_type,
                    "career_url": url
                })
        return candidates

    # Plain text / Markdown parser with category headers
    current_category = default_type
    with open(filepath, "r", encoding="utf-8-sig") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue

            # Detect category header e.g. '# Tier-1 GCC' or '## Unicorns'
            if line_str.startswith("#"):
                header_text = line_str.lstrip("#").strip()
                if header_text:
                    # Strip 'Category:' prefix if present
                    if ":" in header_text:
                        header_text = header_text.split(":", 1)[1].strip()
                    current_category = header_text
                continue

            # Strip markdown bullet list characters
            if line_str.startswith(("-", "*", "•")):
                line_str = line_str.lstrip("-*•").strip()

            # Ignore comments
            if line_str.startswith("//"):
                continue

            # Check if line contains inline comma: "Company Name, Category, URL"
            if "," in line_str:
                parts = [p.strip() for p in line_str.split(",")]
                c_name = parts[0]
                c_type = parts[1] if len(parts) > 1 and parts[1] else current_category
                c_url = parts[2] if len(parts) > 2 else ""
                candidates.append({
                    "name": c_name,
                    "type": c_type,
                    "career_url": c_url
                })
            else:
                candidates.append({
                    "name": line_str,
                    "type": current_category,
                    "career_url": ""
                })

    return candidates


def cmd_add_companies(args: argparse.Namespace) -> int:
    """Handles 'add-companies' subcommand."""
    candidates: List[Dict[str, Any]] = []

    # 1. Parse candidates from file if provided
    if args.input:
        try:
            parsed = parse_input_file(args.input, default_type=args.type)
            candidates.extend(parsed)
            print(f"Loaded {len(parsed)} candidate company entries from '{args.input}'.")
        except Exception as exc:
            print(f"Error reading input file: {exc}", file=sys.stderr)
            return 1

    # 2. Add positional company names from CLI
    if args.companies:
        for c_name in args.companies:
            candidates.append({
                "name": c_name.strip(),
                "type": args.type,
                "career_url": ""
            })

    if not candidates:
        print("Error: No candidate companies provided. Specify --input <file> or provide company names as arguments.", file=sys.stderr)
        return 1

    print(f"\nProcessing {len(candidates)} candidate(s) with deduplication & ATS auto-detection...")
    if args.dry_run:
        print("[DRY RUN MODE ENABLED: Database will not be modified]\n")

    # Run async ingestion
    async def _execute():
        # Ensure database tables exist before ingestion
        try:
            from backend.database import init_db
            await init_db()
        except Exception as e:
            print(f"Notice: Database initialization check: {e}")

        return await ingest_candidates(
            candidates=candidates,
            dry_run=args.dry_run,
            save_unresolved=args.save_unresolved,
            timeout=args.timeout
        )

    results = asyncio.run(_execute())

    # Generate and output summary report
    report_text = generate_ingestion_report(results)
    print("\n" + report_text)

    # Optional file output
    if args.output_report:
        try:
            with open(args.output_report, "w", encoding="utf-8") as rf:
                rf.write(report_text)
            print(f"\n✓ Saved ingestion report to: {args.output_report}")
        except Exception as e:
            print(f"Warning: Could not save report file: {e}", file=sys.stderr)

    # Optional JSON output
    if args.json:
        json_output = json.dumps(results, indent=2, ensure_ascii=False)
        print("\n=== JSON RESULTS ===")
        print(json_output)

    return 0


def cmd_list_companies(args: argparse.Namespace) -> int:
    """Lists company entries currently stored in the database."""
    async def _execute():
        comps = await db_load_all_companies()
        if args.search:
            s = args.search.lower()
            comps = [c for c in comps if s in c["name"].lower() or s in (c.get("ats") or "").lower()]
        return comps

    comps = asyncio.run(_execute())
    print(f"\nFound {len(comps)} companies in database:\n")
    print(f"{'ID':<6} {'Company Name':<32} {'Type':<18} {'ATS':<16} {'Token':<18} {'Active':<8}")
    print("-" * 105)
    for c in comps[:args.limit]:
        c_id = str(c.get("id") or "-")
        name = (c.get("name") or "")[:30]
        c_type = (c.get("company_type") or c.get("type") or "Tech")[:16]
        ats = (c.get("ats") or "unknown")[:14]
        token = (c.get("ats_token") or "-")[:16]
        active = "Yes" if c.get("active", True) else "No"
        print(f"{c_id:<6} {name:<32} {c_type:<18} {ats:<16} {token:<18} {active:<8}")

    if len(comps) > args.limit:
        print(f"... and {len(comps) - args.limit} more companies (use --limit to show more).")
    print()
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    """Displays high-level database metrics."""
    async def _execute():
        from backend.database import AsyncSessionLocal
        from backend.models import Company, Job, ScrapeRun
        from sqlalchemy import select, func

        async with AsyncSessionLocal() as session:
            total_comps = (await session.execute(select(func.count(Company.id)))).scalar_one()
            active_comps = (await session.execute(select(func.count(Company.id)).where(Company.active == True))).scalar_one()
            total_jobs = (await session.execute(select(func.count(Job.id)))).scalar_one()
            total_runs = (await session.execute(select(func.count(ScrapeRun.id)))).scalar_one()

            # Breakdown by ATS
            ats_breakdown = (await session.execute(
                select(Company.ats, func.count(Company.id)).group_by(Company.ats)
            )).all()

            return {
                "total_companies": total_comps,
                "active_companies": active_comps,
                "total_jobs": total_jobs,
                "total_runs": total_runs,
                "ats_breakdown": dict(ats_breakdown)
            }

    metrics = asyncio.run(_execute())
    from backend.config import DATABASE_URL
    print("\n" + "=" * 60)
    print("             JOBSCRAPER DATABASE OVERVIEW")
    print("=" * 60)
    print(f"Target Database   : {DATABASE_URL}")
    print(f"Total Companies   : {metrics['total_companies']}")
    print(f"Active Companies  : {metrics['active_companies']}")
    print(f"Total Jobs Stored : {metrics['total_jobs']}")
    print(f"Total Scrape Runs : {metrics['total_runs']}")
    print("-" * 60)
    print("Companies by ATS Platform:")
    for ats, count in sorted(metrics["ats_breakdown"].items(), key=lambda x: x[1], reverse=True):
        print(f"  • {ats or 'unknown':<18}: {count}")
    print("=" * 60 + "\n")
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="manage.py",
        description="Job Scraper Management & Ingestion CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: add-companies
    parser_add = subparsers.add_parser("add-companies", help="Ingest candidate companies with deduplication and ATS detection")
    parser_add.add_argument("companies", nargs="*", help="Company names to ingest directly")
    parser_add.add_argument("-i", "--input", help="Path to input text or CSV file containing candidates")
    parser_add.add_argument("-t", "--type", default="Tech", help="Default company category/type (default: 'Tech')")
    parser_add.add_argument("--dry-run", action="store_true", help="Perform checks and report results without modifying the database")
    parser_add.add_argument("--save-unresolved", action="store_true", help="Save unresolved ATS companies to DB as inactive (active=False)")
    parser_add.add_argument("-o", "--output-report", help="Save formatted summary report to file")
    parser_add.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser_add.add_argument("--timeout", type=float, default=3.5, help="HTTP timeout for ATS probe requests in seconds (default: 3.5)")

    # Command: list-companies
    parser_list = subparsers.add_parser("list-companies", help="List companies currently in database")
    parser_list.add_argument("-s", "--search", help="Filter companies by name or ATS platform")
    parser_list.add_argument("--limit", type=int, default=50, help="Maximum number of entries to display (default: 50)")

    # Command: stats
    subparsers.add_parser("stats", help="Show database overview and ATS distribution")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "add-companies":
        sys.exit(cmd_add_companies(args))
    elif args.command == "list-companies":
        sys.exit(cmd_list_companies(args))
    elif args.command == "stats":
        sys.exit(cmd_stats(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
