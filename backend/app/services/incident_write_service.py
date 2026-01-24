# Layer: L4 — Domain Engine (DEPRECATED - use incident_write_engine.py)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: DEPRECATED - Backward compatibility shim for IncidentWriteService
# Callers: Any legacy imports
# Reference: PIN-468, DRIVER_ENGINE_CONTRACT.md

"""Incident Write Service - DEPRECATED

This module is deprecated. Use incident_write_engine.py instead.

The service has been split into:
- incident_write_engine.py (L4 - business logic, decisions)
- incident_write_driver.py (L6 - data access, persistence)

PIN-468: Phase 2 Step 2 - L4/L6 Layer Segregation
"""

import warnings

warnings.warn(
    "incident_write_service is deprecated. "
    "Use incident_write_engine instead. "
    "See PIN-468 for migration details.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from engine
from app.services.incident_write_engine import (
    IncidentWriteEngine,
    IncidentWriteService,
    get_incident_write_engine,
    get_incident_write_service,
)

__all__ = [
    "IncidentWriteEngine",
    "IncidentWriteService",
    "get_incident_write_engine",
    "get_incident_write_service",
]
