# app/services/__init__.py
# FROZEN: PIN-508 Gap 5 — no new files or imports permitted
# DEPRECATED: PIN-509 Gap 4 — migrate to app.hoc.cus.{domain}.L5_engines
"""Service layer for business logic.

WARNING: This namespace is FROZEN (PIN-508) and DEPRECATED (PIN-509).
No new files may be added. No new imports from this package are permitted.
All new business logic belongs in app.hoc.cus.{domain}.L5_engines/.
"""
import warnings as _warnings

_warnings.warn(
    "app.services is deprecated (PIN-509). Use app.hoc.cus.{domain}.L5_engines instead.",
    DeprecationWarning,
    stacklevel=2,
)

from .event_emitter import (
    EntityType,
    EventEmitter,
    EventEmitterError,
    EventType,
    OpsEvent,
    get_event_emitter,
)
from .recovery_matcher import RecoveryMatcher
from .tenant_service import (
    QuotaExceededError,
    TenantService,
    TenantServiceError,
    get_tenant_service,
)
# TOMBSTONE_EXPIRY: 2026-03-04
# Removed: worker_registry_service (file does not exist, PIN-511 legacy cleanup)
# Functionality moved to app.hoc.cus.integrations.L6_drivers.worker_registry_driver

__all__ = [
    # Recovery
    "RecoveryMatcher",
    # Tenant Service (M21)
    "TenantService",
    "TenantServiceError",
    "QuotaExceededError",
    "get_tenant_service",
    # Worker Registry Service - REMOVED (PIN-511, file does not exist)
    # Event Emitter (M24)
    "EventEmitter",
    "EventEmitterError",
    "EventType",
    "EntityType",
    "OpsEvent",
    "get_event_emitter",
]
