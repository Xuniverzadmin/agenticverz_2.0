#!/usr/bin/env python3
"""
M25 Graduation Delta Evaluation

# =============================================================================
# M25_FROZEN - DO NOT MODIFY
# =============================================================================
# Any changes here require explicit M25 reopen approval.
# Changes invalidate all prior graduation evidence.
# See PIN-140 for freeze rationale.
# GRADUATION_RULES_VERSION = "1.0.0"
# =============================================================================

STEP 7: Run graduation evaluation after prevention.

Expected outcome:
- Gate 1 movement only (prevention gate)
- Graduation should NOT jump levels
- If it does more than expected → stop and inspect
"""

import os
import sys
from datetime import datetime, timezone


def main():
    import psycopg2
    from psycopg2.extras import DictCursor, Json

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)

    conn = psycopg2.connect(database_url)

    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            print("=" * 60)
            print("M25 GRADUATION DELTA EVALUATION")
            print("=" * 60)

            # Get the active policy
            cur.execute(
                """
                SELECT
                    pr.id AS policy_id,
                    pr.source_pattern_id,
                    pr.tenant_id,
                    paa.activated_at,
                    paa.confidence_at_activation,
                    paa.confidence_version
                FROM policy_rules pr
                LEFT JOIN policy_activation_audit paa ON pr.id = paa.policy_id
                WHERE pr.mode = 'active'
                AND pr.is_active = TRUE
                LIMIT 1
            """
            )
            policy = cur.fetchone()

            if not policy:
                print("ERROR: No active policy found")
                sys.exit(1)

            policy_id = policy["policy_id"]
            pattern_id = policy["source_pattern_id"]
            tenant_id = policy["tenant_id"]
            activated_at = policy["activated_at"]

            print(f"\nPolicy:       {policy_id}")
            print(f"Pattern:      {pattern_id}")
            print(f"Activated:    {activated_at}")
            print(
                f"Confidence:   {policy['confidence_at_activation']} ({policy['confidence_version']})"
            )

            # Gate 1: Prevention count (non-simulated, after activation)
            cur.execute(
                """
                SELECT COUNT(*) as count
                FROM prevention_records
                WHERE policy_id = %s
                AND is_simulated = FALSE
                AND created_at > %s
            """,
                (policy_id, activated_at),
            )
            gate1_result = cur.fetchone()
            gate1_count = gate1_result["count"]

            # Gate 2: Regret count (should be 0)
            cur.execute(
                """
                SELECT regret_count
                FROM policy_rules
                WHERE id = %s
            """,
                (policy_id,),
            )
            gate2_result = cur.fetchone()
            regret_count = gate2_result["regret_count"] or 0

            # Gate 3: Timeline views (non-simulated views for this tenant)
            cur.execute(
                """
                SELECT COUNT(*) as count
                FROM timeline_views
                WHERE tenant_id = %s
                AND is_simulated = FALSE
            """,
                (tenant_id,),
            )
            gate3_result = cur.fetchone()
            timeline_views = gate3_result["count"]

            print("\n" + "=" * 60)
            print("GRADUATION GATES STATUS")
            print("=" * 60)

            # Gate 1: Prevention
            gate1_pass = gate1_count >= 1
            gate1_status = "✅ PASS" if gate1_pass else "❌ FAIL"
            print("\nGate 1 (Prevention):")
            print(f"  Real preventions after activation: {gate1_count}")
            print("  Required: >= 1")
            print(f"  Status: {gate1_status}")

            # Gate 2: Rollback
            gate2_pass = regret_count == 0
            gate2_status = "✅ PASS" if gate2_pass else "❌ FAIL"
            print("\nGate 2 (Rollback/Regret):")
            print(f"  Regret count: {regret_count}")
            print("  Required: 0")
            print(f"  Status: {gate2_status}")

            # Gate 3: Timeline
            gate3_pass = timeline_views >= 1
            gate3_status = "✅ PASS" if gate3_pass else "⏳ PENDING"
            print("\nGate 3 (Timeline Views):")
            print(f"  Real user timeline views: {timeline_views}")
            print("  Required: >= 1")
            print(f"  Status: {gate3_status}")

            # Calculate overall graduation status
            gates_passed = sum([gate1_pass, gate2_pass, gate3_pass])

            print("\n" + "=" * 60)
            print("GRADUATION SUMMARY")
            print("=" * 60)
            print(f"\nGates Passed: {gates_passed}/3")

            if gates_passed == 0:
                status = "NOT_STARTED"
            elif gates_passed == 1:
                status = "PREVENTION_PROVEN"
            elif gates_passed == 2:
                status = "ROLLBACK_SAFE"
            elif gates_passed == 3:
                status = "GRADUATED"
            else:
                status = "UNKNOWN"

            print(f"Status: {status}")

            # Record graduation delta in history
            cur.execute(
                """
                INSERT INTO graduation_history
                (level, gates_json, computed_at, evidence_snapshot)
                VALUES (%s, %s, %s, %s)
            """,
                (
                    status,
                    Json(
                        {
                            "gate1_prevention": {
                                "count": gate1_count,
                                "passed": gate1_pass,
                            },
                            "gate2_rollback": {
                                "regret_count": regret_count,
                                "passed": gate2_pass,
                            },
                            "gate3_timeline": {
                                "views": timeline_views,
                                "passed": gate3_pass,
                            },
                        }
                    ),
                    datetime.now(timezone.utc),
                    Json(
                        {
                            "policy_id": policy_id,
                            "pattern_id": pattern_id,
                            "tenant_id": tenant_id,
                            "gates_passed": gates_passed,
                            "evaluation_type": "m25_graduation_delta",
                        }
                    ),
                ),
            )
            conn.commit()

            print("\nGraduation delta recorded in graduation_history")

            # Expected outcome check
            print("\n" + "=" * 60)
            print("EXPECTED OUTCOME CHECK")
            print("=" * 60)

            # Gate 1 (Prevention) should move with our test
            # Gate 2 (Rollback) is naturally 0 if no regrets have been recorded
            # Gate 3 (Timeline) should NOT pass unless real user viewed
            if gate1_pass and gate3_pass:
                print("⚠️ WARNING: Gate 3 passed unexpectedly - INSPECT")
            elif gate1_pass:
                print("✅ CORRECT: Gate 1 (Prevention) proven")
                if gate2_pass:
                    print("✅ CORRECT: Gate 2 (Rollback) safe - no regrets recorded")
                if not gate3_pass:
                    print(
                        "✅ CORRECT: Gate 3 (Timeline) pending - awaits real user view"
                    )
            else:
                print("❌ Gate 1 did not move - prevention may have failed")

            print("=" * 60)

    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
