# M19 Policy Layer Models
# Constitutional governance for multi-agent systems
#
# These models define the policy types and evaluation results
# that form the "Constitution" of the multi-agent ecosystem.

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field


# =============================================================================
# Policy Categories
# =============================================================================

class PolicyCategory(str, Enum):
    """Categories of policies in the M19 Policy Layer."""
    COMPLIANCE = "compliance"      # Jurisdictional, data handling, consent
    ETHICAL = "ethical"            # No coercion, no fabrication, transparency
    RISK = "risk"                  # Cost limits, retry limits, cascade limits
    SAFETY = "safety"              # Action blocks, hard stops, escalations
    BUSINESS = "business"          # SLAs, tiers, budgets, feature gates


class PolicyDecision(str, Enum):
    """Possible decisions from policy evaluation."""
    ALLOW = "allow"                # Action permitted
    BLOCK = "block"                # Action denied
    MODIFY = "modify"              # Action permitted with modifications


class ActionType(str, Enum):
    """Types of actions that require policy evaluation."""
    ROUTE = "route"                # Routing decision (CARE)
    EXECUTE = "execute"            # Skill/task execution
    ADAPT = "adapt"                # Strategy adaptation (SBA)
    ESCALATE = "escalate"          # Escalation to human
    SELF_MODIFY = "self_modify"    # Agent self-modification
    SPAWN = "spawn"                # Agent spawning
    INVOKE = "invoke"              # Agent invocation
    DATA_ACCESS = "data_access"    # Data access request
    EXTERNAL_CALL = "external_call"  # External API call


class ViolationType(str, Enum):
    """Types of policy violations."""
    COMPLIANCE_BREACH = "compliance_breach"
    ETHICAL_VIOLATION = "ethical_violation"
    RISK_CEILING_BREACH = "risk_ceiling_breach"
    SAFETY_RULE_TRIGGERED = "safety_rule_triggered"
    BUSINESS_RULE_VIOLATION = "business_rule_violation"
    TEMPORAL_LIMIT_EXCEEDED = "temporal_limit_exceeded"
    DEPENDENCY_CONFLICT = "dependency_conflict"


class ViolationSeverity(str, Enum):
    """Enhanced violation severity classifications (GAP 5)."""
    # Critical - Non-recoverable, immediate action required
    ETHICAL_CRITICAL = "ethical_critical"       # Fundamental ethics breach
    COMPLIANCE_CRITICAL = "compliance_critical" # Legal/regulatory breach
    OPERATIONAL_CRITICAL = "operational_critical"  # System stability threat

    # High - Recoverable but serious
    ETHICAL_HIGH = "ethical_high"
    COMPLIANCE_HIGH = "compliance_high"
    OPERATIONAL_HIGH = "operational_high"

    # Medium - Recoverable with intervention
    RECOVERABLE_MEDIUM = "recoverable_medium"

    # Low - Recoverable, warning only
    RECOVERABLE_LOW = "recoverable_low"
    AUDIT_ONLY = "audit_only"


class RecoverabilityType(str, Enum):
    """Whether a violation is recoverable."""
    NON_RECOVERABLE = "non_recoverable"  # Requires immediate freeze
    RECOVERABLE_MANUAL = "recoverable_manual"  # Needs human intervention
    RECOVERABLE_AUTO = "recoverable_auto"  # System can auto-recover
    AUDIT_ONLY = "audit_only"  # Log only, no action needed


class SafetyRuleType(str, Enum):
    """Types of safety rules."""
    ACTION_BLOCK = "action_block"        # Block specific actions
    PATTERN_BLOCK = "pattern_block"      # Block based on patterns
    ESCALATION_REQUIRED = "escalation_required"  # Require human approval
    HARD_STOP = "hard_stop"              # Emergency stop
    COOLDOWN = "cooldown"                # Enforce cooldown period


class EthicalConstraintType(str, Enum):
    """Types of ethical constraints."""
    NO_COERCION = "no_coercion"
    NO_FABRICATION = "no_fabrication"
    NO_MANIPULATION = "no_manipulation"
    TRANSPARENCY = "transparency"


class BusinessRuleType(str, Enum):
    """Types of business rules."""
    PRICING = "pricing"
    TIER_ACCESS = "tier_access"
    SLA = "sla"
    BUDGET = "budget"
    FEATURE_GATE = "feature_gate"


# =============================================================================
# Request/Response Models
# =============================================================================

class PolicyEvaluationRequest(BaseModel):
    """Request for policy evaluation."""
    action_type: ActionType
    agent_id: Optional[str] = None
    tenant_id: Optional[str] = None

    # Context for evaluation
    context: Dict[str, Any] = Field(default_factory=dict)

    # Specific data to check
    proposed_action: Optional[str] = None
    target_resource: Optional[str] = None
    estimated_cost: Optional[float] = None
    data_categories: Optional[List[str]] = None  # PII, financial, etc.
    external_endpoints: Optional[List[str]] = None

    # SBA context
    current_sba: Optional[Dict[str, Any]] = None
    proposed_modification: Optional[Dict[str, Any]] = None

    # Metadata
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PolicyModification(BaseModel):
    """Modification applied to an action by policy engine."""
    parameter: str
    original_value: Any
    modified_value: Any
    reason: str


class PolicyEvaluationResult(BaseModel):
    """Result of policy evaluation."""
    request_id: str
    decision: PolicyDecision
    decision_reason: Optional[str] = None

    # Evaluation details
    policies_evaluated: int = 0
    rules_matched: List[str] = Field(default_factory=list)
    evaluation_ms: float = 0.0

    # Modifications (if decision = MODIFY)
    modifications: List[PolicyModification] = Field(default_factory=list)

    # Violations (if decision = BLOCK)
    violations: List["PolicyViolation"] = Field(default_factory=list)

    # Metadata
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    policy_version: Optional[str] = None


class PolicyViolation(BaseModel):
    """A policy violation record."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    violation_type: ViolationType
    policy_name: str
    severity: float = Field(default=0.5, ge=0.0, le=1.0)
    description: str
    evidence: Dict[str, Any] = Field(default_factory=dict)

    # What caused it
    agent_id: Optional[str] = None
    tenant_id: Optional[str] = None
    action_attempted: Optional[str] = None

    # Governor routing
    routed_to_governor: bool = False
    governor_action: Optional[str] = None

    # Timestamps
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# =============================================================================
# Policy Definition Models
# =============================================================================

class PolicyRule(BaseModel):
    """A single rule within a policy."""
    name: str
    condition: Dict[str, Any]  # Condition expression
    action: PolicyDecision = PolicyDecision.BLOCK
    modification: Optional[Dict[str, Any]] = None  # If action = MODIFY
    priority: int = 100


class Policy(BaseModel):
    """A policy definition."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    category: PolicyCategory
    description: Optional[str] = None

    # Rules
    rules: List[PolicyRule] = Field(default_factory=list)

    # Versioning
    version: int = 1
    is_active: bool = True
    supersedes_id: Optional[str] = None

    # Applicability
    applies_to: Optional[List[str]] = None  # Agent types
    tenant_id: Optional[str] = None  # Null = global
    priority: int = 100  # Lower = higher priority

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None


class RiskCeiling(BaseModel):
    """A risk ceiling definition."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None

    # Ceiling
    metric: str  # e.g., "cost_per_hour", "retries_per_minute"
    max_value: float
    current_value: float = 0.0
    window_seconds: int = 3600

    # Applicability
    applies_to: Optional[List[str]] = None
    tenant_id: Optional[str] = None

    # Breach handling
    breach_action: str = "block"  # block, throttle, alert
    breach_count: int = 0
    last_breach_at: Optional[datetime] = None

    is_active: bool = True


class SafetyRule(BaseModel):
    """A safety rule definition."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None

    # Rule
    rule_type: SafetyRuleType
    condition: Dict[str, Any]
    action: str  # block, escalate, alert, cooldown

    # Cooldown
    cooldown_seconds: Optional[int] = None

    # Applicability
    applies_to: Optional[List[str]] = None
    tenant_id: Optional[str] = None
    priority: int = 100

    is_active: bool = True
    triggered_count: int = 0
    last_triggered_at: Optional[datetime] = None


class EthicalConstraint(BaseModel):
    """An ethical constraint definition."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str

    # Constraint
    constraint_type: EthicalConstraintType
    forbidden_patterns: Optional[List[str]] = None
    required_disclosures: Optional[List[str]] = None
    transparency_threshold: Optional[float] = None  # 0.0-1.0

    # Enforcement
    enforcement_level: str = "strict"  # strict, warn, audit
    violation_action: str = "block"

    is_active: bool = True
    violated_count: int = 0
    last_violated_at: Optional[datetime] = None


class BusinessRule(BaseModel):
    """A business rule definition."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None

    # Rule
    rule_type: BusinessRuleType
    condition: Dict[str, Any]
    constraint: Dict[str, Any]

    # Applicability
    tenant_id: Optional[str] = None
    customer_tier: Optional[str] = None  # free, pro, enterprise
    priority: int = 100

    is_active: bool = True


# =============================================================================
# Composite Models
# =============================================================================

class PolicyState(BaseModel):
    """Current state of the policy layer."""
    total_policies: int = 0
    active_policies: int = 0
    total_evaluations_today: int = 0
    total_violations_today: int = 0
    block_rate: float = 0.0

    # By category
    compliance_violations: int = 0
    ethical_violations: int = 0
    risk_breaches: int = 0
    safety_triggers: int = 0
    business_violations: int = 0

    # Risk ceilings status
    risk_ceilings_active: int = 0
    risk_ceilings_breached: int = 0

    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PolicyLoadResult(BaseModel):
    """Result of loading policies from database."""
    policies_loaded: int = 0
    risk_ceilings_loaded: int = 0
    safety_rules_loaded: int = 0
    ethical_constraints_loaded: int = 0
    business_rules_loaded: int = 0
    temporal_policies_loaded: int = 0
    errors: List[str] = Field(default_factory=list)
    loaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# =============================================================================
# GAP 1: Policy Versioning & Provenance
# =============================================================================

class PolicyVersion(BaseModel):
    """A versioned snapshot of a policy set (GAP 1)."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    version: str  # Semantic version: "1.2.3"
    policy_hash: str  # SHA256 of policy content
    signature: Optional[str] = None  # HMAC signature for tamper protection

    # Provenance
    created_by: str  # System or user ID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    description: Optional[str] = None  # Change description

    # Content snapshot
    policies_snapshot: Dict[str, Any] = Field(default_factory=dict)
    risk_ceilings_snapshot: Dict[str, Any] = Field(default_factory=dict)
    safety_rules_snapshot: Dict[str, Any] = Field(default_factory=dict)
    ethical_constraints_snapshot: Dict[str, Any] = Field(default_factory=dict)
    business_rules_snapshot: Dict[str, Any] = Field(default_factory=dict)
    temporal_policies_snapshot: Dict[str, Any] = Field(default_factory=dict)

    # Rollback info
    parent_version: Optional[str] = None
    is_active: bool = True
    rolled_back_at: Optional[datetime] = None
    rolled_back_by: Optional[str] = None


class PolicyProvenance(BaseModel):
    """Audit trail for policy changes (GAP 1)."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    policy_id: str
    policy_type: str  # "policy", "risk_ceiling", "safety_rule", etc.

    # Change details
    action: str  # "create", "update", "delete", "activate", "deactivate"
    changed_by: str
    changed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Before/after
    previous_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None

    # Version context
    policy_version: str
    reason: Optional[str] = None


# =============================================================================
# GAP 2: Policy Dependency Graph & Conflict Resolution
# =============================================================================

class PolicyDependency(BaseModel):
    """Dependency relationship between policies (GAP 2)."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    source_policy: str  # Policy ID that has the dependency
    target_policy: str  # Policy ID that is depended on
    dependency_type: str  # "requires", "conflicts_with", "overrides", "modifies"

    # Conflict resolution
    resolution_strategy: str = "source_wins"  # "source_wins", "target_wins", "merge", "escalate"
    priority: int = 100  # Lower = higher priority in conflicts

    description: Optional[str] = None
    is_active: bool = True


class PolicyConflict(BaseModel):
    """A detected conflict between policies (GAP 2)."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    policy_a: str
    policy_b: str
    conflict_type: str  # "direct_contradiction", "implicit_override", "cascade_loop"
    severity: float = 0.5

    # Details
    description: str
    affected_action_types: List[ActionType] = Field(default_factory=list)

    # Resolution
    resolved: bool = False
    resolution: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None

    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DependencyGraph(BaseModel):
    """The complete policy dependency graph (GAP 2)."""
    nodes: Dict[str, Dict[str, Any]] = Field(default_factory=dict)  # policy_id -> policy_metadata
    edges: List[PolicyDependency] = Field(default_factory=list)
    conflicts: List[PolicyConflict] = Field(default_factory=list)
    computed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# =============================================================================
# GAP 3: Temporal Policies (Sliding Windows)
# =============================================================================

class TemporalPolicyType(str, Enum):
    """Types of temporal policies."""
    SLIDING_WINDOW = "sliding_window"      # Rolling window limit
    CUMULATIVE_DAILY = "cumulative_daily"  # Resets daily
    CUMULATIVE_WEEKLY = "cumulative_weekly"
    RATE_DECAY = "rate_decay"              # Exponential decay
    BURST_LIMIT = "burst_limit"            # Short-term spike protection


class TemporalPolicy(BaseModel):
    """A temporal/sliding window policy (GAP 3)."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None

    # Temporal definition
    temporal_type: TemporalPolicyType
    metric: str  # What to track: "retries", "cost", "adaptations", "escalations"
    max_value: float
    window_seconds: int  # Sliding window size

    # Scope
    applies_to: Optional[List[str]] = None  # Agent types
    tenant_id: Optional[str] = None
    agent_id: Optional[str] = None  # Per-agent limits

    # Breach handling
    breach_action: str = "block"  # block, throttle, alert, escalate
    cooldown_on_breach: int = 0  # Additional cooldown seconds

    # State
    is_active: bool = True
    breach_count: int = 0
    last_breach_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TemporalMetricWindow(BaseModel):
    """A sliding window of metric values (GAP 3)."""
    policy_id: str
    agent_id: Optional[str] = None
    tenant_id: Optional[str] = None

    # Window data
    values: List[Dict[str, Any]] = Field(default_factory=list)  # [{timestamp, value}, ...]
    window_start: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    window_seconds: int = 3600

    # Aggregates
    current_sum: float = 0.0
    current_count: int = 0
    current_max: float = 0.0


# =============================================================================
# GAP 4: Policy Context Object
# =============================================================================

class PolicyContext(BaseModel):
    """
    Complete policy context passed through the decision cycle (GAP 4).

    This object provides the full state needed for policy evaluation,
    enabling multi-agent coordination and trajectory-based decisions.
    """
    # Agent identity
    agent_id: Optional[str] = None
    agent_type: Optional[str] = None
    agent_capabilities: List[str] = Field(default_factory=list)

    # Tenant context
    tenant_id: Optional[str] = None
    customer_tier: Optional[str] = None  # free, pro, enterprise

    # Risk state
    risk_state: Dict[str, float] = Field(default_factory=dict)  # metric -> current_value
    risk_utilization: Dict[str, float] = Field(default_factory=dict)  # metric -> percentage

    # Historical context
    historical_violation_count: int = 0
    violation_types_24h: Dict[str, int] = Field(default_factory=dict)  # type -> count
    last_violation_at: Optional[datetime] = None
    is_quarantined: bool = False
    quarantine_until: Optional[datetime] = None

    # Action chain context (for cascade/depth tracking)
    action_chain_depth: int = 0
    action_chain_ids: List[str] = Field(default_factory=list)  # Parent action IDs
    origin_trigger: Optional[str] = None  # What started this chain
    root_agent_id: Optional[str] = None  # Original agent in chain

    # Cost tracking
    cumulative_cost_1h: float = 0.0
    cumulative_cost_24h: float = 0.0
    daily_budget_remaining: Optional[float] = None

    # Temporal metrics (for GAP 3)
    temporal_metrics: Dict[str, float] = Field(default_factory=dict)  # metric -> current_window_value
    temporal_utilization: Dict[str, float] = Field(default_factory=dict)  # metric -> percentage

    # Policy versioning (for GAP 1)
    governing_policy_version: Optional[str] = None
    policy_hash: Optional[str] = None

    # Request metadata
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Previous evaluations in this chain
    prior_decisions: List[Dict[str, Any]] = Field(default_factory=list)


# =============================================================================
# Enhanced Policy Evaluation with Context
# =============================================================================

class EnhancedPolicyEvaluationRequest(BaseModel):
    """Enhanced evaluation request with full context (GAP 4)."""
    action_type: ActionType
    policy_context: PolicyContext = Field(default_factory=PolicyContext)

    # Action details
    proposed_action: Optional[str] = None
    target_resource: Optional[str] = None
    estimated_cost: Optional[float] = None
    data_categories: Optional[List[str]] = None
    external_endpoints: Optional[List[str]] = None

    # SBA context
    current_sba: Optional[Dict[str, Any]] = None
    proposed_modification: Optional[Dict[str, Any]] = None

    # Additional context
    context: Dict[str, Any] = Field(default_factory=dict)

    # Request metadata
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EnhancedPolicyViolation(BaseModel):
    """Enhanced violation with severity classification (GAP 5)."""
    id: str = Field(default_factory=lambda: str(uuid4()))

    # Basic violation info
    violation_type: ViolationType
    policy_name: str
    description: str
    evidence: Dict[str, Any] = Field(default_factory=dict)

    # Enhanced severity (GAP 5)
    severity: float = Field(default=0.5, ge=0.0, le=1.0)
    severity_class: ViolationSeverity = ViolationSeverity.RECOVERABLE_MEDIUM
    recoverability: RecoverabilityType = RecoverabilityType.RECOVERABLE_AUTO

    # Context
    agent_id: Optional[str] = None
    tenant_id: Optional[str] = None
    action_attempted: Optional[str] = None
    action_chain_depth: int = 0

    # Governor routing
    routed_to_governor: bool = False
    governor_action: Optional[str] = None
    recommended_action: Optional[str] = None  # freeze, rollback, quarantine, alert

    # Temporal context
    is_temporal_violation: bool = False
    temporal_window_seconds: Optional[int] = None
    temporal_metric_value: Optional[float] = None

    # Provenance
    policy_version: Optional[str] = None
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EnhancedPolicyEvaluationResult(BaseModel):
    """Enhanced evaluation result with full context (GAPs 1-5)."""
    request_id: str
    decision: PolicyDecision
    decision_reason: Optional[str] = None

    # Evaluation details
    policies_evaluated: int = 0
    temporal_policies_evaluated: int = 0
    dependencies_checked: int = 0
    rules_matched: List[str] = Field(default_factory=list)
    evaluation_ms: float = 0.0

    # Modifications (if decision = MODIFY)
    modifications: List[PolicyModification] = Field(default_factory=list)

    # Violations (if decision = BLOCK)
    violations: List[EnhancedPolicyViolation] = Field(default_factory=list)

    # Conflict info (GAP 2)
    conflicts_detected: List[PolicyConflict] = Field(default_factory=list)
    conflict_resolution_applied: Optional[str] = None

    # Temporal info (GAP 3)
    temporal_utilization: Dict[str, float] = Field(default_factory=dict)
    temporal_warnings: List[str] = Field(default_factory=list)

    # Provenance (GAP 1)
    policy_version: Optional[str] = None
    policy_hash: Optional[str] = None

    # Context returned (GAP 4)
    updated_context: Optional[PolicyContext] = None

    # Metadata
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# =============================================================================
# Resolve Forward References (Pydantic v2)
# =============================================================================
# PolicyEvaluationResult references PolicyViolation which is defined after it
PolicyEvaluationResult.model_rebuild()
