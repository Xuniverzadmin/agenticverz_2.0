# app/services/__init__.py
"""Service layer for business logic."""

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
