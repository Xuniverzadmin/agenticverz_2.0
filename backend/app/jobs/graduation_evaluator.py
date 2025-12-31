# Layer: L5 — Execution & Workers
# Product: system-wide
# Temporal:
#   Trigger: scheduler
#   Execution: async
# Role: Agent graduation evaluation job (orchestration only)
# Callers: scheduler
# Allowed Imports: L4, L6
# Domain Engine: graduation_engine.py (L4)
# Forbidden Imports: L1, L2, L3
# Reference: PIN-256 Phase E FIX-01
#
# GOVERNANCE NOTE: L5 owns all DB operations.
# L4 graduation_engine.py provides pure domain logic only.
# This L5 file:
#   - Fetches evidence FROM database (L6)
#   - Calls L4 engine.compute() to get decisions
#   - Persists results TO database (L6)

"""
M25 Graduation Status Periodic Evaluator

This job runs periodically to:
1. Re-evaluate graduation status from evidence
2. Detect degradation when evidence regresses
3. Update capability lockouts
4. Store graduation history for audit trail

Schedule: Every 15 minutes (recommended)

CRITICAL INVARIANTS:
- Graduation is DERIVED from evidence, never manually set
- Simulated records are excluded
- Degradation is detected and recorded
- Capability gates are updated based on graduation level
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


# =============================================================================
# EVIDENCE FETCH (L5 responsibility - moved from L4 graduation_engine.py)
# =============================================================================


async def fetch_graduation_evidence(session, window_days: int = 30):
    """
    Fetch graduation evidence from database.

    This is an L5/L6 responsibility - DB operations stay in L5.
    L4 graduation_engine.py receives only the computed evidence dataclass.

    Reference: PIN-256 Phase E FIX-01, DOMAIN_EXTRACTION_TEMPLATE.md Section 7.1
    """
    from sqlalchemy import text

    from app.integrations.graduation_engine import GraduationEvidence

    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=window_days)

    # Gate 1: Prevention evidence (exclude simulated)
    prevention_result = await session.execute(
        text(
            """
            SELECT
                COUNT(*) FILTER (WHERE outcome = 'prevented') as prevented,
                COUNT(*) as total,
                MAX(created_at) as last_at
            FROM prevention_records
            WHERE created_at >= :window_start
            AND (
                id NOT LIKE 'prev_sim_%' OR id IS NULL
            )
        """
        ),
        {"window_start": window_start},
    )
    prev_row = prevention_result.fetchone()

    # Gate 2: Regret evidence (exclude simulated)
    regret_result = await session.execute(
        text(
            """
            SELECT
                COUNT(*) as total_events,
                COUNT(*) FILTER (WHERE was_auto_rolled_back = true) as demotions,
                MAX(created_at) FILTER (WHERE was_auto_rolled_back = true) as last_demotion
            FROM regret_events
            WHERE created_at >= :window_start
            AND (
                id NOT LIKE 'regret_sim_%' OR id IS NULL
            )
        """
        ),
        {"window_start": window_start},
    )
    regret_row = regret_result.fetchone()

    # Gate 3: Timeline views (real user views only)
    timeline_result = await session.execute(
        text(
            """
            SELECT
                COUNT(*) as views_with_prevention,
                MAX(viewed_at) as last_view
            FROM timeline_views
            WHERE viewed_at >= :window_start
            AND has_prevention = true
            AND is_simulated = false
        """
        ),
        {"window_start": window_start},
    )
    timeline_row = timeline_result.fetchone()

    # Compute rates
    total_prevention_attempts = prev_row.total if prev_row else 0
    total_preventions = prev_row.prevented if prev_row else 0
    prevention_rate = total_preventions / total_prevention_attempts if total_prevention_attempts > 0 else 0.0

    # Get total policy evaluations for regret rate calculation
    total_policy_evaluations = await _get_total_policy_evaluations(session, window_start)
    regret_rate = (regret_row.total_events or 0) / total_policy_evaluations if total_policy_evaluations > 0 else 0.0

    return GraduationEvidence(
        total_preventions=total_preventions,
        total_prevention_attempts=total_prevention_attempts,
        last_prevention_at=prev_row.last_at if prev_row else None,
        prevention_rate=prevention_rate,
        total_regret_events=regret_row.total_events if regret_row else 0,
        total_auto_demotions=regret_row.demotions if regret_row else 0,
        last_demotion_at=regret_row.last_demotion if regret_row else None,
        regret_rate=regret_rate,
        timeline_views_with_prevention=timeline_row.views_with_prevention if timeline_row else 0,
        last_timeline_view_at=timeline_row.last_view if timeline_row else None,
        evaluated_at=now,
        evidence_window_start=window_start,
        evidence_window_end=now,
    )


async def _get_total_policy_evaluations(session, window_start: datetime) -> int:
    """Get total policy evaluations for regret rate calculation.

    Falls back to policy_rules count if policy_evaluations table doesn't exist.
    """
    from sqlalchemy import text

    # Check if policy_evaluations table exists
    table_check = await session.execute(
        text(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'policy_evaluations'
            )
        """
        )
    )
    has_policy_evaluations = table_check.scalar()

    if has_policy_evaluations:
        result = await session.execute(
            text(
                """
                SELECT COUNT(*) as total
                FROM policy_evaluations
                WHERE created_at >= :window_start
            """
            ),
            {"window_start": window_start},
        )
        row = result.fetchone()
        return row.total if row else 0

    # Fall back to policy_rules count
    table_check2 = await session.execute(
        text(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'policy_rules'
            )
        """
        )
    )
    has_policy_rules = table_check2.scalar()

    if has_policy_rules:
        result = await session.execute(
            text(
                """
                SELECT COUNT(*) as total
                FROM policy_rules
                WHERE created_at >= :window_start
            """
            ),
            {"window_start": window_start},
        )
        row = result.fetchone()
        return row.total if row else 0

    return 0


async def evaluate_graduation_status() -> dict:
    """
    Evaluate graduation status from evidence.

    Returns the computed status with degradation info if applicable.

    GOVERNANCE NOTE (Phase E FIX-01):
    - L5 fetches evidence FROM database (fetch_graduation_evidence)
    - L4 computes decision (engine.compute)
    - L5 persists results TO database
    - No DB operations cross into L4. L4 is pure.
    """
    from sqlalchemy import text

    from app.db import get_async_session
    from app.integrations.graduation_engine import (
        CapabilityGates,
        GraduationEngine,
    )

    async with get_async_session() as session:
        engine = GraduationEngine()

        try:
            # L5 responsibility: fetch evidence from DB
            evidence = await fetch_graduation_evidence(session)
            # L4 responsibility: compute domain decision (pure, sync)
            status = engine.compute(evidence)
        except Exception as e:
            logger.error(f"Failed to fetch graduation evidence: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

        # Get previous status for degradation detection
        prev_result = await session.execute(
            text(
                """
                SELECT level, is_degraded
                FROM graduation_history
                ORDER BY computed_at DESC
                LIMIT 1
            """
            )
        )
        prev_row = prev_result.fetchone()

        # Check if degradation just occurred
        degradation_just_occurred = prev_row and not prev_row.is_degraded and status.is_degraded

        # Store in graduation_history
        await session.execute(
            text(
                """
                INSERT INTO graduation_history (
                    level, gates_json, computed_at, is_degraded,
                    degraded_from, degradation_reason, evidence_snapshot
                ) VALUES (
                    :level, :gates_json, NOW(), :is_degraded,
                    :degraded_from, :degradation_reason, :evidence_snapshot
                )
            """
            ),
            {
                "level": status.level.value,
                "gates_json": json.dumps(
                    {
                        name: {
                            "passed": gate.passed,
                            "score": gate.score,
                            "degraded": gate.degraded,
                        }
                        for name, gate in status.gates.items()
                    }
                ),
                "is_degraded": status.is_degraded,
                "degraded_from": status.degraded_from.value if status.degraded_from else None,
                "degradation_reason": status.degradation_reason,
                "evidence_snapshot": json.dumps(
                    {
                        "prevention_count": evidence.prevention_count,
                        "regret_count": evidence.regret_count,
                        "demotion_count": evidence.demotion_count,
                        "timeline_view_count": evidence.timeline_view_count,
                        "prevention_rate": evidence.prevention_rate,
                        "regret_rate": evidence.regret_rate,
                    }
                ),
            },
        )

        # Update m25_graduation_status with derived values
        await session.execute(
            text(
                """
                UPDATE m25_graduation_status
                SET is_derived = true,
                    last_evidence_eval = NOW(),
                    status_label = :status_label,
                    is_graduated = :is_graduated,
                    gate1_passed = :gate1_passed,
                    gate2_passed = :gate2_passed,
                    gate3_passed = :gate3_passed,
                    degraded_from = :degraded_from,
                    degradation_reason = :degradation_reason,
                    last_checked = NOW()
                WHERE id = 1
            """
            ),
            {
                "status_label": status.status_label,
                "is_graduated": status.is_graduated,
                "gate1_passed": status.gates.get("prevention", type("", (), {"passed": False})).passed,
                "gate2_passed": status.gates.get("rollback", type("", (), {"passed": False})).passed,
                "gate3_passed": status.gates.get("timeline", type("", (), {"passed": False})).passed,
                "degraded_from": status.degraded_from.value if status.degraded_from else None,
                "degradation_reason": status.degradation_reason,
            },
        )

        # Update capability lockouts based on gates
        capabilities = {
            "auto_apply_recovery": CapabilityGates.can_auto_apply_recovery(status),
            "auto_activate_policy": CapabilityGates.can_auto_activate_policy(status),
            "full_auto_routing": CapabilityGates.can_full_auto_routing(status),
        }

        for capability, is_unlocked in capabilities.items():
            await session.execute(
                text(
                    """
                    UPDATE capability_lockouts
                    SET is_unlocked = :is_unlocked,
                        unlocked_at = CASE WHEN :is_unlocked AND NOT is_unlocked THEN NOW() ELSE unlocked_at END,
                        last_checked = NOW()
                    WHERE capability = :capability
                """
                ),
                {
                    "capability": capability,
                    "is_unlocked": is_unlocked,
                },
            )

        await session.commit()

        # Log degradation alert if it just occurred
        if degradation_just_occurred:
            logger.warning(
                f"M25 DEGRADATION ALERT: Status degraded from {status.degraded_from.value} "
                f"to {status.level.value}. Reason: {status.degradation_reason}"
            )

        return {
            "status": "evaluated",
            "level": status.level.value,
            "is_graduated": status.is_graduated,
            "is_degraded": status.is_degraded,
            "degradation_just_occurred": degradation_just_occurred,
            "gates_passed": sum(1 for g in status.gates.values() if g.passed),
            "capabilities_unlocked": [k for k, v in capabilities.items() if v],
            "capabilities_blocked": [k for k, v in capabilities.items() if not v],
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }


async def run_periodic_evaluation(interval_seconds: int = 900):
    """
    Run periodic graduation evaluation.

    Default interval: 15 minutes (900 seconds)
    """
    logger.info(f"Starting periodic graduation evaluator (interval: {interval_seconds}s)")

    while True:
        try:
            result = await evaluate_graduation_status()

            if result.get("status") == "evaluated":
                logger.info(f"Graduation evaluated: {result['level']} ({result['gates_passed']}/3 gates)")

                if result.get("degradation_just_occurred"):
                    # Could send alert here (Slack, PagerDuty, etc.)
                    logger.warning("Degradation detected! Alert would be sent here.")
            else:
                logger.warning(f"Graduation evaluation failed: {result}")

        except Exception as e:
            logger.exception(f"Error in graduation evaluator: {e}")

        await asyncio.sleep(interval_seconds)


def main():
    """CLI entry point for manual runs."""
    import argparse

    parser = argparse.ArgumentParser(description="M25 Graduation Evaluator")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--interval", type=int, default=900, help="Evaluation interval in seconds")
    args = parser.parse_args()

    if args.once:
        result = asyncio.run(evaluate_graduation_status())
        print(json.dumps(result, indent=2))
    else:
        asyncio.run(run_periodic_evaluation(args.interval))


if __name__ == "__main__":
    main()
