"""Retention cleanup service: Auto-purges old export spreadsheets and soft-deleted records"""
import os
import argparse
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy import select, and_

from backend.database import AsyncSessionLocal
from backend.models import ExportRecord
from backend.config import RETENTION_DAYS, OUTPUT_DIR, utc_now

logger = logging.getLogger("jobscraper.retention")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


async def run_retention_purge(days: int = RETENTION_DAYS, dry_run: bool = False) -> Dict[str, Any]:
    """
    Purges export files older than specified retention window (default: 14 days).
    Supports dry-run mode and logs what was deleted with timestamps.
    """
    cutoff = utc_now() - timedelta(days=days)
    logger.info(f"Running retention purge (Cutoff: {cutoff.isoformat()}, Dry Run: {dry_run}, Days: {days})")

    purged_records: List[Dict[str, Any]] = []

    async with AsyncSessionLocal() as db:
        stmt = select(ExportRecord).where(
            and_(
                ExportRecord.created_at < cutoff,
                ExportRecord.deleted_at.is_(None)
            )
        )
        result = await db.execute(stmt)
        old_exports = list(result.scalars().all())

        for exp in old_exports:
            record_info = {
                "id": exp.id,
                "filename": exp.filename,
                "filepath": exp.filepath,
                "created_at": exp.created_at.isoformat(),
                "row_count": exp.row_count
            }

            if dry_run:
                logger.info(f"[DRY-RUN] Would delete export #{exp.id}: '{exp.filename}' (created {exp.created_at})")
                purged_records.append(record_info)
            else:
                logger.info(f"[PURGE] Deleting export #{exp.id}: '{exp.filename}' (created {exp.created_at})")
                if os.path.exists(exp.filepath):
                    try:
                        os.remove(exp.filepath)
                        logger.info(f"  ✓ Removed file: {exp.filepath}")
                    except OSError as e:
                        logger.warning(f"  ✗ Could not remove file {exp.filepath}: {e}")

                exp.deleted_at = utc_now()
                purged_records.append(record_info)

        if not dry_run:
            await db.commit()

    if os.path.exists(OUTPUT_DIR):
        for fname in os.listdir(OUTPUT_DIR):
            if fname.endswith(".xlsx"):
                fpath = os.path.join(OUTPUT_DIR, fname)
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
                    if mtime < cutoff:
                        if dry_run:
                            logger.info(f"[DRY-RUN] Would remove orphaned Excel file: {fname} (mtime {mtime})")
                        else:
                            os.remove(fpath)
                            logger.info(f"[PURGE] Removed orphaned Excel file: {fname}")
                except Exception as e:
                    logger.warning(f"Error checking file {fpath}: {e}")

    summary = {
        "timestamp": utc_now().isoformat(),
        "days": days,
        "dry_run": dry_run,
        "purged_count": len(purged_records),
        "purged_items": purged_records
    }
    logger.info(f"Retention complete. Total items purged: {len(purged_records)} (Dry run: {dry_run})")
    return summary


def main():
    parser = argparse.ArgumentParser(description="Clean up old export spreadsheet files.")
    parser.add_argument("--days", type=int, default=RETENTION_DAYS, help="Retention window in days (default: 14)")
    parser.add_argument("--dry-run", action="store_true", help="Log what would be deleted without making changes")
    args = parser.parse_args()

    asyncio.run(run_retention_purge(days=args.days, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
