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
# CROSS-DOMAIN IMPORTS — BROKEN INTENTIONALLY (2026-01-30)
# These re-exports violated spine constitutional boundary.
# Will be re-wired during L1 design via protocol interfaces.
# Previous imports:
#   from app.hoc.cus.logs.L5_support.CRM.engines.audit_engine import (
#       AUDIT_SERVICE_VERSION, AuditCheck, AuditChecks, AuditInput, AuditResult,
#       AuditService, CheckResult, RolloutGate, audit_result_to_record,
#       create_audit_input_from_evidence)
#   from app.hoc.cus.policies.L5_engines.eligibility_engine import (
#       DefaultCapabilityLookup, DefaultContractLookup, DefaultGovernanceSignalLookup,
#       DefaultPreApprovalLookup, DefaultSystemHealthLookup, EligibilityConfig,
#       EligibilityDecision, EligibilityEngine, EligibilityInput, EligibilityVerdict,
#       RuleResult, SystemHealthStatus)
# TODO(L1): Re-export these via protocol-based injection

from app.hoc.hoc_spine.authority.contracts.contract_engine import (
    CONTRACT_SERVICE_VERSION,
    ContractService,
    ContractState,
    ContractStateMachine,
)
from app.hoc.hoc_spine.orchestrator.governance_orchestrator import (
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
from app.hoc.hoc_spine.orchestrator.execution.job_executor import (
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
# BROKEN INTENTIONALLY — rollout_projection relocated to frontend/app/projections/
# Will be re-wired during L1 design. Previous import path:
#   from app.hoc.hoc_spine.frontend.projections.rollout_projection import (...)
# New location: frontend/app/projections/rollout_projection.py
# CROSS-DOMAIN IMPORT — BROKEN INTENTIONALLY (2026-01-30)
# Previous: from app.hoc.cus.account.L5_support.CRM.engines.crm_validator_engine import (
#     IssueType, RecommendedAction, Severity, ValidatorInput, ValidatorService, ValidatorVerdict)
# TODO(L1): Re-export via protocol-based injection

# Cross-Domain Governance (mandatory functions - design/CROSS_DOMAIN_GOVERNANCE.md)
from app.hoc.hoc_spine.drivers.cross_domain import (
    create_incident_from_cost_anomaly,
    create_incident_from_cost_anomaly_sync,
    record_limit_breach,
    record_limit_breach_sync,
    table_exists,
)

# Run Governance Facade (PIN-454 FIX-002 - L5→L4 layer compliance)
# V2.0.0 - hoc_spine
from app.hoc.hoc_spine.orchestrator.run_governance_facade import (
    RunGovernanceFacade,
    get_run_governance_facade,
)

# Operation Registry (PIN-491 - L2→L4→L5 Construction)
# V1.0.0 - domain operation dispatch layer
from app.hoc.hoc_spine.orchestrator.operation_registry import (
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
from app.hoc.hoc_spine.drivers.transaction_coordinator import (
    DomainResult,
    RunCompletionTransaction,
    TransactionFailed,
    TransactionPhase,
    TransactionResult,
    create_transaction_coordinator,
    get_transaction_coordinator,
)

__all__ = [
    # Validator — RELOCATED (2026-01-30), re-export pending L1 design
    # Eligibility — RELOCATED (2026-01-30), re-export pending L1 design
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
    # Audit Service (PIN-295) — RELOCATED (2026-01-30), re-export pending L1 design
    # Rollout Projection (PIN-296) — RELOCATED to frontend/app/projections/
    # Will be re-exported here during L1 design.
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
