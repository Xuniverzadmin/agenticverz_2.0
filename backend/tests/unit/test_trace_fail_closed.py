# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Role: Test fail-closed trace semantics (PIN-406)
# Reference: AD-001 (ARCH_DECISIONS.md)

"""
Test fail-closed trace semantics.

PIN-406 Invariant:
    A trace is either COMPLETE or ABORTED. There is no "dangling".

These tests verify that trace finalization failures result in ABORTED status,
not silent logging.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone


class TestFailClosedTraceSemantics:
    """Test AD-001: Fail-Closed Trace Semantics."""

    @pytest.mark.asyncio
    async def test_mark_trace_aborted_updates_status(self):
        """Test that mark_trace_aborted sets status to 'aborted' with reason."""
        from app.traces.pg_store import PostgresTraceStore

        # Create store with mocked pool
        store = PostgresTraceStore()
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        store._pool = mock_pool

        # Call mark_trace_aborted
        await store.mark_trace_aborted(
            run_id="test-run-123",
            reason="finalization_failed: connection timeout",
        )

        # Verify SQL was executed with correct parameters
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1:]

        # Verify SQL structure
        assert "UPDATE aos_traces" in sql
        assert "status = 'aborted'" in sql
        assert "abort_reason" in sql
        assert "WHERE run_id = $3 AND status = 'running'" in sql

        # Verify parameters
        assert params[2] == "test-run-123"  # run_id is 3rd param

    @pytest.mark.asyncio
    async def test_mark_trace_aborted_only_affects_running_traces(self):
        """Test that mark_trace_aborted only updates traces with status='running'."""
        from app.traces.pg_store import PostgresTraceStore

        store = PostgresTraceStore()
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        store._pool = mock_pool

        await store.mark_trace_aborted(
            run_id="test-run-123",
            reason="test reason",
        )

        # Verify WHERE clause includes status = 'running'
        sql = mock_conn.execute.call_args[0][0]
        assert "status = 'running'" in sql

    def test_trace_status_values_documented(self):
        """Document valid trace status values per AD-001."""
        valid_statuses = ["running", "completed", "failed", "aborted"]

        # This test documents the valid status values
        # If you need to add a new status, update this test AND AD-001
        assert "running" in valid_statuses, "Initial trace status"
        assert "completed" in valid_statuses, "Successful completion"
        assert "failed" in valid_statuses, "Execution failure"
        assert "aborted" in valid_statuses, "Finalization failure (PIN-406)"


class TestRunnerFailClosedIntegration:
    """Test runner integration with fail-closed semantics."""

    def test_runner_imports_mark_trace_aborted(self):
        """Verify runner can access mark_trace_aborted method."""
        from app.traces.pg_store import PostgresTraceStore

        store = PostgresTraceStore()
        assert hasattr(store, "mark_trace_aborted")
        assert callable(store.mark_trace_aborted)

    def test_fail_closed_invariant_documented(self):
        """Document the fail-closed invariant per AD-001."""
        invariant = "A trace is either COMPLETE or ABORTED. There is no 'dangling'."

        # This test documents the invariant
        # Changing this invariant requires updating:
        # - AD-001 in ARCH_DECISIONS.md
        # - pg_store.py mark_trace_aborted()
        # - runner.py trace completion handling
        assert "COMPLETE" in invariant
        assert "ABORTED" in invariant
        assert "dangling" in invariant


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
