#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta (Ops Script)
# Product: system-wide
# Temporal:
#   Trigger: manual (one-time migration)
#   Execution: sync
# Role: Backfill lessons_learned from historical incidents
# Callers: Ops team
# Allowed Imports: psycopg2, os, sys
# Forbidden Imports: app.* (scripts use psycopg2 directly per FA-003)
# Reference: PIN-411, POLICIES_DOMAIN_AUDIT.md Section 11

"""
Backfill Lessons from Historical Incidents

This script creates lessons_learned records from historical incidents
that existed before the LessonsLearnedEngine was wired into IncidentEngine.

Usage:
    python3 scripts/ops/backfill_lessons_from_incidents.py [--dry-run] [--tenant TENANT_ID]

Environment:
    DATABASE_URL: Required. Connection string for Neon database.
    DB_AUTHORITY: Must be "neon" for this operation.

Safety:
    - Uses is_synthetic=false for real historical data
    - Idempotent: won't create duplicate lessons for same incident
    - Supports dry-run mode for verification

Reference: PIN-411
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from uuid import uuid4

# FA-003: Scripts use psycopg2 directly, not app.db
try:
    import psycopg2
    import psycopg2.extras
    from psycopg2.extras import RealDictCursor, Json
except ImportError:
    print("Error: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)


def utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def get_connection():
    """Get database connection with authority validation."""
    # DB-AUTH-001: Authority must be declared, not inferred
    db_authority = os.environ.get("DB_AUTHORITY", "")
    if db_authority != "neon":
        print(f"ERROR: DB_AUTHORITY must be 'neon', got '{db_authority}'")
        print("This script modifies canonical data and requires Neon authority.")
        sys.exit(1)

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)

    return psycopg2.connect(db_url)


def get_incidents_without_lessons(
    conn,
    tenant_id: str | None = None,
    max_age_days: int | None = 90,
) -> list:
    """
    Find incidents that don't have corresponding lessons.

    Only returns FAILURE outcome incidents (not success).

    Args:
        conn: Database connection
        tenant_id: Optional tenant filter
        max_age_days: Only backfill incidents newer than this (default 90 days).
                     Set to None to backfill all (requires --force).

    Returns:
        List of incident dicts
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        query = """
            SELECT
                i.id,
                i.tenant_id,
                i.severity,
                i.category,
                i.error_code,
                i.description,
                i.source_run_id,
                i.is_synthetic,
                i.synthetic_scenario_id,
                i.created_at
            FROM incidents i
            LEFT JOIN lessons_learned ll
                ON ll.source_event_id = i.id
                AND ll.source_event_type = 'incident'
            WHERE ll.id IS NULL
            AND i.status != 'CLOSED'  -- Skip success incidents (PIN-407)
        """
        params = []

        if tenant_id:
            query += " AND i.tenant_id = %s"
            params.append(tenant_id)

        # Age cutoff: prevent historical noise flooding
        if max_age_days is not None:
            query += " AND i.created_at >= NOW() - INTERVAL '%s days'"
            params.append(max_age_days)

        query += " ORDER BY i.created_at ASC"

        cur.execute(query, params)
        return cur.fetchall()


def generate_lesson_content(incident: dict) -> dict:
    """Generate lesson content from incident."""
    error_code = incident.get("error_code") or "UNKNOWN"
    severity = incident.get("severity") or "MEDIUM"
    category = incident.get("category") or "EXECUTION_FAILURE"
    description = incident.get("description") or ""

    title = f"Failure: {error_code}"

    lesson_description = (
        f"Historical incident created lesson.\n\n"
        f"Severity: {severity}\n"
        f"Category: {category}\n"
        f"Error Code: {error_code}\n\n"
        f"Original Description:\n{description}"
    )

    # Generate proposed action based on severity
    if severity in ("CRITICAL", "HIGH"):
        proposed_action = (
            f"Review this {severity} severity pattern and consider creating "
            f"a preventive policy rule to catch similar failures earlier."
        )
    else:
        proposed_action = (
            f"This {severity} severity failure may indicate a pattern. "
            f"Monitor for recurrence before creating a policy."
        )

    return {
        "title": title,
        "description": lesson_description,
        "proposed_action": proposed_action,
        "detected_pattern": {
            "error_code": error_code,
            "severity": severity,
            "category": category,
            "backfilled": True,
        },
    }


def create_lesson(conn, incident: dict, lesson_content: dict, dry_run: bool = False) -> str | None:
    """Create a lesson record for an incident."""
    lesson_id = str(uuid4())
    now = utc_now()

    if dry_run:
        print(f"  [DRY-RUN] Would create lesson {lesson_id[:8]}... for incident {incident['id']}")
        return lesson_id

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO lessons_learned (
                id, tenant_id, lesson_type, severity,
                source_event_id, source_event_type, source_run_id,
                title, description, proposed_action, detected_pattern,
                status, created_at, is_synthetic, synthetic_scenario_id
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            ON CONFLICT DO NOTHING
            """,
            (
                lesson_id,
                incident["tenant_id"],
                "failure",
                incident.get("severity"),
                str(incident["id"]),  # source_event_id from incident
                "incident",  # source_event_type
                str(incident["source_run_id"]) if incident.get("source_run_id") else None,
                lesson_content["title"],
                lesson_content["description"],
                lesson_content["proposed_action"],
                Json(lesson_content["detected_pattern"]),
                "pending",
                now,
                incident.get("is_synthetic", False),
                incident.get("synthetic_scenario_id"),
            ),
        )

    return lesson_id


def main():
    parser = argparse.ArgumentParser(
        description="Backfill lessons_learned from historical incidents"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--tenant",
        type=str,
        default=None,
        help="Only backfill for specific tenant ID",
    )
    parser.add_argument(
        "--max-age",
        type=int,
        default=90,
        help="Only backfill incidents newer than N days (default: 90)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore age cutoff and backfill ALL historical incidents",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Backfill Lessons from Historical Incidents")
    print("=" * 60)
    print()

    if args.dry_run:
        print("*** DRY-RUN MODE - No changes will be made ***")
        print()

    # Age cutoff logic
    max_age_days = None if args.force else args.max_age
    if args.force:
        print("*** FORCE MODE - Backfilling ALL historical incidents ***")
        print("    (Age cutoff disabled)")
        print()
    else:
        print(f"Age cutoff: {args.max_age} days (use --force to override)")
        print()

    # Validate authority
    print("DB AUTHORITY DECLARATION")
    print("  - Declared Authority: neon")
    print("  - Intended Operation: write (backfill)")
    print("  - Justification: Creating lessons from historical incidents")
    print()

    conn = get_connection()

    try:
        # Find incidents without lessons
        print("Scanning for incidents without lessons...")
        incidents = get_incidents_without_lessons(conn, args.tenant, max_age_days)
        print(f"Found {len(incidents)} incidents without lessons")
        print()

        if not incidents:
            print("No backfill needed - all incidents have lessons.")
            return

        # Create lessons
        created = 0
        skipped = 0

        for incident in incidents:
            lesson_content = generate_lesson_content(incident)

            print(f"Processing incident {incident['id']}:")
            print(f"  Tenant: {incident['tenant_id']}")
            print(f"  Severity: {incident.get('severity', 'N/A')}")
            print(f"  Error Code: {incident.get('error_code', 'N/A')}")

            try:
                lesson_id = create_lesson(conn, incident, lesson_content, args.dry_run)
                if lesson_id:
                    created += 1
                    print(f"  Created lesson: {lesson_id}")
                else:
                    skipped += 1
                    print(f"  Skipped (already exists or error)")
            except Exception as e:
                skipped += 1
                print(f"  Error: {e}")

            print()

        if not args.dry_run:
            conn.commit()
            print("Changes committed.")

        print()
        print("=" * 60)
        print("Summary")
        print("=" * 60)
        print(f"  Total incidents scanned: {len(incidents)}")
        print(f"  Lessons created: {created}")
        print(f"  Skipped: {skipped}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
