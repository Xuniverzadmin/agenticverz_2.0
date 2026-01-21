# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Log Exports model for LOGS Domain V2 (O5 evidence bundles)
# Callers: logs API, LogExportService
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: LOGS_DOMAIN_V2_CONTRACT.md

"""
Log Exports Model (LOGS Domain V2)

SCOPE: LOGS domain — O5 evidence bundles.

LogExport tracks audit-grade evidence exports:
- APPEND-ONLY (enforced by DB trigger)
- WRITE-ONCE (no UPDATE, no DELETE)
- Every export is itself logged (audit trail)

Per LOGS_DOMAIN_V2_CONTRACT.md:
- Captures export metadata and provenance
- Integrates with correlation spine
- Supports compliance tags (SOC2, ISO27001)
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


# =============================================================================
# Enums
# =============================================================================


class ExportScope(str, Enum):
    """Scope of the export."""
    LLM_RUN = "llm_run"
    SYSTEM = "system"
    AUDIT = "audit"
    COMPLIANCE = "compliance"


class ExportFormat(str, Enum):
    """Export file format."""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    ZIP = "zip"


class ExportOrigin(str, Enum):
    """Who/what initiated the export."""
    SYSTEM = "SYSTEM"
    HUMAN = "HUMAN"
    AGENT = "AGENT"


class ExportStatus(str, Enum):
    """Export completion status."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# LogExport Model — Immutable Export Record
# =============================================================================


class LogExport(SQLModel, table=True):
    """
    Immutable record for log/evidence exports (LOGS domain O5).

    Tracks audit-grade evidence exports with full provenance.
    APPEND-ONLY: No UPDATE, no DELETE (enforced by DB trigger).

    Per Evidence Metadata Contract:
    - Origin tracks who initiated (HUMAN > AGENT > SYSTEM)
    - source_component identifies the producer
    - correlation_id enables cross-system tracing
    - checksum provides integrity verification
    """
    __tablename__ = "log_exports"

    id: str = Field(default_factory=generate_uuid, primary_key=True, max_length=64)
    tenant_id: str = Field(foreign_key="tenants.id", max_length=64)

    # Scope
    scope: str = Field(max_length=32)  # ExportScope enum
    run_id: Optional[str] = Field(default=None, max_length=64)  # For run-scoped exports

    # Request metadata
    requested_by: str = Field(max_length=128)
    format: str = Field(max_length=16)  # ExportFormat enum

    # Provenance (per Evidence Metadata Contract)
    origin: str = Field(max_length=32)  # ExportOrigin enum
    source_component: str = Field(default="LogExportService", max_length=64)
    correlation_id: Optional[str] = Field(default=None, max_length=64)

    # Completion
    checksum: Optional[str] = Field(default=None, max_length=128)
    status: str = Field(default="pending", max_length=32)  # ExportStatus enum
    delivered_at: Optional[datetime] = None

    # Immutable timestamp
    created_at: datetime = Field(default_factory=utc_now)


# =============================================================================
# Export all
# =============================================================================

__all__ = [
    # Enums
    "ExportScope",
    "ExportFormat",
    "ExportOrigin",
    "ExportStatus",
    # Model
    "LogExport",
]
