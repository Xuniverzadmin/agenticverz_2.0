# AOS Models Package
"""
SQLAlchemy models for async database access.

This package contains pure SQLAlchemy models (not SQLModel) for use with
async sessions. These models mirror the SQLModel definitions in db.py
but are designed for async operations.
"""

from app.models.contract import (
    TERMINAL_STATES,
    VALID_TRANSITIONS,
    AuditVerdict,
    ContractApproval,
    ContractCreate,
    ContractImmutableError,
    ContractRejection,
    ContractResponse,
    ContractSource,
    ContractStatus,
    InvalidTransitionError,
    MayNotVerdictError,
    ProposedChangeType,
    RiskLevel,
    SystemContract,
)
from app.models.costsim_cb import (
    Base,
    CostSimAlertQueueModel,
    CostSimCBIncidentModel,
    CostSimCBStateModel,
    CostSimProvenanceModel,
)
from app.models.external_response import (
    ExternalResponse,
    ExternalResponseCreate,
    ExternalResponseRead,
    InterpretationUpdate,
    InterpretedResponse,
)
from app.models.governance import (
    GovernanceCheckResult,
    GovernanceSignal,
    GovernanceSignalCreate,
    GovernanceSignalQuery,
    GovernanceSignalResponse,
)
from app.models.governance_job import (
    JOB_TERMINAL_STATES,
    JOB_VALID_TRANSITIONS,
    GovernanceJob,
    HealthSnapshot,
    InvalidJobTransitionError,
    JobCreate,
    JobImmutableError,
    JobResponse,
    JobStatus,
    JobStep,
    JobTransitionRecord,
    OrphanJobError,
    StepResult,
    StepStatus,
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
    # Contract models (Part-2 PIN-291)
    "SystemContract",
    "ContractStatus",
    "ContractSource",
    "AuditVerdict",
    "RiskLevel",
    "ProposedChangeType",
    "ContractCreate",
    "ContractResponse",
    "ContractApproval",
    "ContractRejection",
    "InvalidTransitionError",
    "ContractImmutableError",
    "MayNotVerdictError",
    "TERMINAL_STATES",
    "VALID_TRANSITIONS",
    # Governance Job models (Part-2 PIN-292)
    "GovernanceJob",
    "JobStatus",
    "StepStatus",
    "JobStep",
    "StepResult",
    "HealthSnapshot",
    "JobCreate",
    "JobResponse",
    "JobTransitionRecord",
    "JOB_TERMINAL_STATES",
    "JOB_VALID_TRANSITIONS",
    "InvalidJobTransitionError",
    "JobImmutableError",
    "OrphanJobError",
]
