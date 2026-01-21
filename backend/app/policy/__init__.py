# M19 Policy Layer
# Constitutional governance for multi-agent systems
#
# This module provides the policy engine that every agent and subsystem
# must consult before deciding, routing, executing, escalating, or self-modifying.
#
# GAP Fixes (M19.1):
# - GAP 1: Policy Versioning & Provenance
# - GAP 2: Policy Dependency Graph & Conflict Resolution
# - GAP 3: Temporal Policies (Sliding Windows)
# - GAP 4: Policy Context Object
# - GAP 5: Enhanced Violation Classifications

from app.policy.engine import PolicyEngine, get_policy_engine
from app.policy.prevention_engine import (
    PreventionAction,
    PreventionContext,
    PreventionEngine,
    PreventionResult,
    PolicyViolationError,
    ViolationType as PreventionViolationType,
    create_policy_snapshot_for_run,
)
from app.policy.models import (
    # Core enums
    ActionType,
    # Core models
    BusinessRule,
    BusinessRuleType,
    DependencyGraph,
    # Enhanced models (GAPs 4-5)
    EnhancedPolicyEvaluationRequest,
    EnhancedPolicyEvaluationResult,
    EnhancedPolicyViolation,
    EthicalConstraint,
    EthicalConstraintType,
    Policy,
    PolicyCategory,
    PolicyConflict,
    # GAP 4: Policy Context
    PolicyContext,
    PolicyDecision,
    # GAP 2: Dependency Graph
    PolicyDependency,
    PolicyEvaluationRequest,
    PolicyEvaluationResult,
    PolicyLoadResult,
    PolicyModification,
    PolicyProvenance,
    PolicyRule,
    PolicyState,
    # GAP 1: Versioning & Provenance
    PolicyVersion,
    PolicyViolation,
    RecoverabilityType,
    RiskCeiling,
    SafetyRule,
    SafetyRuleType,
    TemporalMetricWindow,
    # GAP 3: Temporal Policies
    TemporalPolicy,
    # GAP 3: Temporal policy types
    TemporalPolicyType,
    # GAP 5: Enhanced severity
    ViolationSeverity,
    ViolationType,
)

__all__ = [
    # Engine
    "PolicyEngine",
    "get_policy_engine",
    # Prevention Engine (GAP-001, GAP-002)
    "PreventionAction",
    "PreventionContext",
    "PreventionEngine",
    "PreventionResult",
    "PolicyViolationError",
    "PreventionViolationType",
    "create_policy_snapshot_for_run",
    # Core enums
    "ActionType",
    "BusinessRuleType",
    "EthicalConstraintType",
    "PolicyCategory",
    "PolicyDecision",
    "SafetyRuleType",
    "ViolationType",
    # GAP 5: Enhanced severity
    "ViolationSeverity",
    "RecoverabilityType",
    # GAP 3: Temporal policy types
    "TemporalPolicyType",
    # Core models
    "BusinessRule",
    "EthicalConstraint",
    "Policy",
    "PolicyEvaluationRequest",
    "PolicyEvaluationResult",
    "PolicyLoadResult",
    "PolicyModification",
    "PolicyRule",
    "PolicyState",
    "PolicyViolation",
    "RiskCeiling",
    "SafetyRule",
    # GAP 1: Versioning & Provenance
    "PolicyVersion",
    "PolicyProvenance",
    # GAP 2: Dependency Graph
    "PolicyDependency",
    "PolicyConflict",
    "DependencyGraph",
    # GAP 3: Temporal Policies
    "TemporalPolicy",
    "TemporalMetricWindow",
    # GAP 4: Policy Context
    "PolicyContext",
    # Enhanced models (GAPs 4-5)
    "EnhancedPolicyEvaluationRequest",
    "EnhancedPolicyViolation",
    "EnhancedPolicyEvaluationResult",
]
