# M4-T5: Observability Deepening - Logging Context
"""
Structured logging context for workflow execution.

Provides:
1. Correlation ID propagation across all workflow operations
2. Structured logging with run_id, step_id, agent_id
3. Context manager for scoped logging
4. Thread-safe context storage using contextvars

Usage:
    with WorkflowLoggingContext(run_id="run-123", agent_id="agent-456"):
        logger.info("Step executed", extra=get_logging_context())
"""

from __future__ import annotations

import contextvars
import logging
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Context variables for thread-safe propagation
_run_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("run_id", default=None)
_workflow_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("workflow_id", default=None)
_agent_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("agent_id", default=None)
_step_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("step_id", default=None)
_step_index: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar("step_index", default=None)
_correlation_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("correlation_id", default=None)
_tenant_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("tenant_id", default=None)


def get_run_id() -> Optional[str]:
    """Get current run ID from context."""
    return _run_id.get()


def get_workflow_id() -> Optional[str]:
    """Get current workflow ID from context."""
    return _workflow_id.get()


def get_agent_id() -> Optional[str]:
    """Get current agent ID from context."""
    return _agent_id.get()


def get_step_id() -> Optional[str]:
    """Get current step ID from context."""
    return _step_id.get()


def get_step_index() -> Optional[int]:
    """Get current step index from context."""
    return _step_index.get()


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID from context."""
    return _correlation_id.get()


def get_tenant_id() -> Optional[str]:
    """Get current tenant ID from context."""
    return _tenant_id.get()


def set_run_id(run_id: str) -> contextvars.Token:
    """Set run ID in context."""
    return _run_id.set(run_id)


def set_workflow_id(workflow_id: str) -> contextvars.Token:
    """Set workflow ID in context."""
    return _workflow_id.set(workflow_id)


def set_agent_id(agent_id: str) -> contextvars.Token:
    """Set agent ID in context."""
    return _agent_id.set(agent_id)


def set_step_context(step_id: str, step_index: int) -> tuple:
    """Set step context."""
    return (_step_id.set(step_id), _step_index.set(step_index))


def set_correlation_id(correlation_id: str) -> contextvars.Token:
    """Set correlation ID in context."""
    return _correlation_id.set(correlation_id)


def set_tenant_id(tenant_id: str) -> contextvars.Token:
    """Set tenant ID in context."""
    return _tenant_id.set(tenant_id)


def get_logging_context() -> Dict[str, Any]:
    """
    Get all current logging context as a dictionary.

    Returns dict with only non-None values for use in logger.info(..., extra=get_logging_context())
    """
    context = {}

    if (v := get_correlation_id()) is not None:
        context["correlation_id"] = v
    if (v := get_run_id()) is not None:
        context["run_id"] = v
    if (v := get_workflow_id()) is not None:
        context["workflow_id"] = v
    if (v := get_agent_id()) is not None:
        context["agent_id"] = v
    if (v := get_step_id()) is not None:
        context["step_id"] = v
    if (v := get_step_index()) is not None:
        context["step_index"] = v
    if (v := get_tenant_id()) is not None:
        context["tenant_id"] = v

    return context


def clear_context() -> None:
    """Clear all context variables."""
    _run_id.set(None)
    _workflow_id.set(None)
    _agent_id.set(None)
    _step_id.set(None)
    _step_index.set(None)
    _correlation_id.set(None)
    _tenant_id.set(None)


@contextmanager
def workflow_context(
    run_id: str,
    workflow_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
):
    """
    Context manager for workflow-scoped logging.

    Usage:
        with workflow_context(run_id="run-123", workflow_id="wf-456"):
            # All log statements within this block will have run_id and workflow_id
            logger.info("Processing step", extra=get_logging_context())
    """
    # Generate correlation ID if not provided
    if correlation_id is None:
        correlation_id = f"corr-{uuid.uuid4().hex[:12]}"

    # Save tokens for cleanup
    tokens = []
    tokens.append(_run_id.set(run_id))
    tokens.append(_correlation_id.set(correlation_id))

    if workflow_id:
        tokens.append(_workflow_id.set(workflow_id))
    if agent_id:
        tokens.append(_agent_id.set(agent_id))
    if tenant_id:
        tokens.append(_tenant_id.set(tenant_id))

    try:
        yield
    finally:
        # Reset to previous values
        for token in tokens:
            try:
                token.var.reset(token)
            except Exception:
                pass


@contextmanager
def step_context(step_id: str, step_index: int):
    """
    Context manager for step-scoped logging.

    Usage:
        with step_context(step_id="step-1", step_index=0):
            logger.info("Executing skill", extra=get_logging_context())
    """
    step_token = _step_id.set(step_id)
    index_token = _step_index.set(step_index)

    try:
        yield
    finally:
        _step_id.reset(step_token)
        _step_index.reset(index_token)


class ContextualLoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that automatically adds workflow context to all log records.

    Usage:
        logger = ContextualLoggerAdapter(logging.getLogger("my.module"))
        logger.info("Message")  # Automatically includes run_id, step_id, etc.
    """

    def process(self, msg, kwargs):
        # Get current context
        context = get_logging_context()

        # Merge with any extra provided
        extra = kwargs.get("extra", {})
        extra.update(context)
        kwargs["extra"] = extra

        return msg, kwargs


class StructuredFormatter(logging.Formatter):
    """
    Structured log formatter that outputs JSON with context fields.

    Format:
    {
        "timestamp": "2024-12-02T12:00:00Z",
        "level": "INFO",
        "logger": "nova.workflow.engine",
        "message": "Step executed",
        "run_id": "run-123",
        "step_id": "step-1",
        ...
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add context fields
        for field in ["correlation_id", "run_id", "workflow_id", "agent_id", "step_id", "step_index", "tenant_id"]:
            if hasattr(record, field) and getattr(record, field) is not None:
                log_data[field] = getattr(record, field)

        # Add any other extra fields
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if (
                    key not in log_data
                    and not key.startswith("_")
                    and key
                    not in [
                        "name",
                        "msg",
                        "args",
                        "created",
                        "filename",
                        "funcName",
                        "levelname",
                        "levelno",
                        "lineno",
                        "module",
                        "msecs",
                        "pathname",
                        "process",
                        "processName",
                        "relativeCreated",
                        "stack_info",
                        "exc_info",
                        "exc_text",
                        "thread",
                        "threadName",
                        "message",
                        "asctime",
                    ]
                ):
                    try:
                        # Only include JSON-serializable values
                        import json

                        json.dumps(value)
                        log_data[key] = value
                    except (TypeError, ValueError):
                        pass

        import json

        return json.dumps(log_data)


def configure_structured_logging(
    level: int = logging.INFO,
    logger_name: Optional[str] = None,
) -> logging.Logger:
    """
    Configure a logger with structured JSON output.

    Args:
        level: Logging level (default: INFO)
        logger_name: Logger name (default: root logger)

    Returns:
        Configured logger
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Add structured handler
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())
    logger.addHandler(handler)

    return logger


def get_contextual_logger(name: str) -> ContextualLoggerAdapter:
    """
    Get a logger that automatically includes workflow context.

    Args:
        name: Logger name

    Returns:
        ContextualLoggerAdapter wrapping the named logger
    """
    return ContextualLoggerAdapter(logging.getLogger(name), {})
