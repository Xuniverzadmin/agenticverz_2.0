#!/usr/bin/env python3
"""
M25 Policy Activation Script

STEP 3: Activate exactly ONE policy for graduation testing.

Criteria:
- Strongest pattern (highest occurrence count)
- Confidence >= 0.85
- Zero regret so far
- Currently in shadow mode
"""

import os
import sys
from datetime import datetime, timezone


def main():
    import psycopg2
    from psycopg2.extras import DictCursor

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)

    conn = psycopg2.connect(database_url)
    conn.autocommit = False

    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            # Find the strongest policy
            cur.execute(
                """
                SELECT
                    pr.id AS policy_id,
                    pr.name,
                    pr.source_pattern_id,
                    pr.source_recovery_id,
                    pr.generation_confidence,
                    pr.mode,
                    pr.regret_count,
                    fp.occurrence_count,
                    pr.tenant_id
                FROM policy_rules pr
                LEFT JOIN failure_patterns fp ON pr.source_pattern_id = fp.id
                WHERE pr.generation_confidence >= 0.85
                AND pr.mode = 'shadow'
                AND pr.regret_count = 0
                ORDER BY fp.occurrence_count DESC NULLS LAST, pr.generation_confidence DESC
                LIMIT 1
            """
            )
            row = cur.fetchone()

            if not row:
                print("ERROR: No eligible policy found for activation")
                print(
                    "Requirements: confidence >= 0.85, mode = shadow, regret_count = 0"
                )
                sys.exit(1)

            policy_id = row["policy_id"]
            pattern_id = row["source_pattern_id"]
            recovery_id = row["source_recovery_id"] or "unknown"
            confidence = row["generation_confidence"]
            tenant_id = row["tenant_id"]
            occurrence_count = row["occurrence_count"]

            print("=" * 60)
            print("M25 POLICY ACTIVATION")
            print("=" * 60)
            print(f"Policy ID:      {policy_id}")
            print(f"Pattern ID:     {pattern_id}")
            print(f"Confidence:     {confidence:.2f}")
            print(f"Occurrences:    {occurrence_count}")
            print(f"Tenant:         {tenant_id}")
            print("=" * 60)

            # Activate the policy
            cur.execute(
                """
                UPDATE policy_rules
                SET mode = 'active',
                    is_active = TRUE,
                    updated_at = NOW()
                WHERE id = %s
            """,
                (policy_id,),
            )

            # Create activation audit record
            loop_trace_id = "loop_activation_m25"  # Manual activation trace
            cur.execute(
                """
                INSERT INTO policy_activation_audit
                (policy_id, source_pattern_id, source_recovery_id,
                 confidence_at_activation, confidence_version, approval_path,
                 loop_trace_id, activated_at, tenant_id)
                VALUES (%s, %s, %s, %s, 'CONFIDENCE_V1', 'manual:m25_graduation',
                        %s, %s, %s)
                ON CONFLICT (policy_id) DO UPDATE SET
                    confidence_at_activation = EXCLUDED.confidence_at_activation,
                    approval_path = 'manual:m25_graduation',
                    activated_at = EXCLUDED.activated_at
            """,
                (
                    policy_id,
                    pattern_id,
                    recovery_id,
                    confidence,
                    loop_trace_id,
                    datetime.now(timezone.utc),
                    tenant_id,
                ),
            )

            conn.commit()

            print()
            print("✅ POLICY ACTIVATED")
            print()
            print("NEXT STEPS:")
            print("1. WAIT at least 30-60 minutes (let system stabilize)")
            print("2. Trigger ONE similar request to the activated pattern")
            print("3. Verify prevention_record is created")
            print("4. Check graduation gate movement")
            print()
            print("Pattern signature to trigger: data_export_blocked")
            print()

    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
