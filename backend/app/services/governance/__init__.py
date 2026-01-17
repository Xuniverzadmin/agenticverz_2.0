# Layer: L4 — Domain Engine
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

from app.services.governance.audit_service import (
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
from app.services.governance.contract_service import (
    CONTRACT_SERVICE_VERSION,
    ContractService,
    ContractState,
    ContractStateMachine,
)
from app.services.governance.eligibility_engine import (
    DefaultCapabilityLookup,
    DefaultContractLookup,
    DefaultGovernanceSignalLookup,
    DefaultPreApprovalLookup,
    DefaultSystemHealthLookup,
    EligibilityConfig,
    EligibilityDecision,
    EligibilityEngine,
    EligibilityInput,
    EligibilityVerdict,
    RuleResult,
    SystemHealthStatus,
)
from app.services.governance.governance_orchestrator import (
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
from app.services.governance.job_executor import (
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
from app.services.governance.rollout_projection import (
    PROJECTION_VERSION,
    STAGE_ORDER,
    AuditSummary,
    BlastRadius,
    ContractSummary,
    CustomerRolloutView,
    ExecutionSummary,
    FounderRolloutView,
    GovernanceCompletionReport,
    RolloutPlan,
    RolloutProjectionService,
    RolloutStage,
    StabilizationWindow,
    completion_report_to_dict,
    founder_view_to_dict,
)
from app.services.governance.validator_service import (
    IssueType,
    RecommendedAction,
    Severity,
    ValidatorInput,
    ValidatorService,
    ValidatorVerdict,
)

# Cross-Domain Governance (mandatory functions - design/CROSS_DOMAIN_GOVERNANCE.md)
from app.services.governance.cross_domain import (
    create_incident_from_cost_anomaly,
    create_incident_from_cost_anomaly_sync,
    record_limit_breach,
    record_limit_breach_sync,
    table_exists,
)

__all__ = [
    # Validator
    "ValidatorService",
    "ValidatorInput",
    "ValidatorVerdict",
    "IssueType",
    "Severity",
    "RecommendedAction",
    # Eligibility
    "EligibilityEngine",
    "EligibilityInput",
    "EligibilityVerdict",
    "EligibilityConfig",
    "EligibilityDecision",
    "RuleResult",
    "SystemHealthStatus",
    # Eligibility Lookups (for testing/injection)
    "DefaultCapabilityLookup",
    "DefaultGovernanceSignalLookup",
    "DefaultSystemHealthLookup",
    "DefaultContractLookup",
    "DefaultPreApprovalLookup",
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
    # Audit Service (PIN-295)
    "AuditService",
    "AuditInput",
    "AuditResult",
    "AuditCheck",
    "AuditChecks",
    "CheckResult",
    "RolloutGate",
    "audit_result_to_record",
    "create_audit_input_from_evidence",
    "AUDIT_SERVICE_VERSION",
    # Rollout Projection (PIN-296) - FINAL LAYER
    "RolloutProjectionService",
    "FounderRolloutView",
    "CustomerRolloutView",
    "GovernanceCompletionReport",
    "RolloutStage",
    "RolloutPlan",
    "BlastRadius",
    "StabilizationWindow",
    "ContractSummary",
    "ExecutionSummary",
    "AuditSummary",
    "founder_view_to_dict",
    "completion_report_to_dict",
    "STAGE_ORDER",
    "PROJECTION_VERSION",
    # Cross-Domain Governance (mandatory functions)
    "create_incident_from_cost_anomaly",
    "create_incident_from_cost_anomaly_sync",
    "record_limit_breach",
    "record_limit_breach_sync",
    "table_exists",
]
