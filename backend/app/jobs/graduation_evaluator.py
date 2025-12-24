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
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def evaluate_graduation_status() -> dict:
    """
    Evaluate graduation status from evidence.

    Returns the computed status with degradation info if applicable.
    """
    from sqlalchemy import text

    from app.db import get_async_session
    from app.integrations.graduation_engine import (
        CapabilityGates,
        GraduationEngine,
        GraduationEvidence,
    )

    async with get_async_session() as session:
        engine = GraduationEngine()

        try:
            evidence = await GraduationEvidence.fetch_from_database(session)
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
