import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, "agent_id"):
            log_data["agent_id"] = record.agent_id
        if hasattr(record, "goal"):
            log_data["goal"] = record.goal
        if hasattr(record, "skill"):
            log_data["skill"] = record.skill
        if hasattr(record, "status"):
            log_data["status"] = record.status
        if hasattr(record, "run_id"):
            log_data["run_id"] = record.run_id
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data

        return json.dumps(log_data)


def setup_logging() -> logging.Logger:
    """Configure structured JSON logging."""
    logger = logging.getLogger("nova")
    logger.setLevel(logging.INFO)

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler with JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def log_request(
    logger: logging.Logger,
    agent_id: str,
    goal: str,
    skill: str,
    status: str,
    run_id: str = None,
    duration_ms: float = None,
    extra_data: Dict[str, Any] = None,
):
    """Log a request with structured data."""
    extra = {
        "agent_id": agent_id,
        "goal": goal,
        "skill": skill,
        "status": status,
    }
    if run_id:
        extra["run_id"] = run_id
    if duration_ms is not None:
        extra["duration_ms"] = duration_ms
    if extra_data:
        extra["extra_data"] = extra_data

    logger.info("skill_execution", extra=extra)


def log_provenance(
    logger: logging.Logger, run_id: str, agent_id: str, goal: str, plan: Dict[str, Any], tool_calls: list
):
    """Log provenance record."""
    extra = {
        "run_id": run_id,
        "agent_id": agent_id,
        "goal": goal,
        "extra_data": {"plan": plan, "tool_calls": tool_calls},
    }
    logger.info("provenance_recorded", extra=extra)
