# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: LLM Run Records and System Records models for Logs domain (PIN-413)
# Callers: runtime_projections/logs/*, worker capture
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-413 Domain Design — Logs v1 Expansion

"""
Logs Records Models (PIN-413)

SCOPE: Logs domain ONLY.

Two immutable record types:
- LLMRunRecord: Immutable execution record for every LLM run
- SystemRecord: Immutable records for system-level events

Both are:
- APPEND-ONLY (enforced by DB trigger)
- WRITE-ONCE (no UPDATE, no DELETE)
- Trust anchors for verification

These are SEPARATE from Activity tables:
- Activity is stateful, lifecycle-driven
- Logs are immutable facts
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


# =============================================================================
# LLM Run Record Enums
# =============================================================================


class ExecutionStatus(str, Enum):
    """LLM run execution status values."""
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    TIMEOUT = "TIMEOUT"


class RecordSource(str, Enum):
    """Source of the record."""
    API = "API"
    SDK = "SDK"
    SYSTEM = "SYSTEM"
    SYNTHETIC = "SYNTHETIC"
    WORKER = "WORKER"


# =============================================================================
# System Record Enums
# =============================================================================


class SystemComponent(str, Enum):
    """System component types."""
    WORKER = "worker"
    API = "api"
    SCHEDULER = "scheduler"
    DB = "db"
    AUTH = "auth"
    MIGRATION = "migration"


class SystemEventType(str, Enum):
    """System event types."""
    STARTUP = "STARTUP"
    SHUTDOWN = "SHUTDOWN"
    RESTART = "RESTART"
    DEPLOY = "DEPLOY"
    MIGRATION = "MIGRATION"
    AUTH_CHANGE = "AUTH_CHANGE"
    CONFIG_CHANGE = "CONFIG_CHANGE"
    ERROR = "ERROR"
    HEALTH_CHECK = "HEALTH_CHECK"


class SystemSeverity(str, Enum):
    """System event severity levels."""
    INFO = "INFO"
    WARN = "WARN"
    CRITICAL = "CRITICAL"


class SystemCausedBy(str, Enum):
    """What caused the system event."""
    SYSTEM = "SYSTEM"
    HUMAN = "HUMAN"
    AUTOMATION = "AUTOMATION"


# =============================================================================
# LLM Run Record Model — Immutable Execution Record
# =============================================================================


class LLMRunRecord(SQLModel, table=True):
    """
    Immutable execution record for every LLM run (Logs domain).

    This is the TRUST ANCHOR, not Activity UI.
    Records are WRITE-ONCE - no UPDATE, no DELETE (enforced by DB trigger).

    Answers:
    - Did this run really happen?
    - What exactly was sent/received (via hashes)?
    - What provider, model, tokens, cost?
    """
    __tablename__ = "llm_run_records"

    id: str = Field(default_factory=generate_uuid, primary_key=True, max_length=64)
    tenant_id: str = Field(foreign_key="tenants.id", max_length=64)
    run_id: str = Field(max_length=64, index=True)
    trace_id: Optional[str] = Field(default=None, max_length=64)

    # Provider / Model
    provider: str = Field(max_length=64)
    model: str = Field(max_length=128)

    # Content hashes (for verification without storing content)
    prompt_hash: Optional[str] = Field(default=None, max_length=64)
    response_hash: Optional[str] = Field(default=None, max_length=64)

    # Token counts
    input_tokens: int = Field(default=0)
    output_tokens: int = Field(default=0)
    cost_cents: int = Field(default=0)

    # Execution status
    execution_status: str = Field(max_length=32)  # ExecutionStatus enum

    # Timestamps
    started_at: datetime
    completed_at: Optional[datetime] = None

    # Source tracking
    source: str = Field(max_length=32)  # RecordSource enum
    is_synthetic: bool = Field(default=False)
    synthetic_scenario_id: Optional[str] = Field(default=None, max_length=64)

    # Record timestamp (immutable)
    created_at: datetime = Field(default_factory=utc_now)


# =============================================================================
# System Record Model — Immutable System Event Log
# =============================================================================


class SystemRecord(SQLModel, table=True):
    """
    Immutable records for system-level events that affect trust (Logs domain).

    NOT:
    - stdout spam
    - infra noise

    YES:
    - worker restarts
    - deployment changes
    - schema migrations
    - auth / permission changes

    Records are WRITE-ONCE - no UPDATE, no DELETE (enforced by DB trigger).
    """
    __tablename__ = "system_records"

    id: str = Field(default_factory=generate_uuid, primary_key=True, max_length=64)
    tenant_id: Optional[str] = Field(default=None, max_length=64)  # NULL for system-wide events

    # Event classification
    component: str = Field(max_length=64)  # SystemComponent enum
    event_type: str = Field(max_length=64)  # SystemEventType enum
    severity: str = Field(max_length=16)  # SystemSeverity enum

    # Event content
    summary: str
    details: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))

    # Causation
    caused_by: Optional[str] = Field(default=None, max_length=32)  # SystemCausedBy enum
    correlation_id: Optional[str] = Field(default=None, max_length=64)

    # Record timestamp (immutable)
    created_at: datetime = Field(default_factory=utc_now)


# =============================================================================
# Export all
# =============================================================================

__all__ = [
    # Enums
    "ExecutionStatus",
    "RecordSource",
    "SystemComponent",
    "SystemEventType",
    "SystemSeverity",
    "SystemCausedBy",
    # Models
    "LLMRunRecord",
    "SystemRecord",
]
