#!/usr/bin/env python3
"""
M10 Retention & Archive Job

Archives old provenance and input records from m10_recovery tables.
Designed to run as a cron job or scheduled task.

Features:
- Configurable retention periods per table
- Atomic archive + delete operations
- Updates retention_jobs table with run metadata
- Dry-run mode for testing
- Prometheus metrics integration (optional)

Usage:
    # Dry run (no changes)
    python m10_retention_archive.py --dry-run

    # Archive records older than 90 days (default)
    python m10_retention_archive.py

    # Custom retention period
    python m10_retention_archive.py --retention-days 60

    # Specific job only
    python m10_retention_archive.py --job provenance_archive

Environment Variables:
    DATABASE_URL: PostgreSQL connection string

Cron Example (weekly, Sundays at 3am):
    0 3 * * 0 /opt/agenticverz/venv/bin/python /opt/agenticverz/scripts/ops/m10_retention_archive.py >> /var/log/agenticverz/retention.log 2>&1
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlmodel import Session, create_engine

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
)
logger = logging.getLogger("nova.ops.retention")


# Job definitions
ARCHIVE_JOBS = {
    "provenance_archive": {
        "source_table": "m10_recovery.suggestion_provenance",
        "archive_table": "m10_recovery.suggestion_provenance_archive",
        "date_column": "created_at",
        "default_retention_days": 90,
    },
    "inputs_archive": {
        "source_table": "m10_recovery.suggestion_input",
        "archive_table": "m10_recovery.suggestion_input_archive",
        "date_column": "created_at",
        "default_retention_days": 90,
    },
    "candidates_archive": {
        "source_table": "recovery_candidates",
        "archive_table": None,  # No archive, just tracking
        "date_column": "created_at",
        "default_retention_days": 180,
        "archive_only_status": ["approved", "rejected"],  # Don't archive pending
    },
}


class RetentionArchiver:
    """Archives old records from M10 recovery tables."""

    def __init__(self, db_url: Optional[str] = None, dry_run: bool = False):
        self.db_url = db_url or os.getenv("DATABASE_URL")
        if not self.db_url:
            raise RuntimeError("DATABASE_URL environment variable is required")

        self.dry_run = dry_run
        self.engine = create_engine(self.db_url, pool_pre_ping=True)

    def _get_session(self) -> Session:
        """Create database session."""
        return Session(self.engine)

    def get_retention_days(self, job_name: str) -> int:
        """Get retention days for a job from DB or default."""
        session = self._get_session()
        try:
            result = session.execute(
                text(
                    """
                    SELECT retention_days FROM m10_recovery.retention_jobs
                    WHERE name = :name
                """
                ),
                {"name": job_name},
            )
            row = result.fetchone()
            if row:
                return row[0]
        except Exception:
            pass
        finally:
            session.close()

        return ARCHIVE_JOBS.get(job_name, {}).get("default_retention_days", 90)

    def archive_provenance(self, retention_days: int) -> Tuple[int, int]:
        """
        Archive old provenance records.

        Returns:
            Tuple of (archived_count, deleted_count)
        """
        session = self._get_session()
        try:
            # Count records to archive
            result = session.execute(
                text(
                    f"""
                    SELECT COUNT(*)
                    FROM m10_recovery.suggestion_provenance
                    WHERE created_at < now() - interval '{retention_days} days'
                """
                )
            )
            count = result.scalar() or 0

            if count == 0:
                logger.info(f"No provenance records older than {retention_days} days")
                return 0, 0

            logger.info(f"Found {count} provenance records to archive")

            if self.dry_run:
                logger.info("[DRY RUN] Would archive and delete records")
                return count, 0

            # Archive records
            session.execute(
                text(
                    f"""
                    INSERT INTO m10_recovery.suggestion_provenance_archive
                    (id, suggestion_id, event_type, details, rule_id, action_id,
                     confidence_before, confidence_after, actor, actor_type,
                     created_at, duration_ms, archived_at)
                    SELECT
                        id, suggestion_id, event_type, details, rule_id, action_id,
                        confidence_before, confidence_after, actor, actor_type,
                        created_at, duration_ms, now()
                    FROM m10_recovery.suggestion_provenance
                    WHERE created_at < now() - interval '{retention_days} days'
                """
                )
            )

            # Delete archived records
            result = session.execute(
                text(
                    f"""
                    DELETE FROM m10_recovery.suggestion_provenance
                    WHERE created_at < now() - interval '{retention_days} days'
                """
                )
            )
            deleted = result.rowcount

            session.commit()
            logger.info(f"Archived {count} records, deleted {deleted}")
            return count, deleted

        except Exception as e:
            session.rollback()
            logger.error(f"Provenance archive failed: {e}")
            raise
        finally:
            session.close()

    def archive_inputs(self, retention_days: int) -> Tuple[int, int]:
        """
        Archive old input records.

        Returns:
            Tuple of (archived_count, deleted_count)
        """
        session = self._get_session()
        try:
            # Count records to archive
            result = session.execute(
                text(
                    f"""
                    SELECT COUNT(*)
                    FROM m10_recovery.suggestion_input
                    WHERE created_at < now() - interval '{retention_days} days'
                """
                )
            )
            count = result.scalar() or 0

            if count == 0:
                logger.info(f"No input records older than {retention_days} days")
                return 0, 0

            logger.info(f"Found {count} input records to archive")

            if self.dry_run:
                logger.info("[DRY RUN] Would archive and delete records")
                return count, 0

            # Archive records
            session.execute(
                text(
                    f"""
                    INSERT INTO m10_recovery.suggestion_input_archive
                    (id, suggestion_id, input_type, raw_value, normalized_value,
                     parsed_data, confidence, weight, source, created_at, archived_at)
                    SELECT
                        id, suggestion_id, input_type, raw_value, normalized_value,
                        parsed_data, confidence, weight, source, created_at, now()
                    FROM m10_recovery.suggestion_input
                    WHERE created_at < now() - interval '{retention_days} days'
                """
                )
            )

            # Delete archived records
            result = session.execute(
                text(
                    f"""
                    DELETE FROM m10_recovery.suggestion_input
                    WHERE created_at < now() - interval '{retention_days} days'
                """
                )
            )
            deleted = result.rowcount

            session.commit()
            logger.info(f"Archived {count} records, deleted {deleted}")
            return count, deleted

        except Exception as e:
            session.rollback()
            logger.error(f"Input archive failed: {e}")
            raise
        finally:
            session.close()

    def count_candidates_for_archive(self, retention_days: int) -> int:
        """
        Count old approved/rejected candidates (for reporting only).

        We don't delete candidates, just track how many could be archived.
        """
        session = self._get_session()
        try:
            result = session.execute(
                text(
                    f"""
                    SELECT COUNT(*)
                    FROM recovery_candidates
                    WHERE created_at < now() - interval '{retention_days} days'
                      AND decision IN ('approved', 'rejected')
                """
                )
            )
            return result.scalar() or 0
        finally:
            session.close()

    def update_job_metadata(
        self,
        job_name: str,
        archived: int,
        deleted: int,
    ) -> None:
        """Update retention_jobs table with run results."""
        if self.dry_run:
            return

        session = self._get_session()
        try:
            session.execute(
                text(
                    """
                    UPDATE m10_recovery.retention_jobs
                    SET
                        last_run = now(),
                        rows_archived = :archived,
                        rows_deleted = :deleted,
                        updated_at = now()
                    WHERE name = :name
                """
                ),
                {"name": job_name, "archived": archived, "deleted": deleted},
            )
            session.commit()
        except Exception as e:
            session.rollback()
            logger.warning(f"Failed to update job metadata: {e}")
        finally:
            session.close()

    def run_job(self, job_name: str, retention_days: Optional[int] = None) -> Dict:
        """
        Run a specific archive job.

        Args:
            job_name: Name of the job to run
            retention_days: Override retention period

        Returns:
            Dict with job results
        """
        if job_name not in ARCHIVE_JOBS:
            raise ValueError(f"Unknown job: {job_name}")

        if retention_days is None:
            retention_days = self.get_retention_days(job_name)

        logger.info(f"Running {job_name} with retention_days={retention_days}")

        start_time = datetime.now(timezone.utc)
        archived = 0
        deleted = 0
        error = None

        try:
            if job_name == "provenance_archive":
                archived, deleted = self.archive_provenance(retention_days)
            elif job_name == "inputs_archive":
                archived, deleted = self.archive_inputs(retention_days)
            elif job_name == "candidates_archive":
                archived = self.count_candidates_for_archive(retention_days)
                deleted = 0  # We don't delete candidates
                logger.info(f"Found {archived} old candidates (not deleted)")

            self.update_job_metadata(job_name, archived, deleted)

        except Exception as e:
            error = str(e)
            logger.error(f"Job {job_name} failed: {e}")

        duration = (datetime.now(timezone.utc) - start_time).total_seconds()

        return {
            "job": job_name,
            "retention_days": retention_days,
            "archived": archived,
            "deleted": deleted,
            "duration_seconds": round(duration, 2),
            "dry_run": self.dry_run,
            "error": error,
        }

    def run_all(self, retention_days: Optional[int] = None) -> List[Dict]:
        """Run all archive jobs."""
        results = []
        for job_name in ARCHIVE_JOBS:
            result = self.run_job(job_name, retention_days)
            results.append(result)
        return results


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="M10 Retention & Archive Job",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python m10_retention_archive.py --dry-run
  python m10_retention_archive.py --retention-days 60
  python m10_retention_archive.py --job provenance_archive
        """,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be archived without making changes",
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=None,
        help="Override retention period for all jobs",
    )
    parser.add_argument(
        "--job",
        type=str,
        choices=list(ARCHIVE_JOBS.keys()),
        help="Run specific job only",
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    try:
        archiver = RetentionArchiver(dry_run=args.dry_run)

        if args.job:
            results = [archiver.run_job(args.job, args.retention_days)]
        else:
            results = archiver.run_all(args.retention_days)

        if args.json:
            import json

            print(json.dumps(results, indent=2))
        else:
            print("\n=== Retention Archive Results ===")
            for r in results:
                status = "✓" if not r.get("error") else "✗"
                dry = " [DRY RUN]" if r.get("dry_run") else ""
                print(f"{status} {r['job']}{dry}")
                print(f"   Retention: {r['retention_days']} days")
                print(f"   Archived: {r['archived']}, Deleted: {r['deleted']}")
                print(f"   Duration: {r['duration_seconds']}s")
                if r.get("error"):
                    print(f"   Error: {r['error']}")
                print()

        # Exit with error if any job failed
        if any(r.get("error") for r in results):
            sys.exit(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
