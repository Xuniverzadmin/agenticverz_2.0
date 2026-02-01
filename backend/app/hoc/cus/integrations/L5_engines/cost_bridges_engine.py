# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: (via driver)
#   Writes: none (pure business logic)
# Role: Cost-related integration bridges (cost loop business logic)
# Callers: cost services, workers
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, HOC_LAYER_TOPOLOGY_V1.md, INTEGRATIONS_PHASE2.5_IMPLEMENTATION_PLAN.md

"""
M27 Cost Loop Integration Bridges

Wires Cost Intelligence into M25 Integration Loop:
- C1: Cost Anomaly → Incident
- C2: Cost Pattern → Failure Catalog
- C3: Cost Recovery Generator
- C4: Cost Policy Generator
- C5: Cost Routing Adjuster

The Invariant: Every cost anomaly enters the loop.
Every loop completion reduces future cost risk.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

from app.hoc.cus.integrations.L5_schemas.loop_events import (
    LoopEvent,
    LoopStage,
    PatternMatchResult,
    PolicyRule,
    RecoverySuggestion,
    RoutingAdjustment,
    ensure_json_serializable,
)

# V2.0.0 - hoc_spine orchestrator
from app.hoc.cus.hoc_spine.orchestrator import create_incident_from_cost_anomaly_sync

logger = logging.getLogger("nova.integrations.cost")


# =============================================================================
# COST ANOMALY TYPES
# =============================================================================


class AnomalyType(str, Enum):
    """Types of cost anomalies."""

    USER_SPIKE = "user_spike"
    FEATURE_SPIKE = "feature_spike"
    TENANT_SPIKE = "tenant_spike"  # Added for snapshot-based detection
    MODEL_SPIKE = "model_spike"  # Added for snapshot-based detection
    BUDGET_WARNING = "budget_warning"
    BUDGET_EXCEEDED = "budget_exceeded"
    UNUSUAL_MODEL = "unusual_model"
    RATE_ANOMALY = "rate_anomaly"


class AnomalySeverity(str, Enum):
    """Severity levels for cost anomalies."""

    LOW = "low"  # Information only
    MEDIUM = "medium"  # Worth watching
    HIGH = "high"  # Requires attention
    CRITICAL = "critical"  # Immediate action needed


@dataclass
class CostAnomaly:
    """
    Detected cost anomaly from M26 Cost Intelligence.

    This is the input to the M27 Cost Loop.
    """

    id: str
    tenant_id: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    entity_type: str  # "user", "feature", "model", "tenant"
    entity_id: str
    current_value_cents: int
    expected_value_cents: int
    deviation_pct: float
    message: str
    detected_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        tenant_id: str,
        anomaly_type: AnomalyType,
        entity_type: str,
        entity_id: str,
        current_value_cents: int,
        expected_value_cents: int,
        metadata: dict[str, Any] | None = None,
    ) -> "CostAnomaly":
        """Factory method for creating cost anomalies."""
        deviation_pct = (
            (current_value_cents - expected_value_cents) / expected_value_cents * 100
            if expected_value_cents > 0
            else 0.0
        )

        # Determine severity based on deviation
        if deviation_pct >= 500:
            severity = AnomalySeverity.CRITICAL
        elif deviation_pct >= 300:
            severity = AnomalySeverity.HIGH
        elif deviation_pct >= 200:
            severity = AnomalySeverity.MEDIUM
        else:
            severity = AnomalySeverity.LOW

        # Generate message
        messages = {
            AnomalyType.USER_SPIKE: f"User {entity_id} spent ${current_value_cents / 100:.2f} ({deviation_pct:.0f}% above average)",
            AnomalyType.FEATURE_SPIKE: f"Feature {entity_id} cost ${current_value_cents / 100:.2f} ({deviation_pct:.0f}% increase)",
            AnomalyType.BUDGET_WARNING: f"Budget at {deviation_pct:.0f}% - approaching limit",
            AnomalyType.BUDGET_EXCEEDED: f"Budget exceeded by ${(current_value_cents - expected_value_cents) / 100:.2f}",
            AnomalyType.UNUSUAL_MODEL: f"Model {entity_id} usage {deviation_pct:.0f}% above normal",
            AnomalyType.RATE_ANOMALY: f"Unusual request rate: {deviation_pct:.0f}% above baseline",
        }

        return cls(
            id=f"anom_{uuid.uuid4().hex[:16]}",
            tenant_id=tenant_id,
            anomaly_type=anomaly_type,
            severity=severity,
            entity_type=entity_type,
            entity_id=entity_id,
            current_value_cents=current_value_cents,
            expected_value_cents=expected_value_cents,
            deviation_pct=deviation_pct,
            message=messages.get(anomaly_type, f"Cost anomaly: {entity_id}"),
            detected_at=datetime.now(timezone.utc),
            metadata=metadata or {},
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "anomaly_type": self.anomaly_type.value,
            "severity": self.severity.value,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "current_value_cents": self.current_value_cents,
            "expected_value_cents": self.expected_value_cents,
            "deviation_pct": self.deviation_pct,
            "message": self.message,
            "detected_at": self.detected_at.isoformat(),
            "metadata": self.metadata,
        }


# =============================================================================
# BRIDGE C1: COST ANOMALY → INCIDENT
# =============================================================================


class CostLoopBridge:
    """
    Bridge C1: Cost Anomaly → Incident (MANDATORY GOVERNANCE).

    Creates real incidents from cost anomalies using mandatory governance.
    No simulation. No optional dispatcher. Every HIGH+ anomaly creates an incident or crashes.
    """

    def __init__(self, db_session):
        """
        Initialize with database session.

        Args:
            db_session: Database session for creating incidents (REQUIRED)
        """
        if db_session is None:
            raise ValueError("db_session is required for CostLoopBridge - governance is not optional")
        self.db_session = db_session

    def on_anomaly_detected(self, anomaly: CostAnomaly) -> Optional[str]:
        """
        Create incident from cost anomaly if severity warrants.

        MANDATORY GOVERNANCE: HIGH+ anomalies create incidents or raise GovernanceError.
        There is no optional dispatcher. Governance is not negotiable.

        Returns incident_id if created, None otherwise.

        Raises:
            GovernanceError: If incident creation fails (mandatory)
        """
        # Only HIGH and CRITICAL anomalies trigger incidents
        if anomaly.severity not in [AnomalySeverity.HIGH, AnomalySeverity.CRITICAL]:
            logger.info(f"Skipping {anomaly.severity.value} severity anomaly: {anomaly.id}")
            return None

        # MANDATORY: Create real incident via governance function
        # This will raise GovernanceError if it fails - no silent failure allowed
        incident_id = create_incident_from_cost_anomaly_sync(
            session=self.db_session,
            tenant_id=anomaly.tenant_id,
            anomaly_id=anomaly.id,
            anomaly_type=anomaly.anomaly_type.value,
            severity=anomaly.severity.value,
            current_value_cents=anomaly.current_value_cents,
            expected_value_cents=anomaly.expected_value_cents,
            entity_type=anomaly.entity_type,
            entity_id=anomaly.entity_id,
        )

        logger.info(f"[GOVERNANCE] Created cost incident {incident_id} from anomaly {anomaly.id}")

        return incident_id

    def _map_severity_to_incident_severity(self, severity: AnomalySeverity) -> str:
        """Map cost anomaly severity to incident severity."""
        mapping = {
            AnomalySeverity.LOW: "low",
            AnomalySeverity.MEDIUM: "medium",
            AnomalySeverity.HIGH: "high",
            AnomalySeverity.CRITICAL: "critical",
        }
        return mapping.get(severity, "medium")


# =============================================================================
# BRIDGE C2: COST PATTERN MATCHER
# =============================================================================


class CostPatternMatcher:
    """
    Bridge C2: Match cost anomalies to failure patterns.

    Cost patterns are categorized by:
    - Entity type (user, feature, model, tenant)
    - Anomaly type (spike, budget, unusual)
    - Severity threshold
    """

    # Pre-defined cost pattern signatures
    COST_PATTERN_SIGNATURES = {
        "user_daily_spike": {
            "entity_type": "user",
            "anomaly_type": "user_spike",
            "min_deviation_pct": 200,
            "description": "Single user daily spend spike > 200%",
        },
        "user_hourly_spike": {
            "entity_type": "user",
            "anomaly_type": "user_spike",
            "min_deviation_pct": 500,
            "time_window": "hourly",
            "description": "Single user hourly spend spike > 500%",
        },
        "feature_cost_explosion": {
            "entity_type": "feature",
            "anomaly_type": "feature_spike",
            "min_deviation_pct": 300,
            "description": "Feature cost increase > 300%",
        },
        "tenant_daily_spike": {
            "entity_type": "tenant",
            "anomaly_type": "tenant_spike",
            "min_deviation_pct": 200,
            "description": "Tenant-level daily spend spike > 200%",
        },
        "model_daily_spike": {
            "entity_type": "model",
            "anomaly_type": "model_spike",
            "min_deviation_pct": 200,
            "description": "Model usage cost spike > 200%",
        },
        "budget_breach": {
            "entity_type": "tenant",
            "anomaly_type": "budget_exceeded",
            "min_deviation_pct": 100,
            "description": "Tenant budget exceeded",
        },
        "model_cost_anomaly": {
            "entity_type": "model",
            "anomaly_type": "unusual_model",
            "min_deviation_pct": 200,
            "description": "Unusual expensive model usage",
        },
    }

    def __init__(self, db_session=None):
        self.db_session = db_session

    async def match_cost_pattern(
        self,
        anomaly: CostAnomaly,
        incident_id: str,
    ) -> PatternMatchResult:
        """Match anomaly to existing or new cost pattern."""

        # Build signature from anomaly
        signature = self._build_signature(anomaly)
        signature_hash = self._hash_signature(signature)

        # Try to find matching pre-defined pattern
        matched_pattern = self._find_predefined_match(anomaly)

        if matched_pattern:
            # Calculate confidence based on match quality
            confidence = self._calculate_confidence(anomaly, matched_pattern)
            pattern_id = f"pat_cost_{matched_pattern}"

            return PatternMatchResult.from_match(
                incident_id=incident_id,
                pattern_id=pattern_id,
                confidence=confidence,
                signature_hash=signature_hash,
                is_new=False,
                details={
                    "pattern_type": "cost",
                    "pattern_name": matched_pattern,
                    "signature": signature,
                },
            )

        # Create new pattern for novel anomaly
        pattern_id = f"pat_cost_{uuid.uuid4().hex[:12]}"

        return PatternMatchResult.from_match(
            incident_id=incident_id,
            pattern_id=pattern_id,
            confidence=0.6,  # Lower confidence for new patterns
            signature_hash=signature_hash,
            is_new=True,
            details={
                "pattern_type": "cost",
                "pattern_name": "novel_cost_pattern",
                "signature": signature,
            },
        )

    def _build_signature(self, anomaly: CostAnomaly) -> dict[str, Any]:
        """Build pattern signature from anomaly."""
        return {
            "entity_type": anomaly.entity_type,
            "anomaly_type": anomaly.anomaly_type.value,
            "deviation_range": self._deviation_bucket(anomaly.deviation_pct),
            "severity": anomaly.severity.value,
        }

    def _hash_signature(self, signature: dict[str, Any]) -> str:
        """Create hash of signature for matching."""
        import hashlib
        import json

        sig_str = json.dumps(signature, sort_keys=True)
        return hashlib.sha256(sig_str.encode()).hexdigest()[:16]

    def _deviation_bucket(self, pct: float) -> str:
        """Bucket deviation percentages for pattern matching."""
        if pct >= 500:
            return "extreme"  # 500%+
        elif pct >= 300:
            return "high"  # 300-500%
        elif pct >= 200:
            return "medium"  # 200-300%
        else:
            return "low"  # <200%

    def _find_predefined_match(self, anomaly: CostAnomaly) -> Optional[str]:
        """Find matching pre-defined pattern."""
        for pattern_name, pattern_def in self.COST_PATTERN_SIGNATURES.items():
            if (
                pattern_def["entity_type"] == anomaly.entity_type
                and pattern_def["anomaly_type"] == anomaly.anomaly_type.value
                and anomaly.deviation_pct >= pattern_def["min_deviation_pct"]
            ):
                return pattern_name
        return None

    def _calculate_confidence(self, anomaly: CostAnomaly, pattern_name: str) -> float:
        """Calculate match confidence based on pattern fit."""
        pattern_def = self.COST_PATTERN_SIGNATURES.get(pattern_name, {})
        min_deviation = pattern_def.get("min_deviation_pct", 100)

        # Higher confidence for stronger deviations
        deviation_ratio = anomaly.deviation_pct / min_deviation
        if deviation_ratio >= 2.0:
            return 0.90
        elif deviation_ratio >= 1.5:
            return 0.85
        elif deviation_ratio >= 1.0:
            return 0.75
        else:
            return 0.65


# =============================================================================
# BRIDGE C3: COST RECOVERY GENERATOR
# =============================================================================


class CostRecoveryGenerator:
    """
    Bridge C3: Generate recovery suggestions for cost anomalies.

    Recovery strategies by anomaly type:
    - USER_SPIKE → Rate limit, notify user, review usage
    - FEATURE_SPIKE → Optimize prompts, model downgrade, caching
    - BUDGET_EXCEEDED → Hard block, escalate, increase budget
    - UNUSUAL_MODEL → Route to cheaper model, review routing
    """

    RECOVERY_STRATEGIES: dict[str, list[dict[str, Any]]] = {
        "user_spike": [
            {
                "action": "rate_limit_user",
                "description": "Apply rate limit to user",
                "confidence": 0.9,
                "auto_apply": False,
                "params": {"requests_per_hour": 50, "duration_hours": 24},
            },
            {
                "action": "notify_user",
                "description": "Send cost alert notification to user",
                "confidence": 0.95,
                "auto_apply": True,
                "params": {"template": "cost_spike_alert"},
            },
            {
                "action": "review_usage",
                "description": "Flag for usage review",
                "confidence": 0.85,
                "auto_apply": True,
                "params": {},
            },
        ],
        "feature_spike": [
            {
                "action": "optimize_prompts",
                "description": "Reduce prompt size for this feature",
                "confidence": 0.7,
                "auto_apply": False,
                "params": {"max_prompt_tokens": 2000, "max_output_tokens": 1000},
            },
            {
                "action": "enable_caching",
                "description": "Enable response caching for feature",
                "confidence": 0.8,
                "auto_apply": False,
                "params": {"cache_ttl_seconds": 3600},
            },
            {
                "action": "model_downgrade",
                "description": "Route to cheaper model",
                "confidence": 0.75,
                "auto_apply": False,
                "params": {"target_model": "gpt-4o-mini", "fallback_threshold_cents": 50},
            },
        ],
        "budget_exceeded": [
            {
                "action": "enforce_hard_limit",
                "description": "Block requests exceeding budget",
                "confidence": 0.95,
                "auto_apply": False,
                "params": {},
            },
            {
                "action": "escalate_to_admin",
                "description": "Escalate to account admin",
                "confidence": 0.99,
                "auto_apply": True,
                "params": {"notification_channels": ["email"]},
            },
            {
                "action": "temporary_throttle",
                "description": "Throttle all requests by 50%",
                "confidence": 0.85,
                "auto_apply": False,
                "params": {"throttle_pct": 50, "duration_hours": 4},
            },
        ],
        "unusual_model": [
            {
                "action": "route_to_cheaper",
                "description": "Route to cost-optimized model",
                "confidence": 0.85,
                "auto_apply": False,
                "params": {"target_model": "gpt-4o-mini", "quality_threshold": 0.9},
            },
            {
                "action": "review_routing_rules",
                "description": "Flag routing configuration for review",
                "confidence": 0.9,
                "auto_apply": True,
                "params": {},
            },
        ],
        "budget_warning": [
            {
                "action": "notify_admin",
                "description": "Send budget warning to admin",
                "confidence": 0.95,
                "auto_apply": True,
                "params": {"template": "budget_warning"},
            }
        ],
        "rate_anomaly": [
            {
                "action": "temporary_rate_limit",
                "description": "Apply temporary rate limit",
                "confidence": 0.85,
                "auto_apply": False,
                "params": {"requests_per_minute": 10, "duration_minutes": 60},
            }
        ],
        "tenant_spike": [
            {
                "action": "notify_admin",
                "description": "Send tenant cost spike alert to admin",
                "confidence": 0.95,
                "auto_apply": True,
                "params": {"template": "tenant_cost_spike"},
            },
            {
                "action": "review_usage",
                "description": "Flag tenant for usage review",
                "confidence": 0.85,
                "auto_apply": True,
                "params": {},
            },
            {
                "action": "escalate_to_admin",
                "description": "Escalate to account admin",
                "confidence": 0.90,
                "auto_apply": False,
                "params": {"notification_channels": ["email", "slack"]},
            },
        ],
        "model_spike": [
            {
                "action": "review_model_usage",
                "description": "Review model usage patterns",
                "confidence": 0.85,
                "auto_apply": True,
                "params": {},
            },
            {
                "action": "route_to_cheaper",
                "description": "Route to more cost-effective model",
                "confidence": 0.80,
                "auto_apply": False,
                "params": {"target_model": "gpt-4o-mini"},
            },
        ],
    }

    def __init__(self, db_session=None):
        self.db_session = db_session

    async def generate_recovery(
        self,
        anomaly: CostAnomaly,
        pattern_result: PatternMatchResult,
        incident_id: str,
    ) -> list[RecoverySuggestion]:
        """Generate recovery suggestions for cost incident."""

        strategies = self.RECOVERY_STRATEGIES.get(anomaly.anomaly_type.value, [])

        suggestions = []
        for strategy in strategies:
            # Adjust confidence based on pattern match confidence
            adjusted_confidence = strategy["confidence"] * pattern_result.confidence

            # Calculate required confirmations based on confidence
            if adjusted_confidence >= 0.9:
                requires_confirmation = 0
            elif adjusted_confidence >= 0.7:
                requires_confirmation = 1
            else:
                requires_confirmation = 2

            suggestion = RecoverySuggestion.create(
                incident_id=incident_id,
                pattern_id=pattern_result.pattern_id,
                action_type=strategy["action"],
                action_params=strategy["params"],
                confidence=adjusted_confidence,
                suggestion_type="template",
                requires_confirmation=requires_confirmation,
            )

            # Override auto_applicable based on strategy definition
            suggestion.auto_applicable = (
                strategy["auto_apply"] and adjusted_confidence >= 0.9 and requires_confirmation == 0
            )

            suggestions.append(suggestion)

            logger.info(
                f"Generated recovery suggestion: {suggestion.action_type} "
                f"(confidence: {adjusted_confidence:.2f}, auto: {suggestion.auto_applicable})"
            )

        return suggestions


# =============================================================================
# BRIDGE C4: COST POLICY GENERATOR
# =============================================================================


class CostPolicyGenerator:
    """
    Bridge C4: Generate policies from cost recoveries.

    Policy categories:
    - operational: Rate limits, throttling
    - routing: Model selection, cost-aware routing
    - safety: Hard budget blocks
    """

    POLICY_TEMPLATES: dict[str, dict[str, Any]] = {
        "rate_limit_user": {
            "category": "operational",
            "condition_template": "user.id == '{entity_id}' AND user.requests_today > {requests_per_hour}",
            "action": "rate_limit",
            "description_template": "Rate limit user {entity_id} to {requests_per_hour} requests/hour",
        },
        "notify_user": {
            "category": "operational",
            "condition_template": "user.id == '{entity_id}' AND user.cost_anomaly_detected == true",
            "action": "notify",
            "action_params": {"channel": "email", "template": "cost_spike_alert"},
            "description_template": "Notify user {entity_id} about cost spike",
        },
        "review_usage": {
            "category": "operational",
            "condition_template": "user.id == '{entity_id}' AND user.needs_usage_review == true",
            "action": "flag_review",
            "action_params": {"review_type": "cost_usage"},
            "description_template": "Flag user {entity_id} for usage review",
        },
        "model_downgrade": {
            "category": "routing",
            "condition_template": "request.estimated_cost_cents > {fallback_threshold_cents}",
            "action": "route_to_model",
            "action_params": {"model": "gpt-4o-mini"},
            "description_template": "Route to gpt-4o-mini when cost > ${threshold}",
        },
        "enforce_hard_limit": {
            "category": "safety",
            "condition_template": "tenant.daily_spend_cents >= tenant.daily_budget_cents",
            "action": "block",
            "description_template": "Block requests when daily budget exceeded",
        },
        "temporary_throttle": {
            "category": "operational",
            "condition_template": "tenant.id == '{tenant_id}' AND NOW() < '{expires_at}'",
            "action": "throttle",
            "action_params": {"rate": 50},
            "description_template": "Throttle tenant {tenant_id} by {throttle_pct}%",
        },
        "optimize_prompts": {
            "category": "operational",
            "condition_template": "feature_tag == '{feature_tag}'",
            "action": "limit_tokens",
            "action_params": {"max_prompt": 2000, "max_output": 1000},
            "description_template": "Limit tokens for feature {feature_tag}",
        },
        "escalate_to_admin": {
            "category": "safety",
            "condition_template": "tenant.id == '{tenant_id}' AND incident.severity IN ('high', 'critical')",
            "action": "escalate",
            "action_params": {"channel": "slack", "priority": "high"},
            "description_template": "Escalate cost incident to admin for tenant {tenant_id}",
        },
        "notify_admin": {
            "category": "operational",
            "condition_template": "tenant.id == '{tenant_id}' AND tenant.cost_anomaly_detected == true",
            "action": "notify",
            "action_params": {"channel": "email", "template": "tenant_cost_spike", "recipients": ["admin"]},
            "description_template": "Notify admin about cost spike for tenant {tenant_id}",
        },
        "review_model_usage": {
            "category": "operational",
            "condition_template": "model.id == '{model_id}' AND model.needs_usage_review == true",
            "action": "flag_review",
            "action_params": {"review_type": "model_cost"},
            "description_template": "Flag model {model_id} for usage review",
        },
        "route_to_cheaper": {
            "category": "routing",
            "condition_template": "request.model == '{current_model}'",
            "action": "route_to_model",
            "action_params": {"model": "gpt-4o-mini"},
            "description_template": "Route from {current_model} to gpt-4o-mini",
        },
    }

    def __init__(self, db_session=None):
        self.db_session = db_session

    async def generate_policy(
        self,
        recovery: RecoverySuggestion,
        anomaly: CostAnomaly,
        pattern_result: PatternMatchResult,
    ) -> Optional[PolicyRule]:
        """Generate policy from applied recovery."""

        template = self.POLICY_TEMPLATES.get(recovery.action_type)
        if not template:
            logger.warning(f"No policy template for action: {recovery.action_type}")
            return None

        # Build context for template substitution
        context = {
            **recovery.action_params,
            "entity_id": anomaly.entity_id,
            "tenant_id": anomaly.tenant_id,
            "threshold": recovery.action_params.get("fallback_threshold_cents", 0) / 100,
            "feature_tag": anomaly.metadata.get("feature_tag", "unknown"),
            "throttle_pct": recovery.action_params.get("throttle_pct", 50),
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(hours=recovery.action_params.get("duration_hours", 24))
            ).isoformat(),
        }

        # Generate condition string
        try:
            condition = template["condition_template"].format(**context)
            description = template["description_template"].format(**context)
        except KeyError as e:
            logger.warning(f"Missing context key for policy template: {e}")
            condition = template["condition_template"]
            description = f"Cost policy: {recovery.action_type}"

        # Calculate confirmations based on category
        confirmations = {
            "safety": 3,  # Safety policies need more review
            "routing": 2,  # Routing changes need review
            "operational": 1,  # Operational changes need minimal review
        }

        policy = PolicyRule.create(
            name=f"Cost Policy: {recovery.action_type}",
            description=description,
            category=template["category"],
            condition=condition,
            action=template["action"],
            source_pattern_id=pattern_result.pattern_id,
            source_recovery_id=recovery.recovery_id,
            confidence=recovery.confidence,
            scope_type="tenant",
            scope_id=anomaly.tenant_id,
            confirmations_required=confirmations.get(template["category"], 2),
        )

        logger.info(
            f"Generated cost policy: {policy.policy_id} (category: {policy.category}, mode: {policy.mode.value})"
        )

        return policy


# =============================================================================
# BRIDGE C5: COST ROUTING ADJUSTER
# =============================================================================


class CostRoutingAdjuster:
    """
    Bridge C5: Adjust CARE routing based on cost policies.

    Routing adjustments:
    - Add cost estimation probe before execution
    - Route expensive requests to cheaper models
    - Add budget-check middleware
    - Adjust agent confidence based on cost efficiency
    """

    def __init__(self, db_session=None):
        self.db_session = db_session

    async def on_cost_policy_created(
        self,
        policy: PolicyRule,
    ) -> list[RoutingAdjustment]:
        """Adjust CARE routing based on new cost policy."""

        adjustments = []

        if policy.action == "route_to_model":
            adjustment = self._create_model_routing_adjustment(policy)
            adjustments.append(adjustment)

        elif policy.action == "rate_limit":
            adjustment = self._create_rate_limit_adjustment(policy)
            adjustments.append(adjustment)

        elif policy.action == "block":
            adjustment = self._create_budget_block_adjustment(policy)
            adjustments.append(adjustment)

        elif policy.action == "limit_tokens":
            adjustment = self._create_token_limit_adjustment(policy)
            adjustments.append(adjustment)

        elif policy.action == "throttle":
            adjustment = self._create_throttle_adjustment(policy)
            adjustments.append(adjustment)

        elif policy.action == "notify":
            adjustment = self._create_notify_adjustment(policy)
            adjustments.append(adjustment)

        elif policy.action == "flag_review":
            adjustment = self._create_review_adjustment(policy)
            adjustments.append(adjustment)

        elif policy.action == "escalate":
            adjustment = self._create_escalation_adjustment(policy)
            adjustments.append(adjustment)

        for adj in adjustments:
            logger.info(
                f"Created routing adjustment: {adj.adjustment_id} "
                f"(type: {adj.adjustment_type}, magnitude: {adj.magnitude})"
            )

        return adjustments

    def _create_model_routing_adjustment(self, policy: PolicyRule) -> RoutingAdjustment:
        """Create cost-based model routing adjustment."""
        return RoutingAdjustment.create(
            agent_id="*",  # Apply to all agents
            adjustment_type="route_block",
            magnitude=-0.3,  # Reduce confidence for expensive model routing
            reason=f"Cost policy: Route to cheaper model ({policy.description})",
            source_policy_id=policy.policy_id,
            capability="expensive_model",
            max_delta=0.3,
            decay_days=14,
        )

    def _create_rate_limit_adjustment(self, policy: PolicyRule) -> RoutingAdjustment:
        """Create rate limiting adjustment."""
        return RoutingAdjustment.create(
            agent_id="*",
            adjustment_type="confidence_penalty",
            magnitude=-0.2,
            reason=f"Cost policy: Rate limit ({policy.description})",
            source_policy_id=policy.policy_id,
            max_delta=0.2,
            decay_days=7,
        )

    def _create_budget_block_adjustment(self, policy: PolicyRule) -> RoutingAdjustment:
        """Create budget blocking adjustment (highest priority)."""
        return RoutingAdjustment.create(
            agent_id="*",
            adjustment_type="route_block",
            magnitude=-1.0,  # Full block
            reason=f"Cost policy: Budget block ({policy.description})",
            source_policy_id=policy.policy_id,
            max_delta=1.0,  # Allow full block for safety
            decay_days=0,  # No decay for budget blocks
        )

    def _create_token_limit_adjustment(self, policy: PolicyRule) -> RoutingAdjustment:
        """Create token limiting adjustment."""
        return RoutingAdjustment.create(
            agent_id="*",
            adjustment_type="weight_shift",
            magnitude=-0.15,
            reason=f"Cost policy: Token limit ({policy.description})",
            source_policy_id=policy.policy_id,
            max_delta=0.2,
            decay_days=7,
        )

    def _create_throttle_adjustment(self, policy: PolicyRule) -> RoutingAdjustment:
        """Create throttling adjustment."""
        return RoutingAdjustment.create(
            agent_id="*",
            adjustment_type="confidence_penalty",
            magnitude=-0.5,  # Significant penalty for throttled tenants
            reason=f"Cost policy: Throttle ({policy.description})",
            source_policy_id=policy.policy_id,
            max_delta=0.5,
            decay_days=1,  # Short decay for temporary throttle
        )

    def _create_notify_adjustment(self, policy: PolicyRule) -> RoutingAdjustment:
        """Create notification adjustment (minimal routing impact)."""
        return RoutingAdjustment.create(
            agent_id="*",
            adjustment_type="metadata_only",
            magnitude=0.0,  # No routing impact, just records the action
            reason=f"Cost policy: Notify user ({policy.description})",
            source_policy_id=policy.policy_id,
            max_delta=0.0,
            decay_days=0,  # Immediate, no decay
        )

    def _create_review_adjustment(self, policy: PolicyRule) -> RoutingAdjustment:
        """Create review flag adjustment (minimal routing impact)."""
        return RoutingAdjustment.create(
            agent_id="*",
            adjustment_type="metadata_only",
            magnitude=0.0,  # No routing impact, just flags for review
            reason=f"Cost policy: Flag for review ({policy.description})",
            source_policy_id=policy.policy_id,
            max_delta=0.0,
            decay_days=0,
        )

    def _create_escalation_adjustment(self, policy: PolicyRule) -> RoutingAdjustment:
        """Create escalation adjustment (pause + notify admin)."""
        return RoutingAdjustment.create(
            agent_id="*",
            adjustment_type="confidence_penalty",
            magnitude=-0.3,  # Moderate penalty while escalation is pending
            reason=f"Cost policy: Escalated to admin ({policy.description})",
            source_policy_id=policy.policy_id,
            max_delta=0.3,
            decay_days=7,  # Longer decay for escalations
        )


# =============================================================================
# COST ESTIMATION PROBE (CARE Integration)
# =============================================================================


class CostEstimationProbe:
    """
    CARE probe that estimates request cost before execution.

    Used to:
    1. Route to cheaper models if estimate exceeds threshold
    2. Block requests that would exceed budget
    3. Warn users about expensive operations
    """

    # Cost per 1K tokens by model (in cents)
    MODEL_COSTS: dict[str, dict[str, float]] = {
        "claude-opus-4-5-20251101": {"input": 1.5, "output": 7.5},
        "claude-sonnet-4-20250514": {"input": 0.3, "output": 1.5},
        "claude-3-5-haiku-20241022": {"input": 0.08, "output": 0.4},
        "gpt-4o": {"input": 0.5, "output": 1.5},
        "gpt-4o-mini": {"input": 0.015, "output": 0.06},
    }

    def __init__(self, db_session=None):
        self.db_session = db_session

    async def probe(
        self,
        model: str,
        prompt_tokens: int,
        expected_output_tokens: int,
        tenant_id: str,
        cost_threshold_cents: int = 100,
    ) -> dict[str, Any]:
        """
        Estimate cost and return routing decision.

        Returns:
            {
                "status": "allowed" | "reroute" | "blocked",
                "estimated_cost_cents": int,
                "reason": str,
                "suggested_model": str | None,
            }
        """
        cost_cents = self._calculate_cost(model, prompt_tokens, expected_output_tokens)

        # Check if would exceed budget (placeholder - would check DB in production)
        if cost_cents > 1000:  # $10 threshold for blocking
            return {
                "status": "blocked",
                "estimated_cost_cents": cost_cents,
                "reason": f"Request would exceed budget (${cost_cents / 100:.2f})",
                "suggested_model": None,
            }

        # Check if should route to cheaper model
        if cost_cents > cost_threshold_cents:
            cheaper = self._find_cheaper_model(model, prompt_tokens, expected_output_tokens)
            if cheaper:
                return {
                    "status": "reroute",
                    "estimated_cost_cents": cost_cents,
                    "reason": f"Routing to {cheaper['model']} to save ${(cost_cents - cheaper['cost']) / 100:.2f}",
                    "suggested_model": cheaper["model"],
                    "optimized_cost_cents": cheaper["cost"],
                }

        return {
            "status": "allowed",
            "estimated_cost_cents": cost_cents,
            "reason": "Within budget",
            "suggested_model": None,
        }

    def _calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        output_tokens: int,
    ) -> int:
        """Calculate cost in cents."""
        costs = self.MODEL_COSTS.get(model, {"input": 1.0, "output": 5.0})
        return int((prompt_tokens / 1000 * costs["input"]) + (output_tokens / 1000 * costs["output"]))

    def _find_cheaper_model(
        self,
        current_model: str,
        prompt_tokens: int,
        output_tokens: int,
    ) -> Optional[dict[str, Any]]:
        """Find a cheaper model that can handle the request."""
        current_cost = self._calculate_cost(current_model, prompt_tokens, output_tokens)

        # Models ranked by cost efficiency (cheapest first)
        cheaper_models = ["gpt-4o-mini", "claude-3-5-haiku-20241022"]

        for model in cheaper_models:
            if model == current_model:
                continue

            model_cost = self._calculate_cost(model, prompt_tokens, output_tokens)
            if model_cost < current_cost:
                return {
                    "model": model,
                    "cost": model_cost,
                    "savings": current_cost - model_cost,
                }

        return None


# =============================================================================
# ORCHESTRATOR: Full Cost Loop
# =============================================================================


class CostLoopOrchestrator:
    """
    Orchestrates the full M27 cost loop:
    Anomaly → Incident → Pattern → Recovery → Policy → Routing

    MANDATORY GOVERNANCE: Incident creation is not optional.
    If db_session is missing, initialization fails.
    """

    def __init__(self, db_session):
        """
        Initialize orchestrator with database session.

        Args:
            db_session: Database session for governance operations (REQUIRED)
        """
        if db_session is None:
            raise ValueError("db_session is required for CostLoopOrchestrator - governance is not optional")
        self.db_session = db_session

        # Initialize bridges
        self.bridge_c1 = CostLoopBridge(db_session)
        self.bridge_c2 = CostPatternMatcher(db_session)
        self.bridge_c3 = CostRecoveryGenerator(db_session)
        self.bridge_c4 = CostPolicyGenerator(db_session)
        self.bridge_c5 = CostRoutingAdjuster(db_session)

    async def process_anomaly(self, anomaly: CostAnomaly) -> dict[str, Any]:
        """
        Process a cost anomaly through the full loop.

        MANDATORY GOVERNANCE: HIGH+ anomalies create incidents or raise GovernanceError.

        Returns loop status with all artifacts.

        Raises:
            GovernanceError: If incident creation fails (mandatory)
        """
        results: dict[str, Any] = {
            "anomaly_id": anomaly.id,
            "stages_completed": [],
            "artifacts": {},
        }

        # C1: Anomaly → Incident (MANDATORY GOVERNANCE - sync, not async)
        incident_id = self.bridge_c1.on_anomaly_detected(anomaly)
        if not incident_id:
            results["status"] = "skipped"
            results["reason"] = f"Severity {anomaly.severity.value} below threshold"
            return results

        results["incident_id"] = incident_id
        results["stages_completed"].append("incident_created")

        # C2: Incident → Pattern
        pattern_result = await self.bridge_c2.match_cost_pattern(anomaly, incident_id)
        results["artifacts"]["pattern"] = pattern_result.to_dict()
        results["stages_completed"].append("pattern_matched")

        # C3: Pattern → Recovery
        recoveries = await self.bridge_c3.generate_recovery(anomaly, pattern_result, incident_id)
        results["artifacts"]["recoveries"] = [r.to_dict() for r in recoveries]
        results["stages_completed"].append("recovery_suggested")

        # C4: Recovery → Policy (use highest confidence recovery)
        if recoveries:
            best_recovery = max(recoveries, key=lambda r: r.confidence)
            policy = await self.bridge_c4.generate_policy(best_recovery, anomaly, pattern_result)
            if policy:
                results["artifacts"]["policy"] = policy.to_dict()
                results["stages_completed"].append("policy_generated")

                # C5: Policy → Routing
                adjustments = await self.bridge_c5.on_cost_policy_created(policy)
                results["artifacts"]["adjustments"] = [a.to_dict() for a in adjustments]
                results["stages_completed"].append("routing_adjusted")

        results["status"] = "complete" if len(results["stages_completed"]) == 5 else "partial"
        return results
