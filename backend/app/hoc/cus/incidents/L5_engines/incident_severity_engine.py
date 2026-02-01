# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Role: TOMBSTONE — re-exports from L5_schemas/severity_policy.py
# Reference: PIN-507 (Law 1 remediation)
# artifact_class: CODE

"""
TOMBSTONE (PIN-507 Law 1, 2026-02-01):
Severity policy moved to incidents/L5_schemas/severity_policy.py.
Canonical import: app.hoc.cus.incidents.L5_schemas.severity_policy

This file re-exports for backward compatibility only.
Remove re-exports after cleansing cycle.
"""

from app.hoc.cus.incidents.L5_schemas.severity_policy import (  # noqa: F401
    DEFAULT_SEVERITY,
    IncidentSeverityEngine,
    SeverityConfig,
    TRIGGER_SEVERITY_MAP,
    generate_incident_title,
)

__all__ = [
    "IncidentSeverityEngine",
    "SeverityConfig",
    "TRIGGER_SEVERITY_MAP",
    "DEFAULT_SEVERITY",
    "generate_incident_title",
]
