# M4-T5: Observability Deepening Tests
"""
Tests for structured logging and correlation ID propagation.

Tests:
1. Context propagation across workflow execution
2. Structured log formatting
3. Correlation ID generation and threading
4. Step-scoped context isolation
"""

from __future__ import annotations
import asyncio
import json
import logging
import os
from io import StringIO
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

os.environ.setdefault("DISABLE_EXTERNAL_CALLS", "1")


class TestLoggingContext:
    """Tests for workflow logging context."""

    def test_set_and_get_run_id(self):
        """Test setting and getting run_id from context."""
        from app.workflow.logging_context import (
            set_run_id, get_run_id, clear_context
        )

        clear_context()
        assert get_run_id() is None

        set_run_id("test-run-123")
        assert get_run_id() == "test-run-123"

        clear_context()
        assert get_run_id() is None

    def test_workflow_context_manager(self):
        """Test workflow context manager sets and clears context."""
        from app.workflow.logging_context import (
            workflow_context, get_run_id, get_workflow_id, get_correlation_id,
            clear_context
        )

        clear_context()

        with workflow_context(run_id="run-456", workflow_id="wf-789"):
            assert get_run_id() == "run-456"
            assert get_workflow_id() == "wf-789"
            assert get_correlation_id() is not None  # Auto-generated

        # Context should be cleared after exiting
        # Note: Context vars reset to previous value, which was None
        assert get_run_id() is None

    def test_step_context_manager(self):
        """Test step context manager is scoped correctly."""
        from app.workflow.logging_context import (
            workflow_context, step_context, get_step_id, get_step_index,
            get_run_id, clear_context
        )

        clear_context()

        with workflow_context(run_id="run-abc"):
            assert get_step_id() is None

            with step_context(step_id="step-1", step_index=0):
                assert get_step_id() == "step-1"
                assert get_step_index() == 0
                assert get_run_id() == "run-abc"  # Still has parent context

            # Step context cleared, workflow context remains
            assert get_step_id() is None
            assert get_run_id() == "run-abc"

    def test_nested_step_contexts(self):
        """Test nested step contexts work correctly."""
        from app.workflow.logging_context import (
            workflow_context, step_context, get_step_id, get_step_index,
            clear_context
        )

        clear_context()

        with workflow_context(run_id="run-nested"):
            with step_context(step_id="step-1", step_index=0):
                assert get_step_id() == "step-1"
                assert get_step_index() == 0

            with step_context(step_id="step-2", step_index=1):
                assert get_step_id() == "step-2"
                assert get_step_index() == 1

            with step_context(step_id="step-3", step_index=2):
                assert get_step_id() == "step-3"
                assert get_step_index() == 2

    def test_get_logging_context(self):
        """Test get_logging_context returns correct dict."""
        from app.workflow.logging_context import (
            workflow_context, step_context, get_logging_context, clear_context
        )

        clear_context()

        with workflow_context(
            run_id="run-ctx",
            workflow_id="wf-ctx",
            agent_id="agent-ctx",
            tenant_id="tenant-ctx",
        ):
            with step_context(step_id="step-ctx", step_index=5):
                ctx = get_logging_context()

                assert ctx["run_id"] == "run-ctx"
                assert ctx["workflow_id"] == "wf-ctx"
                assert ctx["agent_id"] == "agent-ctx"
                assert ctx["tenant_id"] == "tenant-ctx"
                assert ctx["step_id"] == "step-ctx"
                assert ctx["step_index"] == 5
                assert "correlation_id" in ctx

    def test_correlation_id_auto_generation(self):
        """Test correlation ID is auto-generated if not provided."""
        from app.workflow.logging_context import (
            workflow_context, get_correlation_id, clear_context
        )

        clear_context()

        with workflow_context(run_id="run-1"):
            corr1 = get_correlation_id()
            assert corr1 is not None
            assert corr1.startswith("corr-")

        with workflow_context(run_id="run-2"):
            corr2 = get_correlation_id()
            assert corr2 is not None
            assert corr2 != corr1  # Different runs get different correlation IDs

    def test_explicit_correlation_id(self):
        """Test explicit correlation ID is used when provided."""
        from app.workflow.logging_context import (
            workflow_context, get_correlation_id, clear_context
        )

        clear_context()

        with workflow_context(run_id="run-x", correlation_id="my-corr-123"):
            assert get_correlation_id() == "my-corr-123"


class TestStructuredFormatter:
    """Tests for structured JSON log formatting."""

    def test_structured_format_basic(self):
        """Test basic structured log formatting."""
        from app.workflow.logging_context import StructuredFormatter

        formatter = StructuredFormatter()

        # Create a log record
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"
        assert data["message"] == "Test message"
        assert "timestamp" in data

    def test_structured_format_with_context(self):
        """Test structured format includes context fields."""
        from app.workflow.logging_context import StructuredFormatter

        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test with context",
            args=(),
            exc_info=None,
        )

        # Add context fields
        record.run_id = "run-struct"
        record.step_id = "step-struct"
        record.correlation_id = "corr-struct"

        output = formatter.format(record)
        data = json.loads(output)

        assert data["run_id"] == "run-struct"
        assert data["step_id"] == "step-struct"
        assert data["correlation_id"] == "corr-struct"


class TestContextualLoggerAdapter:
    """Tests for contextual logger adapter."""

    def test_adapter_adds_context(self):
        """Test that adapter automatically adds context to logs."""
        from app.workflow.logging_context import (
            ContextualLoggerAdapter, workflow_context, step_context,
            clear_context
        )

        clear_context()

        # Setup logger with string buffer to capture output
        buffer = StringIO()
        handler = logging.StreamHandler(buffer)
        handler.setFormatter(logging.Formatter("%(message)s - %(run_id)s"))

        base_logger = logging.getLogger("test.adapter")
        base_logger.handlers = []
        base_logger.addHandler(handler)
        base_logger.setLevel(logging.DEBUG)

        adapter = ContextualLoggerAdapter(base_logger, {})

        with workflow_context(run_id="adapter-run"):
            adapter.info("Test message")

        output = buffer.getvalue()
        assert "adapter-run" in output

    def test_adapter_merges_extra(self):
        """Test adapter merges provided extra with context."""
        from app.workflow.logging_context import (
            ContextualLoggerAdapter, workflow_context, clear_context
        )

        clear_context()

        # Create a real logger with custom handler to capture extra fields
        captured_extras = []

        class CapturingHandler(logging.Handler):
            def emit(self, record):
                captured_extras.append({
                    "run_id": getattr(record, "run_id", None),
                    "custom_field": getattr(record, "custom_field", None),
                })

        base_logger = logging.getLogger("test.adapter.merge")
        base_logger.handlers = []
        base_logger.addHandler(CapturingHandler())
        base_logger.setLevel(logging.DEBUG)

        adapter = ContextualLoggerAdapter(base_logger, {})

        with workflow_context(run_id="merge-run"):
            adapter.info("Message", extra={"custom_field": "custom_value"})

        # Check that handler captured both context and custom field
        assert len(captured_extras) == 1
        assert captured_extras[0]["run_id"] == "merge-run"
        assert captured_extras[0]["custom_field"] == "custom_value"


class TestConcurrentContextIsolation:
    """Tests for context isolation in concurrent scenarios."""

    @pytest.mark.asyncio
    async def test_concurrent_workflows_isolated(self):
        """Test that concurrent workflows have isolated contexts."""
        from app.workflow.logging_context import (
            workflow_context, get_run_id, get_correlation_id, clear_context
        )

        clear_context()

        results = {}

        async def run_workflow(name: str, run_id: str):
            with workflow_context(run_id=run_id):
                # Simulate some async work
                await asyncio.sleep(0.01)
                results[name] = {
                    "run_id": get_run_id(),
                    "correlation_id": get_correlation_id(),
                }
                await asyncio.sleep(0.01)

                # Context should still be correct after await
                assert get_run_id() == run_id

        # Run multiple workflows concurrently
        await asyncio.gather(
            run_workflow("wf1", "run-1"),
            run_workflow("wf2", "run-2"),
            run_workflow("wf3", "run-3"),
        )

        # Each workflow should have captured its own run_id
        assert results["wf1"]["run_id"] == "run-1"
        assert results["wf2"]["run_id"] == "run-2"
        assert results["wf3"]["run_id"] == "run-3"

        # Correlation IDs should be unique
        corr_ids = [results[k]["correlation_id"] for k in results]
        assert len(set(corr_ids)) == 3

    @pytest.mark.asyncio
    async def test_concurrent_steps_isolated(self):
        """Test that concurrent steps within a workflow have isolated step contexts."""
        from app.workflow.logging_context import (
            workflow_context, step_context, get_step_id, get_run_id,
            clear_context
        )

        clear_context()

        results = []

        async def run_step(step_id: str, step_index: int):
            with step_context(step_id=step_id, step_index=step_index):
                await asyncio.sleep(0.01)
                results.append({
                    "step_id": get_step_id(),
                    "run_id": get_run_id(),  # Should be from parent context
                })

        with workflow_context(run_id="concurrent-steps"):
            await asyncio.gather(
                run_step("step-a", 0),
                run_step("step-b", 1),
                run_step("step-c", 2),
            )

        # All steps should have same run_id but different step_ids
        run_ids = [r["run_id"] for r in results]
        step_ids = [r["step_id"] for r in results]

        assert all(rid == "concurrent-steps" for rid in run_ids)
        assert set(step_ids) == {"step-a", "step-b", "step-c"}


class TestConfigureStructuredLogging:
    """Tests for structured logging configuration."""

    def test_configure_structured_logging(self):
        """Test structured logging configuration."""
        from app.workflow.logging_context import configure_structured_logging

        logger = configure_structured_logging(
            level=logging.DEBUG,
            logger_name="test.structured"
        )

        assert logger.level == logging.DEBUG
        assert len(logger.handlers) == 1

        # Handler should have StructuredFormatter
        from app.workflow.logging_context import StructuredFormatter
        assert isinstance(logger.handlers[0].formatter, StructuredFormatter)

    def test_get_contextual_logger(self):
        """Test getting a contextual logger."""
        from app.workflow.logging_context import (
            get_contextual_logger, ContextualLoggerAdapter
        )

        logger = get_contextual_logger("test.contextual")

        assert isinstance(logger, ContextualLoggerAdapter)


class TestLoggingIntegration:
    """Integration tests for logging with actual workflow execution."""

    @pytest.mark.asyncio
    async def test_logging_during_workflow_execution(self):
        """Test logging captures context during simulated workflow execution."""
        from app.workflow.logging_context import (
            workflow_context, step_context, get_contextual_logger,
            get_logging_context, clear_context
        )

        clear_context()

        captured_contexts = []

        # Simulate workflow execution with logging
        with workflow_context(
            run_id="integration-run",
            workflow_id="integration-wf",
            agent_id="integration-agent",
        ):
            # Record context at workflow level
            captured_contexts.append(("workflow_start", get_logging_context().copy()))

            for i in range(3):
                with step_context(step_id=f"step-{i}", step_index=i):
                    # Record context at step level
                    captured_contexts.append((f"step_{i}", get_logging_context().copy()))

            captured_contexts.append(("workflow_end", get_logging_context().copy()))

        # Verify contexts
        wf_start = captured_contexts[0][1]
        assert wf_start["run_id"] == "integration-run"
        assert "step_id" not in wf_start  # No step context yet

        step_0 = captured_contexts[1][1]
        assert step_0["run_id"] == "integration-run"
        assert step_0["step_id"] == "step-0"
        assert step_0["step_index"] == 0

        step_2 = captured_contexts[3][1]
        assert step_2["step_id"] == "step-2"
        assert step_2["step_index"] == 2

        wf_end = captured_contexts[4][1]
        assert wf_end["run_id"] == "integration-run"
        assert "step_id" not in wf_end  # Step context cleared
