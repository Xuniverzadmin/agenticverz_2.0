# capability_id: CAP-006
# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: internal
#   Execution: sync
# Role: Prometheus metrics for authorization system
# Callers: authorization_choke.py
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3
# Reference: docs/invariants/AUTHZ_AUTHORITY.md

"""
Authorization Metrics

Provides Prometheus metrics for authorization decisions.

Metrics:
    authz_m7_fallback_total: Counter for M7→M28 fallback usage
    authz_decision_total: Counter for all authorization decisions
    authz_latency_seconds: Histogram for authorization latency
"""

from __future__ import annotations

import logging

logger = logging.getLogger("nova.auth.metrics")

# Try to import prometheus_client, gracefully degrade if not available
try:
    from prometheus_client import Counter, Gauge, Histogram

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.info("prometheus_client not available, metrics will be logged only")


# =============================================================================
# Prometheus Metrics (T6)
# =============================================================================

if PROMETHEUS_AVAILABLE:
    # Counter: Track M7→M28 fallback usage (for pruning decisions)
    AUTHZ_M7_FALLBACK_TOTAL = Counter(
        "authz_m7_fallback_total",
        "Count of M7 to M28 authorization fallbacks",
        ["resource", "action", "decision", "phase"],
    )

    # Counter: Tripwire hits (T9 - for authority exhaustion)
    AUTHZ_M7_TRIPWIRE_TOTAL = Counter(
        "authz_m7_tripwire_total",
        "Count of M7 tripwire hits (authority exhaustion tracking)",
        ["resource", "action", "principal_type", "entry_point"],
    )

    # Counter: Track all authorization decisions
    AUTHZ_DECISION_TOTAL = Counter(
        "authz_decision_total",
        "Count of all authorization decisions",
        ["source", "resource", "action", "allowed", "phase"],
    )

    # Histogram: Track authorization latency
    AUTHZ_LATENCY_SECONDS = Histogram(
        "authz_latency_seconds",
        "Authorization decision latency in seconds",
        ["source"],
        buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
    )

    # Gauge: Current enforcement phase
    AUTHZ_PHASE_INFO = Gauge(
        "authz_phase_info",
        "Current authorization enforcement phase",
        ["phase"],
    )

    # Gauge: Strict mode status
    AUTHZ_STRICT_MODE = Gauge(
        "authz_strict_mode",
        "Whether strict mode is enabled (1=enabled, 0=disabled)",
    )


def record_m7_fallback(
    resource: str,
    action: str,
    decision: str,
    phase: str,
) -> None:
    """
    Record an M7→M28 fallback metric.

    This is called whenever the choke point uses M7 mapping.
    """
    if PROMETHEUS_AVAILABLE:
        AUTHZ_M7_FALLBACK_TOTAL.labels(
            resource=resource,
            action=action,
            decision=decision,
            phase=phase,
        ).inc()

    logger.debug(
        "authz_m7_fallback_metric",
        extra={
            "resource": resource,
            "action": action,
            "decision": decision,
            "phase": phase,
        },
    )


def record_tripwire_hit(
    resource: str,
    action: str,
    principal_type: str,
    entry_point: str,
    actor_id: str,
    stack_trace: str,
) -> None:
    """
    Record a tripwire hit (T9 - authority exhaustion).

    This is called when M7 fallback occurs in tripwire mode.
    Captures full context for analysis.
    """
    if PROMETHEUS_AVAILABLE:
        AUTHZ_M7_TRIPWIRE_TOTAL.labels(
            resource=resource,
            action=action,
            principal_type=principal_type,
            entry_point=entry_point,
        ).inc()

    # Always log tripwire hits at WARNING level for visibility
    logger.warning(
        "authz_m7_tripwire_hit",
        extra={
            "resource": resource,
            "action": action,
            "principal_type": principal_type,
            "entry_point": entry_point,
            "actor_id": actor_id,
            "stack_trace": stack_trace,
            "severity": "tripwire",
        },
    )


def record_decision(
    source: str,
    resource: str,
    action: str,
    allowed: bool,
    phase: str,
    latency_ms: float,
) -> None:
    """
    Record an authorization decision metric.

    This is called for every authorization decision.
    """
    if PROMETHEUS_AVAILABLE:
        AUTHZ_DECISION_TOTAL.labels(
            source=source,
            resource=resource,
            action=action,
            allowed="true" if allowed else "false",
            phase=phase,
        ).inc()

        AUTHZ_LATENCY_SECONDS.labels(source=source).observe(latency_ms / 1000.0)

    logger.debug(
        "authz_decision_metric",
        extra={
            "source": source,
            "resource": resource,
            "action": action,
            "allowed": allowed,
            "phase": phase,
            "latency_ms": latency_ms,
        },
    )


def update_phase_info(phase: str) -> None:
    """Update the phase info gauge."""
    if PROMETHEUS_AVAILABLE:
        # Reset all phase labels
        for p in ["A", "B", "C"]:
            AUTHZ_PHASE_INFO.labels(phase=p).set(0)
        # Set current phase
        AUTHZ_PHASE_INFO.labels(phase=phase).set(1)


def update_strict_mode(enabled: bool) -> None:
    """Update the strict mode gauge."""
    if PROMETHEUS_AVAILABLE:
        AUTHZ_STRICT_MODE.set(1 if enabled else 0)


# =============================================================================
# Dashboard Queries (PromQL examples for T6)
# =============================================================================

DASHBOARD_QUERIES = {
    "m7_fallback_rate_by_resource": """
        # M7 Fallback Rate by Resource (last 5 minutes)
        sum(rate(authz_m7_fallback_total[5m])) by (resource)
    """,
    "m7_fallback_rate_by_action": """
        # M7 Fallback Rate by Action (last 5 minutes)
        sum(rate(authz_m7_fallback_total[5m])) by (action)
    """,
    "m7_fallback_total_by_phase": """
        # Total M7 Fallbacks by Phase
        sum(authz_m7_fallback_total) by (phase)
    """,
    "authorization_decision_rate": """
        # Authorization Decision Rate (per second)
        sum(rate(authz_decision_total[1m])) by (source, allowed)
    """,
    "authorization_latency_p99": """
        # Authorization Latency P99
        histogram_quantile(0.99, rate(authz_latency_seconds_bucket[5m]))
    """,
    "m7_fallback_ratio": """
        # Ratio of M7 Fallbacks to Total Decisions
        sum(rate(authz_m7_fallback_total[5m])) /
        sum(rate(authz_decision_total[5m]))
    """,
}


# =============================================================================
# Alert Rules (Prometheus alert examples for T6)
# =============================================================================

ALERT_RULES = """
# M7 Authorization Fallback Alerts
# Add these to your Prometheus alerting rules

groups:
  - name: authorization_alerts
    rules:
      - alert: HighM7FallbackRate
        expr: sum(rate(authz_m7_fallback_total[5m])) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High M7 authorization fallback rate"
          description: "M7 fallback rate is {{ $value }} ops/sec. Target: migrate these resources to M28."

      - alert: M7FallbackInPhaseB
        expr: sum(rate(authz_m7_fallback_total{phase="B"}[5m])) by (resource) > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "M7 fallback detected in Phase B"
          description: "Resource {{ $labels.resource }} is using M7 fallback in Phase B. This should be migrated."

      - alert: AuthorizationLatencyHigh
        expr: histogram_quantile(0.99, rate(authz_latency_seconds_bucket[5m])) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Authorization latency P99 > 100ms"
          description: "Authorization P99 latency is {{ $value }}s. Investigate performance."

      - alert: StrictModeDisabled
        expr: authz_strict_mode == 0 and authz_phase_info{phase="C"} == 1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Strict mode disabled in Phase C"
          description: "Strict mode should be enabled in Phase C for full M28 enforcement."
"""


def get_dashboard_queries() -> dict:
    """Get dashboard query templates."""
    return DASHBOARD_QUERIES.copy()


def get_alert_rules() -> str:
    """Get alert rule templates."""
    return ALERT_RULES
