# Layer: L3 — Boundary Adapters
# Product: system-wide
# Role: Package for L3 boundary adapters
# Reference: PIN-258 Phase F

"""
L3 Boundary Adapters Package

This package contains L3 boundary adapters that translate between:
- L2 (API routes) - request handlers
- L4 (Domain commands) - domain decisions

Adapters must:
- Only import from L4 and L6
- Never import from L1, L2, or L5
- Translate requests, not make domain decisions
- Be thin (<200 LOC typically)
"""

# TOMBSTONE_EXPIRY: 2026-03-04
# customer_incidents_adapter import disabled - broken dependency chain via app.services
# Import directly when needed: from app.adapters.customer_incidents_adapter import ...
from app.adapters.customer_keys_adapter import (
    CustomerKeyAction,
    CustomerKeyInfo,
    CustomerKeyListResponse,
    CustomerKeysAdapter,
    get_customer_keys_adapter,
)
from app.adapters.customer_killswitch_adapter import (
    CustomerKillswitchAction,
    CustomerKillswitchAdapter,
    CustomerKillswitchStatus,
    get_customer_killswitch_adapter,
)
from app.adapters.customer_logs_adapter import (
    CustomerLogDetail,
    CustomerLogListResponse,
    CustomerLogsAdapter,
    CustomerLogStep,
    CustomerLogSummary,
    get_customer_logs_adapter,
)
from app.adapters.customer_policies_adapter import (
    CustomerBudgetConstraint,
    CustomerGuardrail,
    CustomerPoliciesAdapter,
    CustomerPolicyConstraints,
    CustomerRateLimit,
    get_customer_policies_adapter,
)

# RESTORED: founder_contract_review_adapter (CRM workflow) - unified review page created
from app.adapters.founder_contract_review_adapter import (
    FounderContractDetailView,
    FounderContractSummaryView,
    FounderReviewAdapter,
    FounderReviewDecision,
    FounderReviewQueueResponse,
    FounderReviewResult,
)
from app.adapters.platform_eligibility_adapter import (
    CapabilityEligibilityView,
    CapabilityHealthView,
    DomainHealthView,
    HealthReasonView,
    PlatformEligibilityAdapter,
    PlatformEligibilityResponse,
    SystemHealthView,
    get_platform_eligibility_adapter,
)
from app.adapters.policy_adapter import (
    PolicyAdapter,
    PolicyEvaluationResult,
    PolicyViolation,
    get_policy_adapter,
)
from app.adapters.runtime_adapter import RuntimeAdapter, get_runtime_adapter
from app.adapters.workers_adapter import (
    ReplayResult,
    WorkerExecutionResult,
    WorkersAdapter,
    get_workers_adapter,
)

__all__ = [
    # Runtime adapter
    "RuntimeAdapter",
    "get_runtime_adapter",
    # Workers adapter
    "WorkersAdapter",
    "get_workers_adapter",
    "WorkerExecutionResult",
    "ReplayResult",
    # Policy adapter
    "PolicyAdapter",
    "get_policy_adapter",
    "PolicyEvaluationResult",
    "PolicyViolation",
    # Customer logs adapter (PIN-281)
    "CustomerLogsAdapter",
    "get_customer_logs_adapter",
    "CustomerLogSummary",
    "CustomerLogStep",
    "CustomerLogDetail",
    "CustomerLogListResponse",
    # Customer policies adapter (PIN-281)
    "CustomerPoliciesAdapter",
    "get_customer_policies_adapter",
    "CustomerBudgetConstraint",
    "CustomerRateLimit",
    "CustomerGuardrail",
    "CustomerPolicyConstraints",
    # Customer incidents adapter (PIN-281) - DISABLED: broken dependency chain
    # Customer keys adapter (PIN-281)
    "CustomerKeysAdapter",
    "get_customer_keys_adapter",
    "CustomerKeyInfo",
    "CustomerKeyListResponse",
    "CustomerKeyAction",
    # Customer killswitch adapter (PIN-281)
    "CustomerKillswitchAdapter",
    "get_customer_killswitch_adapter",
    "CustomerKillswitchStatus",
    "CustomerKillswitchAction",
    # Platform eligibility adapter (PIN-284)
    "PlatformEligibilityAdapter",
    "get_platform_eligibility_adapter",
    "HealthReasonView",
    "CapabilityHealthView",
    "DomainHealthView",
    "SystemHealthView",
    "CapabilityEligibilityView",
    "PlatformEligibilityResponse",
    # Founder Review adapter (PIN-293)
    "FounderReviewAdapter",
    "FounderContractSummaryView",
    "FounderContractDetailView",
    "FounderReviewQueueResponse",
    "FounderReviewDecision",
    "FounderReviewResult",
]
