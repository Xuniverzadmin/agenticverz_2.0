# Layer: L6 — Database Drivers
# AUDIENCE: CUSTOMER
# Role: Database drivers for logs domain - pure data access, returns snapshots
# Reference: HOC_LAYER_TOPOLOGY_V1.md

"""
Logs Domain Drivers (L6)

Database drivers for the logs domain.
All methods return immutable snapshots, never ORM models.

WARNING: Eager re-exports below cause all drivers to load at package
import time. Known Law 0 risk — masked import failures can hide
downstream violations. See PIN-507 Law 0 subsection.
"""

from app.hoc.cus.logs.L6_drivers.export_bundle_store import (
    ExportBundleStore,
    IncidentSnapshot,
    RunSnapshot,
    TraceSummarySnapshot,
    TraceStepSnapshot,
    get_export_bundle_store,
)
from app.hoc.cus.logs.L6_drivers.logs_domain_store import (
    AuditLedgerSnapshot,
    LLMRunSnapshot,
    LogExportSnapshot,
    LogsDomainStore,
    SystemRecordSnapshot,
    TraceStepSnapshot as LogsTraceStepSnapshot,
    get_logs_domain_store,
)

__all__ = [
    # Export Bundle Store
    "ExportBundleStore",
    "get_export_bundle_store",
    "IncidentSnapshot",
    "RunSnapshot",
    "TraceSummarySnapshot",
    "TraceStepSnapshot",
    # Logs Domain Store
    "LogsDomainStore",
    "get_logs_domain_store",
    "LLMRunSnapshot",
    "SystemRecordSnapshot",
    "AuditLedgerSnapshot",
    "LogExportSnapshot",
    "LogsTraceStepSnapshot",
]
