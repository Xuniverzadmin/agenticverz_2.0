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
from .worker_registry_service import (
    WorkerNotFoundError,
    WorkerRegistryError,
    WorkerRegistryService,
    WorkerUnavailableError,
    get_worker_registry_service,
)

__all__ = [
    # Recovery
    "RecoveryMatcher",
    # Tenant Service (M21)
    "TenantService",
    "TenantServiceError",
    "QuotaExceededError",
    "get_tenant_service",
    # Worker Registry Service (M21)
    "WorkerRegistryService",
    "WorkerRegistryError",
    "WorkerNotFoundError",
    "WorkerUnavailableError",
    "get_worker_registry_service",
    # Event Emitter (M24)
    "EventEmitter",
    "EventEmitterError",
    "EventType",
    "EntityType",
    "OpsEvent",
    "get_event_emitter",
]
