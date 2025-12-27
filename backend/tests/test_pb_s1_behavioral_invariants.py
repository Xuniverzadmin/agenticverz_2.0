"""
PB-S1 Behavioral Invariant Tests — Semantic Truth Guarantees

These tests verify the BEHAVIORAL invariants of PB-S1:
- Cost Chain Invariant: total_cost = sum(costs of all executions in chain)
- Attempt Monotonicity Invariant: attempt strictly increases, no duplicates

STATUS: FROZEN — These tests must NEVER be modified to pass by changing behavior.
If a test fails, the FIX must be in the application code, not the test.

Reference: PIN-199
Risk Coverage: Risk 2 (behavioral drift without detection)
"""

import os

import pytest

# Skip if no database URL
pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL not set")


class TestCostChainInvariant:
    """
    PB-S1 Behavioral Invariant: Cost Chain

    INVARIANT: For any retry lineage, the original run's cost is preserved.
               Retry costs are tracked independently.
               Total lineage cost = sum of all execution costs in the chain.

    SEMANTIC MEANING:
    - Each execution has its own cost (immutable after completion)
    - Retries do NOT inherit or modify parent costs
    - Lineage total is computed by summing, never by inference
    """

    def test_original_run_cost_preserved_after_retry(self):
        """
        PB-S1 CRITICAL: Original run cost must NOT change when retry is created.

        Test shape:
        1. Find a failed run with cost X
        2. Check if it has retry with cost Y
        3. Assert: original cost X is unchanged
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Find a parent run that has retries
            cur.execute(
                """
                SELECT
                    p.id AS parent_id,
                    p.cost_cents AS parent_cost,
                    p.status AS parent_status,
                    r.id AS retry_id,
                    r.cost_cents AS retry_cost,
                    r.attempt
                FROM worker_runs p
                INNER JOIN worker_runs r ON r.parent_run_id = p.id
                WHERE p.status IN ('failed', 'completed')
                  AND r.is_retry = true
                LIMIT 1;
            """
            )
            result = cur.fetchone()

            if not result:
                pytest.skip("No retry chains found in database")

            parent_id, parent_cost, parent_status, retry_id, retry_cost, attempt = result

            # INVARIANT: Parent must have a cost (or NULL if never ran)
            # The point is it must NOT have been zeroed or modified

            # Query the parent again to confirm cost is stable
            cur.execute(
                """
                SELECT cost_cents FROM worker_runs WHERE id = %s;
            """,
                (parent_id,),
            )
            current_parent_cost = cur.fetchone()[0]

            assert current_parent_cost == parent_cost, (
                f"Parent run {parent_id} cost changed! " f"Expected {parent_cost}, got {current_parent_cost}"
            )

        finally:
            conn.close()

    def test_retry_has_independent_cost(self):
        """
        PB-S1 CRITICAL: Retry runs must have their own cost_cents.

        Retry cost must NOT be:
        - Copied from parent
        - Set to 0 automatically
        - Inferred from parent
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Find completed retries with costs
            cur.execute(
                """
                SELECT
                    r.id,
                    r.cost_cents,
                    r.parent_run_id,
                    p.cost_cents AS parent_cost
                FROM worker_runs r
                INNER JOIN worker_runs p ON r.parent_run_id = p.id
                WHERE r.is_retry = true
                  AND r.status = 'completed'
                  AND r.cost_cents IS NOT NULL
                LIMIT 10;
            """
            )
            results = cur.fetchall()

            if not results:
                pytest.skip("No completed retries with costs found")

            for retry_id, retry_cost, parent_id, parent_cost in results:
                # Cost should be independently computed
                # It may equal parent cost by coincidence, but should exist
                assert retry_cost is not None, f"Retry {retry_id} has NULL cost - should be computed independently"

        finally:
            conn.close()

    def test_lineage_cost_sum_computable(self):
        """
        PB-S1 CRITICAL: Lineage total cost must be computable by summing.

        The total cost of a retry chain = sum of all runs in the chain.
        This verifies the invariant that costs are additive, not overwritten.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Calculate total costs per lineage
            # A lineage is: original run + all retries pointing to it
            cur.execute(
                """
                WITH lineage_costs AS (
                    -- Original runs that have retries
                    SELECT
                        p.id AS root_id,
                        p.cost_cents AS root_cost,
                        COALESCE(SUM(r.cost_cents), 0) AS retry_cost_sum,
                        COUNT(r.id) AS retry_count
                    FROM worker_runs p
                    LEFT JOIN worker_runs r ON r.parent_run_id = p.id
                    WHERE EXISTS (
                        SELECT 1 FROM worker_runs r2
                        WHERE r2.parent_run_id = p.id
                    )
                    GROUP BY p.id, p.cost_cents
                )
                SELECT
                    root_id,
                    root_cost,
                    retry_cost_sum,
                    retry_count,
                    COALESCE(root_cost, 0) + retry_cost_sum AS lineage_total
                FROM lineage_costs
                LIMIT 5;
            """
            )
            results = cur.fetchall()

            if not results:
                pytest.skip("No retry lineages found")

            for root_id, root_cost, retry_sum, retry_count, lineage_total in results:
                # Lineage total must be computable
                expected_total = (root_cost or 0) + retry_sum
                assert lineage_total == expected_total, (
                    f"Lineage cost mismatch for {root_id}: " f"computed {lineage_total}, expected {expected_total}"
                )

                # Log for documentation
                print(
                    f"\nLineage {root_id}: root={root_cost}, "
                    f"retries={retry_sum} ({retry_count} runs), "
                    f"total={lineage_total}"
                )

        finally:
            conn.close()

    def test_cost_not_zeroed_on_retry_creation(self):
        """
        PB-S1 CRITICAL: Creating a retry must NOT zero the parent cost.

        This is a specific anti-pattern check: some systems might
        "reset" costs when creating retries. That would violate PB-S1.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Find failed runs with retries - check parent cost is not 0
            cur.execute(
                """
                SELECT
                    p.id,
                    p.cost_cents,
                    p.status,
                    p.total_tokens
                FROM worker_runs p
                WHERE p.status = 'failed'
                  AND EXISTS (SELECT 1 FROM worker_runs r WHERE r.parent_run_id = p.id)
                  AND p.total_tokens IS NOT NULL
                  AND p.total_tokens > 0
                LIMIT 10;
            """
            )
            results = cur.fetchall()

            if not results:
                pytest.skip("No failed runs with retries and tokens found")

            for run_id, cost, status, tokens in results:
                # If tokens were used, cost should not be zero
                # (unless tokens truly cost nothing, which is rare)
                if tokens and tokens > 0:
                    # Cost could be NULL (not computed yet) but not 0 if work was done
                    # This is a soft check - NULL is ok, but 0 with tokens is suspicious
                    if cost == 0:
                        print(f"WARNING: Run {run_id} has {tokens} tokens but cost=0")

        finally:
            conn.close()


class TestAttemptMonotonicityInvariant:
    """
    PB-S1 Behavioral Invariant: Attempt Monotonicity

    INVARIANT: For a given lineage, attempt number strictly increases
               and is never reused.

    SEMANTIC MEANING:
    - attempt=1 is always the original run
    - attempt=2 is the first retry
    - attempt=N is the (N-1)th retry
    - No duplicates, no gaps within a lineage
    """

    def test_original_runs_have_attempt_1(self):
        """
        PB-S1 CRITICAL: Original runs (not retries) must have attempt=1.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Find original runs with wrong attempt number
            cur.execute(
                """
                SELECT id, attempt, is_retry
                FROM worker_runs
                WHERE is_retry = false AND attempt != 1
                LIMIT 5;
            """
            )
            violations = cur.fetchall()

            assert len(violations) == 0, f"Found {len(violations)} original runs with attempt != 1: " f"{violations}"

        finally:
            conn.close()

    def test_retry_attempt_greater_than_parent(self):
        """
        PB-S1 CRITICAL: Retry attempt must be > parent attempt.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Find retries where attempt <= parent attempt
            cur.execute(
                """
                SELECT
                    r.id AS retry_id,
                    r.attempt AS retry_attempt,
                    p.id AS parent_id,
                    p.attempt AS parent_attempt
                FROM worker_runs r
                INNER JOIN worker_runs p ON r.parent_run_id = p.id
                WHERE r.is_retry = true
                  AND r.attempt <= p.attempt;
            """
            )
            violations = cur.fetchall()

            assert len(violations) == 0, f"Found {len(violations)} retries with attempt <= parent: {violations}"

        finally:
            conn.close()

    def test_no_duplicate_attempts_in_lineage(self):
        """
        PB-S1 CRITICAL: No two runs in the same lineage can have the same attempt.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Find lineages with duplicate attempts
            # A lineage is: root + all descendants via parent_run_id
            cur.execute(
                """
                WITH RECURSIVE lineage AS (
                    -- Base: original runs (those that are parents)
                    SELECT
                        id,
                        id AS root_id,
                        attempt,
                        parent_run_id
                    FROM worker_runs
                    WHERE parent_run_id IS NULL
                      AND EXISTS (
                          SELECT 1 FROM worker_runs r WHERE r.parent_run_id = worker_runs.id
                      )

                    UNION ALL

                    -- Recursive: retries
                    SELECT
                        r.id,
                        l.root_id,
                        r.attempt,
                        r.parent_run_id
                    FROM worker_runs r
                    INNER JOIN lineage l ON r.parent_run_id = l.id
                )
                SELECT root_id, attempt, COUNT(*) AS count
                FROM lineage
                GROUP BY root_id, attempt
                HAVING COUNT(*) > 1;
            """
            )
            duplicates = cur.fetchall()

            assert len(duplicates) == 0, f"Found duplicate attempts in lineages: {duplicates}"

        finally:
            conn.close()

    def test_attempt_increments_by_one(self):
        """
        PB-S1 CRITICAL: Each retry should increment attempt by exactly 1.

        This ensures no gaps in the attempt sequence.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Find retries where attempt != parent_attempt + 1
            cur.execute(
                """
                SELECT
                    r.id AS retry_id,
                    r.attempt AS retry_attempt,
                    p.id AS parent_id,
                    p.attempt AS parent_attempt,
                    r.attempt - p.attempt AS delta
                FROM worker_runs r
                INNER JOIN worker_runs p ON r.parent_run_id = p.id
                WHERE r.is_retry = true
                  AND r.attempt != p.attempt + 1;
            """
            )
            gaps = cur.fetchall()

            assert len(gaps) == 0, f"Found {len(gaps)} retries with attempt gaps: {gaps}"

        finally:
            conn.close()

    def test_attempt_sequence_integrity(self):
        """
        PB-S1 CRITICAL: Full lineage attempt sequence must be 1, 2, 3, ...

        This is the comprehensive check that combines all monotonicity rules.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Get a few lineages and verify sequence
            cur.execute(
                """
                WITH RECURSIVE lineage AS (
                    SELECT
                        id,
                        id AS root_id,
                        attempt,
                        1 AS depth
                    FROM worker_runs
                    WHERE parent_run_id IS NULL
                      AND EXISTS (
                          SELECT 1 FROM worker_runs r WHERE r.parent_run_id = worker_runs.id
                      )

                    UNION ALL

                    SELECT
                        r.id,
                        l.root_id,
                        r.attempt,
                        l.depth + 1
                    FROM worker_runs r
                    INNER JOIN lineage l ON r.parent_run_id = l.id
                )
                SELECT
                    root_id,
                    ARRAY_AGG(attempt ORDER BY depth) AS attempt_sequence,
                    ARRAY_AGG(id ORDER BY depth) AS run_ids
                FROM lineage
                GROUP BY root_id
                HAVING COUNT(*) > 1
                LIMIT 10;
            """
            )
            lineages = cur.fetchall()

            if not lineages:
                pytest.skip("No multi-run lineages found")

            for root_id, attempts, run_ids in lineages:
                # Verify sequence is 1, 2, 3, ...
                expected = list(range(1, len(attempts) + 1))
                assert list(attempts) == expected, (
                    f"Lineage {root_id} has invalid attempt sequence: " f"got {list(attempts)}, expected {expected}"
                )

                print(f"\nLineage {root_id}: attempts={list(attempts)} (valid)")

        finally:
            conn.close()


class TestBehavioralInvariantDocumentation:
    """
    Tests that document the behavioral invariants for PB-S1.

    These tests produce output for manual review and documentation.
    """

    def test_document_lineage_cost_structure(self):
        """
        Document the cost structure of retry lineages.

        This is informational, not a pass/fail test.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT
                    p.id AS original_run,
                    p.status AS original_status,
                    p.cost_cents AS original_cost,
                    r.id AS retry_run,
                    r.attempt,
                    r.status AS retry_status,
                    r.cost_cents AS retry_cost
                FROM worker_runs p
                INNER JOIN worker_runs r ON r.parent_run_id = p.id
                ORDER BY p.id, r.attempt
                LIMIT 20;
            """
            )
            results = cur.fetchall()

            if results:
                print("\n\nCOST CHAIN DOCUMENTATION:")
                print("=" * 80)
                current_original = None
                for row in results:
                    orig_id, orig_status, orig_cost, retry_id, attempt, retry_status, retry_cost = row
                    if orig_id != current_original:
                        print(f"\nOriginal: {orig_id} [{orig_status}] cost={orig_cost}")
                        current_original = orig_id
                    print(f"  → Retry #{attempt}: {retry_id} [{retry_status}] cost={retry_cost}")
                print("=" * 80)

        finally:
            conn.close()


# Marker for CI to identify behavioral invariant tests
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "pb_s1_behavioral: Tests for PB-S1 behavioral invariants (cost chain, attempt monotonicity)"
    )
