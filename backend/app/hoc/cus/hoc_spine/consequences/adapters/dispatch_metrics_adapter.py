# Layer: L4 — HOC Spine (Consequences Adapter)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (post-dispatch, every operation)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: DispatchRecord via ConsequenceAdapter protocol
# Data Access:
#   Reads: none
#   Writes: none (in-memory aggregation only)
# Role: Dispatch metrics aggregator — tracks operation counts, error rates, latencies
# Callers: consequences/pipeline.py
# Allowed Imports: hoc_spine/services (dispatch_audit), consequences/ports
# Forbidden Imports: L1, L2, L5, L6, sqlalchemy, app.db
# Reference: Constitution §2.3, Gap G4 consequences expansion
# artifact_class: CODE

"""
Dispatch Metrics Adapter.

Aggregates operational metrics from DispatchRecords:
- Per-operation call counts (total, success, failure)
- Per-operation latency tracking (min, max, sum for avg computation)
- Per-tenant operation counts

In-memory only — no external dependencies. Thread-safe via Lock.
Metrics are queryable for observability dashboards and health checks.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from threading import Lock
from typing import Dict, Optional

from app.hoc.cus.hoc_spine.services.dispatch_audit import DispatchRecord

logger = logging.getLogger("nova.hoc_spine.consequences.dispatch_metrics")


@dataclass
class OperationMetrics:
    """Aggregated metrics for a single operation name."""

    total: int = 0
    success: int = 0
    failure: int = 0
    latency_sum_ms: float = 0.0
    latency_min_ms: float = float("inf")
    latency_max_ms: float = 0.0

    @property
    def avg_latency_ms(self) -> float:
        """Average latency in milliseconds."""
        return self.latency_sum_ms / self.total if self.total > 0 else 0.0

    @property
    def error_rate(self) -> float:
        """Error rate as a fraction (0.0–1.0)."""
        return self.failure / self.total if self.total > 0 else 0.0

    def to_dict(self) -> dict:
        """Serialize for API/logging."""
        return {
            "total": self.total,
            "success": self.success,
            "failure": self.failure,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "min_latency_ms": round(self.latency_min_ms, 2) if self.total > 0 else 0.0,
            "max_latency_ms": round(self.latency_max_ms, 2),
            "error_rate": round(self.error_rate, 4),
        }


class DispatchMetricsAdapter:
    """
    Post-dispatch consequence: aggregate operation metrics.

    Satisfies ConsequenceAdapter protocol. Thread-safe.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self._operations: Dict[str, OperationMetrics] = defaultdict(OperationMetrics)
        self._tenant_counts: Dict[str, int] = defaultdict(int)

    @property
    def name(self) -> str:
        return "dispatch_metrics"

    def handle(self, record: DispatchRecord) -> None:
        """Aggregate metrics from a dispatch record."""
        with self._lock:
            m = self._operations[record.operation]
            m.total += 1
            if record.success:
                m.success += 1
            else:
                m.failure += 1
            m.latency_sum_ms += record.duration_ms
            if record.duration_ms < m.latency_min_ms:
                m.latency_min_ms = record.duration_ms
            if record.duration_ms > m.latency_max_ms:
                m.latency_max_ms = record.duration_ms

            self._tenant_counts[record.tenant_id] += 1

    def get_operation_metrics(self, operation: Optional[str] = None) -> dict:
        """
        Get aggregated metrics.

        Args:
            operation: Filter by operation name. If None, returns all.

        Returns:
            Dict of operation_name -> metrics dict
        """
        with self._lock:
            if operation:
                m = self._operations.get(operation)
                return {operation: m.to_dict()} if m else {}
            return {op: m.to_dict() for op, m in self._operations.items()}

    def get_tenant_counts(self) -> dict:
        """Get per-tenant dispatch counts."""
        with self._lock:
            return dict(self._tenant_counts)

    def get_summary(self) -> dict:
        """Get high-level summary across all operations."""
        with self._lock:
            total = sum(m.total for m in self._operations.values())
            failures = sum(m.failure for m in self._operations.values())
            return {
                "total_dispatches": total,
                "total_failures": failures,
                "error_rate": round(failures / total, 4) if total > 0 else 0.0,
                "operation_count": len(self._operations),
                "tenant_count": len(self._tenant_counts),
            }


# Module-level singleton
_instance: Optional[DispatchMetricsAdapter] = None


def get_dispatch_metrics_adapter() -> DispatchMetricsAdapter:
    """Get the dispatch metrics adapter singleton."""
    global _instance
    if _instance is None:
        _instance = DispatchMetricsAdapter()
    return _instance
