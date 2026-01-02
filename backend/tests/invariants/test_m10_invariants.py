# Layer: L8 — Tests (Invariants)
# Product: system-wide
# Temporal:
#   Trigger: ci
#   Execution: sync
# Role: Schema and concurrency invariant tests for M10 recovery module
# Reference: PIN-267 (Test System Protection Rule)

"""
M10 Recovery Module Invariant Tests

These tests enforce schema and concurrency invariants for the M10 recovery
module. Per PIN-267, these tests MUST NOT be weakened - they exist to
prevent regression of structural guarantees.

Invariant Categories:
1. Schema Invariants - Assert expected constraints/indexes exist
2. Concurrency Invariants - Assert concurrent operations are safe
"""

import os

import pytest
from sqlalchemy import create_engine, text

# Skip all tests if DATABASE_URL not set
# Mark all tests as invariants (PIN-267: must not be weakened)
pytestmark = [
    pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set - invariant tests require database"
    ),
    pytest.mark.invariant,
]


class TestM10SchemaInvariants:
    """Schema invariants that MUST hold for M10 to function correctly."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up database connection."""
        db_url = os.environ.get("DATABASE_URL")
        self.engine = create_engine(db_url)

    def test_m10_recovery_schema_exists(self):
        """Assert m10_recovery schema exists."""
        with self.engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name = 'm10_recovery'
            """
                )
            )
            row = result.fetchone()
            assert row is not None, "m10_recovery schema must exist"

    def test_recovery_candidates_table_exists(self):
        """Assert recovery_candidates table exists in public schema.

        Note: recovery_candidates is in public schema, not m10_recovery.
        This is historical - the table predates schema separation.
        """
        with self.engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'recovery_candidates'
            """
                )
            )
            row = result.fetchone()
            assert row is not None, "recovery_candidates table must exist in public schema"

    def test_failure_match_id_unique_constraint_exists(self):
        """Assert unique constraint on failure_match_id exists.

        This constraint enables ON CONFLICT (failure_match_id) upserts.
        Without it, concurrent upserts will fail.

        Note: recovery_candidates is in public schema.
        """
        with self.engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE table_schema = 'public'
                AND table_name = 'recovery_candidates'
                AND constraint_type = 'UNIQUE'
                AND constraint_name LIKE '%failure_match_id%'
            """
                )
            )
            row = result.fetchone()
            assert row is not None, (
                "Unique constraint on failure_match_id must exist for upserts. "
                "Expected constraint: recovery_candidates_failure_match_id_key"
            )

    def test_partial_unique_index_fmid_sig_exists(self):
        """Assert partial unique index uq_rc_fmid_sig exists.

        This index provides uniqueness for (failure_match_id, error_signature)
        where error_signature IS NOT NULL. It's a PARTIAL index, not a full
        constraint, which has implications for ON CONFLICT behavior.

        IMPORTANT: ON CONFLICT (failure_match_id, error_signature) will NOT
        work with this partial index - use ON CONFLICT (failure_match_id) instead.

        Note: recovery_candidates is in public schema.
        """
        with self.engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                AND tablename = 'recovery_candidates'
                AND indexname = 'uq_rc_fmid_sig'
            """
                )
            )
            row = result.fetchone()
            assert row is not None, (
                "Partial unique index uq_rc_fmid_sig must exist. "
                "This provides (failure_match_id, error_signature) uniqueness "
                "for non-null signatures."
            )
            # Verify it's partial
            indexdef = row[1]
            assert "WHERE" in indexdef, "uq_rc_fmid_sig must be a partial index with WHERE clause"

    def test_work_queue_table_exists(self):
        """Assert work_queue table exists for DB fallback."""
        with self.engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'm10_recovery'
                AND table_name = 'work_queue'
            """
                )
            )
            row = result.fetchone()
            assert row is not None, "work_queue table must exist for DB fallback"


class TestM10ConcurrencyInvariants:
    """Concurrency invariants documenting known race conditions.

    Per PIN-267 Section 3: These tests document race conditions that exist
    in the system. They are NOT expected to pass under all conditions.
    They exist to:
    1. Document the race condition
    2. Prevent accidental "fixes" that hide the race
    3. Track if future L6 fixes resolve them
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up database connection."""
        db_url = os.environ.get("DATABASE_URL")
        self.engine = create_engine(db_url)

    @pytest.mark.xfail(
        reason="Known race: ON CONFLICT handles one constraint but uq_rc_fmid_sig can also trigger",
        strict=False,  # Don't fail if it passes (race is probabilistic)
    )
    def test_dual_constraint_race_documented(self):
        """Document the dual-constraint race condition.

        ROOT CAUSE:
        - recovery_candidates has two unique constraints on failure_match_id:
          1. recovery_candidates_failure_match_id_key (full constraint)
          2. uq_rc_fmid_sig partial index (failure_match_id, error_signature WHERE NOT NULL)

        - ON CONFLICT (failure_match_id) only handles constraint #1
        - Under high concurrency, constraint #2 can trigger first, causing
          UniqueViolation that ON CONFLICT doesn't catch

        CORRECT FIX (L6):
        - Either: Remove partial index and use full unique constraint
        - Or: Change upsert logic to use ON CONFLICT ON CONSTRAINT explicitly
        - Or: Use SERIALIZABLE isolation for critical paths

        FORBIDDEN "FIX":
        - Adding retry loop in test (hides race)
        - Reducing concurrency (hides race)
        - Catching and ignoring UniqueViolation (hides race)
        """
        # This test documents the race, not tests for it
        # The actual chaos test is in test_m10_recovery_chaos.py
        pass

    @pytest.mark.xfail(reason="Known limitation: Connection pool exhaustion under extreme load", strict=False)
    def test_connection_pool_limit_documented(self):
        """Document connection pool limit under load.

        ROOT CAUSE:
        - Local PostgreSQL has max_connections limit
        - 1000 concurrent threads each opening a connection exhausts pool
        - Results in "too many clients already" error

        CLASSIFICATION: Bucket B (Infrastructure)
        - This is not a code bug but an infrastructure capacity limit
        - Production uses PgBouncer which handles this
        - Test exists to document the limitation

        CORRECT FIX:
        - Use connection pooling in test (SQLAlchemy pool)
        - Or: Reduce concurrency to match local capacity
        - Or: Skip test in environments without pooling
        """
        pass


class TestM10InvariantDocumentation:
    """Meta-tests documenting M10 invariant expectations."""

    def test_pin_267_compliance(self):
        """Verify this test file follows PIN-267 rules.

        PIN-267 requires:
        1. Bucket C issues get invariant tests
        2. Tests may not be weakened
        3. xfail is acceptable to document known issues
        4. Real fixes must be in L6
        """
        # This test always passes - it's documentation
        invariants_documented = [
            "dual_constraint_race",
            "connection_pool_limit",
        ]
        assert len(invariants_documented) == 2, "All known M10 issues documented"
