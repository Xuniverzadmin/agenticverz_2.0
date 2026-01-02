"""
PB-S5 Prediction Without Determinism Loss Tests

These tests verify the PB-S5 truth guarantee:
- System may predict likely future failures or cost overruns
- System must NEVER modify execution behavior, scheduling, retries, policies, or history
- Predictions are advisory only, with zero side-effects

STATUS: FROZEN — These tests must NEVER be modified to pass by changing behavior.
If a test fails, the FIX must be in the application code, not the test.

Reference: PIN-205
"""

import os

import pytest

# Skip if no database URL
pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL not set")


class TestPBS5PredictionSeparation:
    """
    Test that predictions are stored separately from execution data.

    INVARIANT: Predictions table is separate from worker_runs/traces.
    ENFORCEMENT: Database schema + service design.
    """

    def test_pb_s5_prediction_events_table_exists(self):
        """
        PB-S5: prediction_events table must exist as separate storage.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_name = 'prediction_events';
            """
            )
            result = cur.fetchone()

            assert result is not None, "prediction_events table does not exist"
            assert result[0] == "prediction_events"

        finally:
            conn.close()

    def test_pb_s5_prediction_has_advisory_flag(self):
        """
        PB-S5: Predictions must have is_advisory column (always true).
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'prediction_events'
                AND column_name = 'is_advisory';
            """
            )
            result = cur.fetchone()

            assert result is not None, "is_advisory column missing"
            assert result[1] == "boolean", "is_advisory should be boolean"

        finally:
            conn.close()

    def test_pb_s5_prediction_not_linked_to_execution_by_fk(self):
        """
        PB-S5: Predictions should NOT have FK to worker_runs.

        This ensures predictions cannot cascade to execution data.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT tc.constraint_name
                FROM information_schema.table_constraints tc
                WHERE tc.table_name = 'prediction_events'
                AND tc.constraint_type = 'FOREIGN KEY';
            """
            )
            results = cur.fetchall()

            # Check no FK references worker_runs
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
                    assert ref[0] != "worker_runs", f"FK {name} references worker_runs - violates PB-S5 separation"

        finally:
            conn.close()


class TestPBS5FailurePrediction:
    """
    Test PB-S5-S1: Failure Likelihood Prediction.

    INVARIANT: Predictions are created without modifying execution data.
    """

    def test_pb_s5_failure_prediction_is_advisory(self):
        """
        PB-S5-S1: Failure predictions must be advisory only.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Get current state
            cur.execute("SELECT COUNT(*) FROM worker_runs")
            before_runs = cur.fetchone()[0]

            # Insert a test prediction
            cur.execute(
                """
                INSERT INTO prediction_events
                (tenant_id, prediction_type, subject_type, subject_id,
                 confidence_score, prediction_value, contributing_factors, is_advisory, expires_at)
                VALUES
                ('test-tenant-001', 'failure_likelihood', 'worker', 'test-worker',
                 0.8, '{"predicted_outcome": "high_failure"}'::jsonb, '[]'::jsonb, true, NOW() + INTERVAL '1 day')
                RETURNING is_advisory;
            """
            )
            result = cur.fetchone()
            assert result[0] is True, "Prediction must be advisory"

            conn.commit()

            # Verify no side effects
            cur.execute("SELECT COUNT(*) FROM worker_runs")
            after_runs = cur.fetchone()[0]
            assert before_runs == after_runs, "Prediction modified worker_runs!"

            # Cleanup
            cur.execute("DELETE FROM prediction_events WHERE subject_id = 'test-worker'")
            conn.commit()

        finally:
            conn.close()


class TestPBS5CostPrediction:
    """
    Test PB-S5-S2: Cost Overrun Prediction.

    INVARIANT: Cost predictions do not modify actual costs.
    """

    def test_pb_s5_cost_prediction_does_not_modify_costs(self):
        """
        PB-S5-S2: Cost predictions must not modify actual cost values.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Get current cost state
            cur.execute("SELECT SUM(cost_cents) FROM worker_runs")
            before_cost = cur.fetchone()[0]

            # Insert a cost prediction
            cur.execute(
                """
                INSERT INTO prediction_events
                (tenant_id, prediction_type, subject_type, subject_id,
                 confidence_score, prediction_value, contributing_factors, is_advisory, expires_at)
                VALUES
                ('test-tenant-001', 'cost_overrun', 'worker', 'test-worker-cost',
                 0.7, '{"projected_cost_cents": 500}'::jsonb, '[]'::jsonb, true, NOW() + INTERVAL '1 day')
                RETURNING id;
            """
            )
            pred_id = cur.fetchone()[0]
            conn.commit()

            # Verify costs unchanged
            cur.execute("SELECT SUM(cost_cents) FROM worker_runs")
            after_cost = cur.fetchone()[0]
            assert before_cost == after_cost, "Cost prediction modified actual costs!"

            # Cleanup
            cur.execute(f"DELETE FROM prediction_events WHERE id = '{pred_id}'")
            conn.commit()

        finally:
            conn.close()


class TestPBS5ImmutabilityGuarantee:
    """
    Test that predictions do NOT modify execution data.

    INVARIANT: Execution history is never modified by predictions.
    """

    def test_pb_s5_prediction_cannot_modify_runs(self):
        """
        PB-S5 CRITICAL: Creating predictions does not modify worker_runs.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Get current state of worker_runs
            cur.execute("SELECT COUNT(*), SUM(cost_cents) FROM worker_runs")
            before_count, before_cost = cur.fetchone()

            # Create a prediction
            cur.execute(
                """
                INSERT INTO prediction_events
                (tenant_id, prediction_type, subject_type, subject_id,
                 confidence_score, prediction_value, contributing_factors, is_advisory, expires_at)
                VALUES
                ('test-tenant-001', 'failure_likelihood', 'worker', 'immutability-test',
                 0.9, '{"test": true}'::jsonb, '[]'::jsonb, true, NOW() + INTERVAL '1 day')
                RETURNING id;
            """
            )
            pred_id = cur.fetchone()[0]
            conn.commit()

            # Verify worker_runs unchanged
            cur.execute("SELECT COUNT(*), SUM(cost_cents) FROM worker_runs")
            after_count, after_cost = cur.fetchone()

            assert before_count == after_count, "Prediction modified run count!"
            assert before_cost == after_cost, "Prediction modified costs!"

            # Cleanup
            cur.execute(f"DELETE FROM prediction_events WHERE id = '{pred_id}'")
            conn.commit()

        finally:
            conn.close()

    def test_pb_s5_prediction_cannot_trigger_retry(self):
        """
        PB-S5 CRITICAL: Predictions do not trigger retries or throttling.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Get current run count
            cur.execute("SELECT COUNT(*) FROM worker_runs")
            before_count = cur.fetchone()[0]

            # Create a high-confidence failure prediction
            cur.execute(
                """
                INSERT INTO prediction_events
                (tenant_id, prediction_type, subject_type, subject_id,
                 confidence_score, prediction_value, contributing_factors, is_advisory, expires_at)
                VALUES
                ('test-tenant-001', 'failure_likelihood', 'worker', 'retry-test',
                 0.99, '{"predicted_outcome": "certain_failure"}'::jsonb, '[]'::jsonb, true, NOW() + INTERVAL '1 day')
                RETURNING id;
            """
            )
            pred_id = cur.fetchone()[0]
            conn.commit()

            # Verify no new runs created (no automatic retry/throttle)
            cur.execute("SELECT COUNT(*) FROM worker_runs")
            after_count = cur.fetchone()[0]

            assert before_count == after_count, "Prediction triggered retry or new run!"

            # Cleanup
            cur.execute(f"DELETE FROM prediction_events WHERE id = '{pred_id}'")
            conn.commit()

        finally:
            conn.close()

    def test_pb_s5_all_predictions_are_advisory(self):
        """
        PB-S5: All predictions in the system must be advisory.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT COUNT(*) FROM prediction_events WHERE is_advisory = false;
            """
            )
            non_advisory_count = cur.fetchone()[0]

            assert non_advisory_count == 0, f"Found {non_advisory_count} non-advisory predictions - violates PB-S5!"

        finally:
            conn.close()


class TestPBS5ServiceExists:
    """
    Verify the prediction service exists.
    """

    def test_pb_s5_prediction_module_exists(self):
        """
        Verify the prediction service exists and has expected functions.
        """
        try:
            from app.services import prediction

            assert hasattr(prediction, "predict_failure_likelihood")
            assert hasattr(prediction, "predict_cost_overrun")
            assert hasattr(prediction, "emit_prediction")
            print("prediction module: all expected functions present")
        except ImportError as e:
            pytest.fail(f"Cannot import prediction service: {e}")

    def test_pb_s5_prediction_model_exists(self):
        """
        Verify the PredictionEvent model exists.
        """
        try:
            from app.models.prediction import PredictionEvent

            assert PredictionEvent.__tablename__ == "prediction_events"
            print("PredictionEvent model: exists")
        except ImportError as e:
            pytest.fail(f"Cannot import PredictionEvent model: {e}")


# Marker for CI to identify PB-S5 tests
def pytest_configure(config):
    config.addinivalue_line("markers", "pb_s5: Tests for PB-S5 truth guarantee (prediction)")
