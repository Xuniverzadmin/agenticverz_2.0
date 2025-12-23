#!/usr/bin/env python3
"""
M25 Gate Passage Demo Script (HARDENED VERSION)

Simulates the 3 graduation gates for demo/testing purposes:
- Gate 1: Prevention Proof (policy prevented recurrence)
- Gate 2: Regret Rollback (policy auto-demoted for harm)
- Gate 3: Console Timeline (user viewed prevention in timeline)

IMPORTANT: This script creates SIMULATED data (is_simulated=true)
which does NOT count toward real graduation. Real graduation
requires real evidence from production operations.

Usage:
    python scripts/ops/m25_gate_passage_demo.py --gate 1
    python scripts/ops/m25_gate_passage_demo.py --gate 2
    python scripts/ops/m25_gate_passage_demo.py --gate 3
    python scripts/ops/m25_gate_passage_demo.py --all
    python scripts/ops/m25_gate_passage_demo.py --status
    python scripts/ops/m25_gate_passage_demo.py --reset
    python scripts/ops/m25_gate_passage_demo.py --evaluate  # Run graduation engine

Environment:
    DATABASE_URL: PostgreSQL connection string
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from uuid import uuid4

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))


SIMULATION_WARNING = """
╔════════════════════════════════════════════════════════════════════════════╗
║  ⚠️  SIMULATION MODE - DATA DOES NOT COUNT TOWARD REAL GRADUATION           ║
╠════════════════════════════════════════════════════════════════════════════╣
║  All records created by this script are marked is_simulated=true.          ║
║  Real M25 graduation requires real evidence from production operations.    ║
║                                                                            ║
║  To see real graduation status: python scripts/ops/m25_gate_passage_demo.py --status
║  To run graduation engine:      python scripts/ops/m25_gate_passage_demo.py --evaluate
╚════════════════════════════════════════════════════════════════════════════╝
"""


async def get_graduation_status(session) -> dict:
    """Get current graduation status from database."""
    from sqlalchemy import text

    result = await session.execute(
        text("SELECT * FROM m25_graduation_status WHERE id = 1")
    )
    row = result.fetchone()
    if not row:
        return {
            "status": "M25-ALPHA (0/3 gates) [not initialized]",
            "gate1_passed": False,
            "gate2_passed": False,
            "gate3_passed": False,
            "is_graduated": False,
            "is_derived": False,
        }
    return {
        "status": row.status_label,
        "gate1_passed": row.gate1_passed,
        "gate2_passed": row.gate2_passed,
        "gate3_passed": row.gate3_passed,
        "is_graduated": row.is_graduated,
        "is_derived": getattr(row, 'is_derived', False),
    }


async def get_simulation_counts(session) -> dict:
    """Count simulated vs real records."""
    from sqlalchemy import text

    # Prevention records
    prev_result = await session.execute(
        text("""
            SELECT
                COUNT(*) FILTER (WHERE is_simulated = true) as simulated,
                COUNT(*) FILTER (WHERE is_simulated = false OR is_simulated IS NULL) as real
            FROM prevention_records
        """)
    )
    prev_row = prev_result.fetchone()

    # Regret events
    regret_result = await session.execute(
        text("""
            SELECT
                COUNT(*) FILTER (WHERE is_simulated = true) as simulated,
                COUNT(*) FILTER (WHERE is_simulated = false OR is_simulated IS NULL) as real
            FROM regret_events
        """)
    )
    regret_row = regret_result.fetchone()

    # Timeline views
    try:
        tv_result = await session.execute(
            text("""
                SELECT
                    COUNT(*) FILTER (WHERE is_simulated = true) as simulated,
                    COUNT(*) FILTER (WHERE is_simulated = false) as real
                FROM timeline_views
            """)
        )
        tv_row = tv_result.fetchone()
        timeline_simulated = tv_row.simulated or 0
        timeline_real = tv_row.real or 0
    except Exception:
        timeline_simulated = 0
        timeline_real = 0

    return {
        "prevention": {"simulated": prev_row.simulated or 0, "real": prev_row.real or 0},
        "regret": {"simulated": regret_row.simulated or 0, "real": regret_row.real or 0},
        "timeline": {"simulated": timeline_simulated, "real": timeline_real},
    }


async def simulate_gate1_prevention(session) -> dict:
    """
    Simulate Gate 1: Prevention Proof

    Creates a SIMULATED prevention record (is_simulated=true).
    Does NOT update graduation status - that's derived from real evidence.
    """
    from sqlalchemy import text

    # Use sim_ prefix to clearly identify simulated records
    record_id = f"prev_sim_{uuid4().hex[:12]}"
    policy_id = f"pol_sim_{uuid4().hex[:8]}"
    pattern_id = f"pat_sim_{uuid4().hex[:8]}"
    original_incident_id = f"inc_sim_original_{uuid4().hex[:8]}"
    blocked_incident_id = f"inc_sim_blocked_{uuid4().hex[:8]}"
    tenant_id = "tenant_demo"

    print(f"  Creating SIMULATED prevention record: {record_id}")
    print(f"  Policy: {policy_id}")
    print(f"  Original incident: {original_incident_id}")
    print(f"  Blocked incident: {blocked_incident_id}")

    # Insert prevention record WITH is_simulated=true
    await session.execute(
        text("""
            INSERT INTO prevention_records (
                id, policy_id, pattern_id, original_incident_id,
                blocked_incident_id, tenant_id, outcome,
                signature_match_confidence, policy_age_seconds,
                is_simulated, created_at
            ) VALUES (
                :id, :policy_id, :pattern_id, :original_incident_id,
                :blocked_incident_id, :tenant_id, 'prevented',
                :confidence, 7200,
                true, NOW()
            )
        """),
        {
            "id": record_id,
            "policy_id": policy_id,
            "pattern_id": pattern_id,
            "original_incident_id": original_incident_id,
            "blocked_incident_id": blocked_incident_id,
            "tenant_id": tenant_id,
            "confidence": 0.92,
        },
    )

    # DO NOT update m25_graduation_status directly!
    # Graduation is DERIVED from real evidence only.

    await session.commit()

    return {
        "gate": 1,
        "name": "Prevention Proof",
        "simulated": True,
        "prevention_id": record_id,
        "counts_toward_graduation": False,
        "message": "SIMULATED prevention created (does not affect real graduation)",
    }


async def simulate_gate2_regret(session) -> dict:
    """
    Simulate Gate 2: Regret Rollback

    Creates a SIMULATED regret event (is_simulated=true).
    Does NOT update graduation status - that's derived from real evidence.
    """
    from sqlalchemy import text

    regret_id = f"regret_sim_{uuid4().hex[:12]}"
    policy_id = f"pol_sim_harmful_{uuid4().hex[:8]}"
    tenant_id = "tenant_demo"

    print(f"  Creating SIMULATED regret event: {regret_id}")
    print(f"  Harmful policy: {policy_id}")
    print(f"  Severity: 8 (high)")

    # Insert regret event WITH is_simulated=true
    await session.execute(
        text("""
            INSERT INTO regret_events (
                id, policy_id, tenant_id, regret_type,
                description, severity, affected_calls, affected_users,
                impact_duration_seconds, was_auto_rolled_back,
                is_simulated, created_at
            ) VALUES (
                :id, :policy_id, :tenant_id, 'false_positive',
                'SIMULATED: Policy blocked legitimate requests causing user complaints',
                8, 150, 25, 1800, true,
                true, NOW()
            )
        """),
        {
            "id": regret_id,
            "policy_id": policy_id,
            "tenant_id": tenant_id,
        },
    )

    # Insert policy regret summary (marked as simulated demotion)
    await session.execute(
        text("""
            INSERT INTO policy_regret_summary (
                policy_id, regret_score, regret_event_count,
                demoted_at, demoted_reason, last_updated
            ) VALUES (
                :policy_id, 4.0, 1,
                NOW(), 'SIMULATED demotion - does not count toward graduation',
                NOW()
            )
            ON CONFLICT (policy_id) DO UPDATE SET
                regret_score = policy_regret_summary.regret_score + 4.0,
                regret_event_count = policy_regret_summary.regret_event_count + 1,
                demoted_at = NOW(),
                demoted_reason = 'SIMULATED demotion - does not count toward graduation',
                last_updated = NOW()
        """),
        {"policy_id": policy_id},
    )

    # DO NOT update m25_graduation_status directly!

    await session.commit()

    return {
        "gate": 2,
        "name": "Regret Rollback",
        "simulated": True,
        "regret_id": regret_id,
        "policy_demoted": policy_id,
        "counts_toward_graduation": False,
        "message": "SIMULATED regret/demotion created (does not affect real graduation)",
    }


async def simulate_gate3_timeline(session) -> dict:
    """
    Simulate Gate 3: Console Timeline

    Creates a SIMULATED timeline view (is_simulated=true).
    Does NOT update graduation status - that's derived from real evidence.
    """
    from sqlalchemy import text

    view_id = f"tv_sim_{uuid4().hex[:12]}"
    incident_id = f"inc_sim_viewed_{uuid4().hex[:8]}"
    tenant_id = "tenant_demo"

    print(f"  Creating SIMULATED timeline view: {view_id}")
    print(f"  Incident: {incident_id}")

    # Insert into timeline_views WITH is_simulated=true
    await session.execute(
        text("""
            INSERT INTO timeline_views (
                id, incident_id, tenant_id, user_id,
                has_prevention, has_rollback,
                is_simulated, session_id, viewed_at
            ) VALUES (
                :id, :incident_id, :tenant_id, 'demo_user',
                true, false,
                true, :session_id, NOW()
            )
        """),
        {
            "id": view_id,
            "incident_id": incident_id,
            "tenant_id": tenant_id,
            "session_id": f"sim_session_{uuid4().hex[:8]}",
        },
    )

    # DO NOT update m25_graduation_status directly!

    await session.commit()

    return {
        "gate": 3,
        "name": "Console Timeline",
        "simulated": True,
        "view_id": view_id,
        "viewed_incident": incident_id,
        "counts_toward_graduation": False,
        "message": "SIMULATED timeline view created (does not affect real graduation)",
    }


async def run_graduation_engine(session) -> dict:
    """
    Run the graduation engine to compute real status from evidence.

    This excludes all simulated records.
    """
    from app.integrations.graduation_engine import (
        GraduationEngine,
        GraduationEvidence,
        CapabilityGates,
    )

    engine = GraduationEngine()
    evidence = await GraduationEvidence.fetch_from_database(session)
    status = engine.compute(evidence)

    return {
        "level": status.level.value,
        "status_label": status.status_label,
        "is_graduated": status.is_graduated,
        "is_degraded": status.is_degraded,
        "gates": {
            name: {
                "passed": gate.passed,
                "score": gate.score,
                "degraded": gate.degraded,
            }
            for name, gate in status.gates.items()
        },
        "capabilities": {
            "auto_apply_recovery": CapabilityGates.can_auto_apply_recovery(status),
            "auto_activate_policy": CapabilityGates.can_auto_activate_policy(status),
            "full_auto_routing": CapabilityGates.can_full_auto_routing(status),
        },
        "evidence": {
            "prevention_count (real)": evidence.prevention_count,
            "regret_count (real)": evidence.regret_count,
            "demotion_count (real)": evidence.demotion_count,
            "timeline_view_count (real)": evidence.timeline_view_count,
        },
    }


async def main():
    parser = argparse.ArgumentParser(description="M25 Gate Passage Demo (HARDENED)")
    parser.add_argument("--gate", type=int, choices=[1, 2, 3], help="Gate number to simulate")
    parser.add_argument("--all", action="store_true", help="Simulate all gates")
    parser.add_argument("--status", action="store_true", help="Show current graduation status")
    parser.add_argument("--reset", action="store_true", help="Reset graduation status")
    parser.add_argument("--evaluate", action="store_true", help="Run graduation engine (real status)")
    parser.add_argument("--counts", action="store_true", help="Show simulated vs real counts")
    args = parser.parse_args()

    # Check for DATABASE_URL
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    # Connect to database
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    # Convert to async URL if needed
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        if args.status:
            print("\n=== M25 Graduation Status ===\n")
            status = await get_graduation_status(session)
            print(f"Status: {status['status']}")
            print(f"Gate 1 (Prevention Proof): {'PASSED' if status['gate1_passed'] else 'pending'}")
            print(f"Gate 2 (Regret Rollback): {'PASSED' if status['gate2_passed'] else 'pending'}")
            print(f"Gate 3 (Console Timeline): {'PASSED' if status['gate3_passed'] else 'pending'}")
            print(f"Is Graduated: {'YES' if status['is_graduated'] else 'NO'}")
            print(f"Is Derived: {'YES (computed from evidence)' if status['is_derived'] else 'NO (legacy mode)'}")
            return

        if args.counts:
            print("\n=== Simulated vs Real Record Counts ===\n")
            counts = await get_simulation_counts(session)
            for category, data in counts.items():
                print(f"{category.title()}:")
                print(f"  Simulated: {data['simulated']}")
                print(f"  Real: {data['real']}")
            print("\nNote: Only REAL records count toward graduation.")
            return

        if args.evaluate:
            print("\n=== M25 Graduation Engine (Real Status) ===\n")
            try:
                result = await run_graduation_engine(session)
                print(f"Level: {result['level']}")
                print(f"Status: {result['status_label']}")
                print(f"Is Graduated: {'YES' if result['is_graduated'] else 'NO'}")
                print(f"Is Degraded: {'YES' if result['is_degraded'] else 'NO'}")
                print("\nGates (from REAL evidence only):")
                for name, gate in result['gates'].items():
                    status_str = "PASSED" if gate['passed'] else "pending"
                    print(f"  {name}: {status_str} (score: {gate['score']:.2f})")
                print("\nCapabilities:")
                for cap, unlocked in result['capabilities'].items():
                    status_str = "UNLOCKED" if unlocked else "BLOCKED"
                    print(f"  {cap}: {status_str}")
                print("\nEvidence (REAL records only):")
                for key, value in result['evidence'].items():
                    print(f"  {key}: {value}")
            except Exception as e:
                print(f"Error running graduation engine: {e}")
                print("Ensure migration 044_m25_graduation_hardening has been run.")
            return

        if args.reset:
            from sqlalchemy import text
            print("\n=== Resetting M25 Graduation Status ===\n")
            await session.execute(
                text("""
                    UPDATE m25_graduation_status
                    SET gate1_passed = false,
                        gate1_passed_at = NULL,
                        gate1_evidence = NULL,
                        gate2_passed = false,
                        gate2_passed_at = NULL,
                        gate2_evidence = NULL,
                        gate3_passed = false,
                        gate3_passed_at = NULL,
                        gate3_evidence = NULL,
                        is_graduated = false,
                        graduated_at = NULL,
                        status_label = 'M25-ALPHA (0/3 gates)',
                        is_derived = true,
                        last_evidence_eval = NULL,
                        last_checked = NOW()
                    WHERE id = 1
                """)
            )
            await session.commit()
            print("Graduation status reset to M25-ALPHA (0/3 gates)")
            print("Note: Simulated records are NOT deleted. Use --counts to see them.")
            return

        gates_to_run = []
        if args.all:
            gates_to_run = [1, 2, 3]
        elif args.gate:
            gates_to_run = [args.gate]
        else:
            parser.print_help()
            return

        print(SIMULATION_WARNING)
        print("=== M25 Gate Passage Demo (SIMULATION) ===\n")

        for gate_num in gates_to_run:
            print(f"--- Gate {gate_num} ---")
            if gate_num == 1:
                result = await simulate_gate1_prevention(session)
            elif gate_num == 2:
                result = await simulate_gate2_regret(session)
            elif gate_num == 3:
                result = await simulate_gate3_timeline(session)

            print(f"  Result: {result['message']}")
            print(f"  Counts toward graduation: {'YES' if result.get('counts_toward_graduation', False) else 'NO'}")
            print()

        # Show counts
        print("=== Record Counts ===\n")
        counts = await get_simulation_counts(session)
        for category, data in counts.items():
            print(f"{category.title()}: {data['simulated']} simulated, {data['real']} real")

        print("\n" + "="*60)
        print("To see REAL graduation status: --evaluate")
        print("To see stored status: --status")
        print("="*60)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
