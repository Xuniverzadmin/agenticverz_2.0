# AOS Models Package
"""
SQLAlchemy models for async database access.

This package contains pure SQLAlchemy models (not SQLModel) for use with
async sessions. These models mirror the SQLModel definitions in db.py
but are designed for async operations.
"""

from app.models.costsim_cb import (
    Base,
    CostSimAlertQueueModel,
    CostSimCBIncidentModel,
    CostSimCBStateModel,
    CostSimProvenanceModel,
)
from app.models.governance import (
    GovernanceSignal,
    GovernanceSignalCreate,
    GovernanceSignalResponse,
    GovernanceSignalQuery,
    GovernanceCheckResult,
)
from app.models.external_response import (
    ExternalResponse,
    ExternalResponseCreate,
    ExternalResponseRead,
    InterpretationUpdate,
    InterpretedResponse,
)
from app.models.tenant import (
    PLAN_QUOTAS,
    APIKey,
    AuditLog,
    Subscription,
    Tenant,
    TenantMembership,
    UsageRecord,
    User,
    WorkerConfig,
    WorkerRegistry,
    WorkerRun,
)

__all__ = [
    "Base",
    "CostSimCBStateModel",
    "CostSimCBIncidentModel",
    "CostSimProvenanceModel",
    "CostSimAlertQueueModel",
    # Governance models (Phase E FIX-03)
    "GovernanceSignal",
    "GovernanceSignalCreate",
    "GovernanceSignalResponse",
    "GovernanceSignalQuery",
    "GovernanceCheckResult",
    # External response models (Phase E FIX-04)
    "ExternalResponse",
    "ExternalResponseCreate",
    "ExternalResponseRead",
    "InterpretationUpdate",
    "InterpretedResponse",
    # Tenant models (M21)
    "Tenant",
    "User",
    "TenantMembership",
    "APIKey",
    "Subscription",
    "UsageRecord",
    "WorkerRegistry",
    "WorkerConfig",
    "WorkerRun",
    "AuditLog",
    "PLAN_QUOTAS",
]
