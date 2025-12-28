"""
PB-S3 Controlled Feedback Loops Tests

These tests verify the PB-S3 truth guarantee:
- System may observe patterns and emit feedback
- System must NEVER modify past executions, costs, statuses, or traces
- Feedback is stored SEPARATELY from execution tables

STATUS: FROZEN — These tests must NEVER be modified to pass by changing behavior.
If a test fails, the FIX must be in the application code, not the test.

Reference: PIN-203
"""

import os

import pytest

# Skip if no database URL
pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL not set")


class TestPBS3FeedbackSeparation:
    """
    Test that feedback is stored separately from execution data.

    INVARIANT: Feedback table is separate from worker_runs/traces.
    ENFORCEMENT: Database schema + service design.
    """

    def test_pb_s3_pattern_feedback_table_exists(self):
        """
        PB-S3: pattern_feedback table must exist as separate storage.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_name = 'pattern_feedback';
            """
            )
            result = cur.fetchone()

            assert result is not None, "pattern_feedback table does not exist"
            assert result[0] == "pattern_feedback"

        finally:
            conn.close()

    def test_pb_s3_feedback_has_provenance_column(self):
        """
        PB-S3: Feedback must have provenance (references to source runs).
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'pattern_feedback'
                AND column_name = 'provenance';
            """
            )
            result = cur.fetchone()

            assert result is not None, "provenance column missing"
            assert result[1] == "jsonb", "provenance should be JSONB"

        finally:
            conn.close()

    def test_pb_s3_feedback_not_linked_by_fk(self):
        """
        PB-S3: Feedback should NOT have FK to worker_runs (read-only refs).

        This ensures feedback cannot cascade to execution data.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT tc.constraint_name
                FROM information_schema.table_constraints tc
                WHERE tc.table_name = 'pattern_feedback'
                AND tc.constraint_type = 'FOREIGN KEY';
            """
            )
            results = cur.fetchall()

            # Should have no FKs that reference worker_runs
            fk_names = [r[0] for r in results]
            for name in fk_names:
                cur.execute(
                    f"""
                    SELECT ccu.table_name
                    FROM information_schema.constraint_column_usage ccu
                    WHERE ccu.constraint_name = '{name}';
                """
                )
                ref = cur.fetchone()
                if ref:
                    assert ref[0] != "worker_runs", f"FK {name} references worker_runs - violates PB-S3 separation"

        finally:
            conn.close()


class TestPBS3FailurePatternDetection:
    """
    Test PB-S3-S1: Repeated Failure Pattern Detection.

    INVARIANT: Failure patterns are detected without modifying execution data.
    """

    def test_pb_s3_failure_pattern_query_works(self):
        """
        PB-S3-S1: Failure pattern detection query must work.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # This query detects failure patterns
            cur.execute(
                """
                SELECT md5(lower(error)) as signature, COUNT(*) as count
                FROM worker_runs
                WHERE status = 'failed'
                AND created_at >= NOW() - INTERVAL '24 hours'
                AND error IS NOT NULL
                GROUP BY md5(lower(error))
                HAVING COUNT(*) >= 3;
            """
            )
            # Query should execute without error
            results = cur.fetchall()
            print(f"Found {len(results)} failure patterns")

        finally:
            conn.close()

    def test_pb_s3_failure_feedback_record_structure(self):
        """
        PB-S3-S1: Failure feedback records have required fields.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT id, pattern_type, description, provenance, occurrence_count
                FROM pattern_feedback
                WHERE pattern_type = 'failure_pattern'
                LIMIT 1;
            """
            )
            result = cur.fetchone()

            if not result:
                pytest.skip("No failure_pattern feedback to verify")

            record_id, ptype, desc, prov, count = result
            assert ptype == "failure_pattern"
            assert desc is not None
            assert prov is not None  # Provenance must be set
            assert count >= 1

        finally:
            conn.close()


class TestPBS3CostSpikeDetection:
    """
    Test PB-S3-S2: Cost Spike Pattern Detection.

    INVARIANT: Cost spikes are detected without modifying cost data.
    """

    def test_pb_s3_cost_spike_query_works(self):
        """
        PB-S3-S2: Cost spike detection query must work.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            cur.execute(
                """
                WITH costs AS (
                    SELECT worker_id, cost_cents,
                           ROW_NUMBER() OVER (PARTITION BY worker_id ORDER BY created_at DESC) as rn
                    FROM worker_runs
                    WHERE status = 'completed' AND cost_cents > 0
                ),
                recent AS (SELECT * FROM costs WHERE rn = 1),
                baseline AS (SELECT worker_id, AVG(cost_cents) as avg_cost FROM costs WHERE rn > 1 GROUP BY worker_id)
                SELECT r.worker_id, r.cost_cents as recent_cost, b.avg_cost
                FROM recent r
                JOIN baseline b ON r.worker_id = b.worker_id
                WHERE (r.cost_cents - b.avg_cost) / b.avg_cost > 0.5;
            """
            )
            results = cur.fetchall()
            print(f"Found {len(results)} cost spikes")

        finally:
            conn.close()

    def test_pb_s3_cost_feedback_record_structure(self):
        """
        PB-S3-S2: Cost feedback records have required fields.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT id, pattern_type, description, provenance, metadata
                FROM pattern_feedback
                WHERE pattern_type = 'cost_spike'
                LIMIT 1;
            """
            )
            result = cur.fetchone()

            if not result:
                pytest.skip("No cost_spike feedback to verify")

            record_id, ptype, desc, prov, meta = result
            assert ptype == "cost_spike"
            assert desc is not None
            assert prov is not None

        finally:
            conn.close()


class TestPBS3ImmutabilityGuarantee:
    """
    Test that feedback does NOT modify execution data.

    INVARIANT: Execution history is never modified by feedback.
    """

    def test_pb_s3_feedback_cannot_modify_runs(self):
        """
        PB-S3 CRITICAL: Inserting feedback does not modify worker_runs.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Get current state of worker_runs
            cur.execute("SELECT COUNT(*), SUM(cost_cents) FROM worker_runs")
            before_count, before_cost = cur.fetchone()

            # Insert feedback
            cur.execute(
                """
                INSERT INTO pattern_feedback
                (tenant_id, pattern_type, severity, description, provenance, occurrence_count, acknowledged)
                VALUES
                ('test-tenant-001', 'test_pattern', 'info', 'Test', '[]', 1, false);
            """
            )
            conn.commit()

            # Verify worker_runs unchanged
            cur.execute("SELECT COUNT(*), SUM(cost_cents) FROM worker_runs")
            after_count, after_cost = cur.fetchone()

            assert before_count == after_count, "Feedback modified run count!"
            assert before_cost == after_cost, "Feedback modified costs!"

            # Cleanup
            cur.execute("DELETE FROM pattern_feedback WHERE pattern_type = 'test_pattern'")
            conn.commit()

        finally:
            conn.close()

    def test_pb_s3_feedback_has_no_cascade(self):
        """
        PB-S3: Deleting feedback does not affect worker_runs.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Get current run count
            cur.execute("SELECT COUNT(*) FROM worker_runs")
            before_count = cur.fetchone()[0]

            # Insert and delete feedback
            cur.execute(
                """
                INSERT INTO pattern_feedback
                (tenant_id, pattern_type, severity, description, provenance, occurrence_count, acknowledged)
                VALUES
                ('test-tenant-001', 'cascade_test', 'info', 'Test', '[]', 1, false)
                RETURNING id;
            """
            )
            fb_id = cur.fetchone()[0]
            conn.commit()

            cur.execute(f"DELETE FROM pattern_feedback WHERE id = '{fb_id}'")
            conn.commit()

            # Verify runs unchanged
            cur.execute("SELECT COUNT(*) FROM worker_runs")
            after_count = cur.fetchone()[0]

            assert before_count == after_count, "Deleting feedback affected runs!"

        finally:
            conn.close()


class TestPBS3ServiceExists:
    """
    Verify the pattern detection service exists.
    """

    def test_pb_s3_pattern_detection_module_exists(self):
        """
        Verify the pattern_detection service exists and has expected functions.
        """
        try:
            from app.services import pattern_detection

            assert hasattr(pattern_detection, "detect_failure_patterns")
            assert hasattr(pattern_detection, "detect_cost_spikes")
            assert hasattr(pattern_detection, "emit_feedback")
            print("pattern_detection module: all expected functions present")
        except ImportError as e:
            pytest.fail(f"Cannot import pattern_detection service: {e}")

    def test_pb_s3_feedback_model_exists(self):
        """
        Verify the PatternFeedback model exists.
        """
        try:
            from app.models.feedback import PatternFeedback

            assert PatternFeedback.__tablename__ == "pattern_feedback"
            print("PatternFeedback model: exists")
        except ImportError as e:
            pytest.fail(f"Cannot import PatternFeedback model: {e}")


# Marker for CI to identify PB-S3 tests
def pytest_configure(config):
    config.addinivalue_line("markers", "pb_s3: Tests for PB-S3 truth guarantee (controlled feedback)")
