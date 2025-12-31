# Layer: L5 — Execution & Workers
# Product: system-wide
# Temporal:
#   Trigger: scheduler
#   Execution: async
# Role: Failure aggregation background job (orchestration only)
# Callers: scheduler
# Allowed Imports: L4, L6
# Domain Engine: failure_classification_engine.py (L4)
# Reference: M9 Failure System, PIN-256 Phase E FIX-01

#!/usr/bin/env python3
"""
M9: Failure Pattern Aggregation Job

Runs nightly to:
1. Query unmatched failures (catalog_entry_id IS NULL)
2. Group by error signature
3. Produce candidate_failure_patterns.json for catalog expansion
4. Upload to Cloudflare R2 for durable storage (with local fallback)
5. Alert on high-frequency unknown errors

Usage:
    python -m app.jobs.failure_aggregation
    python -m app.jobs.failure_aggregation --output /custom/path/patterns.json
    python -m app.jobs.failure_aggregation --days 14 --min-occurrences 5
    python -m app.jobs.failure_aggregation --skip-r2  # Local only, no R2 upload

Schedule via cron/systemd:
    0 2 * * * cd /root/agenticverz2.0/backend && python -m app.jobs.failure_aggregation
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# hashlib, defaultdict removed - moved to L4 engine (Phase E FIX-01)

# Phase E FIX-01: Import domain classification logic from L4 engine
from app.jobs.failure_classification_engine import (
    aggregate_patterns,
    compute_signature,
    get_summary_stats,
)

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("nova.jobs.failure_aggregation")

# Default output path
DEFAULT_OUTPUT_PATH = Path("/opt/agenticverz/state/candidate_failure_patterns.json")
FALLBACK_OUTPUT_PATH = Path("/root/agenticverz2.0/backend/data/candidate_failure_patterns.json")


# compute_signature() moved to L4 engine (Phase E FIX-01)


def fetch_unmatched_failures(
    days: int = 7,
    min_occurrences: int = 3,
) -> List[Dict[str, Any]]:
    """
    Fetch unmatched failures from database.

    Args:
        days: Look back period in days
        min_occurrences: Minimum occurrences to include

    Returns:
        List of aggregated failure patterns
    """
    try:
        from sqlmodel import Session, text

        from app.db import engine

        query = text(
            """
            SELECT
                error_code,
                error_message,
                COUNT(*) AS occurrence_count,
                MAX(created_at) AS last_seen,
                MIN(created_at) AS first_seen,
                array_agg(DISTINCT skill_id) FILTER (WHERE skill_id IS NOT NULL) AS affected_skills,
                array_agg(DISTINCT tenant_id) FILTER (WHERE tenant_id IS NOT NULL) AS affected_tenants,
                array_agg(DISTINCT run_id) AS sample_run_ids
            FROM failure_matches
            WHERE catalog_entry_id IS NULL
              AND created_at > :cutoff
            GROUP BY error_code, error_message
            HAVING COUNT(*) >= :min_occurrences
            ORDER BY occurrence_count DESC
            LIMIT 100
        """
        )

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        with Session(engine) as session:
            result = session.execute(query, {"cutoff": cutoff, "min_occurrences": min_occurrences})

            patterns = []
            for row in result:
                patterns.append(
                    {
                        "error_code": row.error_code,
                        "error_message": row.error_message,
                        "occurrence_count": row.occurrence_count,
                        "last_seen": row.last_seen.isoformat() if row.last_seen else None,
                        "first_seen": row.first_seen.isoformat() if row.first_seen else None,
                        "affected_skills": row.affected_skills or [],
                        "affected_tenants": row.affected_tenants or [],
                        "sample_run_ids": (row.sample_run_ids or [])[:5],  # Limit samples
                    }
                )

            return patterns

    except Exception as e:
        logger.error(f"Failed to fetch unmatched failures: {e}")
        return []


# aggregate_patterns() moved to L4 engine (Phase E FIX-01)
# L4 engine now OWNS classification decisions (imports from L4 recovery_rule_engine)
# L5 passes DATA ONLY - no function injection, no callbacks


# GOVERNANCE: Classification authority removed from L5 (Phase E FIX-01 correction)
# Previously: L5 had suggest_category/suggest_recovery wrappers injected into L4
# This was a VIOLATION - L5 cannot inject behavior into L4
# Now: L4 failure_classification_engine.py imports directly from L4 recovery_rule_engine.py
# L5 only passes data, receives decisions. No executable code crosses the boundary.
# Reference: PIN-256 Phase E FIX-01, DOMAIN_EXTRACTION_TEMPLATE.md


def write_output(
    patterns: List[Dict[str, Any]],
    output_path: Path,
) -> bool:
    """
    Write aggregated patterns to JSON file.

    Args:
        patterns: Aggregated patterns
        output_path: Output file path

    Returns:
        True if successful
    """
    try:
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        output = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "pattern_count": len(patterns),
            "patterns": patterns,
        }

        with open(output_path, "w") as f:
            json.dump(output, f, indent=2, default=str)

        logger.info(f"Wrote {len(patterns)} patterns to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to write output: {e}")
        return False


# get_summary_stats() moved to L4 engine (Phase E FIX-01)


def run_aggregation(
    days: int = 7,
    min_occurrences: int = 3,
    output_path: Optional[Path] = None,
    skip_r2: bool = False,
) -> Dict[str, Any]:
    """
    Run the full aggregation pipeline.

    Args:
        days: Look back period
        min_occurrences: Minimum occurrences
        output_path: Output file path
        skip_r2: If True, skip R2 upload (local file only)

    Returns:
        Summary statistics
    """
    logger.info(f"Starting failure aggregation (days={days}, min_occurrences={min_occurrences})")

    # Determine output path
    if output_path is None:
        output_path = DEFAULT_OUTPUT_PATH
        if not output_path.parent.exists():
            output_path = FALLBACK_OUTPUT_PATH

    # Fetch raw patterns
    raw_patterns = fetch_unmatched_failures(days=days, min_occurrences=min_occurrences)
    logger.info(f"Fetched {len(raw_patterns)} raw patterns from database")

    if not raw_patterns:
        logger.info("No unmatched failures found, nothing to aggregate")
        return {"total_patterns": 0, "total_occurrences": 0}

    # Aggregate patterns using L4 engine - L4 OWNS classification decisions
    # L5 passes DATA ONLY. No function injection. No callbacks.
    # L4 engine imports classification authority from L4 recovery_rule_engine.py
    aggregated = aggregate_patterns(raw_patterns)
    logger.info(f"Aggregated into {len(aggregated)} unique patterns")

    # Write local output
    success = write_output(aggregated, output_path)

    # Generate summary
    stats = get_summary_stats(aggregated)
    stats["output_path"] = str(output_path)
    stats["success"] = success

    # Upload to R2 (unless skipped)
    if not skip_r2:
        try:
            from app.jobs.storage import write_candidate_json_and_upload

            output_payload = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "pattern_count": len(aggregated),
                "patterns": aggregated,
                "summary": stats,
            }

            r2_result = write_candidate_json_and_upload(output_payload)
            stats["r2_upload"] = r2_result

            if r2_result.get("status") == "uploaded":
                logger.info(f"Uploaded to R2: {r2_result.get('key')} ({r2_result.get('size')} bytes)")
            elif r2_result.get("status") == "fallback_local":
                logger.warning(f"R2 upload failed, fallback to: {r2_result.get('path')}")
            elif r2_result.get("status") == "disabled":
                logger.info("R2 storage not configured, skipping upload")

        except Exception as e:
            logger.error(f"R2 upload failed: {e}")
            stats["r2_upload"] = {"status": "error", "error": str(e)}
    else:
        logger.info("R2 upload skipped (--skip-r2 flag)")
        stats["r2_upload"] = {"status": "skipped"}

    # Log summary
    logger.info(
        f"Aggregation complete: {stats['total_patterns']} patterns, {stats['total_occurrences']} total occurrences"
    )
    if stats["top_error_codes"]:
        logger.info(f"Top error codes: {stats['top_error_codes'][:3]}")

    return stats


def main():
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="M9: Failure Pattern Aggregation Job")
    parser.add_argument("--days", type=int, default=7, help="Look back period in days (default: 7)")
    parser.add_argument("--min-occurrences", type=int, default=3, help="Minimum occurrences to include (default: 3)")
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: /opt/agenticverz/state/candidate_failure_patterns.json)",
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--skip-r2", action="store_true", help="Skip R2 upload (local file only)")

    args = parser.parse_args()

    output_path = Path(args.output) if args.output else None

    try:
        stats = run_aggregation(
            days=args.days,
            min_occurrences=args.min_occurrences,
            output_path=output_path,
            skip_r2=args.skip_r2,
        )

        if args.json:
            print(json.dumps(stats, indent=2))
        else:
            print(f"Aggregation complete: {stats['total_patterns']} patterns found")
            if stats.get("r2_upload"):
                r2_status = stats["r2_upload"].get("status", "unknown")
                if r2_status == "uploaded":
                    print(f"R2 upload: {stats['r2_upload'].get('key')}")
                elif r2_status == "fallback_local":
                    print(f"R2 fallback: {stats['r2_upload'].get('path')}")
                else:
                    print(f"R2 status: {r2_status}")

        sys.exit(0 if stats.get("success", True) else 1)

    except Exception as e:
        logger.exception(f"Aggregation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
