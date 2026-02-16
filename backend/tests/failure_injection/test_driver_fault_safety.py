# Layer: TEST
# AUDIENCE: INTERNAL
# Role: Deterministic fault injection — driver exceptions, timeouts, stale reads
# Reference: BA-22 Business Assurance Guardrails
# artifact_class: TEST

"""
Fault-injection tests for L6 driver safety behaviour.

Each test injects a specific fault into a minimal mock driver and verifies
that the caller layer produces a structured, safe error response rather than
leaking raw exceptions or leaving the system in an inconsistent state.

Structured error contract:
    {"error": True, "code": <str>, "message": <str>, "safe": True, ...}
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Minimal mock driver infrastructure (no production imports)
# ---------------------------------------------------------------------------

class _MockSession:
    """Simulates a DB session with transaction tracking."""

    def __init__(self):
        self.committed = False
        self.rolled_back = False
        self.begun = False
        self._writes: list[dict] = []

    def begin(self):
        self.begun = True
        return self

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True
        self._writes.clear()

    def add_write(self, record: dict):
        self._writes.append(record)

    def __enter__(self):
        self.begin()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        return False  # do not suppress exceptions


class _MockDriver:
    """Minimal stand-in for an L6 driver."""

    def __init__(self, *, side_effect=None, return_value=None):
        self._side_effect = side_effect
        self._return_value = return_value

    def execute(self, **kwargs):
        if self._side_effect is not None:
            raise self._side_effect
        return self._return_value


# ---------------------------------------------------------------------------
# Caller-layer safety harness (what an L4 handler would do)
# ---------------------------------------------------------------------------

def _safe_call(driver: _MockDriver, session: _MockSession, **kwargs) -> dict:
    """
    Simulates an L4 handler wrapping a driver call with safety semantics.

    Returns a structured error dict on any fault, ensuring the session is
    rolled back and the system remains in a known-good state.
    """
    try:
        with session:
            result = driver.execute(**kwargs)
            if result is None:
                session.rollback()
                return {
                    "error": True,
                    "code": "NULL_RESULT",
                    "message": "Driver returned no data when a result was expected",
                    "safe": True,
                }
            return {"error": False, "data": result}
    except TimeoutError:
        return {
            "error": True,
            "code": "TIMEOUT",
            "message": "Driver operation timed out",
            "safe": True,
            "retryable": True,
        }
    except ConnectionRefusedError:
        return {
            "error": True,
            "code": "SERVICE_UNAVAILABLE",
            "message": "Connection to downstream service refused",
            "safe": True,
            "retryable": True,
        }
    except _IntegrityError:
        return {
            "error": True,
            "code": "CONFLICT",
            "message": "Duplicate key or constraint violation",
            "safe": True,
            "retryable": False,
        }
    except _SerializationError:
        return {
            "error": True,
            "code": "SERIALIZATION_FAILURE",
            "message": "Transaction serialization conflict — retryable",
            "safe": True,
            "retryable": True,
        }
    except RuntimeError as exc:
        return {
            "error": True,
            "code": "DRIVER_ERROR",
            "message": str(exc),
            "safe": True,
        }
    except Exception as exc:
        return {
            "error": True,
            "code": "UNKNOWN",
            "message": f"Unhandled driver fault: {exc}",
            "safe": True,
        }


# Custom exception stand-ins (avoid importing real DB libraries)
class _IntegrityError(Exception):
    """Stand-in for sqlalchemy.exc.IntegrityError / psycopg duplicate key."""


class _SerializationError(Exception):
    """Stand-in for serialization/deadlock errors."""


# ---------------------------------------------------------------------------
# Staleness detection helper
# ---------------------------------------------------------------------------

def _check_staleness(result: dict, expected_sequence_no: int) -> dict:
    """
    Verifies that a driver result carries a sequence_no >= expected.
    Returns a structured error if the data is stale.
    """
    actual_seq = result.get("sequence_no")
    if actual_seq is None:
        return {
            "error": True,
            "code": "MISSING_SEQUENCE",
            "message": "Driver result missing sequence_no — cannot verify freshness",
            "safe": True,
        }
    if actual_seq < expected_sequence_no:
        return {
            "error": True,
            "code": "STALE_READ",
            "message": (
                f"Stale data detected: got sequence_no={actual_seq}, "
                f"expected >= {expected_sequence_no}"
            ),
            "safe": True,
        }
    return {"error": False, "data": result}


# ---------------------------------------------------------------------------
# Partial-write safety harness
# ---------------------------------------------------------------------------

def _safe_multi_write(session: _MockSession, records: list[dict], *, fail_at: int | None = None) -> dict:
    """
    Simulates writing multiple records through a driver.  If *fail_at* is
    set, the driver raises after that many successful writes — the session
    context manager must roll back all writes.
    """
    try:
        with session:
            for idx, record in enumerate(records):
                if fail_at is not None and idx >= fail_at:
                    raise RuntimeError(f"Partial write failure after record {idx}")
                session.add_write(record)
            return {"error": False, "written": len(records)}
    except RuntimeError as exc:
        return {
            "error": True,
            "code": "PARTIAL_WRITE",
            "message": str(exc),
            "safe": True,
        }


# ===================================================================
# Tests
# ===================================================================


class TestDriverFaultSafety:
    """BA-22: deterministic fault-injection tests for L6 driver safety."""

    # ---------------------------------------------------------------
    # FI-001  RuntimeError
    # ---------------------------------------------------------------
    def test_driver_exception_returns_safe_error(self):
        """Simulate a driver raising RuntimeError — verify structured error."""
        driver = _MockDriver(side_effect=RuntimeError("disk I/O error"))
        session = _MockSession()

        result = _safe_call(driver, session)

        assert result["error"] is True
        assert result["code"] == "DRIVER_ERROR"
        assert "disk I/O error" in result["message"]
        assert result["safe"] is True
        # Session must have been rolled back
        assert session.rolled_back is True
        assert session.committed is False

    # ---------------------------------------------------------------
    # FI-002  TimeoutError
    # ---------------------------------------------------------------
    def test_driver_timeout_returns_safe_fallback(self):
        """Simulate a driver timeout — verify safe fallback response."""
        driver = _MockDriver(side_effect=TimeoutError("query exceeded 30s"))
        session = _MockSession()

        result = _safe_call(driver, session)

        assert result["error"] is True
        assert result["code"] == "TIMEOUT"
        assert "timed out" in result["message"]
        assert result["safe"] is True
        assert result["retryable"] is True
        # Session must have been rolled back
        assert session.rolled_back is True

    # ---------------------------------------------------------------
    # FI-003  Stale Read
    # ---------------------------------------------------------------
    def test_stale_read_detected_by_sequence_check(self):
        """Simulate stale data — verify staleness detected via sequence_no."""
        stale_data = {"id": "rec-1", "value": "old-value", "sequence_no": 5}
        expected_sequence_no = 10

        result = _check_staleness(stale_data, expected_sequence_no)

        assert result["error"] is True
        assert result["code"] == "STALE_READ"
        assert "sequence_no=5" in result["message"]
        assert f"expected >= {expected_sequence_no}" in result["message"]
        assert result["safe"] is True

        # Verify a fresh read passes
        fresh_data = {"id": "rec-1", "value": "current", "sequence_no": 12}
        fresh_result = _check_staleness(fresh_data, expected_sequence_no)
        assert fresh_result["error"] is False
        assert fresh_result["data"] == fresh_data

    # ---------------------------------------------------------------
    # FI-004  ConnectionRefusedError
    # ---------------------------------------------------------------
    def test_connection_refused_returns_service_unavailable(self):
        """Simulate connection refused — verify SERVICE_UNAVAILABLE response."""
        driver = _MockDriver(side_effect=ConnectionRefusedError("port 5432 refused"))
        session = _MockSession()

        result = _safe_call(driver, session)

        assert result["error"] is True
        assert result["code"] == "SERVICE_UNAVAILABLE"
        assert "refused" in result["message"].lower()
        assert result["safe"] is True
        assert result["retryable"] is True
        assert session.rolled_back is True

    # ---------------------------------------------------------------
    # FI-005  Partial Write
    # ---------------------------------------------------------------
    def test_partial_write_does_not_corrupt_state(self):
        """Simulate partial write failure — verify full rollback, zero persisted."""
        session = _MockSession()
        records = [
            {"id": 1, "name": "alpha"},
            {"id": 2, "name": "bravo"},
            {"id": 3, "name": "charlie"},
        ]

        result = _safe_multi_write(session, records, fail_at=2)

        assert result["error"] is True
        assert result["code"] == "PARTIAL_WRITE"
        assert result["safe"] is True
        # After rollback, the session's write buffer must be empty
        assert session.rolled_back is True
        assert len(session._writes) == 0, (
            "Partial writes must be cleared on rollback to prevent state corruption"
        )

    # ---------------------------------------------------------------
    # FI-006  Null Result
    # ---------------------------------------------------------------
    def test_null_result_from_driver_handled_gracefully(self):
        """Simulate driver returning None — verify graceful handling."""
        driver = _MockDriver(return_value=None)
        session = _MockSession()

        result = _safe_call(driver, session)

        assert result["error"] is True
        assert result["code"] == "NULL_RESULT"
        assert "no data" in result["message"].lower()
        assert result["safe"] is True

    # ---------------------------------------------------------------
    # FI-007  IntegrityError (duplicate key)
    # ---------------------------------------------------------------
    def test_duplicate_key_error_returns_conflict(self):
        """Simulate duplicate-key IntegrityError — verify CONFLICT response."""
        driver = _MockDriver(
            side_effect=_IntegrityError(
                "duplicate key value violates unique constraint \"pk_entity\""
            )
        )
        session = _MockSession()

        result = _safe_call(driver, session)

        assert result["error"] is True
        assert result["code"] == "CONFLICT"
        assert "duplicate" in result["message"].lower() or "constraint" in result["message"].lower()
        assert result["safe"] is True
        assert result["retryable"] is False
        assert session.rolled_back is True

    # ---------------------------------------------------------------
    # FI-008  Serialization Error
    # ---------------------------------------------------------------
    def test_serialization_error_retryable(self):
        """Simulate serialization failure — verify retryable error marker."""
        driver = _MockDriver(
            side_effect=_SerializationError(
                "could not serialize access due to concurrent update"
            )
        )
        session = _MockSession()

        result = _safe_call(driver, session)

        assert result["error"] is True
        assert result["code"] == "SERIALIZATION_FAILURE"
        assert result["safe"] is True
        assert result["retryable"] is True
        assert session.rolled_back is True


# ===================================================================
# Policy-specific fault-injection tests (POL-DELTA-05)
# ===================================================================


def _safe_policy_activate(driver: _MockDriver, session: _MockSession, schema: object) -> dict:
    """
    Simulates an L4 handler for policy.activate with schema validation.
    Returns structured error on invalid schema or driver fault.
    """
    # Schema validation (fail-closed)
    if not schema:
        return {
            "error": True,
            "code": "INVALID_SCHEMA",
            "message": "policy_schema is required but missing or empty",
            "safe": True,
        }
    if not isinstance(schema, (str, dict)):
        return {
            "error": True,
            "code": "INVALID_SCHEMA",
            "message": f"policy_schema must be str or dict, got {type(schema).__name__}",
            "safe": True,
        }
    return _safe_call(driver, session, schema=schema)


def _safe_policy_deactivate(
    driver: _MockDriver, session: _MockSession,
    is_system: bool, actor_type: str,
    current_version: int | None = None, expected_version: int | None = None,
) -> dict:
    """
    Simulates an L4 handler for policy.deactivate with authority + staleness checks.
    """
    if is_system and actor_type not in ("founder", "platform"):
        return {
            "error": True,
            "code": "FORBIDDEN",
            "message": f"system policy cannot be deactivated by '{actor_type}' caller",
            "safe": True,
        }
    # Stale read check (optimistic concurrency)
    if expected_version is not None and current_version is not None:
        if current_version != expected_version:
            return {
                "error": True,
                "code": "STALE_READ",
                "message": (
                    f"Policy was concurrently modified: "
                    f"expected version={expected_version}, current={current_version}"
                ),
                "safe": True,
            }
    return _safe_call(driver, session, is_system=is_system, actor_type=actor_type)


class TestPolicyFaultInjection:
    """POL-DELTA-05: Policy-domain-specific fault-injection proofs."""

    # ---------------------------------------------------------------
    # PFI-001  Policy driver DB timeout
    # ---------------------------------------------------------------
    def test_policy_driver_timeout_returns_safe_error(self):
        """Policy driver raises TimeoutError → structured error, no crash."""
        driver = _MockDriver(side_effect=TimeoutError("policy table lock timeout"))
        session = _MockSession()

        result = _safe_policy_activate(driver, session, schema={"rules": []})

        assert result["error"] is True
        assert result["code"] == "TIMEOUT"
        assert result["safe"] is True
        assert result["retryable"] is True
        assert session.rolled_back is True

    # ---------------------------------------------------------------
    # PFI-002  Policy schema validation failure (missing)
    # ---------------------------------------------------------------
    def test_policy_missing_schema_returns_structured_error(self):
        """policy.activate with None schema → structured error, not crash."""
        driver = _MockDriver(return_value={"policy_id": "p-1"})
        session = _MockSession()

        result = _safe_policy_activate(driver, session, schema=None)

        assert result["error"] is True
        assert result["code"] == "INVALID_SCHEMA"
        assert "missing" in result["message"]
        assert result["safe"] is True
        # Driver should NOT have been called
        assert session.begun is False

    # ---------------------------------------------------------------
    # PFI-003  Policy schema validation failure (wrong type)
    # ---------------------------------------------------------------
    def test_policy_invalid_schema_type_returns_structured_error(self):
        """policy.activate with int schema → structured error, not crash."""
        driver = _MockDriver(return_value={"policy_id": "p-1"})
        session = _MockSession()

        result = _safe_policy_activate(driver, session, schema=42)

        assert result["error"] is True
        assert result["code"] == "INVALID_SCHEMA"
        assert "int" in result["message"]
        assert result["safe"] is True
        assert session.begun is False

    # ---------------------------------------------------------------
    # PFI-004  Policy stale read (concurrent deactivation)
    # ---------------------------------------------------------------
    def test_policy_stale_read_concurrent_deactivation(self):
        """Concurrent deactivation detected via version mismatch → safe fallback."""
        driver = _MockDriver(return_value={"policy_id": "p-1", "status": "inactive"})
        session = _MockSession()

        result = _safe_policy_deactivate(
            driver, session,
            is_system=False, actor_type="user",
            current_version=5, expected_version=3,  # stale
        )

        assert result["error"] is True
        assert result["code"] == "STALE_READ"
        assert "concurrently modified" in result["message"]
        assert result["safe"] is True
        # Driver should NOT have been called due to stale check
        assert session.begun is False

    # ---------------------------------------------------------------
    # PFI-005  Policy deactivate authority rejection
    # ---------------------------------------------------------------
    def test_policy_deactivate_tenant_on_system_policy_returns_forbidden(self):
        """Tenant caller on system policy → FORBIDDEN, not driver call."""
        driver = _MockDriver(return_value={"policy_id": "p-1"})
        session = _MockSession()

        result = _safe_policy_deactivate(
            driver, session,
            is_system=True, actor_type="user",
        )

        assert result["error"] is True
        assert result["code"] == "FORBIDDEN"
        assert "system policy" in result["message"]
        assert result["safe"] is True
        assert session.begun is False

    # ---------------------------------------------------------------
    # PFI-006  Policy driver connection refused
    # ---------------------------------------------------------------
    def test_policy_driver_connection_refused(self):
        """Policy driver raises ConnectionRefusedError → SERVICE_UNAVAILABLE."""
        driver = _MockDriver(side_effect=ConnectionRefusedError("port 5432"))
        session = _MockSession()

        result = _safe_policy_activate(driver, session, schema={"rules": ["r1"]})

        assert result["error"] is True
        assert result["code"] == "SERVICE_UNAVAILABLE"
        assert result["safe"] is True
        assert result["retryable"] is True
        assert session.rolled_back is True

    # ---------------------------------------------------------------
    # PFI-007  Happy path: valid schema + version match
    # ---------------------------------------------------------------
    def test_policy_activate_happy_path(self):
        """policy.activate with valid schema → success."""
        driver = _MockDriver(return_value={"policy_id": "p-1", "status": "active"})
        session = _MockSession()

        result = _safe_policy_activate(driver, session, schema={"rules": ["r1"]})

        assert result["error"] is False
        assert result["data"]["status"] == "active"

    def test_policy_deactivate_happy_path(self):
        """policy.deactivate with valid authority + matching version → success."""
        driver = _MockDriver(return_value={"policy_id": "p-1", "status": "inactive"})
        session = _MockSession()

        result = _safe_policy_deactivate(
            driver, session,
            is_system=False, actor_type="user",
            current_version=3, expected_version=3,
        )

        assert result["error"] is False
        assert result["data"]["status"] == "inactive"
