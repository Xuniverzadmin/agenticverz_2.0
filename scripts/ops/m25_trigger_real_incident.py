#!/usr/bin/env python3
"""
M25 Real Incident Trigger Script

PURPOSE: Trigger ONE real incident through the M25 integration loop.
         Creates REAL evidence (not simulated) for graduation.

RULES:
- Creates ONE real incident
- Triggers the M25 integration loop
- Incident flows through all 5 bridges
- NO simulation flags

USAGE:
    export DATABASE_URL="postgresql://..."
    export REDIS_URL="redis://localhost:6379/0"
    python scripts/ops/m25_trigger_real_incident.py \
        --tenant-id tenant_demo \
        --trigger-type policy_violation \
        --title "Data export request blocked"

Per PIN-131: Real evidence only.
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from uuid import uuid4

# Ensure proper path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))


async def create_real_incident(
    tenant_id: str,
    trigger_type: str,
    title: str,
    error_type: str = "policy_violation",
    severity: int = 3,
) -> dict:
    """
    Create a REAL incident in the database.

    This is NOT a simulation - creates a real incident that will
    flow through the M25 integration loop.
    """
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable not set")

    engine = create_engine(DATABASE_URL)

    # Generate real incident ID (no sim_ prefix!)
    incident_id = f"inc_{uuid4().hex[:16]}"
    call_id = f"call_{uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)

    with Session(engine) as session:
        # Create the real incident (using actual schema)
        session.execute(
            text(
                """
                INSERT INTO incidents (
                    id, tenant_id, title, severity, status,
                    trigger_type, trigger_value, calls_affected,
                    cost_delta_cents, auto_action, started_at, created_at
                ) VALUES (
                    :id, :tenant_id, :title, :severity, 'open',
                    :trigger_type, :trigger_value, 1,
                    0, 'block', :now, :now
                )
            """
            ),
            {
                "id": incident_id,
                "tenant_id": tenant_id,
                "title": title,
                "severity": str(severity),  # severity is varchar
                "trigger_type": trigger_type,
                "trigger_value": f"{error_type}: {title}",
                "now": now,
            },
        )

        # Create incident event
        session.execute(
            text(
                """
                INSERT INTO incident_events (
                    id, incident_id, event_type, description, created_at
                ) VALUES (
                    :id, :incident_id, 'TRIGGERED', :description, :now
                )
            """
            ),
            {
                "id": str(uuid4()),
                "incident_id": incident_id,
                "description": f"Policy violation detected: {title}",
                "now": now,
            },
        )

        session.commit()

    print(f"Created REAL incident: {incident_id}")
    print(f"  Tenant: {tenant_id}")
    print(f"  Title: {title}")
    print(f"  Trigger: {trigger_type}")
    print(f"  Severity: {severity}")

    return {
        "incident_id": incident_id,
        "tenant_id": tenant_id,
        "title": title,
        "trigger_type": trigger_type,
        "error_type": error_type,
        "severity": severity,
        "call_id": call_id,
        "created_at": now.isoformat(),
    }


async def trigger_m25_loop(incident_data: dict) -> dict:
    """
    Trigger the M25 integration loop for the incident.

    This dispatches the incident through all 5 bridges:
    1. Incident -> Pattern (Bridge 1)
    2. Pattern -> Recovery (Bridge 2)
    3. Recovery -> Policy (Bridge 3)
    4. Policy -> Routing (Bridge 4)
    5. Loop -> Console (Bridge 5)
    """
    from app.integrations import trigger_integration_loop

    incident_id = incident_data["incident_id"]
    tenant_id = incident_data["tenant_id"]

    print(f"\nTriggering M25 integration loop for {incident_id}...")

    # Trigger the loop
    result = await trigger_integration_loop(
        incident_id=incident_id,
        tenant_id=tenant_id,
        incident_data={
            "error_type": incident_data.get("error_type", "unknown"),
            "trigger_type": incident_data.get("trigger_type"),
            "title": incident_data.get("title"),
            "severity": incident_data.get("severity"),
            "context": {
                "call_id": incident_data.get("call_id"),
                "tenant_id": tenant_id,
            },
        },
    )

    print("\nLoop result:")
    print(f"  Final stage: {result.stage.value}")
    print(f"  Success: {result.is_success}")
    if result.failure_state:
        print(f"  Failure state: {result.failure_state.value}")

    # Return summary
    return {
        "incident_id": incident_id,
        "final_stage": result.stage.value,
        "success": result.is_success,
        "failure_state": result.failure_state.value if result.failure_state else None,
        "details": result.details,
    }


async def verify_loop_trace(incident_id: str) -> dict:
    """
    Verify that the loop trace was created in the database.
    """
    from sqlalchemy import create_engine, text

    DATABASE_URL = os.environ.get("DATABASE_URL")
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # Check loop_traces
        trace_result = conn.execute(
            text(
                """
                SELECT id, stages, is_complete, started_at, completed_at
                FROM loop_traces
                WHERE incident_id = :incident_id
                ORDER BY started_at DESC
                LIMIT 1
            """
            ),
            {"incident_id": incident_id},
        ).fetchone()

        # Check loop_events
        events_result = conn.execute(
            text(
                """
                SELECT stage, COUNT(*) as count
                FROM loop_events
                WHERE incident_id = :incident_id
                GROUP BY stage
            """
            ),
            {"incident_id": incident_id},
        ).fetchall()

        # Check failure_patterns
        pattern_result = conn.execute(
            text(
                """
                SELECT id, signature, occurrence_count
                FROM failure_patterns
                WHERE first_incident_id = :incident_id
                ORDER BY created_at DESC
                LIMIT 1
            """
            ),
            {"incident_id": incident_id},
        ).fetchone()

    result = {
        "incident_id": incident_id,
        "has_loop_trace": trace_result is not None,
        "loop_events": [{"stage": r[0], "count": r[1]} for r in events_result],
        "has_pattern": pattern_result is not None,
    }

    if trace_result:
        result["loop_trace"] = {
            "id": trace_result[0],
            "stages": trace_result[1],
            "is_complete": trace_result[2],
        }

    if pattern_result:
        result["pattern"] = {
            "id": pattern_result[0],
            "occurrence_count": pattern_result[2],
        }

    print(f"\nLoop verification for {incident_id}:")
    print(f"  Has loop trace: {result['has_loop_trace']}")
    print(f"  Loop events: {result['loop_events']}")
    print(f"  Has pattern: {result['has_pattern']}")

    if result.get("pattern"):
        print(f"  Pattern ID: {result['pattern']['id']}")

    return result


async def main():
    parser = argparse.ArgumentParser(description="Trigger real M25 incident")
    parser.add_argument(
        "--tenant-id",
        default="tenant_demo",
        help="Tenant ID (default: tenant_demo)",
    )
    parser.add_argument(
        "--trigger-type",
        default="policy_violation",
        help="Trigger type (default: policy_violation)",
    )
    parser.add_argument(
        "--error-type",
        default="policy_violation",
        help="Error type for pattern matching (default: policy_violation)",
    )
    parser.add_argument(
        "--title",
        default="Policy blocked data export request",
        help="Incident title",
    )
    parser.add_argument(
        "--severity",
        type=int,
        default=3,
        choices=[1, 2, 3, 4, 5],
        help="Severity level (1-5, default: 3)",
    )
    parser.add_argument(
        "--verify-only",
        metavar="INCIDENT_ID",
        help="Only verify an existing incident (skip creation)",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("M25 REAL INCIDENT TRIGGER")
    print("=" * 60)
    print()
    print("WARNING: This creates REAL data, not simulations.")
    print("Real evidence is required for M25 graduation.")
    print()

    if args.verify_only:
        # Just verify an existing incident
        verification = await verify_loop_trace(args.verify_only)
        print(f"\nVerification complete: {json.dumps(verification, indent=2)}")
        return

    try:
        # Step 1: Create real incident
        print("STEP 1: Creating real incident...")
        incident_data = await create_real_incident(
            tenant_id=args.tenant_id,
            trigger_type=args.trigger_type,
            title=args.title,
            error_type=args.error_type,
            severity=args.severity,
        )

        # Step 2: Trigger M25 loop
        print("\nSTEP 2: Triggering M25 integration loop...")
        loop_result = await trigger_m25_loop(incident_data)

        # Step 3: Verify
        print("\nSTEP 3: Verifying loop trace...")
        verification = await verify_loop_trace(incident_data["incident_id"])

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Incident ID: {incident_data['incident_id']}")
        print(f"Loop success: {loop_result['success']}")
        print(f"Final stage: {loop_result['final_stage']}")
        if verification.get("pattern"):
            print(f"Pattern created: {verification['pattern']['id']}")
        print()
        print("To capture evidence trail later:")
        print("  python scripts/ops/m25_capture_evidence_trail.py \\")
        print(f"      --incident-id {incident_data['incident_id']}")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
