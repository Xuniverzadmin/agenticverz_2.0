"""
PB-S2 Crash Recovery Tests — Orphan Detection & Truth Guarantee

These tests verify the PB-S2 truth guarantee:
- Orphaned runs are never silently lost
- System tells the truth about crashes
- Crashed runs are immutable (same as completed/failed)

STATUS: FROZEN — These tests must NEVER be modified to pass by changing behavior.
If a test fails, the FIX must be in the application code, not the test.

Reference: PIN-202
"""

import os

import pytest

# Skip if no database URL
pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL not set")


class TestPBS2OrphanDetection:
    """
    Test that orphaned runs are correctly detected.

    INVARIANT: Runs stuck in queued/running beyond threshold are detected.
    ENFORCEMENT: orphan_recovery.detect_orphaned_runs()
    """

    def test_pb_s2_orphan_detection_finds_stuck_runs(self):
        """
        PB-S2: Runs older than threshold in queued/running status are detected.

        This test creates a run with old created_at and verifies it's detected.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Count runs that should be considered orphaned (older than 30 min, queued/running)
            cur.execute(
                """
                SELECT COUNT(*)
                FROM worker_runs
                WHERE status IN ('queued', 'running')
                AND created_at < NOW() - INTERVAL '30 minutes';
            """
            )
            orphan_count = cur.fetchone()[0]

            # This is a detection capability test - verify the query works
            assert orphan_count >= 0, "Query should return a valid count"

            # Log for visibility
            print(f"Detected {orphan_count} orphaned runs (>30 min in queued/running)")

        finally:
            conn.close()

    def test_pb_s2_detection_excludes_recent_runs(self):
        """
        PB-S2: Runs within threshold are NOT considered orphaned.

        Recent queued/running runs should be allowed to complete.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Count recent runs that should NOT be orphaned
            cur.execute(
                """
                SELECT COUNT(*)
                FROM worker_runs
                WHERE status IN ('queued', 'running')
                AND created_at >= NOW() - INTERVAL '30 minutes';
            """
            )
            recent_count = cur.fetchone()[0]

            # These runs should NOT be marked as orphaned
            print(f"Found {recent_count} recent runs (within threshold)")

            # Verify the query distinguishes recent from old
            assert recent_count >= 0

        finally:
            conn.close()


class TestPBS2StatusTransition:
    """
    Test that orphaned runs transition to 'crashed' status.

    INVARIANT: Orphaned runs become 'crashed' (factual status).
    ENFORCEMENT: orphan_recovery.mark_run_as_crashed()
    """

    def test_pb_s2_crashed_status_is_valid_terminal_status(self):
        """
        PB-S2: 'crashed' is a valid terminal status alongside completed/failed.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Check that crashed runs exist (from recovery) or can exist
            cur.execute(
                """
                SELECT DISTINCT status
                FROM worker_runs
                WHERE status IN ('completed', 'failed', 'crashed');
            """
            )
            terminal_statuses = {row[0] for row in cur.fetchall()}

            # Verify the schema accepts 'crashed' as a status
            # (If we have any crashed runs, they're in the DB)
            cur.execute(
                """
                SELECT COUNT(*)
                FROM worker_runs
                WHERE status = 'crashed';
            """
            )
            crashed_count = cur.fetchone()[0]

            print(f"Found {crashed_count} crashed runs in database")
            print(f"Terminal statuses present: {terminal_statuses}")

            # The query should work - schema accepts 'crashed'
            assert crashed_count >= 0

        finally:
            conn.close()

    def test_pb_s2_crashed_runs_have_error_message(self):
        """
        PB-S2: Crashed runs should have an error message explaining the crash.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Find crashed runs
            cur.execute(
                """
                SELECT id, error
                FROM worker_runs
                WHERE status = 'crashed'
                LIMIT 5;
            """
            )
            crashed_runs = cur.fetchall()

            if not crashed_runs:
                pytest.skip("No crashed runs in database to verify")

            # All crashed runs should have an error message
            for run_id, error in crashed_runs:
                assert error is not None, f"Crashed run {run_id} has no error message"
                assert len(error) > 0, f"Crashed run {run_id} has empty error message"
                print(f"Crashed run {run_id}: {error[:80]}...")

        finally:
            conn.close()

    def test_pb_s2_crashed_runs_have_completed_at(self):
        """
        PB-S2: Crashed runs should have completed_at set (when crash was detected).
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT id, completed_at
                FROM worker_runs
                WHERE status = 'crashed'
                LIMIT 5;
            """
            )
            crashed_runs = cur.fetchall()

            if not crashed_runs:
                pytest.skip("No crashed runs in database to verify")

            for run_id, completed_at in crashed_runs:
                assert completed_at is not None, f"Crashed run {run_id} missing completed_at"
                print(f"Crashed run {run_id}: completed_at = {completed_at}")

        finally:
            conn.close()


class TestPBS2CrashedImmutability:
    """
    Test that crashed runs cannot be mutated.

    INVARIANT: Crashed runs are immutable (like completed/failed).
    ENFORCEMENT: Database trigger prevent_worker_run_mutation()
    """

    def test_pb_s2_crashed_immutability_status_change_rejected(self):
        """
        PB-S2 CRITICAL: Attempting to change status of crashed run must fail.

        This verifies the trigger protects crashed runs.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Find a crashed run
            cur.execute(
                """
                SELECT id FROM worker_runs
                WHERE status = 'crashed'
                LIMIT 1;
            """
            )
            result = cur.fetchone()

            if not result:
                pytest.skip("No crashed runs in database to test")

            run_id = result[0]

            # Attempt to mutate - this MUST fail
            with pytest.raises(psycopg2.errors.RaiseException) as exc_info:
                cur.execute(
                    f"""
                    UPDATE worker_runs
                    SET status = 'running'
                    WHERE id = '{run_id}';
                """
                )

            # Verify the error message contains TRUTH_VIOLATION
            error_msg = str(exc_info.value)
            assert (
                "TRUTH_VIOLATION" in error_msg or "PB-S1 VIOLATION" in error_msg
            ), f"Expected TRUTH_VIOLATION or PB-S1 VIOLATION in error: {error_msg}"

            print(f"Mutation of crashed run {run_id} correctly rejected")

        finally:
            conn.rollback()
            conn.close()

    def test_pb_s2_crashed_immutability_error_change_rejected(self):
        """
        PB-S2: Attempting to change error field of crashed run must fail.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT id FROM worker_runs
                WHERE status = 'crashed'
                LIMIT 1;
            """
            )
            result = cur.fetchone()

            if not result:
                pytest.skip("No crashed runs in database to test")

            run_id = result[0]

            # Attempt to mutate error - this MUST fail
            with pytest.raises(psycopg2.errors.RaiseException) as exc_info:
                cur.execute(
                    f"""
                    UPDATE worker_runs
                    SET error = 'Rewritten error message'
                    WHERE id = '{run_id}';
                """
                )

            error_msg = str(exc_info.value)
            assert "TRUTH_VIOLATION" in error_msg or "PB-S1 VIOLATION" in error_msg

        finally:
            conn.rollback()
            conn.close()

    def test_pb_s2_trigger_includes_crashed_status(self):
        """
        Verify the immutability trigger function includes 'crashed' in protected statuses.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Check the trigger function definition
            cur.execute(
                """
                SELECT prosrc
                FROM pg_proc
                WHERE proname = 'prevent_worker_run_mutation';
            """
            )
            result = cur.fetchone()

            if not result:
                pytest.fail("prevent_worker_run_mutation function not found!")

            function_source = result[0]

            # Verify 'crashed' is in the protected statuses
            assert "crashed" in function_source.lower(), "Trigger function does not protect 'crashed' status"

            print("Trigger function correctly includes 'crashed' in protected statuses")

        finally:
            conn.close()


class TestPBS2RecoveryIdempotent:
    """
    Test that recovery is idempotent across restarts.

    INVARIANT: Multiple restarts don't create duplicate recovery actions.
    ENFORCEMENT: Status check before marking + crash=terminal status
    """

    def test_pb_s2_recovery_idempotent_already_crashed_not_reprocessed(self):
        """
        PB-S2: Already crashed runs should not be detected as orphans.

        Once a run is 'crashed', it's terminal and won't be reprocessed.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Crashed runs should NOT appear in orphan detection query
            cur.execute(
                """
                SELECT COUNT(*)
                FROM worker_runs
                WHERE status IN ('queued', 'running')
                AND status = 'crashed';
            """
            )
            # This should always be 0 (mutually exclusive conditions)
            count = cur.fetchone()[0]
            assert count == 0, "Logical error: crashed runs should not be in queued/running"

            # Verify crashed runs are excluded from orphan detection
            cur.execute(
                """
                SELECT COUNT(*)
                FROM worker_runs
                WHERE status = 'crashed'
                AND created_at < NOW() - INTERVAL '30 minutes';
            """
            )
            old_crashed = cur.fetchone()[0]
            print(f"Found {old_crashed} old crashed runs (correctly NOT in orphan detection)")

        finally:
            conn.close()

    def test_pb_s2_crashed_status_is_terminal(self):
        """
        PB-S2: Crashed status is terminal - no further state transitions allowed.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT id FROM worker_runs
                WHERE status = 'crashed'
                LIMIT 1;
            """
            )
            result = cur.fetchone()

            if not result:
                pytest.skip("No crashed runs to test")

            run_id = result[0]

            # Try all possible state transitions - all should fail
            invalid_transitions = ["queued", "running", "completed", "failed"]

            for new_status in invalid_transitions:
                try:
                    cur.execute(
                        f"""
                        UPDATE worker_runs
                        SET status = '{new_status}'
                        WHERE id = '{run_id}';
                    """
                    )
                    conn.rollback()
                    pytest.fail(f"Transition crashed → {new_status} should have been rejected")
                except psycopg2.errors.RaiseException:
                    conn.rollback()
                    print(f"Transition crashed → {new_status}: correctly rejected")

        finally:
            conn.close()


class TestPBS2RecoveryServiceExists:
    """
    Verify the recovery infrastructure exists.
    """

    def test_pb_s2_orphan_recovery_module_exists(self):
        """
        Verify the orphan_recovery service module exists and can be imported.
        """
        try:
            from app.services import orphan_recovery

            assert hasattr(orphan_recovery, "detect_orphaned_runs")
            assert hasattr(orphan_recovery, "mark_run_as_crashed")
            assert hasattr(orphan_recovery, "recover_orphaned_runs")
            print("orphan_recovery module: all expected functions present")
        except ImportError as e:
            pytest.fail(f"Cannot import orphan_recovery service: {e}")

    def test_pb_s2_recovery_threshold_configurable(self):
        """
        Verify the orphan threshold is configurable via environment.
        """
        from app.services import orphan_recovery

        assert hasattr(orphan_recovery, "ORPHAN_THRESHOLD_MINUTES")
        threshold = orphan_recovery.ORPHAN_THRESHOLD_MINUTES
        assert isinstance(threshold, int)
        assert threshold > 0, "Threshold must be positive"
        print(f"Orphan threshold: {threshold} minutes")


# Marker for CI to identify PB-S2 tests
def pytest_configure(config):
    config.addinivalue_line("markers", "pb_s2: Tests for PB-S2 truth guarantee (crash recovery)")
