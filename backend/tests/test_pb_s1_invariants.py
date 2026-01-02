"""
PB-S1 Invariant Tests — Retry Creates New Execution

These tests verify the PB-S1 truth guarantee:
- Retry creates NEW execution (not mutation)
- Original runs are immutable after completion
- Database trigger enforces immutability

STATUS: FROZEN — These tests must NEVER be modified to pass by changing behavior.
If a test fails, the FIX must be in the application code, not the test.

Reference: PIN-199
"""

import os
import uuid

import pytest

# Skip if no database URL
pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL not set")


class TestPBS1ImmutabilityTrigger:
    """
    Test that the database trigger prevents mutation of completed/failed runs.

    INVARIANT: Completed/failed worker_runs cannot be mutated.
    ENFORCEMENT: Database trigger `prevent_worker_run_mutation()`
    """

    def test_mutation_of_failed_run_is_rejected(self):
        """
        PB-S1 CRITICAL: Attempting to mutate a failed run must raise an error.

        This test directly attempts to UPDATE a failed worker_run.
        The database trigger must reject this with 'PB-S1 VIOLATION'.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Find a failed run
            cur.execute(
                """
                SELECT id FROM worker_runs
                WHERE status = 'failed'
                LIMIT 1;
            """
            )
            result = cur.fetchone()

            if not result:
                pytest.skip("No failed runs in database to test")

            run_id = result[0]

            # Attempt to mutate - this MUST fail
            with pytest.raises(psycopg2.errors.RestrictViolation) as exc_info:
                cur.execute(
                    f"""
                    UPDATE worker_runs
                    SET status = 'queued'
                    WHERE id = '{run_id}';
                """
                )

            # Verify the error message contains TRUTH_VIOLATION (PB-S1 enforcement)
            assert "TRUTH_VIOLATION" in str(exc_info.value)

        finally:
            conn.rollback()
            conn.close()

    def test_mutation_of_completed_run_is_rejected(self):
        """
        PB-S1 CRITICAL: Attempting to mutate a completed run must raise an error.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Find a completed run
            cur.execute(
                """
                SELECT id FROM worker_runs
                WHERE status = 'completed'
                LIMIT 1;
            """
            )
            result = cur.fetchone()

            if not result:
                pytest.skip("No completed runs in database to test")

            run_id = result[0]

            # Attempt to mutate - this MUST fail
            with pytest.raises(psycopg2.errors.RestrictViolation) as exc_info:
                cur.execute(
                    f"""
                    UPDATE worker_runs
                    SET status = 'failed'
                    WHERE id = '{run_id}';
                """
                )

            # Verify the error message contains TRUTH_VIOLATION (PB-S1 enforcement)
            assert "TRUTH_VIOLATION" in str(exc_info.value)

        finally:
            conn.rollback()
            conn.close()

    def test_immutability_trigger_exists(self):
        """
        Verify the immutability trigger is installed in the database.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT trigger_name
                FROM information_schema.triggers
                WHERE trigger_name = 'worker_runs_immutable_guard';
            """
            )
            result = cur.fetchone()

            assert result is not None, "Immutability trigger not found!"
            assert result[0] == "worker_runs_immutable_guard"

        finally:
            conn.close()


class TestPBS1RetryCreatesNewRow:
    """
    Test that retry operations create NEW rows, not mutations.

    INVARIANT: Retry must create a new execution with parent linkage.
    ENFORCEMENT: /admin/retry endpoint + database schema
    """

    def test_retry_schema_has_required_columns(self):
        """
        Verify the schema has parent_run_id, attempt, is_retry columns.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'worker_runs'
                AND column_name IN ('parent_run_id', 'attempt', 'is_retry');
            """
            )
            columns = {row[0] for row in cur.fetchall()}

            assert "parent_run_id" in columns, "parent_run_id column missing"
            assert "attempt" in columns, "attempt column missing"
            assert "is_retry" in columns, "is_retry column missing"

        finally:
            conn.close()

    def test_retry_history_view_exists(self):
        """
        Verify the retry_history audit view exists.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT table_name
                FROM information_schema.views
                WHERE table_name = 'retry_history';
            """
            )
            result = cur.fetchone()

            assert result is not None, "retry_history view not found"

        finally:
            conn.close()

    def test_retry_creates_new_row_not_mutation(self):
        """
        PB-S1 CRITICAL: Verify that retry runs are linked via parent_run_id.

        If is_retry=true, then parent_run_id must be set.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Check all retry runs have parent linkage
            cur.execute(
                """
                SELECT COUNT(*)
                FROM worker_runs
                WHERE is_retry = true AND parent_run_id IS NULL;
            """
            )
            orphan_retries = cur.fetchone()[0]

            assert orphan_retries == 0, f"Found {orphan_retries} retry runs without parent linkage (PB-S1 violation)"

        finally:
            conn.close()

    def test_parent_run_preserved_after_retry(self):
        """
        Verify that parent runs are not mutated when retry is created.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Find a retry and its parent
            cur.execute(
                """
                SELECT r.id, r.parent_run_id, r.status, p.status as parent_status
                FROM worker_runs r
                JOIN worker_runs p ON r.parent_run_id = p.id
                WHERE r.is_retry = true
                LIMIT 1;
            """
            )
            result = cur.fetchone()

            if not result:
                pytest.skip("No retry runs found to test")

            retry_id, parent_id, retry_status, parent_status = result

            # Parent must still be in terminal state (failed/completed)
            assert parent_status in (
                "failed",
                "completed",
            ), f"Parent run {parent_id} has status {parent_status} - expected terminal state"

        finally:
            conn.close()


class TestPBS1EndpointBehavior:
    """
    Test the /admin/retry and /admin/rerun endpoint behavior.
    """

    def test_rerun_endpoint_returns_410_gone(self):
        """
        PB-S1: /admin/rerun must be permanently disabled (HTTP 410 Gone).
        """
        import requests

        # This test requires the backend to be running with proper auth
        api_key = os.getenv("AOS_API_KEY")
        # Skip if no key, or if using test stub key from conftest.py
        if not api_key or api_key == "test-key-for-testing":
            pytest.skip("Valid AOS_API_KEY not set - cannot test authenticated endpoint")

        try:
            response = requests.post(
                "http://localhost:8000/admin/rerun",
                json={"run_id": str(uuid.uuid4()), "reason": "test"},
                headers={"X-AOS-Key": api_key, "X-Roles": "founder"},
                timeout=5,
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend not running")

        assert response.status_code == 410, f"Expected 410 Gone, got {response.status_code}"

        data = response.json()
        assert data.get("detail", {}).get("error") == "endpoint_removed"


class TestPBS1WorkerBehavior:
    """
    Test that workers do not infer state from parent runs.

    INVARIANT: Workers execute only their own row, no implicit inheritance.
    """

    def test_retry_run_has_independent_execution_context(self):
        """
        Verify retry runs have their own execution fields, not inherited.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Check retry runs have their own timestamps
            cur.execute(
                """
                SELECT r.id, r.created_at, r.started_at, r.completed_at,
                       p.created_at as parent_created_at
                FROM worker_runs r
                JOIN worker_runs p ON r.parent_run_id = p.id
                WHERE r.is_retry = true
                LIMIT 1;
            """
            )
            result = cur.fetchone()

            if not result:
                pytest.skip("No retry runs found")

            retry_id, retry_created, retry_started, retry_completed, parent_created = result

            # Retry must have its own created_at (different from parent)
            assert retry_created != parent_created, "Retry has same created_at as parent - should be independent"

        finally:
            conn.close()


# Marker for CI to identify PB-S1 tests
def pytest_configure(config):
    config.addinivalue_line("markers", "pb_s1: Tests for PB-S1 truth guarantee (retry immutability)")
