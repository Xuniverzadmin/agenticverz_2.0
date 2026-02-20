# capability_id: CAP-012
# Layer: L4 — HOC Spine (Service)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Lifecycle:
#   Emits: Prometheus metrics
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: none (metrics are in-memory)
# Role: CostSim V2 Prometheus metrics (drift detection, circuit breaker)
# Callers: controls L6 drivers, analytics L5 engines
# Allowed Imports: stdlib, prometheus_client, hoc_spine services
# Forbidden Imports: L5_engines, L6, L7, sqlalchemy
# Reference: PIN-521 (extracted from analytics/L5_engines/metrics_engine.py)

"""
CostSim V2 Prometheus Metrics - HOC Spine Shared Service

PIN-521 Migration:
- Extracted from analytics/L5_engines/metrics_engine.py to hoc_spine/services
- L6 drivers can import this without layer violation
- Analytics L5_engines re-exports for backward compatibility

Metrics (6 required):
1. costsim_v2_drift_score - Drift score histogram
2. costsim_v2_cost_delta_cents - Cost delta distribution
3. costsim_v2_schema_errors_total - Schema validation errors
4. costsim_v2_simulation_duration_ms - V2 simulation latency
5. costsim_v2_comparison_verdict - Verdict distribution
6. costsim_v2_circuit_breaker_state - Circuit breaker state

Alert Rules:
- P1: drift_score > 0.2 for 5m (auto-disable)
- P2: drift_score > 0.15 for 15m (warning)
- P3: schema_errors > 5 in 1h (investigate)
"""

from __future__ import annotations

import logging
from typing import Optional

try:
    from prometheus_client import Counter, Gauge, Histogram, Info

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

from app.hoc.cus.hoc_spine.services.costsim_config import get_config

logger = logging.getLogger("nova.costsim.metrics")


# Metric buckets
DRIFT_SCORE_BUCKETS = (0.01, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 1.0)
COST_DELTA_BUCKETS = (1, 5, 10, 25, 50, 100, 250, 500, 1000)
DURATION_BUCKETS = (1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000)


class CostSimMetrics:
    """
    Prometheus metrics for CostSim V2.

    Usage:
        metrics = CostSimMetrics()
        metrics.record_drift(drift_score=0.15, verdict="minor_drift")
        metrics.record_cost_delta(delta_cents=25)
        metrics.record_schema_error()
    """

    def __init__(self, prefix: str = "costsim_v2"):
        """
        Initialize metrics.

        Args:
            prefix: Metric name prefix
        """
        self.prefix = prefix
        self._initialized = False

        if PROMETHEUS_AVAILABLE:
            self._init_metrics()
        else:
            logger.warning("prometheus_client not available, metrics disabled")

    def _init_metrics(self) -> None:
        """Initialize Prometheus metrics."""
        if self._initialized:
            return

        # 1. Drift score histogram
        self._drift_score = Histogram(
            f"{self.prefix}_drift_score",
            "CostSim V2 drift score distribution",
            ["tenant_id"],
            buckets=DRIFT_SCORE_BUCKETS,
        )

        # 2. Cost delta histogram
        self._cost_delta_cents = Histogram(
            f"{self.prefix}_cost_delta_cents",
            "Cost delta between V1 and V2 (absolute cents)",
            ["tenant_id"],
            buckets=COST_DELTA_BUCKETS,
        )

        # 3. Schema errors counter
        self._schema_errors_total = Counter(
            f"{self.prefix}_schema_errors_total",
            "Total schema validation errors in V2",
            ["tenant_id", "error_type"],
        )

        # 4. Simulation duration histogram
        self._simulation_duration_ms = Histogram(
            f"{self.prefix}_simulation_duration_ms",
            "V2 simulation duration in milliseconds",
            ["tenant_id"],
            buckets=DURATION_BUCKETS,
        )

        # 5. Comparison verdict counter
        self._comparison_verdict_total = Counter(
            f"{self.prefix}_comparison_verdict_total",
            "Comparison verdict counts",
            ["tenant_id", "verdict"],
        )

        # 6. Circuit breaker state gauge
        self._circuit_breaker_state = Gauge(
            f"{self.prefix}_circuit_breaker_state",
            "Circuit breaker state (0=closed, 1=open)",
            ["tenant_id"],
        )

        # Additional metrics
        self._simulations_total = Counter(
            f"{self.prefix}_simulations_total",
            "Total V2 simulations",
            ["tenant_id", "status"],
        )

        self._provenance_logs_total = Counter(
            f"{self.prefix}_provenance_logs_total",
            "Total provenance log entries",
            ["tenant_id"],
        )

        self._canary_runs_total = Counter(
            f"{self.prefix}_canary_runs_total",
            "Total canary runs",
            ["status"],
        )

        self._kl_divergence = Gauge(
            f"{self.prefix}_kl_divergence",
            "Latest KL divergence from canary run",
            ["tenant_id"],
        )

        # Info metric for versioning
        self._version_info = Info(
            f"{self.prefix}_version",
            "CostSim V2 version information",
        )

        config = get_config()
        self._version_info.info(
            {
                "model_version": config.model_version,
                "adapter_version": config.adapter_version,
            }
        )

        # Circuit Breaker Event Metrics
        self._cb_disabled_total = Counter(
            "costsim_cb_disabled_total",
            "Total circuit breaker disable events",
            ["reason", "severity"],
        )

        self._cb_incidents_total = Counter(
            "costsim_cb_incidents_total",
            "Total circuit breaker incidents",
            ["severity", "resolved"],
        )

        self._cb_alert_queue_depth = Gauge(
            "costsim_cb_alert_queue_depth",
            "Current depth of alert queue (pending alerts)",
        )

        self._cb_alert_send_failures_total = Counter(
            "costsim_cb_alert_send_failures_total",
            "Total alert send failures",
            ["alert_type", "error_type"],
        )

        self._cb_enabled_total = Counter(
            "costsim_cb_enabled_total",
            "Total circuit breaker enable (recovery) events",
            ["reason"],
        )

        self._cb_auto_recovery_total = Counter(
            "costsim_cb_auto_recovery_total",
            "Total auto-recovery events after TTL expiry",
        )

        self._cb_consecutive_failures = Gauge(
            "costsim_cb_consecutive_failures",
            "Current consecutive failure count",
        )

        self._initialized = True

    def record_drift(
        self,
        drift_score: float,
        verdict: str,
        tenant_id: str = "default",
    ) -> None:
        """Record drift observation."""
        if not PROMETHEUS_AVAILABLE or not self._initialized:
            return
        self._drift_score.labels(tenant_id=tenant_id).observe(drift_score)
        self._comparison_verdict_total.labels(
            tenant_id=tenant_id,
            verdict=verdict,
        ).inc()

    def record_cost_delta(
        self,
        delta_cents: int,
        tenant_id: str = "default",
    ) -> None:
        """Record cost delta."""
        if not PROMETHEUS_AVAILABLE or not self._initialized:
            return
        self._cost_delta_cents.labels(tenant_id=tenant_id).observe(abs(delta_cents))

    def record_schema_error(
        self,
        error_type: str = "validation",
        tenant_id: str = "default",
    ) -> None:
        """Record schema validation error."""
        if not PROMETHEUS_AVAILABLE or not self._initialized:
            return
        self._schema_errors_total.labels(
            tenant_id=tenant_id,
            error_type=error_type,
        ).inc()

    def record_simulation_duration(
        self,
        duration_ms: int,
        tenant_id: str = "default",
    ) -> None:
        """Record simulation duration."""
        if not PROMETHEUS_AVAILABLE or not self._initialized:
            return
        self._simulation_duration_ms.labels(tenant_id=tenant_id).observe(duration_ms)

    def record_simulation(
        self,
        status: str,
        tenant_id: str = "default",
    ) -> None:
        """Record simulation completion."""
        if not PROMETHEUS_AVAILABLE or not self._initialized:
            return
        self._simulations_total.labels(
            tenant_id=tenant_id,
            status=status,
        ).inc()

    def set_circuit_breaker_state(
        self,
        is_open: bool,
        tenant_id: str = "default",
    ) -> None:
        """Set circuit breaker state."""
        if not PROMETHEUS_AVAILABLE or not self._initialized:
            return
        self._circuit_breaker_state.labels(tenant_id=tenant_id).set(1 if is_open else 0)

    def record_provenance_log(self, tenant_id: str = "default") -> None:
        """Record provenance log entry."""
        if not PROMETHEUS_AVAILABLE or not self._initialized:
            return
        self._provenance_logs_total.labels(tenant_id=tenant_id).inc()

    def record_canary_run(self, status: str) -> None:
        """Record canary run completion."""
        if not PROMETHEUS_AVAILABLE or not self._initialized:
            return
        self._canary_runs_total.labels(status=status).inc()

    def set_kl_divergence(
        self,
        kl_divergence: float,
        tenant_id: str = "default",
    ) -> None:
        """Set latest KL divergence."""
        if not PROMETHEUS_AVAILABLE or not self._initialized:
            return
        self._kl_divergence.labels(tenant_id=tenant_id).set(kl_divergence)

    def record_cb_disabled(
        self,
        reason: str = "drift",
        severity: str = "P1",
    ) -> None:
        """Record circuit breaker disable event."""
        if not PROMETHEUS_AVAILABLE or not self._initialized:
            return
        self._cb_disabled_total.labels(reason=reason, severity=severity).inc()

    def record_cb_enabled(self, reason: str = "manual") -> None:
        """Record circuit breaker enable (recovery) event."""
        if not PROMETHEUS_AVAILABLE or not self._initialized:
            return
        self._cb_enabled_total.labels(reason=reason).inc()

    def record_cb_incident(
        self,
        severity: str = "P1",
        resolved: bool = False,
    ) -> None:
        """Record circuit breaker incident."""
        if not PROMETHEUS_AVAILABLE or not self._initialized:
            return
        self._cb_incidents_total.labels(
            severity=severity,
            resolved=str(resolved).lower(),
        ).inc()

    def set_alert_queue_depth(self, depth: int) -> None:
        """Set current alert queue depth."""
        if not PROMETHEUS_AVAILABLE or not self._initialized:
            return
        self._cb_alert_queue_depth.set(depth)

    def record_alert_send_failure(
        self,
        alert_type: str = "disable",
        error_type: str = "connection",
    ) -> None:
        """Record alert send failure."""
        if not PROMETHEUS_AVAILABLE or not self._initialized:
            return
        self._cb_alert_send_failures_total.labels(
            alert_type=alert_type,
            error_type=error_type,
        ).inc()

    def record_auto_recovery(self) -> None:
        """Record auto-recovery event after TTL expiry."""
        if not PROMETHEUS_AVAILABLE or not self._initialized:
            return
        self._cb_auto_recovery_total.inc()

    def set_consecutive_failures(self, count: int) -> None:
        """Set current consecutive failure count."""
        if not PROMETHEUS_AVAILABLE or not self._initialized:
            return
        self._cb_consecutive_failures.set(count)


# Global metrics instance
_metrics: Optional[CostSimMetrics] = None


def get_metrics() -> CostSimMetrics:
    """Get the global CostSim metrics instance."""
    global _metrics
    if _metrics is None:
        _metrics = CostSimMetrics()
    return _metrics


# Public API
__all__ = [
    "CostSimMetrics",
    "get_metrics",
    "DRIFT_SCORE_BUCKETS",
    "COST_DELTA_BUCKETS",
    "DURATION_BUCKETS",
]
