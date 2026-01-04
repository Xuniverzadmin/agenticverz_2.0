# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Part-2 CRM Workflow Governance Services
# Callers: L2 (governance APIs), L3 (adapters)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: PIN-287, PIN-288, PIN-289, part2-design-v1

"""
Part-2 CRM Workflow Governance Services

L4 domain services for the Part-2 governance workflow:
- Validator: Issue analysis (advisory, stateless)
- Eligibility: Contract gating (pure rules)
- Contract Service: State machine (stateful)

Implementation Order (from VALIDATOR_LOGIC.md):
1. Validator (pure analysis) - DONE (PIN-288)
2. Eligibility engine (pure rules) - DONE (PIN-289)
3. Contract model (stateful)
4. Governance services
5. Founder review surface
6. Job execution
7. Audit wiring
8. Rollout projection
"""

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
from app.services.governance.validator_service import (
    IssueType,
    RecommendedAction,
    Severity,
    ValidatorInput,
    ValidatorService,
    ValidatorVerdict,
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
]
