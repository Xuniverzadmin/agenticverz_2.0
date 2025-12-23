#!/usr/bin/env python3
"""
M25 Evidence Trail Capture Script

PURPOSE: Capture ONE non-simulated, end-to-end closed-loop proof.
         This is for auditors and skeptics, not developers.

RULES:
- NO writes
- NO simulations
- NO recomputation
- READ-ONLY queries only
- Hashes included for integrity

USAGE:
    export DATABASE_URL="postgresql://..."
    python scripts/ops/m25_capture_evidence_trail.py \
        --incident-id inc_XXXXX \
        --output evidence_trail.json

Per PIN-131: M25 Real Evidence Trail Capture Protocol
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional

# Ensure proper path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def compute_hash(data: dict) -> str:
    """Compute SHA256 hash of canonical JSON representation."""
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def capture_evidence_trail(
    incident_id: str,
    tenant_id: Optional[str] = None,
    time_window_hours: int = 168,  # 7 days
) -> dict:
    """
    Capture complete evidence trail for a single incident.

    Returns immutable evidence bundle with:
    - incident metadata
    - loop_trace_id
    - matched_pattern_id
    - recovery_id
    - policy_id
    - shadow -> active transition timestamps
    - prevention event reference
    - graduation delta (before/after)
    - integrity hashes
    """
    from sqlalchemy import create_engine, text

    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        return {
            "error": "DATABASE_URL environment variable not set",
            "captured_at": datetime.now(timezone.utc).isoformat(),
        }

    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # =====================================================================
        # STAGE 1: Incident Metadata
        # =====================================================================
        incident_result = conn.execute(text("""
            SELECT id, tenant_id, title, severity, created_at, status
            FROM incidents
            WHERE id = :incident_id
        """), {"incident_id": incident_id}).fetchone()

        if not incident_result:
            return {
                "error": f"Incident {incident_id} not found",
                "captured_at": datetime.now(timezone.utc).isoformat(),
            }

        # Validate not a simulation ID
        if incident_id.startswith("sim_") or incident_id.startswith("inc_sim_"):
            return {
                "error": "REJECTED: Incident ID has simulation prefix. Real evidence required.",
                "incident_id": incident_id,
                "captured_at": datetime.now(timezone.utc).isoformat(),
            }

        stage_1 = {
            "incident_id": incident_result[0],
            "tenant_id": incident_result[1],
            "title": incident_result[2],
            "severity": incident_result[3],
            "created_at": str(incident_result[4]) if incident_result[4] else None,
            "status": incident_result[5],
        }

        if tenant_id and stage_1["tenant_id"] != tenant_id:
            return {
                "error": f"Tenant mismatch: incident belongs to {stage_1['tenant_id']}, not {tenant_id}",
                "captured_at": datetime.now(timezone.utc).isoformat(),
            }

        effective_tenant_id = tenant_id or stage_1["tenant_id"]

        # =====================================================================
        # STAGE 2: Loop Trace & Pattern Matching
        # =====================================================================
        # Check if loop_traces table exists
        table_check = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'loop_traces'
            )
        """)).scalar()

        stage_2 = None
        loop_trace_id = None

        if table_check:
            loop_trace_result = conn.execute(text("""
                SELECT id, stages, failure_state, started_at, completed_at, is_complete
                FROM loop_traces
                WHERE incident_id = :incident_id
                ORDER BY started_at DESC
                LIMIT 1
            """), {"incident_id": incident_id}).fetchone()

            if loop_trace_result:
                loop_trace_id = loop_trace_result[0]
                stages = loop_trace_result[1] or {}

                # Extract pattern matching from stages
                pattern_stage = stages.get("pattern_matched", {})

                stage_2 = {
                    "loop_trace_id": loop_trace_id,
                    "pattern_id": pattern_stage.get("pattern_id"),
                    "confidence_band": pattern_stage.get("confidence_band"),
                    "matched_at": pattern_stage.get("matched_at"),
                    "stages": stages,
                    "failure_state": loop_trace_result[2],
                    "started_at": str(loop_trace_result[3]) if loop_trace_result[3] else None,
                    "completed_at": str(loop_trace_result[4]) if loop_trace_result[4] else None,
                    "is_complete": loop_trace_result[5],
                }
        else:
            stage_2 = {"warning": "loop_traces table not found - migrations 042+ not applied"}

        # Also check loop_events for pattern matching
        loop_event_result = None
        if table_check:
            loop_event_result = conn.execute(text("""
                SELECT id, stage, details, confidence_band, created_at
                FROM loop_events
                WHERE incident_id = :incident_id
                AND stage = 'pattern_matched'
                ORDER BY created_at DESC
                LIMIT 1
            """), {"incident_id": incident_id}).fetchone()

            if loop_event_result and stage_2:
                stage_2["loop_event_id"] = loop_event_result[0]
                if loop_event_result[3]:  # confidence_band from event
                    stage_2["confidence_band"] = loop_event_result[3]

        # =====================================================================
        # STAGE 3: Recovery Application
        # =====================================================================
        # Check schema version - M25 migrations add source_incident_id column
        has_source_incident_id = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'recovery_candidates'
                AND column_name = 'source_incident_id'
            )
        """)).scalar()

        stage_3 = None

        if has_source_incident_id:
            # M25 schema - query by source_incident_id
            recovery_result = conn.execute(text("""
                SELECT id, decision, suggestion, executed_at, created_at
                FROM recovery_candidates
                WHERE source_incident_id = :incident_id
                AND decision = 'applied'
                ORDER BY executed_at DESC
                LIMIT 1
            """), {"incident_id": incident_id}).fetchone()

            if recovery_result:
                stage_3 = {
                    "recovery_id": str(recovery_result[0]),
                    "status": recovery_result[1],
                    "suggestion": recovery_result[2],
                    "applied_at": str(recovery_result[3]) if recovery_result[3] else None,
                    "created_at": str(recovery_result[4]) if recovery_result[4] else None,
                }
            else:
                # Check if any recovery exists (not just applied)
                any_recovery = conn.execute(text("""
                    SELECT id, decision, suggestion, created_at
                    FROM recovery_candidates
                    WHERE source_incident_id = :incident_id
                    ORDER BY created_at DESC
                    LIMIT 1
                """), {"incident_id": incident_id}).fetchone()

                if any_recovery:
                    stage_3 = {
                        "warning": f"Recovery exists but decision is '{any_recovery[1]}', not 'applied'",
                        "recovery_id": str(any_recovery[0]),
                        "status": any_recovery[1],
                        "suggestion": any_recovery[2],
                    }
                else:
                    stage_3 = {"warning": "No recovery candidate found for this incident"}
        else:
            # Pre-M25 schema - migrations not applied
            # The current schema doesn't directly link incidents to recovery_candidates
            # We need M25 migrations applied first
            stage_3 = {
                "warning": "M25 migrations (042-044) not applied",
                "action_required": "Run: DATABASE_URL=... alembic upgrade head",
                "migrations_needed": [
                    "042_m25_integration_loop.py",
                    "043_m25_learning_proof.py",
                    "044_m25_graduation_hardening.py",
                ],
            }

        # =====================================================================
        # STAGE 4: Policy Generation & Mode Transition
        # =====================================================================
        # Check if policy_rules table exists
        policy_table_check = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'policy_rules'
            )
        """)).scalar()

        stage_4 = None
        policy_id = None

        if policy_table_check:
            # Find policy born from this recovery
            recovery_id = stage_3.get("recovery_id") if stage_3 and "recovery_id" in stage_3 else None

            if recovery_id:
                policy_result = conn.execute(text("""
                    SELECT id, mode, source_type, created_at, activated_at,
                           shadow_evaluations, shadow_would_block, confirmations_received
                    FROM policy_rules
                    WHERE source_recovery_id = :recovery_id
                    ORDER BY created_at DESC
                    LIMIT 1
                """), {"recovery_id": recovery_id}).fetchone()

                if policy_result:
                    policy_id = policy_result[0]
                    stage_4 = {
                        "policy_id": policy_id,
                        "mode": policy_result[1],
                        "source_type": policy_result[2],
                        "created_at": str(policy_result[3]) if policy_result[3] else None,
                        "activated_at": str(policy_result[4]) if policy_result[4] else None,
                        "shadow_evaluations": policy_result[5],
                        "shadow_would_block": policy_result[6],
                        "confirmations_received": policy_result[7],
                        "mode_transition": "pending" if not policy_result[4] else "shadow -> active",
                    }
                else:
                    stage_4 = {"warning": f"No policy found for recovery {recovery_id}"}
            else:
                stage_4 = {"warning": "No recovery_id to trace policy from"}
        else:
            stage_4 = {"warning": "policy_rules table not found - migrations not complete"}

        # =====================================================================
        # STAGE 5: Prevention Event (THE PROOF)
        # =====================================================================
        # Check if prevention_records table exists
        prevention_table_check = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'prevention_records'
            )
        """)).scalar()

        stage_5 = None

        if prevention_table_check:
            # Find prevention event that references original incident
            prevention_result = conn.execute(text("""
                SELECT id, policy_id, pattern_id, blocked_incident_id, outcome,
                       signature_match_confidence, is_simulated, created_at
                FROM prevention_records
                WHERE original_incident_id = :incident_id
                AND is_simulated = false
                ORDER BY created_at DESC
                LIMIT 1
            """), {"incident_id": incident_id}).fetchone()

            if prevention_result:
                # CRITICAL: Verify is_simulated = false
                if prevention_result[6]:  # is_simulated = true
                    stage_5 = {
                        "error": "REJECTED: Prevention record has is_simulated=true",
                        "prevention_id": prevention_result[0],
                        "is_simulated": True,
                    }
                else:
                    stage_5 = {
                        "prevention_id": prevention_result[0],
                        "policy_id": prevention_result[1],
                        "pattern_id": prevention_result[2],
                        "blocked_incident_id": prevention_result[3],
                        "outcome": prevention_result[4],
                        "signature_match_confidence": prevention_result[5],
                        "is_simulated": False,
                        "created_at": str(prevention_result[7]) if prevention_result[7] else None,
                    }
            else:
                # Check if any prevention exists (including simulated)
                any_prevention = conn.execute(text("""
                    SELECT id, is_simulated, created_at
                    FROM prevention_records
                    WHERE original_incident_id = :incident_id
                    ORDER BY created_at DESC
                    LIMIT 1
                """), {"incident_id": incident_id}).fetchone()

                if any_prevention:
                    stage_5 = {
                        "warning": "Prevention exists but is_simulated=true - does not count",
                        "prevention_id": any_prevention[0],
                        "is_simulated": any_prevention[1],
                    }
                else:
                    stage_5 = {
                        "warning": "No prevention event found yet for this incident",
                        "status": "WAITING_FOR_PREVENTION",
                    }
        else:
            stage_5 = {"warning": "prevention_records table not found - migrations 043+ not applied"}

        # =====================================================================
        # STAGE 6: Graduation Delta
        # =====================================================================
        # Check if graduation_history table exists
        graduation_table_check = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'graduation_history'
            )
        """)).scalar()

        stage_6 = None

        if graduation_table_check and stage_5 and "prevention_id" in stage_5 and not stage_5.get("is_simulated"):
            prevention_created_at = stage_5.get("created_at")

            if prevention_created_at:
                # Get graduation state BEFORE prevention
                before_result = conn.execute(text("""
                    SELECT level, gates_json, computed_at, is_degraded
                    FROM graduation_history
                    WHERE computed_at < :prevention_time
                    ORDER BY computed_at DESC
                    LIMIT 1
                """), {"prevention_time": prevention_created_at}).fetchone()

                # Get graduation state AFTER prevention
                after_result = conn.execute(text("""
                    SELECT level, gates_json, computed_at, is_degraded
                    FROM graduation_history
                    WHERE computed_at >= :prevention_time
                    ORDER BY computed_at ASC
                    LIMIT 1
                """), {"prevention_time": prevention_created_at}).fetchone()

                before_state = None
                after_state = None

                if before_result:
                    before_state = {
                        "level": before_result[0],
                        "gates": before_result[1],
                        "computed_at": str(before_result[2]) if before_result[2] else None,
                        "is_degraded": before_result[3],
                    }

                if after_result:
                    after_state = {
                        "level": after_result[0],
                        "gates": after_result[1],
                        "computed_at": str(after_result[2]) if after_result[2] else None,
                        "is_degraded": after_result[3],
                    }

                # Compute delta
                delta = None
                if before_state and after_state:
                    before_gates = before_state.get("gates") or {}
                    after_gates = after_state.get("gates") or {}

                    delta = {
                        "level_change": f"{before_state['level']} -> {after_state['level']}" if before_state['level'] != after_state['level'] else "unchanged",
                        "gate1_change": f"{before_gates.get('prevention', False)} -> {after_gates.get('prevention', False)}",
                        "gate2_change": f"{before_gates.get('rollback', False)} -> {after_gates.get('rollback', False)}",
                        "gate3_change": f"{before_gates.get('timeline', False)} -> {after_gates.get('timeline', False)}",
                    }

                stage_6 = {
                    "before": before_state,
                    "after": after_state,
                    "delta": delta,
                }

                if not before_state and not after_state:
                    stage_6["warning"] = "No graduation history records found"
            else:
                stage_6 = {"warning": "Cannot compute delta without prevention timestamp"}
        else:
            stage_6 = {"warning": "graduation_history table not found or no valid prevention event"}

    # =========================================================================
    # BUILD EVIDENCE BUNDLE
    # =========================================================================
    captured_at = datetime.now(timezone.utc).isoformat()

    evidence_bundle = {
        "evidence_trail_id": f"trail_{hashlib.sha256(incident_id.encode()).hexdigest()[:16]}",
        "captured_at": captured_at,
        "capture_version": "1.0.0",
        "is_simulated": False,

        "source_incident_id": incident_id,
        "tenant_id": effective_tenant_id,

        "stages": {
            "stage_1_incident": stage_1,
            "stage_2_pattern": stage_2,
            "stage_3_recovery": stage_3,
            "stage_4_policy": stage_4,
            "stage_5_prevention": stage_5,
            "stage_6_graduation": stage_6,
        },

        "completeness": {
            "has_incident": stage_1 is not None and "error" not in stage_1,
            "has_loop_trace": stage_2 is not None and "warning" not in stage_2,
            "has_recovery": stage_3 is not None and "warning" not in stage_3,
            "has_policy": stage_4 is not None and "warning" not in stage_4,
            "has_prevention": stage_5 is not None and "prevention_id" in stage_5 and not stage_5.get("is_simulated"),
            "has_graduation_delta": stage_6 is not None and "delta" in stage_6,
        },
    }

    # Compute completeness score
    completeness = evidence_bundle["completeness"]
    stages_complete = sum([
        completeness["has_incident"],
        completeness["has_loop_trace"],
        completeness["has_recovery"],
        completeness["has_policy"],
        completeness["has_prevention"],
        completeness["has_graduation_delta"],
    ])

    evidence_bundle["completeness"]["score"] = f"{stages_complete}/6"
    evidence_bundle["completeness"]["is_complete"] = stages_complete == 6

    # Determine overall status
    if stages_complete == 6:
        evidence_bundle["status"] = "COMPLETE"
        evidence_bundle["message"] = "Full closed-loop proof captured. M26 can proceed."
    elif completeness["has_incident"] and completeness["has_recovery"] and not completeness["has_prevention"]:
        evidence_bundle["status"] = "WAITING_FOR_PREVENTION"
        evidence_bundle["message"] = "Incident processed, recovery applied, awaiting prevention event."
    elif not completeness["has_incident"]:
        evidence_bundle["status"] = "INVALID"
        evidence_bundle["message"] = "Source incident not found."
    else:
        evidence_bundle["status"] = "INCOMPLETE"
        missing = [k.replace("has_", "") for k, v in completeness.items() if isinstance(v, bool) and not v]
        evidence_bundle["message"] = f"Missing stages: {', '.join(missing)}"

    # =========================================================================
    # COMPUTE INTEGRITY HASHES
    # =========================================================================
    # Hash each stage independently
    stage_hashes = {}
    for stage_name, stage_data in evidence_bundle["stages"].items():
        if stage_data:
            stage_hashes[stage_name] = compute_hash(stage_data)

    # Compute root hash
    root_hash = compute_hash({
        "stages": stage_hashes,
        "captured_at": captured_at,
        "source_incident_id": incident_id,
    })

    evidence_bundle["integrity"] = {
        "stage_hashes": stage_hashes,
        "root_hash": root_hash,
        "algorithm": "SHA256",
        "canonical_format": "JSON, sorted keys, str(datetime)",
    }

    return evidence_bundle


def main():
    parser = argparse.ArgumentParser(
        description="M25 Evidence Trail Capture (READ-ONLY)",
        epilog="Per PIN-131: M25 Real Evidence Trail Capture Protocol"
    )
    parser.add_argument(
        "--incident-id",
        required=True,
        help="Real incident ID (must NOT have sim_ prefix)"
    )
    parser.add_argument(
        "--tenant-id",
        help="Optional tenant ID filter"
    )
    parser.add_argument(
        "--time-window",
        type=int,
        default=168,
        help="Time window in hours (default: 168 = 7 days)"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path (default: stdout)"
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty print JSON output"
    )

    args = parser.parse_args()

    # Validate incident ID doesn't have simulation prefix
    if args.incident_id.startswith("sim_") or args.incident_id.startswith("inc_sim_"):
        print(json.dumps({
            "error": "REJECTED: Incident ID has simulation prefix. Real evidence only.",
            "incident_id": args.incident_id,
        }, indent=2))
        sys.exit(1)

    # Capture evidence
    evidence = capture_evidence_trail(
        incident_id=args.incident_id,
        tenant_id=args.tenant_id,
        time_window_hours=args.time_window,
    )

    # Output
    indent = 2 if args.pretty else None
    output = json.dumps(evidence, indent=indent, default=str)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Evidence trail written to: {args.output}")
        print(f"Status: {evidence.get('status', 'UNKNOWN')}")
        print(f"Completeness: {evidence.get('completeness', {}).get('score', '?')}")
    else:
        print(output)

    # Exit code based on status
    status = evidence.get("status", "UNKNOWN")
    if status == "COMPLETE":
        sys.exit(0)
    elif status == "WAITING_FOR_PREVENTION":
        sys.exit(2)  # Retry later
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
