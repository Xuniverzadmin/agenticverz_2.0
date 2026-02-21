# capability_id: CAP-001
# Layer: L3 — Boundary Adapter
# Product: system-wide
# Temporal:
#   Trigger: event
#   Execution: sync
# Role: Event handlers for audit-related events
# Callers: EventReactor (L3)
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L5
# Reference: PIN-454, Phase 5 (Audit Alert Handlers)

"""
Audit Event Handlers

Handles audit-related events from the Runtime Audit Contract (RAC):
- Audit reconciliation failures
- Missing domain acknowledgments
- Drift detection
- Stale run detection

These handlers emit alerts and take corrective actions when
audit violations are detected.

Usage:
    from app.events.subscribers import get_event_reactor
    from app.events.audit_handlers import register_audit_handlers

    reactor = get_event_reactor()
    register_audit_handlers(reactor)
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict

logger = logging.getLogger("nova.events.audit_handlers")

# Configuration
AUDIT_ALERTS_ENABLED = os.getenv("AUDIT_ALERTS_ENABLED", "true").lower() == "true"
AUDIT_ALERT_SEVERITY_MISSING = os.getenv("AUDIT_ALERT_SEVERITY_MISSING", "HIGH")
AUDIT_ALERT_SEVERITY_DRIFT = os.getenv("AUDIT_ALERT_SEVERITY_DRIFT", "MEDIUM")
AUDIT_ALERT_SEVERITY_STALE = os.getenv("AUDIT_ALERT_SEVERITY_STALE", "HIGH")

# Prometheus metrics (optional)
try:
    from prometheus_client import Counter

    AUDIT_ALERTS_TOTAL = Counter(
        "aos_audit_alerts_total",
        "Total audit alerts emitted",
        ["alert_type", "severity"],
    )
    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False


class AuditAlertType(str, Enum):
    """Types of audit alerts."""

    MISSING_ACK = "MISSING_ACK"  # Expected operation not acknowledged
    DRIFT = "DRIFT"  # Unexpected operation performed
    STALE_RUN = "STALE_RUN"  # Run never finalized
    RECONCILIATION_FAILED = "RECONCILIATION_FAILED"  # Reconciliation error
    EXPECTATION_TIMEOUT = "EXPECTATION_TIMEOUT"  # Expectation exceeded deadline


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class AuditAlert:
    """Audit alert data structure."""

    alert_type: AuditAlertType
    severity: AlertSeverity
    run_id: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime


def register_audit_handlers(reactor: Any) -> None:
    """
    Register audit event handlers with the event reactor.

    Args:
        reactor: EventReactor instance
    """
    if not AUDIT_ALERTS_ENABLED:
        logger.info("audit_handlers_disabled")
        return

    # Register handlers
    reactor.register_handler(
        "audit.reconciliation.missing",
        handle_missing_ack,
        name="audit_missing_ack_handler",
        priority=100,  # High priority
    )

    reactor.register_handler(
        "audit.reconciliation.drift",
        handle_drift,
        name="audit_drift_handler",
        priority=90,
    )

    reactor.register_handler(
        "audit.reconciliation.stale",
        handle_stale_run,
        name="audit_stale_run_handler",
        priority=100,  # High priority
    )

    reactor.register_handler(
        "audit.reconciliation.failed",
        handle_reconciliation_failed,
        name="audit_reconciliation_failed_handler",
        priority=80,
    )

    reactor.register_handler(
        "audit.expectation.timeout",
        handle_expectation_timeout,
        name="audit_expectation_timeout_handler",
        priority=90,
    )

    # Generic run events that may need audit attention
    reactor.register_handler(
        "run.failed",
        handle_run_failed,
        name="audit_run_failed_handler",
        priority=50,
    )

    reactor.register_handler(
        "run.completed",
        handle_run_completed,
        name="audit_run_completed_handler",
        priority=50,
    )

    logger.info("audit_handlers_registered", extra={"handler_count": 7})


def handle_missing_ack(payload: Dict[str, Any]) -> None:
    """
    Handle missing acknowledgment alert.

    Triggered when an expected domain operation was not acknowledged.
    This indicates a potential data inconsistency.

    Payload:
        run_id: str
        missing_actions: List[tuple[str, str]]  # [(domain, action), ...]
        expected_count: int
        acked_count: int
    """
    run_id = payload.get("run_id", "unknown")
    missing_actions = payload.get("missing_actions", [])

    alert = AuditAlert(
        alert_type=AuditAlertType.MISSING_ACK,
        severity=AlertSeverity[AUDIT_ALERT_SEVERITY_MISSING],
        run_id=run_id,
        message=f"Missing acknowledgments for run {run_id}: {len(missing_actions)} actions",
        details={
            "missing_actions": missing_actions,
            "expected_count": payload.get("expected_count", 0),
            "acked_count": payload.get("acked_count", 0),
        },
        timestamp=datetime.now(timezone.utc),
    )

    _emit_alert(alert)

    # Log detailed missing actions
    for domain, action in missing_actions:
        logger.warning(
            "audit_missing_ack",
            extra={
                "run_id": run_id,
                "domain": domain,
                "action": action,
                "severity": alert.severity.value,
            },
        )


def handle_drift(payload: Dict[str, Any]) -> None:
    """
    Handle drift detection alert.

    Triggered when unexpected domain operations were performed.
    This may indicate a bug or race condition.

    Payload:
        run_id: str
        drift_actions: List[tuple[str, str]]  # [(domain, action), ...]
    """
    run_id = payload.get("run_id", "unknown")
    drift_actions = payload.get("drift_actions", [])

    alert = AuditAlert(
        alert_type=AuditAlertType.DRIFT,
        severity=AlertSeverity[AUDIT_ALERT_SEVERITY_DRIFT],
        run_id=run_id,
        message=f"Drift detected for run {run_id}: {len(drift_actions)} unexpected actions",
        details={
            "drift_actions": drift_actions,
        },
        timestamp=datetime.now(timezone.utc),
    )

    _emit_alert(alert)

    # Log detailed drift actions
    for domain, action in drift_actions:
        logger.warning(
            "audit_drift_detected",
            extra={
                "run_id": run_id,
                "domain": domain,
                "action": action,
                "severity": alert.severity.value,
            },
        )


def handle_stale_run(payload: Dict[str, Any]) -> None:
    """
    Handle stale run detection alert.

    Triggered when a run was expected to finalize but never did.
    This indicates a stuck or zombie run.

    Payload:
        run_id: str
        expected_finalize_by: str (ISO timestamp)
        last_activity: str (ISO timestamp, optional)
    """
    run_id = payload.get("run_id", "unknown")

    alert = AuditAlert(
        alert_type=AuditAlertType.STALE_RUN,
        severity=AlertSeverity[AUDIT_ALERT_SEVERITY_STALE],
        run_id=run_id,
        message=f"Stale run detected: {run_id} never finalized",
        details={
            "expected_finalize_by": payload.get("expected_finalize_by"),
            "last_activity": payload.get("last_activity"),
        },
        timestamp=datetime.now(timezone.utc),
    )

    _emit_alert(alert)

    logger.error(
        "audit_stale_run",
        extra={
            "run_id": run_id,
            "expected_finalize_by": payload.get("expected_finalize_by"),
            "severity": alert.severity.value,
        },
    )

    # Attempt to mark run as failed if still in running state
    _attempt_mark_run_failed(run_id, "Stale run - never finalized")


def handle_reconciliation_failed(payload: Dict[str, Any]) -> None:
    """
    Handle reconciliation failure alert.

    Triggered when the reconciliation process itself failed.

    Payload:
        run_id: str
        error: str
    """
    run_id = payload.get("run_id", "unknown")
    error = payload.get("error", "Unknown error")

    alert = AuditAlert(
        alert_type=AuditAlertType.RECONCILIATION_FAILED,
        severity=AlertSeverity.HIGH,
        run_id=run_id,
        message=f"Reconciliation failed for run {run_id}: {error}",
        details={
            "error": error,
        },
        timestamp=datetime.now(timezone.utc),
    )

    _emit_alert(alert)

    logger.error(
        "audit_reconciliation_failed",
        extra={
            "run_id": run_id,
            "error": error,
        },
    )


def handle_expectation_timeout(payload: Dict[str, Any]) -> None:
    """
    Handle expectation timeout alert.

    Triggered when an expectation exceeded its deadline.

    Payload:
        run_id: str
        domain: str
        action: str
        deadline_ms: int
        elapsed_ms: int
    """
    run_id = payload.get("run_id", "unknown")
    domain = payload.get("domain", "unknown")
    action = payload.get("action", "unknown")

    alert = AuditAlert(
        alert_type=AuditAlertType.EXPECTATION_TIMEOUT,
        severity=AlertSeverity.HIGH,
        run_id=run_id,
        message=f"Expectation timeout for run {run_id}: {domain}/{action}",
        details={
            "domain": domain,
            "action": action,
            "deadline_ms": payload.get("deadline_ms", 0),
            "elapsed_ms": payload.get("elapsed_ms", 0),
        },
        timestamp=datetime.now(timezone.utc),
    )

    _emit_alert(alert)

    logger.warning(
        "audit_expectation_timeout",
        extra={
            "run_id": run_id,
            "domain": domain,
            "action": action,
            "deadline_ms": payload.get("deadline_ms"),
            "elapsed_ms": payload.get("elapsed_ms"),
        },
    )


def handle_run_failed(payload: Dict[str, Any]) -> None:
    """
    Handle run.failed event for audit purposes.

    Logs the failure for audit trail and triggers reconciliation
    if audit contract is active.

    Payload:
        run_id: str
        error_code: str
        error_message: str
        tenant_id: str
    """
    run_id = payload.get("run_id", "unknown")

    logger.info(
        "audit_run_failed_event",
        extra={
            "run_id": run_id,
            "error_code": payload.get("error_code"),
            "tenant_id": payload.get("tenant_id"),
        },
    )

    # Trigger reconciliation check after a delay
    # In production, this would schedule an async task
    _schedule_reconciliation_check(run_id, delay_seconds=5)


def handle_run_completed(payload: Dict[str, Any]) -> None:
    """
    Handle run.completed event for audit purposes.

    Logs the completion for audit trail and triggers reconciliation
    verification.

    Payload:
        run_id: str
        tenant_id: str
        incident_id: str (optional)
        policy_eval_id: str (optional)
        trace_id: str (optional)
    """
    run_id = payload.get("run_id", "unknown")

    logger.info(
        "audit_run_completed_event",
        extra={
            "run_id": run_id,
            "tenant_id": payload.get("tenant_id"),
            "has_incident": payload.get("incident_id") is not None,
            "has_policy_eval": payload.get("policy_eval_id") is not None,
            "has_trace": payload.get("trace_id") is not None,
        },
    )

    # Trigger reconciliation verification
    _schedule_reconciliation_check(run_id, delay_seconds=2)


def _emit_alert(alert: AuditAlert) -> None:
    """
    Emit an audit alert.

    In production, this would:
    - Send to alerting system (PagerDuty, Slack, etc.)
    - Write to alerts table
    - Update metrics

    For now, we log and update metrics.
    """
    if METRICS_ENABLED:
        AUDIT_ALERTS_TOTAL.labels(
            alert_type=alert.alert_type.value,
            severity=alert.severity.value,
        ).inc()

    logger.info(
        "audit_alert_emitted",
        extra={
            "alert_type": alert.alert_type.value,
            "severity": alert.severity.value,
            "run_id": alert.run_id,
            "message": alert.message,
        },
    )

    # TODO: Integrate with external alerting service
    # TODO: Write to audit_alerts table


def _attempt_mark_run_failed(run_id: str, reason: str) -> None:
    """
    Attempt to mark a stale run as failed.

    This is a corrective action for stale runs.
    """
    try:
        from sqlmodel import Session

        from app.db import engine
        from app.models.run import Run

        with Session(engine) as session:
            run = session.get(Run, run_id)
            if run and run.status == "running":
                run.status = "failed"
                run.error_code = "STALE_RUN"
                run.error_message = reason
                run.completed_at = datetime.now(timezone.utc)
                session.add(run)
                session.commit()

                logger.info(
                    "stale_run_marked_failed",
                    extra={"run_id": run_id, "reason": reason},
                )

    except Exception as e:
        logger.error(
            "failed_to_mark_stale_run",
            extra={"run_id": run_id, "error": str(e)},
        )


def _schedule_reconciliation_check(run_id: str, delay_seconds: int = 5) -> None:
    """
    Schedule a reconciliation check for a run.

    In production, this would use a task queue (Celery, etc.).
    For now, we just log the intent.
    """
    logger.debug(
        "reconciliation_check_scheduled",
        extra={"run_id": run_id, "delay_seconds": delay_seconds},
    )

    # TODO: Integrate with task queue for async reconciliation
