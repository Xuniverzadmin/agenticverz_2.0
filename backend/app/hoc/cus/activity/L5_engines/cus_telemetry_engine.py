# Layer: L5 — Domain Engine
# STUB_ENGINE: True
# AUDIENCE: CUSTOMER
# Role: Customer telemetry engine - LLM usage ingestion and reporting
# NOTE: Renamed cus_telemetry_service.py → cus_telemetry_engine.py (2026-01-31)
#       per BANNED_NAMING rule (*_service.py → *_engine.py for L5 files)
# Temporal:
#   Trigger: api
#   Execution: async
# Callers: cus_telemetry.py
# Allowed Imports: L6 (drivers)
# Forbidden Imports: L1, L2, L3, sqlalchemy direct
# Reference: SWEEP-03 Batch 2, PIN-468

"""
CusTelemetryEngine (SWEEP-03 Batch 2)

PURPOSE:
    Customer telemetry ingestion and usage reporting.
    Called by cus_telemetry.py API endpoints.

INTERFACE:
    - CusTelemetryEngine (stub, disconnected from legacy)
    - CusTelemetryService (alias for CusTelemetryEngine)
    - IngestResult (dataclass)
    - BatchIngestResult (dataclass)
    - get_cus_telemetry_engine() -> CusTelemetryEngine
    - get_cus_telemetry_service() -> CusTelemetryService

Usage:
    from app.hoc.cus.activity.L5_engines.cus_telemetry_engine import get_cus_telemetry_engine

IMPLEMENTATION NOTES:
    Legacy import disconnected (PIN-503 Cleansing Cycle, 2026-01-31).
    Stub classes maintain interface contract. Methods raise NotImplementedError
    until HOC-native implementation is wired.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# =============================================================================
# LEGACY DISCONNECTED (2026-01-31) — Cleansing Cycle PIN-503
# Was: from app.services.cus_telemetry_engine import (
#     BatchIngestResult, CusTelemetryEngine, IngestResult, get_cus_telemetry_engine,
# )
# TODO: rewire to HOC equivalent candidate during rewiring phase
#       Real implementation lives in app/services/cus_telemetry_engine.py
#       Requires ideal contractor analysis: does telemetry belong in activity domain?
# =============================================================================


@dataclass
class IngestResult:
    """Result of single usage ingestion."""
    status: str  # "accepted" or "duplicate"
    id: Optional[str] = None
    call_id: Optional[str] = None


@dataclass
class BatchIngestResult:
    """Result of batch usage ingestion."""
    accepted: int = 0
    duplicates: int = 0
    errors: int = 0
    total: int = 0


class CusTelemetryEngine:
    """Stub: Customer telemetry engine (disconnected from legacy).

    TODO: rewire to HOC equivalent candidate during rewiring phase.
    Original implementation: app/services/cus_telemetry_engine.py
    """

    def __init__(self, driver: Any = None):
        self._driver = driver

    async def ingest_usage(self, tenant_id: str, integration_id: str, payload: Any) -> IngestResult:
        raise NotImplementedError("CusTelemetryEngine disconnected from legacy — awaiting HOC rewire (PIN-503)")

    async def ingest_batch(self, tenant_id: str, default_integration_id: Optional[str], records: List[Any]) -> BatchIngestResult:
        raise NotImplementedError("CusTelemetryEngine disconnected from legacy — awaiting HOC rewire (PIN-503)")

    async def get_usage(self, tenant_id: str, **kwargs: Any) -> List[Dict[str, Any]]:
        raise NotImplementedError("CusTelemetryEngine disconnected from legacy — awaiting HOC rewire (PIN-503)")

    async def get_usage_summary(self, tenant_id: str, **kwargs: Any) -> Dict[str, Any]:
        raise NotImplementedError("CusTelemetryEngine disconnected from legacy — awaiting HOC rewire (PIN-503)")


def get_cus_telemetry_engine() -> CusTelemetryEngine:
    """Stub factory — returns disconnected engine."""
    return CusTelemetryEngine()

# =============================================================================
# HOC Aliases
# =============================================================================

# Alias for backward compatibility
CusTelemetryService = CusTelemetryEngine


def get_cus_telemetry_service() -> CusTelemetryService:
    """Get the CusTelemetryService instance.

    Returns:
        CusTelemetryService instance

    Note:
        Delegates to get_cus_telemetry_engine() which creates the engine
        with proper L6 driver injection.
    """
    return get_cus_telemetry_engine()


__all__ = [
    "CusTelemetryService",
    "CusTelemetryEngine",
    "IngestResult",
    "BatchIngestResult",
    "get_cus_telemetry_service",
    "get_cus_telemetry_engine",
]
