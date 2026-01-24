# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: scheduler/ROK
#   Execution: sync
# Role: Reconcile audit expectations against acknowledgments
# Callers: ROK (L5), Scheduler (L5)
# Allowed Imports: L4 (audit models/store), L6
# Forbidden Imports: L1, L2, L3
# Reference: PIN-454 (Cross-Domain Orchestration Audit)

"""
Audit Reconciler

Performs four-way validation of expectations vs acknowledgments:

1. expected − acked → missing (audit alert)
2. acked − expected → drift (unexpected action)
3. missing finalization → stale run (liveness violation)
4. expectations without deadline → invalid contract

This is the core of the Runtime Audit Contract (RAC).

Usage:
    reconciler = get_audit_reconciler()
    result = reconciler.reconcile(run_id)

    if not result.is_clean:
        # Handle issues
        if result.has_missing:
            alert_missing_actions(result.missing_actions)
        if result.stale_run:
            alert_stale_run(run_id)
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Set, Tuple
from uuid import UUID

from prometheus_client import Counter, Histogram

from app.services.audit.models import (
    AuditAction,
    AuditDomain,
    AuditExpectation,
    AuditStatus,
    DomainAck,
    ReconciliationResult,
)
from app.services.audit.store import AuditStore, get_audit_store

logger = logging.getLogger("nova.services.audit.reconciler")

# =============================================================================
# Metrics
# =============================================================================

RECONCILIATION_TOTAL = Counter(
    "rac_reconciliation_total",
    "Total reconciliations performed",
    ["status"],  # COMPLETE, INCOMPLETE, STALE
)

MISSING_ACTIONS_TOTAL = Counter(
    "rac_missing_actions_total",
    "Total missing actions detected",
    ["domain", "action"],
)

DRIFT_ACTIONS_TOTAL = Counter(
    "rac_drift_actions_total",
    "Total drift actions detected",
    ["domain", "action"],
)

STALE_RUNS_TOTAL = Counter(
    "rac_stale_runs_total",
    "Total stale runs detected",
)

RECONCILIATION_DURATION = Histogram(
    "rac_reconciliation_duration_seconds",
    "Time spent reconciling",
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5],
)


class AuditReconciler:
    """
    Reconciles expectations with acknowledgments.

    This is the heart of the RAC system. It performs set operations
    to identify:
    - Missing actions (expected but not acked)
    - Drift actions (acked but not expected)
    - Stale runs (finalize_run never acked)

    Layer: L4 (Domain Logic)
    Callers: ROK (L5), Scheduler (L5)
    """

    def __init__(self, store: Optional[AuditStore] = None):
        """
        Initialize the reconciler.

        Args:
            store: Audit store instance (defaults to singleton)
        """
        self._store = store or get_audit_store()

    def reconcile(self, run_id: UUID) -> ReconciliationResult:
        """
        Reconcile expectations against acknowledgments for a run.

        Four-way validation:
        1. expected − acked → missing (audit alert)
        2. acked − expected → drift (unexpected action)
        3. missing finalization → stale run (liveness violation)
        4. expectations without deadline → invalid contract

        Args:
            run_id: The run to reconcile

        Returns:
            ReconciliationResult with findings
        """
        start_time = datetime.now(timezone.utc)

        # Get expectations and acks
        expectations = self._store.get_expectations(run_id)
        acks = self._store.get_acks(run_id)

        # Build key sets for comparison
        expected_set: Set[Tuple[str, str]] = {exp.key() for exp in expectations}
        acked_set: Set[Tuple[str, str]] = {ack.key() for ack in acks}

        # Validation 1: Missing actions (expected − acked)
        missing = expected_set - acked_set
        missing_actions = list(missing)

        # Validation 2: Drift actions (acked − expected)
        drift = acked_set - expected_set
        drift_actions = list(drift)

        # Validation 3: Failed actions (acked with error)
        failed_actions = [
            ack.key() for ack in acks if not ack.is_success
        ]

        # Validation 4: Liveness check (finalize_run expectation)
        finalize_expected = any(
            exp.domain == AuditDomain.ORCHESTRATOR
            and exp.action == AuditAction.FINALIZE_RUN
            for exp in expectations
        )
        finalize_acked = any(
            ack.domain == AuditDomain.ORCHESTRATOR
            and ack.action == AuditAction.FINALIZE_RUN
            for ack in acks
        )
        stale_run = finalize_expected and not finalize_acked

        # Determine overall status
        if stale_run:
            status = "STALE"
        elif missing or drift or failed_actions:
            status = "INCOMPLETE"
        else:
            status = "COMPLETE"

        # Build result
        result = ReconciliationResult(
            run_id=run_id,
            status=status,
            missing_actions=missing_actions,
            drift_actions=drift_actions,
            failed_actions=failed_actions,
            stale_run=stale_run,
            expectations_count=len(expectations),
            acks_count=len(acks),
        )

        # Record metrics
        self._record_metrics(result)

        # Log findings
        duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        logger.info(
            "audit_reconciler.reconcile",
            extra={
                "run_id": str(run_id),
                "status": status,
                "missing_count": len(missing_actions),
                "drift_count": len(drift_actions),
                "failed_count": len(failed_actions),
                "stale_run": stale_run,
                "duration_ms": duration_ms,
            }
        )

        return result

    def check_deadline_violations(self, run_id: UUID) -> List[AuditExpectation]:
        """
        Check for expectations that have exceeded their deadlines.

        Called by scheduler to identify late acks.

        Args:
            run_id: The run to check

        Returns:
            List of expectations past deadline
        """
        now = datetime.now(timezone.utc)
        expectations = self._store.get_expectations(run_id)

        violations = []
        for exp in expectations:
            if exp.status == AuditStatus.PENDING:
                deadline = exp.created_at.timestamp() + (exp.deadline_ms / 1000)
                if now.timestamp() > deadline:
                    violations.append(exp)

        if violations:
            logger.warning(
                "audit_reconciler.deadline_violations",
                extra={
                    "run_id": str(run_id),
                    "count": len(violations),
                    "domains": [v.domain.value for v in violations],
                }
            )

        return violations

    def get_run_audit_summary(self, run_id: UUID) -> dict:
        """
        Get a summary of the audit state for a run.

        Useful for debugging and operator visibility.

        Args:
            run_id: The run to summarize

        Returns:
            Dictionary with audit state
        """
        expectations = self._store.get_expectations(run_id)
        acks = self._store.get_acks(run_id)

        return {
            "run_id": str(run_id),
            "expectations": [
                {
                    "domain": exp.domain.value,
                    "action": exp.action.value,
                    "status": exp.status.value,
                    "deadline_ms": exp.deadline_ms,
                }
                for exp in expectations
            ],
            "acks": [
                {
                    "domain": ack.domain.value,
                    "action": ack.action.value,
                    "success": ack.is_success,
                    "result_id": ack.result_id,
                }
                for ack in acks
            ],
            "expectations_count": len(expectations),
            "acks_count": len(acks),
        }

    def _record_metrics(self, result: ReconciliationResult) -> None:
        """Record Prometheus metrics for reconciliation."""
        # Overall status
        RECONCILIATION_TOTAL.labels(status=result.status).inc()

        # Missing actions
        for domain, action in result.missing_actions:
            MISSING_ACTIONS_TOTAL.labels(domain=domain, action=action).inc()

        # Drift actions
        for domain, action in result.drift_actions:
            DRIFT_ACTIONS_TOTAL.labels(domain=domain, action=action).inc()

        # Stale runs
        if result.stale_run:
            STALE_RUNS_TOTAL.inc()


# =============================================================================
# Module-level singleton
# =============================================================================

_reconciler_instance: Optional[AuditReconciler] = None


def get_audit_reconciler(store: Optional[AuditStore] = None) -> AuditReconciler:
    """
    Get the audit reconciler singleton.

    Args:
        store: Optional audit store (only used on first call)

    Returns:
        AuditReconciler instance
    """
    global _reconciler_instance
    if _reconciler_instance is None:
        _reconciler_instance = AuditReconciler(store=store)
    return _reconciler_instance
