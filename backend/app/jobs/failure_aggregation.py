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
import hashlib
import json
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("nova.jobs.failure_aggregation")

# Default output path
DEFAULT_OUTPUT_PATH = Path("/opt/agenticverz/state/candidate_failure_patterns.json")
FALLBACK_OUTPUT_PATH = Path("/root/agenticverz2.0/backend/data/candidate_failure_patterns.json")


def compute_signature(error_code: str, error_message: Optional[str]) -> str:
    """
    Compute deterministic signature for error grouping.

    Uses SHA256 of normalized error code + message prefix.
    """
    normalized_code = (error_code or "unknown").upper().strip()
    # Take first 100 chars of message for grouping
    normalized_msg = (error_message or "")[:100].lower().strip()

    content = f"{normalized_code}:{normalized_msg}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


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
        from app.db import engine
        from sqlmodel import Session, text

        query = text("""
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
        """)

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        with Session(engine) as session:
            result = session.execute(
                query,
                {"cutoff": cutoff, "min_occurrences": min_occurrences}
            )

            patterns = []
            for row in result:
                patterns.append({
                    "error_code": row.error_code,
                    "error_message": row.error_message,
                    "occurrence_count": row.occurrence_count,
                    "last_seen": row.last_seen.isoformat() if row.last_seen else None,
                    "first_seen": row.first_seen.isoformat() if row.first_seen else None,
                    "affected_skills": row.affected_skills or [],
                    "affected_tenants": row.affected_tenants or [],
                    "sample_run_ids": (row.sample_run_ids or [])[:5],  # Limit samples
                })

            return patterns

    except Exception as e:
        logger.error(f"Failed to fetch unmatched failures: {e}")
        return []


def aggregate_patterns(
    raw_patterns: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Aggregate patterns by signature for deduplication.

    Groups similar errors that may have slightly different messages.
    """
    grouped: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "signatures": [],
        "error_codes": set(),
        "total_occurrences": 0,
        "affected_skills": set(),
        "affected_tenants": set(),
        "examples": [],
        "last_seen": None,
        "first_seen": None,
    })

    for pattern in raw_patterns:
        sig = compute_signature(pattern["error_code"], pattern["error_message"])
        group = grouped[sig]

        group["signatures"].append(sig)
        group["error_codes"].add(pattern["error_code"])
        group["total_occurrences"] += pattern["occurrence_count"]
        group["affected_skills"].update(pattern["affected_skills"])
        group["affected_tenants"].update(pattern["affected_tenants"])

        # Track examples
        if len(group["examples"]) < 3:
            group["examples"].append({
                "error_code": pattern["error_code"],
                "error_message": pattern["error_message"],
                "occurrence_count": pattern["occurrence_count"],
            })

        # Update timestamps
        if pattern["last_seen"]:
            if not group["last_seen"] or pattern["last_seen"] > group["last_seen"]:
                group["last_seen"] = pattern["last_seen"]
        if pattern["first_seen"]:
            if not group["first_seen"] or pattern["first_seen"] < group["first_seen"]:
                group["first_seen"] = pattern["first_seen"]

    # Convert to list
    result = []
    for sig, group in grouped.items():
        result.append({
            "signature": sig,
            "primary_error_code": list(group["error_codes"])[0] if group["error_codes"] else "UNKNOWN",
            "all_error_codes": list(group["error_codes"]),
            "total_occurrences": group["total_occurrences"],
            "affected_skills": list(group["affected_skills"]),
            "affected_tenants": list(group["affected_tenants"]),
            "examples": group["examples"],
            "last_seen": group["last_seen"],
            "first_seen": group["first_seen"],
            "suggested_category": suggest_category(list(group["error_codes"])),
            "suggested_recovery": suggest_recovery(list(group["error_codes"])),
        })

    # Sort by occurrences
    result.sort(key=lambda x: x["total_occurrences"], reverse=True)
    return result


def suggest_category(error_codes: List[str]) -> str:
    """Suggest category based on error code patterns."""
    codes_str = " ".join(error_codes).lower()

    if any(k in codes_str for k in ["timeout", "network", "connection", "dns"]):
        return "TRANSIENT"
    if any(k in codes_str for k in ["permission", "auth", "forbidden", "401", "403"]):
        return "PERMISSION"
    if any(k in codes_str for k in ["budget", "quota", "rate", "limit"]):
        return "RESOURCE"
    if any(k in codes_str for k in ["validation", "schema", "invalid", "parse"]):
        return "VALIDATION"
    if any(k in codes_str for k in ["db", "database", "sql", "postgres"]):
        return "INFRASTRUCTURE"
    if any(k in codes_str for k in ["llm", "claude", "openai", "anthropic"]):
        return "PLANNER"

    return "PERMANENT"


def suggest_recovery(error_codes: List[str]) -> str:
    """Suggest recovery mode based on error code patterns."""
    codes_str = " ".join(error_codes).lower()

    if any(k in codes_str for k in ["timeout", "network", "unavailable", "503"]):
        return "RETRY_EXPONENTIAL"
    if any(k in codes_str for k in ["rate", "429"]):
        return "RETRY_WITH_JITTER"
    if any(k in codes_str for k in ["permission", "auth", "forbidden"]):
        return "ESCALATE"
    if any(k in codes_str for k in ["validation", "invalid"]):
        return "ABORT"

    return "ABORT"


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


def get_summary_stats(patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary statistics for logging/alerting."""
    if not patterns:
        return {
            "total_patterns": 0,
            "total_occurrences": 0,
            "top_error_codes": [],
            "most_affected_skills": [],
        }

    total_occurrences = sum(p["total_occurrences"] for p in patterns)

    # Top error codes
    code_counts = defaultdict(int)
    for p in patterns:
        for code in p["all_error_codes"]:
            code_counts[code] += p["total_occurrences"]
    top_codes = sorted(code_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    # Most affected skills
    skill_counts = defaultdict(int)
    for p in patterns:
        for skill in p["affected_skills"]:
            skill_counts[skill] += p["total_occurrences"]
    top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "total_patterns": len(patterns),
        "total_occurrences": total_occurrences,
        "top_error_codes": [{"code": c, "count": n} for c, n in top_codes],
        "most_affected_skills": [{"skill": s, "count": n} for s, n in top_skills],
    }


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

    # Aggregate patterns
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
    logger.info(f"Aggregation complete: {stats['total_patterns']} patterns, {stats['total_occurrences']} total occurrences")
    if stats["top_error_codes"]:
        logger.info(f"Top error codes: {stats['top_error_codes'][:3]}")

    return stats


def main():
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="M9: Failure Pattern Aggregation Job"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Look back period in days (default: 7)"
    )
    parser.add_argument(
        "--min-occurrences",
        type=int,
        default=3,
        help="Minimum occurrences to include (default: 3)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: /opt/agenticverz/state/candidate_failure_patterns.json)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    parser.add_argument(
        "--skip-r2",
        action="store_true",
        help="Skip R2 upload (local file only)"
    )

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
