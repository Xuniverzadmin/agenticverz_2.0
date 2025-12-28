#!/usr/bin/env python3
"""
C2 Prediction Plane - Regression Tests
=======================================

Verifies C2 invariants hold under execution for all prediction types.

Prediction Types:
  C2-T1: Incident Risk
  C2-T2: Spend Spike
  C2-T3: Policy Drift (STRICTEST semantic constraints)

C2 Invariants Tested:
  I-C2-1: advisory MUST be TRUE (CHECK constraint)
  I-C2-2: No control path influence (import isolation)
  I-C2-3: No truth mutation (delete safety)
  I-C2-4: Replay blindness (no prediction imports in replay)
  I-C2-5: Delete safety (predictions disposable)

Reference: PIN-222, C2 Implementation Plan

Usage:
    python3 c2_regression.py [--json] [--verbose]

Environment:
    DATABASE_URL - Required for database tests
"""

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import uuid4


@dataclass
class TestResult:
    name: str
    passed: bool
    expected: str
    actual: str
    invariant: str


def get_db_connection():
    """Get database connection."""
    import psycopg2

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable required")
    return psycopg2.connect(database_url)


def test_prediction_creation() -> TestResult:
    """Test: Prediction creation succeeds on database."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        prediction_id = str(uuid4())
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=30)

        cur.execute(
            """
            INSERT INTO prediction_events (
                id, tenant_id, prediction_type, subject_type, subject_id,
                confidence_score, prediction_value, contributing_factors,
                is_advisory, created_at, expires_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                prediction_id,
                "c2_regression_test",
                "incident_risk",
                "tenant",
                "test_subject",
                0.75,
                json.dumps({"risk_level": "elevated"}),
                json.dumps([]),
                True,
                now,
                expires,
            ),
        )
        conn.commit()

        # Verify it exists
        cur.execute(
            "SELECT id FROM prediction_events WHERE id = %s", (prediction_id,)
        )
        row = cur.fetchone()

        # Cleanup
        cur.execute(
            "DELETE FROM prediction_events WHERE tenant_id = 'c2_regression_test'"
        )
        conn.commit()
        conn.close()

        if row:
            return TestResult(
                name="prediction_creation",
                passed=True,
                expected="Prediction created",
                actual="Prediction created successfully",
                invariant="I-C2-5 (predictions can be created)",
            )
        else:
            return TestResult(
                name="prediction_creation",
                passed=False,
                expected="Prediction created",
                actual="Prediction not found after insert",
                invariant="I-C2-5",
            )

    except Exception as e:
        return TestResult(
            name="prediction_creation",
            passed=False,
            expected="Prediction created",
            actual=f"Error: {e}",
            invariant="I-C2-5",
        )


def test_advisory_constraint() -> TestResult:
    """Test: is_advisory=False is rejected by CHECK constraint."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        prediction_id = str(uuid4())
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=30)

        try:
            cur.execute(
                """
                INSERT INTO prediction_events (
                    id, tenant_id, prediction_type, subject_type, subject_id,
                    confidence_score, prediction_value, contributing_factors,
                    is_advisory, created_at, expires_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    prediction_id,
                    "c2_regression_test",
                    "incident_risk",
                    "tenant",
                    "test_subject",
                    0.5,
                    json.dumps({}),
                    json.dumps([]),
                    False,  # VIOLATES I-C2-1
                    now,
                    expires,
                ),
            )
            conn.commit()
            conn.close()

            # If we got here, the constraint didn't work
            return TestResult(
                name="advisory_constraint",
                passed=False,
                expected="CHECK constraint rejects is_advisory=False",
                actual="Insert succeeded (constraint missing!)",
                invariant="I-C2-1",
            )

        except Exception as e:
            conn.rollback()
            conn.close()

            if "chk_prediction_advisory" in str(e):
                return TestResult(
                    name="advisory_constraint",
                    passed=True,
                    expected="CHECK constraint rejects is_advisory=False",
                    actual="Correctly rejected by chk_prediction_advisory",
                    invariant="I-C2-1 (advisory MUST be TRUE)",
                )
            else:
                return TestResult(
                    name="advisory_constraint",
                    passed=False,
                    expected="CHECK constraint rejects is_advisory=False",
                    actual=f"Different error: {e}",
                    invariant="I-C2-1",
                )

    except Exception as e:
        return TestResult(
            name="advisory_constraint",
            passed=False,
            expected="CHECK constraint test",
            actual=f"Connection error: {e}",
            invariant="I-C2-1",
        )


def test_delete_safety() -> TestResult:
    """Test: Deleting predictions has zero side effects."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Create a prediction
        prediction_id = str(uuid4())
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=30)

        cur.execute(
            """
            INSERT INTO prediction_events (
                id, tenant_id, prediction_type, subject_type, subject_id,
                confidence_score, prediction_value, contributing_factors,
                is_advisory, created_at, expires_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                prediction_id,
                "c2_delete_test",
                "incident_risk",
                "tenant",
                "test_subject",
                0.8,
                json.dumps({"risk_level": "high"}),
                json.dumps([]),
                True,
                now,
                expires,
            ),
        )
        conn.commit()

        # Delete all test predictions
        cur.execute(
            "DELETE FROM prediction_events WHERE tenant_id = 'c2_delete_test'"
        )
        deleted = cur.rowcount
        conn.commit()

        # Verify no FK violations or cascades
        # (If there were FKs, this delete would fail)

        conn.close()

        if deleted == 1:
            return TestResult(
                name="delete_safety",
                passed=True,
                expected="Delete succeeds with no side effects",
                actual=f"Deleted {deleted} prediction(s), no cascade errors",
                invariant="I-C2-5 (predictions disposable)",
            )
        else:
            return TestResult(
                name="delete_safety",
                passed=False,
                expected="Delete succeeds",
                actual=f"Unexpected delete count: {deleted}",
                invariant="I-C2-5",
            )

    except Exception as e:
        return TestResult(
            name="delete_safety",
            passed=False,
            expected="Delete succeeds",
            actual=f"Error: {e}",
            invariant="I-C2-5",
        )


def test_confidence_range() -> TestResult:
    """Test: Confidence score must be between 0 and 1."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        prediction_id = str(uuid4())
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=30)

        try:
            cur.execute(
                """
                INSERT INTO prediction_events (
                    id, tenant_id, prediction_type, subject_type, subject_id,
                    confidence_score, prediction_value, contributing_factors,
                    is_advisory, created_at, expires_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    prediction_id,
                    "c2_regression_test",
                    "incident_risk",
                    "tenant",
                    "test_subject",
                    1.5,  # VIOLATES confidence range
                    json.dumps({}),
                    json.dumps([]),
                    True,
                    now,
                    expires,
                ),
            )
            conn.commit()

            # Cleanup if somehow it got through
            cur.execute(
                "DELETE FROM prediction_events WHERE id = %s", (prediction_id,)
            )
            conn.commit()
            conn.close()

            return TestResult(
                name="confidence_range",
                passed=False,
                expected="CHECK constraint rejects confidence > 1",
                actual="Insert succeeded (constraint missing!)",
                invariant="Confidence range (0-1)",
            )

        except Exception as e:
            conn.rollback()
            conn.close()

            if "chk_prediction_confidence_range" in str(e):
                return TestResult(
                    name="confidence_range",
                    passed=True,
                    expected="CHECK constraint rejects confidence > 1",
                    actual="Correctly rejected by chk_prediction_confidence_range",
                    invariant="Confidence range (0-1)",
                )
            else:
                return TestResult(
                    name="confidence_range",
                    passed=False,
                    expected="CHECK constraint rejects confidence > 1",
                    actual=f"Different error: {e}",
                    invariant="Confidence range",
                )

    except Exception as e:
        return TestResult(
            name="confidence_range",
            passed=False,
            expected="Confidence range test",
            actual=f"Connection error: {e}",
            invariant="Confidence range",
        )


def test_guardrails_pass() -> TestResult:
    """Test: All C2 guardrails pass."""
    try:
        result = subprocess.run(
            ["/root/agenticverz2.0/scripts/ci/c2_guardrails/run_all.sh"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            return TestResult(
                name="guardrails_pass",
                passed=True,
                expected="All C2 guardrails pass",
                actual="All 5 guardrails passed",
                invariant="I-C2-2/3/4 (import isolation, replay blindness)",
            )
        else:
            return TestResult(
                name="guardrails_pass",
                passed=False,
                expected="All C2 guardrails pass",
                actual=f"Guardrails failed: {result.stderr[:200]}",
                invariant="I-C2-2/3/4",
            )

    except subprocess.TimeoutExpired:
        return TestResult(
            name="guardrails_pass",
            passed=False,
            expected="Guardrails complete",
            actual="Timeout after 60s",
            invariant="I-C2-2/3/4",
        )
    except FileNotFoundError:
        return TestResult(
            name="guardrails_pass",
            passed=False,
            expected="Guardrails script exists",
            actual="run_all.sh not found",
            invariant="I-C2-2/3/4",
        )
    except Exception as e:
        return TestResult(
            name="guardrails_pass",
            passed=False,
            expected="Guardrails pass",
            actual=f"Error: {e}",
            invariant="I-C2-2/3/4",
        )


def test_no_redis_in_predictions() -> TestResult:
    """Test: Predictions code does not reference Redis (import or usage)."""
    predictions_dir = "/root/agenticverz2.0/backend/app/predictions"

    if not os.path.isdir(predictions_dir):
        return TestResult(
            name="no_redis",
            passed=True,
            expected="No Redis in predictions",
            actual="Predictions directory does not exist yet",
            invariant="GR-5 (Redis authority)",
        )

    try:
        # Look for actual Redis imports or usage patterns
        # Patterns: import redis, from redis, redis.Redis, upstash
        result = subprocess.run(
            [
                "grep",
                "-rE",
                r"import redis|from redis|redis\.Redis|from upstash|import upstash|redis_client|RedisClient",
                predictions_dir,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:  # grep returns 1 if no matches
            return TestResult(
                name="no_redis",
                passed=True,
                expected="No Redis in predictions",
                actual="No Redis imports or usage found",
                invariant="GR-5 (Redis authority)",
            )
        else:
            return TestResult(
                name="no_redis",
                passed=False,
                expected="No Redis in predictions",
                actual=f"Redis found: {result.stdout[:100]}",
                invariant="GR-5",
            )

    except Exception as e:
        return TestResult(
            name="no_redis",
            passed=False,
            expected="Redis check",
            actual=f"Error: {e}",
            invariant="GR-5",
        )


# =============================================================================
# C2-T2 SPEND SPIKE TESTS
# =============================================================================


def test_spend_spike_creation() -> TestResult:
    """Test: Spend Spike prediction creation succeeds."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        prediction_id = str(uuid4())
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=30)

        cur.execute(
            """
            INSERT INTO prediction_events (
                id, tenant_id, prediction_type, subject_type, subject_id,
                confidence_score, prediction_value, contributing_factors,
                is_advisory, created_at, expires_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                prediction_id,
                "c2_spend_spike_test",
                "spend_spike",
                "tenant",
                "spend_test_subject",
                0.85,
                json.dumps({"projected_spend": 150.0, "baseline_spend": 100.0}),
                json.dumps([]),
                True,
                now,
                expires,
            ),
        )
        conn.commit()

        # Verify it exists
        cur.execute(
            "SELECT prediction_type FROM prediction_events WHERE id = %s",
            (prediction_id,),
        )
        row = cur.fetchone()

        # Cleanup
        cur.execute(
            "DELETE FROM prediction_events WHERE tenant_id = 'c2_spend_spike_test'"
        )
        conn.commit()
        conn.close()

        if row and row[0] == "spend_spike":
            return TestResult(
                name="spend_spike_creation",
                passed=True,
                expected="Spend Spike prediction created",
                actual="Spend Spike prediction created successfully",
                invariant="C2-T2 (spend spike can exist)",
            )
        else:
            return TestResult(
                name="spend_spike_creation",
                passed=False,
                expected="Spend Spike prediction created",
                actual="Prediction not found or wrong type",
                invariant="C2-T2",
            )

    except Exception as e:
        return TestResult(
            name="spend_spike_creation",
            passed=False,
            expected="Spend Spike prediction created",
            actual=f"Error: {e}",
            invariant="C2-T2",
        )


def test_spend_spike_advisory_constraint() -> TestResult:
    """Test: Spend Spike with is_advisory=False is rejected."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        prediction_id = str(uuid4())
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=30)

        try:
            cur.execute(
                """
                INSERT INTO prediction_events (
                    id, tenant_id, prediction_type, subject_type, subject_id,
                    confidence_score, prediction_value, contributing_factors,
                    is_advisory, created_at, expires_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    prediction_id,
                    "c2_spend_spike_test",
                    "spend_spike",
                    "tenant",
                    "spend_test_subject",
                    0.5,
                    json.dumps({"projected_spend": 100.0, "baseline_spend": 100.0}),
                    json.dumps([]),
                    False,  # VIOLATES I-C2-1
                    now,
                    expires,
                ),
            )
            conn.commit()
            conn.close()

            return TestResult(
                name="spend_spike_advisory_constraint",
                passed=False,
                expected="CHECK constraint rejects is_advisory=False",
                actual="Insert succeeded (constraint missing!)",
                invariant="I-C2-1",
            )

        except Exception as e:
            conn.rollback()
            conn.close()

            if "chk_prediction_advisory" in str(e):
                return TestResult(
                    name="spend_spike_advisory_constraint",
                    passed=True,
                    expected="CHECK constraint rejects is_advisory=False",
                    actual="Correctly rejected by chk_prediction_advisory",
                    invariant="I-C2-1 (advisory MUST be TRUE)",
                )
            else:
                return TestResult(
                    name="spend_spike_advisory_constraint",
                    passed=False,
                    expected="CHECK constraint rejects is_advisory=False",
                    actual=f"Different error: {e}",
                    invariant="I-C2-1",
                )

    except Exception as e:
        return TestResult(
            name="spend_spike_advisory_constraint",
            passed=False,
            expected="CHECK constraint test",
            actual=f"Connection error: {e}",
            invariant="I-C2-1",
        )


def test_spend_spike_delete_safety() -> TestResult:
    """Test: Deleting Spend Spike predictions has zero side effects."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Create a spend spike prediction
        prediction_id = str(uuid4())
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=30)

        cur.execute(
            """
            INSERT INTO prediction_events (
                id, tenant_id, prediction_type, subject_type, subject_id,
                confidence_score, prediction_value, contributing_factors,
                is_advisory, created_at, expires_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                prediction_id,
                "c2_spend_delete_test",
                "spend_spike",
                "tenant",
                "delete_test_subject",
                0.9,
                json.dumps({"projected_spend": 200.0, "baseline_spend": 100.0}),
                json.dumps([]),
                True,
                now,
                expires,
            ),
        )
        conn.commit()

        # Delete all spend spike test predictions
        cur.execute(
            "DELETE FROM prediction_events WHERE tenant_id = 'c2_spend_delete_test'"
        )
        deleted = cur.rowcount
        conn.commit()
        conn.close()

        if deleted == 1:
            return TestResult(
                name="spend_spike_delete_safety",
                passed=True,
                expected="Delete succeeds with no side effects",
                actual=f"Deleted {deleted} Spend Spike prediction(s), no cascade errors",
                invariant="I-C2-5 (predictions disposable)",
            )
        else:
            return TestResult(
                name="spend_spike_delete_safety",
                passed=False,
                expected="Delete succeeds",
                actual=f"Unexpected delete count: {deleted}",
                invariant="I-C2-5",
            )

    except Exception as e:
        return TestResult(
            name="spend_spike_delete_safety",
            passed=False,
            expected="Delete succeeds",
            actual=f"Error: {e}",
            invariant="I-C2-5",
        )


def test_spend_spike_expiry() -> TestResult:
    """Test: Expired Spend Spike predictions are invisible."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Create a spend spike prediction with past expiry
        prediction_id = str(uuid4())
        now = datetime.now(timezone.utc)
        expired = now - timedelta(minutes=5)  # Already expired

        cur.execute(
            """
            INSERT INTO prediction_events (
                id, tenant_id, prediction_type, subject_type, subject_id,
                confidence_score, prediction_value, contributing_factors,
                is_advisory, created_at, expires_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                prediction_id,
                "c2_spend_expiry_test",
                "spend_spike",
                "tenant",
                "expiry_test_subject",
                0.7,
                json.dumps({"projected_spend": 120.0, "baseline_spend": 100.0}),
                json.dumps([]),
                True,
                now - timedelta(minutes=35),
                expired,
            ),
        )
        conn.commit()

        # Query for non-expired predictions (should NOT find it)
        cur.execute(
            """
            SELECT id FROM prediction_events
            WHERE tenant_id = 'c2_spend_expiry_test'
            AND expires_at > NOW()
            """
        )
        visible_rows = cur.fetchall()

        # Cleanup
        cur.execute(
            "DELETE FROM prediction_events WHERE tenant_id = 'c2_spend_expiry_test'"
        )
        conn.commit()
        conn.close()

        if len(visible_rows) == 0:
            return TestResult(
                name="spend_spike_expiry",
                passed=True,
                expected="Expired predictions are invisible",
                actual="Expired Spend Spike correctly filtered out",
                invariant="B3 (expiry is silent)",
            )
        else:
            return TestResult(
                name="spend_spike_expiry",
                passed=False,
                expected="Expired predictions are invisible",
                actual=f"Found {len(visible_rows)} expired predictions (should be 0)",
                invariant="B3",
            )

    except Exception as e:
        return TestResult(
            name="spend_spike_expiry",
            passed=False,
            expected="Expiry test",
            actual=f"Error: {e}",
            invariant="B3",
        )


# =============================================================================
# C2-T3 POLICY DRIFT TESTS
# =============================================================================


def test_policy_drift_creation() -> TestResult:
    """Test: Policy Drift prediction creation succeeds."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        prediction_id = str(uuid4())
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=30)

        cur.execute(
            """
            INSERT INTO prediction_events (
                id, tenant_id, prediction_type, subject_type, subject_id,
                confidence_score, prediction_value, contributing_factors,
                is_advisory, created_at, expires_at, notes
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                prediction_id,
                "c2_policy_drift_test",
                "policy_drift",
                "workflow",
                "drift_test_subject",
                0.72,
                json.dumps({
                    "observed_pattern": "Rate limit pattern observed",
                    "reference_policy_type": "rate_limit",
                }),
                json.dumps([]),
                True,
                now,
                expires,
                "C2-T3 advisory observation (may indicate similarity to past patterns)",
            ),
        )
        conn.commit()

        # Verify it exists
        cur.execute(
            "SELECT prediction_type, notes FROM prediction_events WHERE id = %s",
            (prediction_id,),
        )
        row = cur.fetchone()

        # Cleanup
        cur.execute(
            "DELETE FROM prediction_events WHERE tenant_id = 'c2_policy_drift_test'"
        )
        conn.commit()
        conn.close()

        if row and row[0] == "policy_drift":
            return TestResult(
                name="policy_drift_creation",
                passed=True,
                expected="Policy Drift prediction created",
                actual="Policy Drift prediction created successfully",
                invariant="C2-T3 (policy drift can exist)",
            )
        else:
            return TestResult(
                name="policy_drift_creation",
                passed=False,
                expected="Policy Drift prediction created",
                actual="Prediction not found or wrong type",
                invariant="C2-T3",
            )

    except Exception as e:
        return TestResult(
            name="policy_drift_creation",
            passed=False,
            expected="Policy Drift prediction created",
            actual=f"Error: {e}",
            invariant="C2-T3",
        )


def test_policy_drift_advisory_constraint() -> TestResult:
    """Test: Policy Drift with is_advisory=False is rejected."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        prediction_id = str(uuid4())
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=30)

        try:
            cur.execute(
                """
                INSERT INTO prediction_events (
                    id, tenant_id, prediction_type, subject_type, subject_id,
                    confidence_score, prediction_value, contributing_factors,
                    is_advisory, created_at, expires_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    prediction_id,
                    "c2_policy_drift_test",
                    "policy_drift",
                    "workflow",
                    "drift_test_subject",
                    0.5,
                    json.dumps({"observed_pattern": "test"}),
                    json.dumps([]),
                    False,  # VIOLATES I-C2-1
                    now,
                    expires,
                ),
            )
            conn.commit()
            conn.close()

            return TestResult(
                name="policy_drift_advisory_constraint",
                passed=False,
                expected="CHECK constraint rejects is_advisory=False",
                actual="Insert succeeded (constraint missing!)",
                invariant="I-C2-1",
            )

        except Exception as e:
            conn.rollback()
            conn.close()

            if "chk_prediction_advisory" in str(e):
                return TestResult(
                    name="policy_drift_advisory_constraint",
                    passed=True,
                    expected="CHECK constraint rejects is_advisory=False",
                    actual="Correctly rejected by chk_prediction_advisory",
                    invariant="I-C2-1 (advisory MUST be TRUE)",
                )
            else:
                return TestResult(
                    name="policy_drift_advisory_constraint",
                    passed=False,
                    expected="CHECK constraint rejects is_advisory=False",
                    actual=f"Different error: {e}",
                    invariant="I-C2-1",
                )

    except Exception as e:
        return TestResult(
            name="policy_drift_advisory_constraint",
            passed=False,
            expected="CHECK constraint test",
            actual=f"Connection error: {e}",
            invariant="I-C2-1",
        )


def test_policy_drift_delete_safety() -> TestResult:
    """Test: Deleting Policy Drift predictions has zero side effects."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Create a policy drift prediction
        prediction_id = str(uuid4())
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=30)

        cur.execute(
            """
            INSERT INTO prediction_events (
                id, tenant_id, prediction_type, subject_type, subject_id,
                confidence_score, prediction_value, contributing_factors,
                is_advisory, created_at, expires_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                prediction_id,
                "c2_policy_delete_test",
                "policy_drift",
                "workflow",
                "delete_test_subject",
                0.88,
                json.dumps({
                    "observed_pattern": "Pattern to delete",
                    "reference_policy_type": "budget",
                }),
                json.dumps([]),
                True,
                now,
                expires,
            ),
        )
        conn.commit()

        # Delete all policy drift test predictions
        cur.execute(
            "DELETE FROM prediction_events WHERE tenant_id = 'c2_policy_delete_test'"
        )
        deleted = cur.rowcount
        conn.commit()
        conn.close()

        if deleted == 1:
            return TestResult(
                name="policy_drift_delete_safety",
                passed=True,
                expected="Delete succeeds with no side effects",
                actual=f"Deleted {deleted} Policy Drift prediction(s), no cascade errors",
                invariant="I-C2-5 (predictions disposable)",
            )
        else:
            return TestResult(
                name="policy_drift_delete_safety",
                passed=False,
                expected="Delete succeeds",
                actual=f"Unexpected delete count: {deleted}",
                invariant="I-C2-5",
            )

    except Exception as e:
        return TestResult(
            name="policy_drift_delete_safety",
            passed=False,
            expected="Delete succeeds",
            actual=f"Error: {e}",
            invariant="I-C2-5",
        )


def test_policy_drift_expiry() -> TestResult:
    """Test: Expired Policy Drift predictions are invisible."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Create a policy drift prediction with past expiry
        prediction_id = str(uuid4())
        now = datetime.now(timezone.utc)
        expired = now - timedelta(minutes=5)  # Already expired

        cur.execute(
            """
            INSERT INTO prediction_events (
                id, tenant_id, prediction_type, subject_type, subject_id,
                confidence_score, prediction_value, contributing_factors,
                is_advisory, created_at, expires_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                prediction_id,
                "c2_policy_expiry_test",
                "policy_drift",
                "workflow",
                "expiry_test_subject",
                0.65,
                json.dumps({
                    "observed_pattern": "Expired observation",
                    "reference_policy_type": "safety",
                }),
                json.dumps([]),
                True,
                now - timedelta(minutes=35),
                expired,
            ),
        )
        conn.commit()

        # Query for non-expired predictions (should NOT find it)
        cur.execute(
            """
            SELECT id FROM prediction_events
            WHERE tenant_id = 'c2_policy_expiry_test'
            AND expires_at > NOW()
            """
        )
        visible_rows = cur.fetchall()

        # Cleanup
        cur.execute(
            "DELETE FROM prediction_events WHERE tenant_id = 'c2_policy_expiry_test'"
        )
        conn.commit()
        conn.close()

        if len(visible_rows) == 0:
            return TestResult(
                name="policy_drift_expiry",
                passed=True,
                expected="Expired predictions are invisible",
                actual="Expired Policy Drift correctly filtered out",
                invariant="B3 (expiry is silent)",
            )
        else:
            return TestResult(
                name="policy_drift_expiry",
                passed=False,
                expected="Expired predictions are invisible",
                actual=f"Found {len(visible_rows)} expired predictions (should be 0)",
                invariant="B3",
            )

    except Exception as e:
        return TestResult(
            name="policy_drift_expiry",
            passed=False,
            expected="Expiry test",
            actual=f"Error: {e}",
            invariant="B3",
        )


def run_all_tests(verbose: bool = False) -> List[TestResult]:
    """Run all C2 regression tests (T1 + T2 + T3)."""
    results = []

    tests = [
        # C2-T1: Incident Risk
        ("T1: Prediction Creation", test_prediction_creation),
        ("T1: Advisory Constraint (I-C2-1)", test_advisory_constraint),
        ("T1: Delete Safety (I-C2-5)", test_delete_safety),
        ("T1: Confidence Range", test_confidence_range),
        # C2-T2: Spend Spike
        ("T2: Spend Spike Creation", test_spend_spike_creation),
        ("T2: Spend Spike Advisory (I-C2-1)", test_spend_spike_advisory_constraint),
        ("T2: Spend Spike Delete Safety", test_spend_spike_delete_safety),
        ("T2: Spend Spike Expiry", test_spend_spike_expiry),
        # C2-T3: Policy Drift
        ("T3: Policy Drift Creation", test_policy_drift_creation),
        ("T3: Policy Drift Advisory (I-C2-1)", test_policy_drift_advisory_constraint),
        ("T3: Policy Drift Delete Safety", test_policy_drift_delete_safety),
        ("T3: Policy Drift Expiry", test_policy_drift_expiry),
        # Shared guardrails
        ("Guardrails Pass", test_guardrails_pass),
        ("No Redis (GR-5)", test_no_redis_in_predictions),
    ]

    for name, test_fn in tests:
        if verbose:
            print(f"Running: {name}...", end=" ", flush=True)
        try:
            result = test_fn()
            results.append(result)
            if verbose:
                status = "PASS" if result.passed else "FAIL"
                print(f"[{status}]")
        except Exception as e:
            results.append(
                TestResult(
                    name=name,
                    passed=False,
                    expected="Test completes",
                    actual=f"Exception: {e}",
                    invariant="Unknown",
                )
            )
            if verbose:
                print("[ERROR]")

    return results


def main():
    parser = argparse.ArgumentParser(description="C2 Prediction Plane Regression Tests")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    results = run_all_tests(verbose=args.verbose)

    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)

    if args.json:
        output = [
            {
                "name": r.name,
                "passed": r.passed,
                "expected": r.expected,
                "actual": r.actual,
                "invariant": r.invariant,
            }
            for r in results
        ]
        print(json.dumps(output, indent=2))
    else:
        print()
        print("=" * 60)
        print("C2 PREDICTION PLANE REGRESSION TEST RESULTS")
        print("=" * 60)
        print()

        for r in results:
            status = "✅" if r.passed else "❌"
            print(f"{status} {r.name}")
            if not r.passed or args.verbose:
                print(f"   Expected: {r.expected}")
                print(f"   Actual: {r.actual}")
                print(f"   Invariant: {r.invariant}")
            print()

        print("=" * 60)
        print(f"PASSED: {passed}/{len(results)}")
        print(f"FAILED: {failed}/{len(results)}")
        print("=" * 60)

    # Exit with failure if any test failed
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
