# capability_id: CAP-012
# Layer: L4 — HOC Spine (Orchestrator)
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Part-2 CRM Workflow Governance Services
# Callers: L2 (governance APIs), L3 (adapters)
# Allowed Imports: L5, L6, L8
# Forbidden Imports: L1, L2, L3
# Reference: PIN-287, PIN-288, PIN-289, PIN-291, PIN-292, PIN-294, PIN-295, part2-design-v1

"""
Part-2 CRM Workflow Governance Services

L4 domain services for the Part-2 governance workflow:
- Validator: Issue analysis (advisory, stateless)
- Eligibility: Contract gating (pure rules)
- Contract Service: State machine (stateful)
- Governance Orchestrator: Workflow coordination (orchestration only)
- Job Executor: Step execution (L5)
- Audit Service: Verification (L8)

Implementation Order (from VALIDATOR_LOGIC.md):
1. Validator (pure analysis) - DONE (PIN-288)
2. Eligibility engine (pure rules) - DONE (PIN-289)
3. Contract model (stateful) - DONE (PIN-291)
4. Governance services - DONE (PIN-292)
5. Founder review surface - DONE (PIN-293)
6. Job execution - DONE (PIN-294)
7. Audit wiring - DONE (PIN-295)
8. Rollout projection - DONE (PIN-296) *** PART-2 COMPLETE ***
"""

# =============================================================================
# PIN-513: Cross-domain re-exports removed (L1 re-wiring complete).
# Audit and eligibility types are accessed via their home domains:
#   - AuditService → account/logs/CRM/audit/audit_engine.py
#   - EligibilityEngine → policies/L5_engines/eligibility_engine.py
# L4 code uses Protocol interfaces from hoc_spine/schemas/protocols.py.

from app.hoc.cus.hoc_spine.authority.contracts import (
    ContractService,
    ContractState,
    ContractStateMachine,
)
from app.hoc.cus.hoc_spine.authority.contracts.contract_engine import (
    CONTRACT_SERVICE_VERSION,
)
from app.hoc.cus.hoc_spine.orchestrator.governance_orchestrator import (
    ORCHESTRATOR_VERSION,
    AuditEvidence,
    AuditTrigger,
    ContractActivationError,
    ContractActivationService,
    ExecutionOrchestrator,
    GovernanceOrchestrator,
    HealthLookup,
    JobState,
    JobStateMachine,
    JobStateTracker,
)
from app.hoc.cus.hoc_spine.orchestrator.execution.job_executor import (
    EXECUTOR_VERSION,
    ExecutionContext,
    ExecutionResult,
    FailingHandler,
    HealthObserver,
    JobExecutor,
    NoOpHandler,
    StepHandler,
    StepOutput,
    create_default_executor,
    execution_result_to_evidence,
)

# Audit Service (PIN-295) — L8 verification lives in account-owned CRM audit namespace
from app.hoc.cus.account.logs.CRM.audit.audit_engine import (
    AUDIT_SERVICE_VERSION,
    AuditCheck,
    AuditChecks,
    AuditInput,
    AuditResult,
    AuditService,
    CheckResult,
    RolloutGate,
    audit_result_to_record,
    create_audit_input_from_evidence,
)

# Sandbox (GAP-174) — policy-owned sandbox runtime (wired through hoc_spine)
from app.hoc.cus.policies.L5_engines.sandbox_engine import (
    ExecutionRecord as PolicySandboxExecutionRecord,
    ExecutionRequest as PolicySandboxExecutionRequest,
    SandboxPolicy as PolicySandboxPolicy,
    SandboxService as PolicySandboxService,
)
# PIN-513: rollout_projection relocated to frontend/app/projections/rollout_projection.py
# PIN-513: ValidatorService types accessed via account/L5_engines/crm_validator_engine.py
# L4 code uses Protocol interfaces from hoc_spine/schemas/protocols.py.

# Cross-Domain Governance (mandatory functions - design/CROSS_DOMAIN_GOVERNANCE.md)
from app.hoc.cus.hoc_spine.drivers.cross_domain import (
    create_incident_from_cost_anomaly,
    create_incident_from_cost_anomaly_sync,
    record_limit_breach,
    record_limit_breach_sync,
    table_exists,
)

# Run Governance Facade (PIN-454 FIX-002 - L5→L4 layer compliance)
# V2.0.0 - hoc_spine
from app.hoc.cus.hoc_spine.orchestrator.run_governance_facade import (
    RunGovernanceFacade,
    get_run_governance_facade,
)

# Operation Registry (PIN-491 - L2→L4→L5 Construction)
# V1.0.0 - domain operation dispatch layer
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    REGISTRY_VERSION,
    OperationContext,
    OperationHandler,
    OperationRegistry,
    OperationResult,
    get_operation_registry,
    reset_operation_registry,
)

# Transaction Coordinator (PIN-454 FIX-001 - Atomic cross-domain writes)
# V2.0.0 - hoc_spine
from app.hoc.cus.hoc_spine.drivers.transaction_coordinator import (
    DomainResult,
    RunCompletionTransaction,
    TransactionFailed,
    TransactionPhase,
    TransactionResult,
    create_transaction_coordinator,
    get_transaction_coordinator,
)

__all__ = [
    # Validator — accessed via account/L5_engines (PIN-513)
    # Eligibility — accessed via policies/L5_engines (PIN-513)
    # Contract Service (PIN-291)
    "ContractService",
    "ContractState",
    "ContractStateMachine",
    "CONTRACT_SERVICE_VERSION",
    # Governance Orchestrator (PIN-292)
    "GovernanceOrchestrator",
    "ContractActivationService",
    "ContractActivationError",
    "ExecutionOrchestrator",
    "JobStateMachine",
    "JobStateTracker",
    "JobState",
    "AuditTrigger",
    "AuditEvidence",
    "HealthLookup",
    "ORCHESTRATOR_VERSION",
    # Job Executor (PIN-294)
    "JobExecutor",
    "create_default_executor",
    "execution_result_to_evidence",
    "ExecutionContext",
    "ExecutionResult",
    "StepOutput",
    "StepHandler",
    "HealthObserver",
    "NoOpHandler",
    "FailingHandler",
    "EXECUTOR_VERSION",
    # Audit Service (PIN-295) — accessed via logs/L5_support (PIN-513)
    "AUDIT_SERVICE_VERSION",
    "AuditCheck",
    "AuditChecks",
    "AuditInput",
    "AuditResult",
    "AuditService",
    "CheckResult",
    "RolloutGate",
    "audit_result_to_record",
    "create_audit_input_from_evidence",
    # Sandbox (GAP-174) — policy-owned sandbox runtime
    "PolicySandboxExecutionRecord",
    "PolicySandboxExecutionRequest",
    "PolicySandboxPolicy",
    "PolicySandboxService",
    # Rollout Projection (PIN-296) — relocated to frontend/app/projections/
    # Cross-Domain Governance (mandatory functions)
    "create_incident_from_cost_anomaly",
    "create_incident_from_cost_anomaly_sync",
    "record_limit_breach",
    "record_limit_breach_sync",
    "table_exists",
    # Run Governance Facade (PIN-454)
    "RunGovernanceFacade",
    "get_run_governance_facade",
    # Transaction Coordinator (PIN-454 FIX-001)
    "RunCompletionTransaction",
    "TransactionResult",
    "TransactionFailed",
    "TransactionPhase",
    "DomainResult",
    "get_transaction_coordinator",
    "create_transaction_coordinator",
    # Operation Registry (PIN-491)
    "OperationRegistry",
    "OperationHandler",
    "OperationContext",
    "OperationResult",
    "get_operation_registry",
    "reset_operation_registry",
    "REGISTRY_VERSION",
]
