# Layer: L5 — Domain Engine
# NOTE: Renamed metrics.py → metrics_engine.py (2026-01-31)
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none (metrics emission only)
#   Writes: none
# Role: Re-export CostSim V2 metrics from hoc_spine (backward compatibility)
# Callers: sandbox, canary engines
# Allowed Imports: hoc_spine services
# Forbidden Imports: L6, L7, sqlalchemy (runtime)
# Reference: PIN-470, PIN-521 (metrics extraction)

"""
CostSim V2 Prometheus Metrics - BACKWARD COMPATIBILITY RE-EXPORTS

PIN-521 Migration:
- Canonical home is now hoc_spine/services/costsim_metrics.py
- This file re-exports for backward compatibility
- L6 drivers MUST import from hoc_spine (not here)
- New code SHOULD import from hoc_spine/services

To migrate existing imports:
    OLD: from app.hoc.cus.analytics.L5_engines.metrics_engine import get_metrics
    NEW: from app.hoc.cus.hoc_spine.services.costsim_metrics import get_metrics
"""

# Re-export from canonical location (hoc_spine/services)
from app.hoc.cus.hoc_spine.services.costsim_metrics import (
    COST_DELTA_BUCKETS,
    DRIFT_SCORE_BUCKETS,
    DURATION_BUCKETS,
    CostSimMetrics,
    get_metrics,
)

# Alert rules YAML kept here for backward compatibility
ALERT_RULES_YAML = """
groups:
  - name: costsim_v2_alerts
    rules:
      # P1: High drift - auto-disable V2
      - alert: CostSimV2HighDrift
        expr: histogram_quantile(0.95, rate(costsim_v2_drift_score_bucket[5m])) > 0.2
        for: 5m
        labels:
          severity: critical
          priority: P1
        annotations:
          summary: "CostSim V2 high drift detected"
          description: "V2 drift score p95 > 0.2 for 5 minutes. Auto-disable triggered."
          runbook: "Check /var/lib/aos/costsim_incidents/ for details"

      # P2: Warning drift
      - alert: CostSimV2DriftWarning
        expr: histogram_quantile(0.95, rate(costsim_v2_drift_score_bucket[15m])) > 0.15
        for: 15m
        labels:
          severity: warning
          priority: P2
        annotations:
          summary: "CostSim V2 drift warning"
          description: "V2 drift score p95 > 0.15 for 15 minutes. Investigation recommended."

      # P3: Schema errors
      - alert: CostSimV2SchemaErrors
        expr: increase(costsim_v2_schema_errors_total[1h]) > 5
        for: 5m
        labels:
          severity: warning
          priority: P3
        annotations:
          summary: "CostSim V2 schema errors detected"
          description: "More than 5 schema errors in the last hour."

      # Circuit breaker open
      - alert: CostSimV2CircuitBreakerOpen
        expr: costsim_v2_circuit_breaker_state == 1
        for: 1m
        labels:
          severity: critical
          priority: P1
        annotations:
          summary: "CostSim V2 circuit breaker is OPEN"
          description: "V2 simulation is disabled due to drift. Manual reset required."
"""


def get_alert_rules() -> str:
    """Get Prometheus alert rules YAML."""
    return ALERT_RULES_YAML


__all__ = [
    "CostSimMetrics",
    "get_metrics",
    "DRIFT_SCORE_BUCKETS",
    "COST_DELTA_BUCKETS",
    "DURATION_BUCKETS",
    "ALERT_RULES_YAML",
    "get_alert_rules",
]
