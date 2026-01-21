# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Runtime Audit Contract (RAC) services
# Callers: ROK (L5), Facades (L4), Scheduler (L5)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: PIN-454 (Cross-Domain Orchestration Audit)

"""
Runtime Audit Contract (RAC) Services

This module implements the audit infrastructure for cross-domain operations:

- AuditExpectation: What MUST happen during a run
- DomainAck: Acknowledgment that an action completed
- AuditStore: Storage for expectations and acks
- AuditReconciler: Validates expectations against acks

The RAC ensures:
1. Silent failures are detected (expected - acked = missing)
2. Unexpected actions are flagged (acked - expected = drift)
3. Stale runs are identified (finalize_run never acked)

Reference: PIN-454 Section 8.2
"""

from app.services.audit.models import (
    AckStatus,
    AuditAction,
    AuditDomain,
    AuditExpectation,
    AuditStatus,
    DomainAck,
    ReconciliationResult,
    create_domain_ack,
    create_run_expectations,
)
from app.services.audit.store import (
    AuditStore,
    RACDurabilityError,
    StoreDurabilityMode,
    get_audit_store,
)
from app.services.audit.reconciler import AuditReconciler, get_audit_reconciler

__all__ = [
    # Models
    "AckStatus",
    "AuditAction",
    "AuditDomain",
    "AuditExpectation",
    "AuditStatus",
    "DomainAck",
    "ReconciliationResult",
    "create_domain_ack",
    "create_run_expectations",
    # Store
    "AuditStore",
    "RACDurabilityError",
    "StoreDurabilityMode",
    "get_audit_store",
    # Reconciler
    "AuditReconciler",
    "get_audit_reconciler",
]
