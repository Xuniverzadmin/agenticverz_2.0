# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Role: Policy rule evaluation engine
# Callers: API routes, workers, services
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: Policy System

# M19 Policy Engine
# Constitutional governance for multi-agent systems
#
# This is the core Policy Engine that every agent and subsystem
# (CARE-L, SBA) must consult before:
# - deciding
# - routing
# - executing
# - escalating
# - self-modifying
#
# The Policy Engine is the "Constitution" of the multi-agent ecosystem.

from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple
from uuid import uuid4

if TYPE_CHECKING:
    from app.policy.models import RecoverabilityType, ViolationSeverity

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.policy.models import (
    ActionType,
    BusinessRule,
    BusinessRuleType,
    EthicalConstraint,
    EthicalConstraintType,
    Policy,
    PolicyCategory,
    PolicyDecision,
    PolicyEvaluationRequest,
    PolicyEvaluationResult,
    PolicyLoadResult,
    PolicyModification,
    PolicyRule,
    PolicyState,
    PolicyViolation,
    RiskCeiling,
    SafetyRule,
    SafetyRuleType,
    ViolationType,
)

logger = logging.getLogger("nova.policy.engine")

# Phase 4B: Decision Record Emission (DECISION_RECORD_CONTRACT v0.2)
from app.contracts.decisions import emit_policy_decision

# =============================================================================
# Configuration
# =============================================================================

# Policy signing secret (should come from Vault in production)
POLICY_SIGNING_SECRET = os.environ.get("POLICY_SIGNING_SECRET", "default-policy-secret")

# Evaluation settings
MAX_EVALUATION_TIME_MS = 100  # Evaluation should be fast
CACHE_TTL_SECONDS = 300  # Policy cache TTL

# Default risk ceilings
DEFAULT_COST_CEILING_PER_HOUR = 100.0
DEFAULT_RETRY_CEILING_PER_MINUTE = 30
DEFAULT_CASCADE_DEPTH = 5
DEFAULT_CONCURRENT_AGENTS = 50


# =============================================================================
# Policy Engine
# =============================================================================


class PolicyEngine:
    """
    M19 Policy Engine - Constitutional Governance Layer.

    Every agent decision must go through policy.evaluate() before execution.

    Responsibilities:
    - Enforce compliance rules
    - Enforce ethical constraints
    - Enforce risk ceilings
    - Enforce safety rules
    - Enforce business rules
    - Route violations to M18 Governor
    - Audit all evaluations
    """

    def __init__(self, database_url: Optional[str] = None, governor=None):
        # Use database_url if provided (even if empty), otherwise fall back to env var
        self._db_url = database_url if database_url is not None else os.environ.get("DATABASE_URL")
        self._governor = governor  # M18 Governor for violation routing

        # In-memory policy cache
        self._policies: List[Policy] = []
        self._risk_ceilings: List[RiskCeiling] = []
        self._safety_rules: List[SafetyRule] = []
        self._ethical_constraints: List[EthicalConstraint] = []
        self._business_rules: List[BusinessRule] = []

        # Cache metadata
        self._cache_loaded_at: Optional[datetime] = None
        self._policy_version: str = "1.0.0"

        # Metrics
        self._evaluations_count = 0
        self._violations_count = 0
        self._blocks_count = 0
        self._modifies_count = 0

        # Risk ceiling tracking (in-memory, should use Redis in prod)
        self._risk_values: Dict[str, float] = {}
        self._risk_windows: Dict[str, List[Tuple[datetime, float]]] = {}

        # Cooldown tracking
        self._cooldowns: Dict[str, datetime] = {}  # agent_id -> cooldown_until

    # =========================================================================
    # Core Evaluation
    # =========================================================================

    async def evaluate(
        self, request: PolicyEvaluationRequest, db=None, dry_run: bool = False
    ) -> PolicyEvaluationResult:
        """
        Evaluate a request against all applicable policies.

        This is the central evaluation point that every agent action
        must pass through.

        Args:
            request: The policy evaluation request
            db: Optional database session (for consistency with API)
            dry_run: If True, don't persist results or trigger side effects

        Returns:
            PolicyEvaluationResult with decision (ALLOW, BLOCK, MODIFY)
        """
        start_time = time.time()
        if not dry_run:
            self._evaluations_count += 1

        # Ensure policies are loaded
        if not self._cache_loaded_at or self._is_cache_stale():
            await self._load_policies()

        violations: List[PolicyViolation] = []
        modifications: List[PolicyModification] = []
        rules_matched: List[str] = []
        policies_evaluated = 0

        # 1. Check cooldowns first (fast path)
        cooldown_violation = self._check_cooldown(request)
        if cooldown_violation:
            violations.append(cooldown_violation)

        # 2. Check ethical constraints (non-negotiables)
        ethical_violations = await self._check_ethical_constraints(request)
        violations.extend(ethical_violations)
        if ethical_violations:
            rules_matched.extend([f"ethical:{v.policy_name}" for v in ethical_violations])

        # 3. Check safety rules (hard stops)
        safety_violations = await self._check_safety_rules(request)
        violations.extend(safety_violations)
        if safety_violations:
            rules_matched.extend([f"safety:{v.policy_name}" for v in safety_violations])

        # 4. Check risk ceilings (dynamic limits)
        risk_violations, risk_mods = await self._check_risk_ceilings(request)
        violations.extend(risk_violations)
        modifications.extend(risk_mods)
        if risk_violations:
            rules_matched.extend([f"risk:{v.policy_name}" for v in risk_violations])

        # 5. Check compliance policies
        compliance_violations = await self._check_compliance(request)
        violations.extend(compliance_violations)
        if compliance_violations:
            rules_matched.extend([f"compliance:{v.policy_name}" for v in compliance_violations])

        # 6. Check business rules
        business_violations, business_mods = await self._check_business_rules(request)
        violations.extend(business_violations)
        modifications.extend(business_mods)
        if business_violations:
            rules_matched.extend([f"business:{v.policy_name}" for v in business_violations])

        # Count policies evaluated
        policies_evaluated = (
            len(self._ethical_constraints)
            + len(self._safety_rules)
            + len(self._risk_ceilings)
            + len(self._policies)
            + len(self._business_rules)
        )

        # Determine final decision
        decision = PolicyDecision.ALLOW
        decision_reason = None

        if violations:
            # Check if any violations are blocking
            blocking_violations = [v for v in violations if v.severity >= 0.5]
            if blocking_violations:
                decision = PolicyDecision.BLOCK
                decision_reason = "; ".join(v.description for v in blocking_violations[:3])
                if not dry_run:
                    self._blocks_count += 1
                    self._violations_count += len(violations)

                    # Route to Governor
                    await self._route_to_governor(violations)
            else:
                # Non-blocking violations, but still track
                decision = PolicyDecision.ALLOW
                decision_reason = f"Allowed with {len(violations)} low-severity warnings"

        elif modifications:
            decision = PolicyDecision.MODIFY
            decision_reason = f"Modified {len(modifications)} parameters"
            if not dry_run:
                self._modifies_count += 1

        # Calculate evaluation time
        evaluation_ms = (time.time() - start_time) * 1000

        # Build result
        result = PolicyEvaluationResult(
            request_id=request.request_id,
            decision=decision,
            decision_reason=decision_reason,
            policies_evaluated=policies_evaluated,
            rules_matched=rules_matched,
            evaluation_ms=evaluation_ms,
            modifications=modifications,
            violations=violations,
            policy_version=self._policy_version,
        )

        # Persist evaluation (skip in dry_run mode)
        if not dry_run:
            await self._persist_evaluation(request, result)

        # Log
        logger.info(
            "policy_evaluation",
            extra={
                "request_id": request.request_id,
                "action_type": request.action_type.value,
                "decision": decision.value,
                "policies_evaluated": policies_evaluated,
                "violations": len(violations),
                "evaluation_ms": evaluation_ms,
            },
        )

        # Phase 4B: Emit policy decision record (DECISION_RECORD_CONTRACT v0.2)
        # Rule: Emit records where decisions already happen. No logic changes.
        if not dry_run:
            # Determine severity from violations (highest severity wins)
            severity = "info"
            if violations:
                max_sev = max(v.severity for v in violations)
                if max_sev >= 0.5:
                    severity = "error"
                elif max_sev >= 0.3:
                    severity = "warning"

            emit_policy_decision(
                run_id=None,  # Policy evaluated before run assignment
                policy_id=f"evaluation:{request.request_id}",
                evaluated=True,
                violated=decision == PolicyDecision.BLOCK,
                severity=severity,
                reason=decision_reason,
                tenant_id=request.tenant_id or "default",
            )

        return result

    # =========================================================================
    # Phase 5B: Pre-Check for Run Creation
    # =========================================================================

    async def pre_check(
        self,
        request_id: str,
        agent_id: str,
        goal: str,
        tenant_id: str = "default",
    ) -> Dict[str, Any]:
        """
        Pre-check policy constraints before run creation.

        Phase 5B: This is a simplified check that returns one of three states:
        - passed: Policy allows execution
        - failed: Policy blocks execution (violations found)
        - unavailable: Policy service is not available

        This is NOT a full evaluation. It checks minimum viability only.
        No side effects. No decision emission (that happens in caller).

        Returns:
            {
                "passed": bool,
                "violations": List[str],
                "service_available": bool
            }
        """
        try:
            # Check if policies can be loaded
            if not self._cache_loaded_at or self._is_cache_stale():
                try:
                    await self._load_policies()
                except Exception as e:
                    logger.warning(f"Policy load failed during pre_check: {e}")
                    return {
                        "passed": False,
                        "violations": [],
                        "service_available": False,
                    }

            # If no policies loaded, service is effectively unavailable
            if not self._policies and not self._ethical_constraints and not self._safety_rules:
                # Service available but no policies = allow
                return {
                    "passed": True,
                    "violations": [],
                    "service_available": True,
                }

            # Create a minimal evaluation request
            from app.policy.models import ActionType, PolicyEvaluationRequest

            eval_request = PolicyEvaluationRequest(
                request_id=request_id,
                action_type=ActionType.EXECUTE,
                agent_id=agent_id,
                tenant_id=tenant_id,
                proposed_action=goal,
            )

            # Run dry evaluation (no persistence, no side effects)
            result = await self.evaluate(eval_request, dry_run=True)

            # Extract violations
            violations = []
            if result.violations:
                violations = [v.description for v in result.violations]

            # Determine pass/fail based on decision
            passed = result.decision != PolicyDecision.BLOCK

            return {
                "passed": passed,
                "violations": violations,
                "service_available": True,
            }

        except Exception as e:
            logger.error(f"Pre-check failed with error: {e}", exc_info=True)
            return {
                "passed": False,
                "violations": [],
                "service_available": False,
            }

    # =========================================================================
    # Ethical Constraints (Non-Negotiables)
    # =========================================================================

    async def _check_ethical_constraints(self, request: PolicyEvaluationRequest) -> List[PolicyViolation]:
        """Check request against ethical constraints."""
        violations = []

        for constraint in self._ethical_constraints:
            if not constraint.is_active:
                continue

            violation = self._evaluate_ethical_constraint(constraint, request)
            if violation:
                violations.append(violation)

        return violations

    def _evaluate_ethical_constraint(
        self, constraint: EthicalConstraint, request: PolicyEvaluationRequest
    ) -> Optional[PolicyViolation]:
        """Evaluate a single ethical constraint."""

        # Get text content to analyze
        text_content = self._extract_text_content(request)

        # Check forbidden patterns
        if constraint.forbidden_patterns:
            for pattern in constraint.forbidden_patterns:
                if pattern.lower() in text_content.lower():
                    return PolicyViolation(
                        violation_type=ViolationType.ETHICAL_VIOLATION,
                        policy_name=constraint.name,
                        severity=1.0,  # Ethical violations are always severe
                        description=f"Forbidden pattern detected: {pattern}",
                        evidence={
                            "pattern": pattern,
                            "constraint_type": constraint.constraint_type.value,
                        },
                        agent_id=request.agent_id,
                        tenant_id=request.tenant_id,
                        action_attempted=request.proposed_action,
                    )

        # Check transparency threshold
        if constraint.constraint_type == EthicalConstraintType.TRANSPARENCY:
            if constraint.transparency_threshold:
                explainability = request.context.get("explainability_score", 1.0)
                if explainability < constraint.transparency_threshold:
                    return PolicyViolation(
                        violation_type=ViolationType.ETHICAL_VIOLATION,
                        policy_name=constraint.name,
                        severity=0.8,
                        description=f"Decision not sufficiently explainable: {explainability:.2f} < {constraint.transparency_threshold}",
                        evidence={
                            "explainability_score": explainability,
                            "threshold": constraint.transparency_threshold,
                        },
                        agent_id=request.agent_id,
                        tenant_id=request.tenant_id,
                    )

        return None

    def _extract_text_content(self, request: PolicyEvaluationRequest) -> str:
        """Extract text content from request for analysis."""
        parts = []

        if request.proposed_action:
            parts.append(request.proposed_action)

        if request.context:
            # Extract text from context
            for key in ["task", "prompt", "input", "message", "query"]:
                if key in request.context:
                    parts.append(str(request.context[key]))

        if request.proposed_modification:
            parts.append(json.dumps(request.proposed_modification))

        return " ".join(parts)

    # =========================================================================
    # Safety Rules (Hard Stops)
    # =========================================================================

    async def _check_safety_rules(self, request: PolicyEvaluationRequest) -> List[PolicyViolation]:
        """Check request against safety rules."""
        violations = []

        # Sort by priority (lower = higher priority)
        sorted_rules = sorted(self._safety_rules, key=lambda r: r.priority)

        for rule in sorted_rules:
            if not rule.is_active:
                continue

            # Check applicability
            if rule.tenant_id and rule.tenant_id != request.tenant_id:
                continue
            if rule.applies_to and request.agent_id:
                # Check if agent type matches
                agent_type = request.context.get("agent_type")
                if agent_type and agent_type not in rule.applies_to:
                    continue

            violation = self._evaluate_safety_rule(rule, request)
            if violation:
                violations.append(violation)

                # Update triggered count
                rule.triggered_count += 1
                rule.last_triggered_at = datetime.now(timezone.utc)

        return violations

    def _evaluate_safety_rule(self, rule: SafetyRule, request: PolicyEvaluationRequest) -> Optional[PolicyViolation]:
        """Evaluate a single safety rule."""
        condition = rule.condition

        # Action block
        if rule.rule_type == SafetyRuleType.ACTION_BLOCK:
            blocked_actions = condition.get("actions", [])
            proposed = request.proposed_action or ""
            for blocked in blocked_actions:
                if blocked.lower() in proposed.lower():
                    return PolicyViolation(
                        violation_type=ViolationType.SAFETY_RULE_TRIGGERED,
                        policy_name=rule.name,
                        severity=1.0,
                        description=f"Blocked action: {blocked}",
                        evidence={"blocked_action": blocked, "proposed": proposed},
                        agent_id=request.agent_id,
                        tenant_id=request.tenant_id,
                        action_attempted=proposed,
                    )

        # Pattern block
        elif rule.rule_type == SafetyRuleType.PATTERN_BLOCK:
            patterns = condition.get("patterns", [])
            text_content = self._extract_text_content(request)
            for pattern in patterns:
                if re.search(pattern, text_content, re.IGNORECASE):
                    return PolicyViolation(
                        violation_type=ViolationType.SAFETY_RULE_TRIGGERED,
                        policy_name=rule.name,
                        severity=1.0,
                        description=f"Blocked pattern detected: {pattern}",
                        evidence={"pattern": pattern},
                        agent_id=request.agent_id,
                        tenant_id=request.tenant_id,
                    )

        # Escalation required
        elif rule.rule_type == SafetyRuleType.ESCALATION_REQUIRED:
            cost_threshold = condition.get("cost_threshold")
            if cost_threshold and request.estimated_cost:
                if request.estimated_cost >= cost_threshold:
                    return PolicyViolation(
                        violation_type=ViolationType.SAFETY_RULE_TRIGGERED,
                        policy_name=rule.name,
                        severity=0.7,  # Not blocking, but requires escalation
                        description=f"Human escalation required: cost ${request.estimated_cost} >= ${cost_threshold}",
                        evidence={
                            "estimated_cost": request.estimated_cost,
                            "threshold": cost_threshold,
                            "action": "escalate",
                        },
                        agent_id=request.agent_id,
                        tenant_id=request.tenant_id,
                    )

        # Cooldown
        elif rule.rule_type == SafetyRuleType.COOLDOWN:
            failure_count = condition.get("failure_count", 5)
            window_seconds = condition.get("window_seconds", 60)

            # Check recent failures for this agent
            recent_failures = request.context.get("recent_failures", 0)
            if recent_failures >= failure_count:
                # Set cooldown
                if rule.cooldown_seconds:
                    cooldown_key = f"{request.agent_id}:{rule.name}"
                    self._cooldowns[cooldown_key] = datetime.now(timezone.utc) + timedelta(
                        seconds=rule.cooldown_seconds
                    )

                return PolicyViolation(
                    violation_type=ViolationType.SAFETY_RULE_TRIGGERED,
                    policy_name=rule.name,
                    severity=0.8,
                    description=f"Cooldown enforced: {recent_failures} failures in {window_seconds}s",
                    evidence={
                        "recent_failures": recent_failures,
                        "threshold": failure_count,
                        "cooldown_seconds": rule.cooldown_seconds,
                    },
                    agent_id=request.agent_id,
                    tenant_id=request.tenant_id,
                )

        return None

    def _check_cooldown(self, request: PolicyEvaluationRequest) -> Optional[PolicyViolation]:
        """Check if agent is in cooldown."""
        if not request.agent_id:
            return None

        now = datetime.now(timezone.utc)

        for cooldown_key, cooldown_until in list(self._cooldowns.items()):
            if request.agent_id in cooldown_key:
                if now < cooldown_until:
                    return PolicyViolation(
                        violation_type=ViolationType.SAFETY_RULE_TRIGGERED,
                        policy_name="cooldown",
                        severity=1.0,
                        description=f"Agent in cooldown until {cooldown_until.isoformat()}",
                        evidence={
                            "cooldown_until": cooldown_until.isoformat(),
                            "remaining_seconds": (cooldown_until - now).total_seconds(),
                        },
                        agent_id=request.agent_id,
                        tenant_id=request.tenant_id,
                    )
                else:
                    # Cooldown expired, remove it
                    del self._cooldowns[cooldown_key]

        return None

    # =========================================================================
    # Risk Ceilings (Dynamic Limits)
    # =========================================================================

    async def _check_risk_ceilings(
        self, request: PolicyEvaluationRequest
    ) -> Tuple[List[PolicyViolation], List[PolicyModification]]:
        """Check request against risk ceilings."""
        violations = []
        modifications = []

        for ceiling in self._risk_ceilings:
            if not ceiling.is_active:
                continue

            # Check applicability
            if ceiling.tenant_id and ceiling.tenant_id != request.tenant_id:
                continue

            violation, modification = self._evaluate_risk_ceiling(ceiling, request)
            if violation:
                violations.append(violation)
                ceiling.breach_count += 1
                ceiling.last_breach_at = datetime.now(timezone.utc)
            if modification:
                modifications.append(modification)

        return violations, modifications

    def _evaluate_risk_ceiling(
        self, ceiling: RiskCeiling, request: PolicyEvaluationRequest
    ) -> Tuple[Optional[PolicyViolation], Optional[PolicyModification]]:
        """Evaluate a single risk ceiling."""

        current_value = 0.0

        # Get metric value based on type
        if ceiling.metric == "cost_per_hour":
            # Accumulate cost tracking
            key = f"{ceiling.name}:{request.tenant_id or 'global'}"
            current_value = self._get_windowed_value(key, ceiling.window_seconds)
            if request.estimated_cost:
                self._add_windowed_value(key, request.estimated_cost)
                current_value += request.estimated_cost

        elif ceiling.metric == "retries_per_minute":
            retry_count = request.context.get("retry_count", 0)
            current_value = retry_count

        elif ceiling.metric == "cascade_depth":
            cascade_depth = request.context.get("cascade_depth", 0)
            current_value = cascade_depth

        elif ceiling.metric == "concurrent_agents":
            concurrent = request.context.get("concurrent_agents", 0)
            current_value = concurrent

        # Check if ceiling is breached
        if current_value > ceiling.max_value:
            if ceiling.breach_action == "block":
                return PolicyViolation(
                    violation_type=ViolationType.RISK_CEILING_BREACH,
                    policy_name=ceiling.name,
                    severity=0.9,
                    description=f"Risk ceiling breached: {ceiling.metric} = {current_value} > {ceiling.max_value}",
                    evidence={
                        "metric": ceiling.metric,
                        "current_value": current_value,
                        "max_value": ceiling.max_value,
                    },
                    agent_id=request.agent_id,
                    tenant_id=request.tenant_id,
                ), None

            elif ceiling.breach_action == "throttle":
                # Allow but modify to reduce impact
                return None, PolicyModification(
                    parameter="throttle_factor",
                    original_value=1.0,
                    modified_value=ceiling.max_value / current_value,
                    reason=f"Throttled due to {ceiling.name} ceiling",
                )

            elif ceiling.breach_action == "alert":
                # Allow but log warning
                logger.warning(
                    f"Risk ceiling alert: {ceiling.name}",
                    extra={
                        "metric": ceiling.metric,
                        "current_value": current_value,
                        "max_value": ceiling.max_value,
                    },
                )

        # Update current value
        ceiling.current_value = current_value

        return None, None

    def _get_windowed_value(self, key: str, window_seconds: int) -> float:
        """Get accumulated value within time window."""
        if key not in self._risk_windows:
            return 0.0

        window_start = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
        values = self._risk_windows[key]

        # Filter to window
        values = [(t, v) for t, v in values if t >= window_start]
        self._risk_windows[key] = values

        return sum(v for _, v in values)

    def _add_windowed_value(self, key: str, value: float) -> None:
        """Add value to windowed tracking."""
        if key not in self._risk_windows:
            self._risk_windows[key] = []

        self._risk_windows[key].append((datetime.now(timezone.utc), value))

    # =========================================================================
    # Compliance Policies
    # =========================================================================

    async def _check_compliance(self, request: PolicyEvaluationRequest) -> List[PolicyViolation]:
        """Check request against compliance policies."""
        violations = []

        compliance_policies = [p for p in self._policies if p.category == PolicyCategory.COMPLIANCE]

        for policy in compliance_policies:
            if not policy.is_active:
                continue

            # Check applicability
            if policy.tenant_id and policy.tenant_id != request.tenant_id:
                continue

            for rule in policy.rules:
                violation = self._evaluate_compliance_rule(policy, rule, request)
                if violation:
                    violations.append(violation)

        return violations

    def _evaluate_compliance_rule(
        self, policy: Policy, rule: PolicyRule, request: PolicyEvaluationRequest
    ) -> Optional[PolicyViolation]:
        """Evaluate a compliance rule."""
        condition = rule.condition

        # Data category restrictions
        if "forbidden_data_categories" in condition:
            forbidden = condition["forbidden_data_categories"]
            if request.data_categories:
                overlap = set(forbidden) & set(request.data_categories)
                if overlap:
                    return PolicyViolation(
                        violation_type=ViolationType.COMPLIANCE_BREACH,
                        policy_name=f"{policy.name}:{rule.name}",
                        severity=0.9,
                        description=f"Forbidden data categories: {overlap}",
                        evidence={"forbidden": list(overlap)},
                        agent_id=request.agent_id,
                        tenant_id=request.tenant_id,
                    )

        # Jurisdiction restrictions
        if "allowed_jurisdictions" in condition:
            allowed = condition["allowed_jurisdictions"]
            jurisdiction = request.context.get("jurisdiction")
            if jurisdiction and jurisdiction not in allowed:
                return PolicyViolation(
                    violation_type=ViolationType.COMPLIANCE_BREACH,
                    policy_name=f"{policy.name}:{rule.name}",
                    severity=0.9,
                    description=f"Jurisdiction not allowed: {jurisdiction}",
                    evidence={
                        "jurisdiction": jurisdiction,
                        "allowed": allowed,
                    },
                    agent_id=request.agent_id,
                    tenant_id=request.tenant_id,
                )

        # External endpoint restrictions
        if "forbidden_endpoints" in condition:
            forbidden = condition["forbidden_endpoints"]
            if request.external_endpoints:
                for endpoint in request.external_endpoints:
                    for pattern in forbidden:
                        if re.match(pattern, endpoint):
                            return PolicyViolation(
                                violation_type=ViolationType.COMPLIANCE_BREACH,
                                policy_name=f"{policy.name}:{rule.name}",
                                severity=0.9,
                                description=f"Forbidden external endpoint: {endpoint}",
                                evidence={"endpoint": endpoint, "pattern": pattern},
                                agent_id=request.agent_id,
                                tenant_id=request.tenant_id,
                            )

        return None

    # =========================================================================
    # Business Rules
    # =========================================================================

    async def _check_business_rules(
        self, request: PolicyEvaluationRequest
    ) -> Tuple[List[PolicyViolation], List[PolicyModification]]:
        """Check request against business rules."""
        violations = []
        modifications = []

        for rule in self._business_rules:
            if not rule.is_active:
                continue

            # Check applicability
            if rule.tenant_id and rule.tenant_id != request.tenant_id:
                continue

            # Check customer tier
            customer_tier = request.context.get("customer_tier")
            if rule.customer_tier and customer_tier != rule.customer_tier:
                continue

            violation, modification = self._evaluate_business_rule(rule, request)
            if violation:
                violations.append(violation)
            if modification:
                modifications.append(modification)

        return violations, modifications

    def _evaluate_business_rule(
        self, rule: BusinessRule, request: PolicyEvaluationRequest
    ) -> Tuple[Optional[PolicyViolation], Optional[PolicyModification]]:
        """Evaluate a business rule."""
        condition = rule.condition
        constraint = rule.constraint

        # Budget rule
        if rule.rule_type == BusinessRuleType.BUDGET:
            max_budget = constraint.get("max_daily_budget")
            if max_budget and request.estimated_cost:
                daily_spent = request.context.get("daily_spent", 0)
                if daily_spent + request.estimated_cost > max_budget:
                    return PolicyViolation(
                        violation_type=ViolationType.BUSINESS_RULE_VIOLATION,
                        policy_name=rule.name,
                        severity=0.8,
                        description=f"Daily budget exceeded: ${daily_spent + request.estimated_cost} > ${max_budget}",
                        evidence={
                            "daily_spent": daily_spent,
                            "estimated_cost": request.estimated_cost,
                            "max_budget": max_budget,
                        },
                        agent_id=request.agent_id,
                        tenant_id=request.tenant_id,
                    ), None

        # Tier access rule
        elif rule.rule_type == BusinessRuleType.TIER_ACCESS:
            required_tier = constraint.get("required_tier")
            tier_order = {"free": 0, "pro": 1, "enterprise": 2}
            customer_tier = request.context.get("customer_tier", "free")

            if required_tier and tier_order.get(customer_tier, 0) < tier_order.get(required_tier, 0):
                return PolicyViolation(
                    violation_type=ViolationType.BUSINESS_RULE_VIOLATION,
                    policy_name=rule.name,
                    severity=0.7,
                    description=f"Feature requires {required_tier} tier (current: {customer_tier})",
                    evidence={
                        "required_tier": required_tier,
                        "current_tier": customer_tier,
                    },
                    agent_id=request.agent_id,
                    tenant_id=request.tenant_id,
                ), None

        # Feature gate
        elif rule.rule_type == BusinessRuleType.FEATURE_GATE:
            feature = condition.get("feature")
            enabled = constraint.get("enabled", False)
            if feature and request.action_type.value == feature and not enabled:
                return PolicyViolation(
                    violation_type=ViolationType.BUSINESS_RULE_VIOLATION,
                    policy_name=rule.name,
                    severity=0.6,
                    description=f"Feature not enabled: {feature}",
                    evidence={"feature": feature},
                    agent_id=request.agent_id,
                    tenant_id=request.tenant_id,
                ), None

        return None, None

    # =========================================================================
    # Governor Integration
    # =========================================================================

    async def _route_to_governor(self, violations: List[PolicyViolation]) -> None:
        """Route violations to M18 Governor."""
        if not self._governor:
            return

        for violation in violations:
            violation.routed_to_governor = True

            # Determine governor action based on severity
            if violation.severity >= 0.9:
                # Severe violation - request freeze
                try:
                    await self._governor.force_freeze(
                        duration_seconds=300, reason=f"Policy violation: {violation.description}"
                    )
                    violation.governor_action = "freeze"
                except Exception as e:
                    logger.error(f"Failed to route to governor: {e}")

            elif violation.severity >= 0.7:
                # High severity - log for review
                violation.governor_action = "flagged"

            logger.warning(
                "violation_routed_to_governor",
                extra={
                    "violation_type": violation.violation_type.value,
                    "policy_name": violation.policy_name,
                    "severity": violation.severity,
                    "governor_action": violation.governor_action,
                },
            )

    # =========================================================================
    # Policy Loading
    # =========================================================================

    async def _load_policies(self) -> PolicyLoadResult:
        """Load policies from database."""
        result = PolicyLoadResult()

        if not self._db_url:
            # Load defaults
            self._load_default_policies()
            result.policies_loaded = len(self._policies)
            return result

        try:
            engine = create_engine(self._db_url)
            with engine.connect() as conn:
                # Load ethical constraints
                rows = conn.execute(
                    text(
                        """
                    SELECT id, name, description, constraint_type,
                           forbidden_patterns, required_disclosures,
                           transparency_threshold, enforcement_level,
                           violation_action, is_active, violated_count
                    FROM policy.ethical_constraints
                    WHERE is_active = true
                """
                    )
                )
                self._ethical_constraints = []
                for row in rows:
                    self._ethical_constraints.append(
                        EthicalConstraint(
                            id=str(row[0]),
                            name=row[1],
                            description=row[2] or "",
                            constraint_type=EthicalConstraintType(row[3]),
                            forbidden_patterns=row[4],
                            required_disclosures=row[5],
                            transparency_threshold=row[6],
                            enforcement_level=row[7],
                            violation_action=row[8],
                            is_active=row[9],
                            violated_count=row[10],
                        )
                    )
                result.ethical_constraints_loaded = len(self._ethical_constraints)

                # Load risk ceilings
                rows = conn.execute(
                    text(
                        """
                    SELECT id, name, description, metric, max_value,
                           current_value, window_seconds, applies_to,
                           tenant_id, breach_action, breach_count, is_active
                    FROM policy.risk_ceilings
                    WHERE is_active = true
                """
                    )
                )
                self._risk_ceilings = []
                for row in rows:
                    self._risk_ceilings.append(
                        RiskCeiling(
                            id=str(row[0]),
                            name=row[1],
                            description=row[2],
                            metric=row[3],
                            max_value=row[4],
                            current_value=row[5],
                            window_seconds=row[6],
                            applies_to=row[7],
                            tenant_id=row[8],
                            breach_action=row[9],
                            breach_count=row[10],
                            is_active=row[11],
                        )
                    )
                result.risk_ceilings_loaded = len(self._risk_ceilings)

                # Load safety rules
                rows = conn.execute(
                    text(
                        """
                    SELECT id, name, description, rule_type, condition,
                           action, cooldown_seconds, applies_to, tenant_id,
                           priority, is_active, triggered_count
                    FROM policy.safety_rules
                    WHERE is_active = true
                    ORDER BY priority ASC
                """
                    )
                )
                self._safety_rules = []
                for row in rows:
                    self._safety_rules.append(
                        SafetyRule(
                            id=str(row[0]),
                            name=row[1],
                            description=row[2],
                            rule_type=SafetyRuleType(row[3]),
                            condition=row[4] if isinstance(row[4], dict) else json.loads(row[4] or "{}"),
                            action=row[5],
                            cooldown_seconds=row[6],
                            applies_to=row[7],
                            tenant_id=row[8],
                            priority=row[9],
                            is_active=row[10],
                            triggered_count=row[11],
                        )
                    )
                result.safety_rules_loaded = len(self._safety_rules)

                # Load business rules
                rows = conn.execute(
                    text(
                        """
                    SELECT id, name, description, rule_type, condition,
                           constraint, tenant_id, customer_tier, priority, is_active
                    FROM policy.business_rules
                    WHERE is_active = true
                    ORDER BY priority ASC
                """
                    )
                )
                self._business_rules = []
                for row in rows:
                    self._business_rules.append(
                        BusinessRule(
                            id=str(row[0]),
                            name=row[1],
                            description=row[2],
                            rule_type=BusinessRuleType(row[3]),
                            condition=row[4] if isinstance(row[4], dict) else json.loads(row[4] or "{}"),
                            constraint=row[5] if isinstance(row[5], dict) else json.loads(row[5] or "{}"),
                            tenant_id=row[6],
                            customer_tier=row[7],
                            priority=row[8],
                            is_active=row[9],
                        )
                    )
                result.business_rules_loaded = len(self._business_rules)

            engine.dispose()

        except SQLAlchemyError as e:
            logger.error(f"Failed to load policies: {e}")
            result.errors.append(str(e))
            self._load_default_policies()

        self._cache_loaded_at = datetime.now(timezone.utc)
        result.policies_loaded = len(self._policies)

        logger.info(
            "policies_loaded",
            extra={
                "ethical_constraints": result.ethical_constraints_loaded,
                "risk_ceilings": result.risk_ceilings_loaded,
                "safety_rules": result.safety_rules_loaded,
                "business_rules": result.business_rules_loaded,
            },
        )

        return result

    def _load_default_policies(self) -> None:
        """Load default policies when database is unavailable."""
        # Mark cache as loaded to prevent re-loading
        self._cache_loaded_at = datetime.now(timezone.utc)

        # Default ethical constraints
        self._ethical_constraints = [
            EthicalConstraint(
                name="no_coercion",
                description="Agents must never use coercive tactics",
                constraint_type=EthicalConstraintType.NO_COERCION,
                forbidden_patterns=["threaten", "force", "blackmail"],
                enforcement_level="strict",
                violation_action="block",
            ),
            EthicalConstraint(
                name="no_fabrication",
                description="Agents must never fabricate evidence",
                constraint_type=EthicalConstraintType.NO_FABRICATION,
                forbidden_patterns=["fake_data", "false_citation"],
                enforcement_level="strict",
                violation_action="block",
            ),
        ]

        # Default risk ceilings
        self._risk_ceilings = [
            RiskCeiling(
                name="hourly_cost_ceiling",
                metric="cost_per_hour",
                max_value=DEFAULT_COST_CEILING_PER_HOUR,
                breach_action="throttle",
            ),
            RiskCeiling(
                name="retry_rate_ceiling",
                metric="retries_per_minute",
                max_value=DEFAULT_RETRY_CEILING_PER_MINUTE,
                breach_action="block",
            ),
        ]

        # Default safety rules
        self._safety_rules = [
            SafetyRule(
                name="block_dangerous_commands",
                rule_type=SafetyRuleType.ACTION_BLOCK,
                condition={"actions": ["rm -rf", "drop database", "shutdown"]},
                action="block",
                priority=1,
            ),
        ]

    def _is_cache_stale(self) -> bool:
        """Check if policy cache is stale."""
        if not self._cache_loaded_at:
            return True

        age = (datetime.now(timezone.utc) - self._cache_loaded_at).total_seconds()
        return age > CACHE_TTL_SECONDS

    # =========================================================================
    # Persistence
    # =========================================================================

    async def _persist_evaluation(self, request: PolicyEvaluationRequest, result: PolicyEvaluationResult) -> None:
        """Persist evaluation to audit log."""
        if not self._db_url:
            return

        try:
            engine = create_engine(self._db_url)
            with engine.connect() as conn:
                conn.execute(
                    text(
                        """
                        INSERT INTO policy.evaluations (
                            id, action_type, agent_id, tenant_id,
                            request_context, decision, decision_reason,
                            modifications, evaluation_ms, policies_checked,
                            rules_matched, evaluated_at
                        ) VALUES (
                            CAST(:id AS UUID), :action_type, :agent_id, :tenant_id,
                            CAST(:context AS JSONB), :decision, :reason,
                            CAST(:modifications AS JSONB), :eval_ms, :policies,
                            :rules, :evaluated_at
                        )
                    """
                    ),
                    {
                        "id": result.request_id,
                        "action_type": request.action_type.value,
                        "agent_id": request.agent_id,
                        "tenant_id": request.tenant_id,
                        "context": json.dumps(request.context),
                        "decision": result.decision.value,
                        "reason": result.decision_reason,
                        "modifications": json.dumps([m.model_dump() for m in result.modifications]),
                        "eval_ms": result.evaluation_ms,
                        "policies": result.policies_evaluated,
                        "rules": result.rules_matched,
                        "evaluated_at": result.evaluated_at,
                    },
                )
                conn.commit()

                # Persist violations
                for violation in result.violations:
                    conn.execute(
                        text(
                            """
                            INSERT INTO policy.violations (
                                id, evaluation_id, policy_name, violation_type,
                                severity, description, evidence, agent_id,
                                tenant_id, action_attempted, routed_to_governor,
                                governor_action, detected_at
                            ) VALUES (
                                CAST(:id AS UUID), CAST(:eval_id AS UUID), :policy,
                                :type, :severity, :description, CAST(:evidence AS JSONB),
                                :agent_id, :tenant_id, :action, :routed,
                                :gov_action, :detected_at
                            )
                        """
                        ),
                        {
                            "id": violation.id,
                            "eval_id": result.request_id,
                            "policy": violation.policy_name,
                            "type": violation.violation_type.value,
                            "severity": violation.severity,
                            "description": violation.description,
                            "evidence": json.dumps(violation.evidence),
                            "agent_id": violation.agent_id,
                            "tenant_id": violation.tenant_id,
                            "action": violation.action_attempted,
                            "routed": violation.routed_to_governor,
                            "gov_action": violation.governor_action,
                            "detected_at": violation.detected_at,
                        },
                    )
                conn.commit()

            engine.dispose()

        except SQLAlchemyError as e:
            logger.debug(f"Failed to persist evaluation: {e}")

    # =========================================================================
    # State & Metrics
    # =========================================================================

    async def get_state(self, db=None) -> PolicyState:
        """Get current policy layer state."""
        return PolicyState(
            total_policies=len(self._policies)
            + len(self._ethical_constraints)
            + len(self._safety_rules)
            + len(self._business_rules),
            active_policies=len([p for p in self._policies if p.is_active])
            + len(self._ethical_constraints)
            + len(self._safety_rules)
            + len(self._business_rules),
            total_evaluations_today=self._evaluations_count,
            total_violations_today=self._violations_count,
            block_rate=self._blocks_count / max(1, self._evaluations_count),
            risk_ceilings_active=len([c for c in self._risk_ceilings if c.is_active]),
            risk_ceilings_breached=len([c for c in self._risk_ceilings if c.breach_count > 0]),
        )

    async def reload_policies(self, db=None) -> PolicyLoadResult:
        """Force reload policies from database."""
        self._cache_loaded_at = None
        return await self._load_policies()

    def set_governor(self, governor) -> None:
        """Set the M18 Governor for violation routing."""
        self._governor = governor

    # =========================================================================
    # Additional Query Methods (for API)
    # =========================================================================

    async def get_violations(
        self,
        db=None,
        violation_type: Optional[ViolationType] = None,
        agent_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        severity_min: Optional[float] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[PolicyViolation]:
        """Get violations from database with filtering."""
        if not self._db_url:
            return []

        violations = []
        try:
            engine = create_engine(self._db_url)
            with engine.connect() as conn:
                sql = """
                    SELECT id, policy_name, violation_type, severity, description,
                           evidence, agent_id, tenant_id, action_attempted,
                           routed_to_governor, governor_action, detected_at
                    FROM policy.violations
                    WHERE 1=1
                """
                params = {}

                if violation_type:
                    sql += " AND violation_type = :vtype"
                    params["vtype"] = violation_type.value
                if agent_id:
                    sql += " AND agent_id = :agent_id"
                    params["agent_id"] = agent_id
                if tenant_id:
                    sql += " AND tenant_id = :tenant_id"
                    params["tenant_id"] = tenant_id
                if severity_min is not None:
                    sql += " AND severity >= :severity_min"
                    params["severity_min"] = severity_min
                if since:
                    sql += " AND detected_at >= :since"
                    params["since"] = since

                sql += " ORDER BY detected_at DESC LIMIT :limit"
                params["limit"] = limit

                rows = conn.execute(text(sql), params)
                for row in rows:
                    violations.append(
                        PolicyViolation(
                            id=str(row[0]),
                            policy_name=row[1],
                            violation_type=ViolationType(row[2]),
                            severity=row[3],
                            description=row[4],
                            evidence=row[5] if isinstance(row[5], dict) else json.loads(row[5] or "{}"),
                            agent_id=row[6],
                            tenant_id=row[7],
                            action_attempted=row[8],
                            routed_to_governor=row[9],
                            governor_action=row[10],
                            detected_at=row[11],
                        )
                    )
            engine.dispose()
        except SQLAlchemyError as e:
            logger.debug(f"Failed to get violations: {e}")

        return violations

    async def get_violation(self, db, violation_id: str) -> Optional[PolicyViolation]:
        """Get a specific violation by ID."""
        violations = await self.get_violations(db, limit=1)
        # Query specific violation
        if not self._db_url:
            return None

        try:
            engine = create_engine(self._db_url)
            with engine.connect() as conn:
                row = conn.execute(
                    text(
                        """
                        SELECT id, policy_name, violation_type, severity, description,
                               evidence, agent_id, tenant_id, action_attempted,
                               routed_to_governor, governor_action, detected_at
                        FROM policy.violations
                        WHERE id = CAST(:id AS UUID)
                    """
                    ),
                    {"id": violation_id},
                ).fetchone()

                if row:
                    return PolicyViolation(
                        id=str(row[0]),
                        policy_name=row[1],
                        violation_type=ViolationType(row[2]),
                        severity=row[3],
                        description=row[4],
                        evidence=row[5] if isinstance(row[5], dict) else json.loads(row[5] or "{}"),
                        agent_id=row[6],
                        tenant_id=row[7],
                        action_attempted=row[8],
                        routed_to_governor=row[9],
                        governor_action=row[10],
                        detected_at=row[11],
                    )
            engine.dispose()
        except SQLAlchemyError as e:
            logger.debug(f"Failed to get violation: {e}")

        return None

    async def acknowledge_violation(self, db, violation_id: str, notes: Optional[str] = None) -> bool:
        """Mark a violation as acknowledged."""
        if not self._db_url:
            return False

        try:
            engine = create_engine(self._db_url)
            with engine.connect() as conn:
                result = conn.execute(
                    text(
                        """
                        UPDATE policy.violations
                        SET acknowledged_at = NOW(),
                            acknowledgement_notes = :notes
                        WHERE id = CAST(:id AS UUID)
                    """
                    ),
                    {"id": violation_id, "notes": notes},
                )
                conn.commit()
                return result.rowcount > 0
            engine.dispose()
        except SQLAlchemyError as e:
            logger.debug(f"Failed to acknowledge violation: {e}")
        return False

    async def get_risk_ceilings(
        self,
        db=None,
        tenant_id: Optional[str] = None,
        include_inactive: bool = False,
    ) -> List[RiskCeiling]:
        """Get all risk ceilings."""
        await self._load_policies()  # Ensure loaded

        ceilings = self._risk_ceilings
        if not include_inactive:
            ceilings = [c for c in ceilings if c.is_active]
        if tenant_id:
            ceilings = [c for c in ceilings if c.tenant_id == tenant_id or c.tenant_id is None]
        return ceilings

    async def get_risk_ceiling(self, db, ceiling_id: str) -> Optional[RiskCeiling]:
        """Get a specific risk ceiling."""
        await self._load_policies()
        for ceiling in self._risk_ceilings:
            if ceiling.id == ceiling_id:
                return ceiling
        return None

    async def update_risk_ceiling(self, db, ceiling_id: str, updates: Dict[str, Any]) -> Optional[RiskCeiling]:
        """Update a risk ceiling."""
        if not self._db_url:
            return None

        try:
            engine = create_engine(self._db_url)
            with engine.connect() as conn:
                set_clauses = []
                params = {"id": ceiling_id}
                for key, value in updates.items():
                    set_clauses.append(f"{key} = :{key}")
                    params[key] = value

                if set_clauses:
                    conn.execute(
                        text(
                            f"""
                            UPDATE policy.risk_ceilings
                            SET {", ".join(set_clauses)}
                            WHERE id = CAST(:id AS UUID)
                        """
                        ),
                        params,
                    )
                    conn.commit()
            engine.dispose()

            # Reload and return
            await self.reload_policies()
            return await self.get_risk_ceiling(db, ceiling_id)
        except SQLAlchemyError as e:
            logger.debug(f"Failed to update risk ceiling: {e}")
        return None

    async def reset_risk_ceiling(self, db, ceiling_id: str) -> bool:
        """Reset a risk ceiling's current value."""
        if not self._db_url:
            return False

        try:
            engine = create_engine(self._db_url)
            with engine.connect() as conn:
                result = conn.execute(
                    text(
                        """
                        UPDATE policy.risk_ceilings
                        SET current_value = 0
                        WHERE id = CAST(:id AS UUID)
                    """
                    ),
                    {"id": ceiling_id},
                )
                conn.commit()
                return result.rowcount > 0
            engine.dispose()
        except SQLAlchemyError as e:
            logger.debug(f"Failed to reset risk ceiling: {e}")
        return False

    async def get_safety_rules(
        self,
        db=None,
        tenant_id: Optional[str] = None,
        include_inactive: bool = False,
    ) -> List[SafetyRule]:
        """Get all safety rules."""
        await self._load_policies()

        rules = self._safety_rules
        if not include_inactive:
            rules = [r for r in rules if r.is_active]
        if tenant_id:
            rules = [r for r in rules if r.tenant_id == tenant_id or r.tenant_id is None]
        return rules

    async def update_safety_rule(self, db, rule_id: str, updates: Dict[str, Any]) -> Optional[SafetyRule]:
        """Update a safety rule."""
        if not self._db_url:
            return None

        try:
            engine = create_engine(self._db_url)
            with engine.connect() as conn:
                set_clauses = []
                params = {"id": rule_id}
                for key, value in updates.items():
                    if key == "condition":
                        set_clauses.append(f"{key} = CAST(:{key} AS JSONB)")
                        params[key] = json.dumps(value)
                    else:
                        set_clauses.append(f"{key} = :{key}")
                        params[key] = value

                if set_clauses:
                    conn.execute(
                        text(
                            f"""
                            UPDATE policy.safety_rules
                            SET {", ".join(set_clauses)}
                            WHERE id = CAST(:id AS UUID)
                        """
                        ),
                        params,
                    )
                    conn.commit()
            engine.dispose()

            # Reload and return
            await self.reload_policies()
            for rule in self._safety_rules:
                if rule.id == rule_id:
                    return rule
        except SQLAlchemyError as e:
            logger.debug(f"Failed to update safety rule: {e}")
        return None

    async def get_ethical_constraints(
        self,
        db=None,
        include_inactive: bool = False,
    ) -> List[EthicalConstraint]:
        """Get all ethical constraints."""
        await self._load_policies()

        constraints = self._ethical_constraints
        if not include_inactive:
            constraints = [c for c in constraints if c.is_active]
        return constraints

    async def get_active_cooldowns(self, db=None, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all active cooldowns."""
        now = datetime.now(timezone.utc)
        cooldowns = []

        for key, expires_at in list(self._cooldowns.items()):
            if now >= expires_at:
                del self._cooldowns[key]
                continue

            parts = key.split(":", 1)
            cd_agent_id = parts[0] if len(parts) > 0 else ""
            rule_name = parts[1] if len(parts) > 1 else ""

            if agent_id and cd_agent_id != agent_id:
                continue

            cooldowns.append(
                {
                    "agent_id": cd_agent_id,
                    "rule_name": rule_name,
                    "started_at": expires_at - timedelta(seconds=300),  # Approximate
                    "expires_at": expires_at,
                    "remaining_seconds": (expires_at - now).total_seconds(),
                }
            )

        return cooldowns

    async def clear_cooldowns(self, db, agent_id: str, rule_name: Optional[str] = None) -> int:
        """Clear cooldowns for an agent."""
        cleared = 0
        for key in list(self._cooldowns.keys()):
            if agent_id in key:
                if rule_name is None or rule_name in key:
                    del self._cooldowns[key]
                    cleared += 1
        return cleared

    async def get_metrics(self, db=None, hours: int = 24) -> Dict[str, Any]:
        """Get policy engine metrics."""
        return {
            "total_evaluations": self._evaluations_count,
            "total_blocks": self._blocks_count,
            "total_allows": self._evaluations_count - self._blocks_count - self._modifies_count,
            "total_modifications": self._modifies_count,
            "block_rate": self._blocks_count / max(1, self._evaluations_count),
            "avg_evaluation_ms": 0.0,  # Would need to track this
            "violations_by_type": {},  # Would need to aggregate from db
            "evaluations_by_action": {},  # Would need to aggregate from db
        }

    # =========================================================================
    # GAP 1: Policy Versioning & Provenance
    # =========================================================================

    async def get_policy_versions(self, db=None, limit: int = 20, include_inactive: bool = False) -> List[Dict]:
        """Get policy version history."""
        if not self._db_url:
            return [{"version": self._policy_version, "is_active": True}]

        try:
            engine = create_engine(self._db_url)
            with engine.connect() as conn:
                sql = """
                    SELECT id, version, policy_hash, created_by, created_at,
                           description, is_active, rolled_back_at
                    FROM policy.policy_versions
                """
                if not include_inactive:
                    sql += " WHERE rolled_back_at IS NULL"
                sql += " ORDER BY created_at DESC LIMIT :limit"

                rows = conn.execute(text(sql), {"limit": limit})
                return [
                    {
                        "id": str(row[0]),
                        "version": row[1],
                        "policy_hash": row[2],
                        "created_by": row[3],
                        "created_at": row[4].isoformat() if row[4] else None,
                        "description": row[5],
                        "is_active": row[6],
                        "rolled_back_at": row[7].isoformat() if row[7] else None,
                    }
                    for row in rows
                ]
            engine.dispose()
        except Exception as e:
            logger.debug(f"Failed to get versions: {e}")
        return []

    async def get_current_version(self, db=None) -> Optional[Dict]:
        """Get the currently active policy version."""
        if not self._db_url:
            return {"version": self._policy_version, "is_active": True}

        try:
            engine = create_engine(self._db_url)
            with engine.connect() as conn:
                row = conn.execute(
                    text(
                        """
                    SELECT id, version, policy_hash, created_by, created_at, description
                    FROM policy.policy_versions
                    WHERE is_active = true
                    ORDER BY created_at DESC LIMIT 1
                """
                    )
                ).fetchone()

                if row:
                    return {
                        "id": str(row[0]),
                        "version": row[1],
                        "policy_hash": row[2],
                        "created_by": row[3],
                        "created_at": row[4].isoformat() if row[4] else None,
                        "description": row[5],
                        "is_active": True,
                    }
            engine.dispose()
        except Exception as e:
            logger.debug(f"Failed to get current version: {e}")
        return None

    async def create_policy_version(self, db, description: str, created_by: str = "system"):
        """Create a new policy version snapshot."""
        import hashlib

        from app.policy.models import PolicyVersion

        # Compute hash of current policies
        policy_data = json.dumps(
            {
                "policies": [p.model_dump() for p in self._policies],
                "risk_ceilings": [c.model_dump() for c in self._risk_ceilings],
                "safety_rules": [r.model_dump() for r in self._safety_rules],
                "ethical_constraints": [c.model_dump() for c in self._ethical_constraints],
                "business_rules": [r.model_dump() for r in self._business_rules],
            },
            sort_keys=True,
            default=str,
        )
        policy_hash = hashlib.sha256(policy_data.encode()).hexdigest()[:16]

        # Increment version
        current = await self.get_current_version(db)
        if current:
            parts = current["version"].split(".")
            new_version = f"{parts[0]}.{parts[1]}.{int(parts[2]) + 1}"
        else:
            new_version = "1.0.1"

        version = PolicyVersion(
            version=new_version,
            policy_hash=policy_hash,
            created_by=created_by,
            description=description,
            is_active=True,
        )

        if self._db_url:
            try:
                engine = create_engine(self._db_url)
                with engine.connect() as conn:
                    # Deactivate previous versions
                    conn.execute(text("UPDATE policy.policy_versions SET is_active = false"))

                    # Insert new version
                    conn.execute(
                        text(
                            """
                        INSERT INTO policy.policy_versions
                        (id, version, policy_hash, created_by, description, is_active)
                        VALUES (gen_random_uuid(), :version, :hash, :by, :desc, true)
                    """
                        ),
                        {
                            "version": new_version,
                            "hash": policy_hash,
                            "by": created_by,
                            "desc": description,
                        },
                    )
                    conn.commit()
                engine.dispose()
            except Exception as e:
                logger.debug(f"Failed to create version: {e}")

        self._policy_version = new_version
        return version

    async def rollback_to_version(self, db, target_version: str, reason: str, rolled_back_by: str):
        """Rollback to a previous policy version."""
        if not self._db_url:
            return {"success": False, "error": "No database configured"}

        try:
            engine = create_engine(self._db_url)
            with engine.connect() as conn:
                # Find target version
                row = conn.execute(
                    text(
                        """
                    SELECT id, version, policies_snapshot, risk_ceilings_snapshot,
                           safety_rules_snapshot, ethical_constraints_snapshot
                    FROM policy.policy_versions
                    WHERE version = :version
                """
                    ),
                    {"version": target_version},
                ).fetchone()

                if not row:
                    return {"success": False, "error": f"Version {target_version} not found"}

                # Mark current as rolled back
                conn.execute(
                    text(
                        """
                    UPDATE policy.policy_versions
                    SET rolled_back_at = NOW(), rolled_back_by = :by
                    WHERE is_active = true
                """
                    ),
                    {"by": rolled_back_by},
                )

                # Activate target version
                conn.execute(
                    text(
                        """
                    UPDATE policy.policy_versions
                    SET is_active = true
                    WHERE version = :version
                """
                    ),
                    {"version": target_version},
                )

                # Record provenance
                conn.execute(
                    text(
                        """
                    INSERT INTO policy.policy_provenance
                    (policy_id, policy_type, action, changed_by, policy_version, reason)
                    VALUES (gen_random_uuid(), 'version', 'rollback', :by, :version, :reason)
                """
                    ),
                    {"by": rolled_back_by, "version": target_version, "reason": reason},
                )

                conn.commit()

                self._policy_version = target_version
                await self.reload_policies(db)

                return {"success": True, "rolled_back_to": target_version}
            engine.dispose()
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return {"success": False, "error": str(e)}

    async def get_version_provenance(self, db, version_id: str) -> List[Dict]:
        """Get provenance (change history) for a version."""
        if not self._db_url:
            return []

        try:
            engine = create_engine(self._db_url)
            with engine.connect() as conn:
                rows = conn.execute(
                    text(
                        """
                    SELECT policy_type, action, changed_by, changed_at, reason
                    FROM policy.policy_provenance
                    WHERE policy_version = :version
                    ORDER BY changed_at DESC
                """
                    ),
                    {"version": version_id},
                )
                return [
                    {
                        "policy_type": row[0],
                        "action": row[1],
                        "changed_by": row[2],
                        "changed_at": row[3].isoformat() if row[3] else None,
                        "reason": row[4],
                    }
                    for row in rows
                ]
            engine.dispose()
        except Exception as e:
            logger.debug(f"Failed to get provenance: {e}")
        return []

    # =========================================================================
    # GAP 2: Policy Dependency Graph & Conflict Resolution
    # =========================================================================

    async def get_dependency_graph(self, db=None):
        """Get the policy dependency graph."""
        from app.policy.models import DependencyGraph, PolicyConflict, PolicyDependency

        dependencies = []
        conflicts = []

        if self._db_url:
            try:
                engine = create_engine(self._db_url)
                with engine.connect() as conn:
                    # Get dependencies
                    rows = conn.execute(
                        text(
                            """
                        SELECT id, source_policy, target_policy, dependency_type,
                               resolution_strategy, priority, description
                        FROM policy.policy_dependencies
                        WHERE is_active = true
                    """
                        )
                    )
                    for row in rows:
                        dependencies.append(
                            PolicyDependency(
                                id=str(row[0]),
                                source_policy=row[1],
                                target_policy=row[2],
                                dependency_type=row[3],
                                resolution_strategy=row[4],
                                priority=row[5],
                                description=row[6],
                            )
                        )

                    # Get conflicts
                    rows = conn.execute(
                        text(
                            """
                        SELECT id, policy_a, policy_b, conflict_type, severity,
                               description, affected_action_types, resolved, resolution
                        FROM policy.policy_conflicts
                    """
                        )
                    )
                    for row in rows:
                        conflicts.append(
                            PolicyConflict(
                                id=str(row[0]),
                                policy_a=row[1],
                                policy_b=row[2],
                                conflict_type=row[3],
                                severity=row[4],
                                description=row[5],
                                affected_action_types=row[6] or [],
                                resolved=row[7],
                                resolution=row[8],
                            )
                        )
                engine.dispose()
            except Exception as e:
                logger.debug(f"Failed to get dependency graph: {e}")

        # Build nodes from current policies
        nodes = {}
        for p in self._policies:
            nodes[p.name] = {"id": p.id, "category": p.category.value}
        for c in self._ethical_constraints:
            nodes[f"ethical.{c.name}"] = {"id": c.id, "type": "ethical"}
        for r in self._safety_rules:
            nodes[f"safety.{r.name}"] = {"id": r.id, "type": "safety"}

        return DependencyGraph(
            nodes=nodes,
            edges=dependencies,
            conflicts=conflicts,
        )

    async def get_policy_conflicts(self, db=None, include_resolved: bool = False) -> List:
        """Get policy conflicts."""
        from app.policy.models import PolicyConflict

        conflicts = []
        if self._db_url:
            try:
                engine = create_engine(self._db_url)
                with engine.connect() as conn:
                    sql = "SELECT * FROM policy.policy_conflicts"
                    if not include_resolved:
                        sql += " WHERE resolved = false"

                    rows = conn.execute(text(sql))
                    for row in rows:
                        conflicts.append(
                            PolicyConflict(
                                id=str(row[0]),
                                policy_a=row[1],
                                policy_b=row[2],
                                conflict_type=row[3],
                                severity=row[4],
                                description=row[5],
                            )
                        )
                engine.dispose()
            except Exception as e:
                logger.debug(f"Failed to get conflicts: {e}")
        return conflicts

    async def resolve_conflict(self, db, conflict_id: str, resolution: str, resolved_by: str) -> bool:
        """Resolve a policy conflict."""
        if not self._db_url:
            return False

        try:
            engine = create_engine(self._db_url)
            with engine.connect() as conn:
                result = conn.execute(
                    text(
                        """
                    UPDATE policy.policy_conflicts
                    SET resolved = true, resolution = :res, resolved_by = :by, resolved_at = NOW()
                    WHERE id = CAST(:id AS UUID)
                """
                    ),
                    {"id": conflict_id, "res": resolution, "by": resolved_by},
                )
                conn.commit()
                return result.rowcount > 0
            engine.dispose()
        except Exception as e:
            logger.debug(f"Failed to resolve conflict: {e}")
        return False

    # =========================================================================
    # GAP 3: Temporal Policies
    # =========================================================================

    async def get_temporal_policies(
        self, db=None, metric: Optional[str] = None, include_inactive: bool = False
    ) -> List:
        """Get temporal (sliding window) policies."""
        from app.policy.models import TemporalPolicy

        policies = []
        if self._db_url:
            try:
                engine = create_engine(self._db_url)
                with engine.connect() as conn:
                    sql = "SELECT * FROM policy.temporal_policies WHERE 1=1"
                    params = {}
                    if not include_inactive:
                        sql += " AND is_active = true"
                    if metric:
                        sql += " AND metric = :metric"
                        params["metric"] = metric

                    rows = conn.execute(text(sql), params)
                    for row in rows:
                        policies.append(
                            TemporalPolicy(
                                id=str(row[0]),
                                name=row[1],
                                description=row[2],
                                temporal_type=row[3],
                                metric=row[4],
                                max_value=row[5],
                                window_seconds=row[6],
                                breach_action=row[11],
                                breach_count=row[14],
                                is_active=row[13],
                            )
                        )
                engine.dispose()
            except Exception as e:
                logger.debug(f"Failed to get temporal policies: {e}")
        return policies

    async def create_temporal_policy(self, db, data: Dict):
        """Create a temporal policy."""
        from app.policy.models import TemporalPolicy

        policy = TemporalPolicy(**data)

        if self._db_url:
            try:
                engine = create_engine(self._db_url)
                with engine.connect() as conn:
                    conn.execute(
                        text(
                            """
                        INSERT INTO policy.temporal_policies
                        (name, description, temporal_type, metric, max_value,
                         window_seconds, breach_action, cooldown_on_breach)
                        VALUES (:name, :desc, :type, :metric, :max, :window, :action, :cooldown)
                    """
                        ),
                        {
                            "name": data["name"],
                            "desc": data.get("description"),
                            "type": data["temporal_type"],
                            "metric": data["metric"],
                            "max": data["max_value"],
                            "window": data["window_seconds"],
                            "action": data.get("breach_action", "block"),
                            "cooldown": data.get("cooldown_on_breach", 0),
                        },
                    )
                    conn.commit()
                engine.dispose()
            except Exception as e:
                logger.debug(f"Failed to create temporal policy: {e}")

        return policy

    async def get_temporal_utilization(self, db, policy_id: str, agent_id: Optional[str] = None) -> Dict:
        """Get current utilization for a temporal policy."""
        if not self._db_url:
            return {"utilization": 0.0}

        try:
            engine = create_engine(self._db_url)
            with engine.connect() as conn:
                # Get policy
                policy = conn.execute(
                    text(
                        """
                    SELECT max_value, window_seconds FROM policy.temporal_policies
                    WHERE id = CAST(:id AS UUID)
                """
                    ),
                    {"id": policy_id},
                ).fetchone()

                if not policy:
                    return {"error": "Policy not found"}

                # Get current window sum
                row = conn.execute(
                    text(
                        """
                    SELECT COALESCE(SUM(value), 0) as total
                    FROM policy.temporal_metric_events
                    WHERE policy_id = CAST(:id AS UUID)
                    AND occurred_at > NOW() - INTERVAL ':window seconds'
                """.replace(":window", str(policy[1]))
                    ),
                    {"id": policy_id},
                ).fetchone()

                current = row[0] if row else 0
                utilization = current / policy[0] if policy[0] > 0 else 0

                return {
                    "policy_id": policy_id,
                    "current_value": current,
                    "max_value": policy[0],
                    "utilization": utilization,
                    "window_seconds": policy[1],
                }
            engine.dispose()
        except Exception as e:
            logger.debug(f"Failed to get utilization: {e}")
        return {"utilization": 0.0}

    # =========================================================================
    # GAP 4: Context-Aware Evaluation
    # =========================================================================

    async def evaluate_with_context(
        self,
        db,
        action_type,
        policy_context,
        proposed_action: Optional[str] = None,
        target_resource: Optional[str] = None,
        estimated_cost: Optional[float] = None,
        data_categories: Optional[List[str]] = None,
        context: Optional[Dict] = None,
    ):
        """Enhanced evaluation with full policy context."""
        from app.policy.models import (
            EnhancedPolicyEvaluationResult,
            EnhancedPolicyViolation,
            PolicyDecision,
            RecoverabilityType,
            ViolationSeverity,
        )

        start_time = time.time()

        # Load policies if needed
        await self._load_policies()

        violations = []
        modifications = []
        temporal_warnings = []
        temporal_utilization = {}
        conflicts_detected = []

        # Check if agent is quarantined
        if policy_context.is_quarantined:
            if policy_context.quarantine_until and datetime.now(timezone.utc) < policy_context.quarantine_until:
                violations.append(
                    EnhancedPolicyViolation(
                        violation_type=ViolationType.SAFETY_RULE_TRIGGERED,
                        policy_name="quarantine",
                        severity=1.0,
                        severity_class=ViolationSeverity.OPERATIONAL_CRITICAL,
                        recoverability=RecoverabilityType.NON_RECOVERABLE,
                        description="Agent is quarantined",
                        agent_id=policy_context.agent_id,
                        action_chain_depth=policy_context.action_chain_depth,
                    )
                )

        # Check action chain depth
        max_depth = 5  # From risk ceilings
        if policy_context.action_chain_depth > max_depth:
            violations.append(
                EnhancedPolicyViolation(
                    violation_type=ViolationType.RISK_CEILING_BREACH,
                    policy_name="cascade_depth",
                    severity=0.8,
                    severity_class=ViolationSeverity.OPERATIONAL_HIGH,
                    recoverability=RecoverabilityType.RECOVERABLE_AUTO,
                    description=f"Action chain depth {policy_context.action_chain_depth} exceeds max {max_depth}",
                    agent_id=policy_context.agent_id,
                    action_chain_depth=policy_context.action_chain_depth,
                )
            )

        # Check temporal policies
        temporal_policies = await self.get_temporal_policies(db)
        for tp in temporal_policies:
            utilization = await self.get_temporal_utilization(db, tp.id, policy_context.agent_id)
            temporal_utilization[tp.metric] = utilization.get("utilization", 0)

            if utilization.get("utilization", 0) > 0.8:
                temporal_warnings.append(f"{tp.metric} at {utilization['utilization']:.0%} of limit")

            if utilization.get("utilization", 0) >= 1.0:
                violations.append(
                    EnhancedPolicyViolation(
                        violation_type=ViolationType.TEMPORAL_LIMIT_EXCEEDED,
                        policy_name=tp.name,
                        severity=0.7,
                        severity_class=ViolationSeverity.OPERATIONAL_HIGH,
                        recoverability=RecoverabilityType.RECOVERABLE_AUTO,
                        description=f"Temporal limit exceeded for {tp.metric}",
                        is_temporal_violation=True,
                        temporal_window_seconds=tp.window_seconds,
                        temporal_metric_value=utilization.get("current_value", 0),
                    )
                )

        # Standard policy checks (reuse existing logic)
        basic_request = PolicyEvaluationRequest(
            action_type=action_type,
            agent_id=policy_context.agent_id,
            tenant_id=policy_context.tenant_id,
            proposed_action=proposed_action,
            target_resource=target_resource,
            estimated_cost=estimated_cost,
            data_categories=data_categories,
            context=context or {},
        )
        basic_result = await self.evaluate(basic_request, db, dry_run=True)

        # Convert basic violations to enhanced
        for v in basic_result.violations:
            violations.append(
                EnhancedPolicyViolation(
                    violation_type=v.violation_type,
                    policy_name=v.policy_name,
                    severity=v.severity,
                    severity_class=self._classify_severity(v),
                    recoverability=self._classify_recoverability(v),
                    description=v.description,
                    evidence=v.evidence,
                    agent_id=v.agent_id,
                    action_chain_depth=policy_context.action_chain_depth,
                )
            )

        # Determine decision
        if violations:
            blocking = [v for v in violations if v.severity >= 0.5]
            if blocking:
                decision = PolicyDecision.BLOCK
                decision_reason = "; ".join(v.description for v in blocking[:3])
            else:
                decision = PolicyDecision.ALLOW
                decision_reason = f"Allowed with {len(violations)} warnings"
        else:
            decision = PolicyDecision.ALLOW
            decision_reason = "All policies passed"

        # Update context
        updated_context = policy_context.model_copy()
        updated_context.temporal_utilization = temporal_utilization
        updated_context.governing_policy_version = self._policy_version
        updated_context.historical_violation_count += len(violations)
        if violations:
            updated_context.last_violation_at = datetime.now(timezone.utc)

        evaluation_ms = (time.time() - start_time) * 1000

        return EnhancedPolicyEvaluationResult(
            request_id=str(uuid4()),
            decision=decision,
            decision_reason=decision_reason,
            policies_evaluated=basic_result.policies_evaluated,
            temporal_policies_evaluated=len(temporal_policies),
            dependencies_checked=0,  # TODO: implement dependency checking
            rules_matched=basic_result.rules_matched,
            evaluation_ms=evaluation_ms,
            violations=violations,
            conflicts_detected=conflicts_detected,
            temporal_utilization=temporal_utilization,
            temporal_warnings=temporal_warnings,
            policy_version=self._policy_version,
            policy_hash=None,  # TODO: compute hash
            updated_context=updated_context,
        )

    def _classify_severity(self, violation) -> "ViolationSeverity":
        """Classify violation severity (GAP 5)."""
        from app.policy.models import ViolationSeverity

        if violation.violation_type == ViolationType.ETHICAL_VIOLATION:
            if violation.severity >= 0.9:
                return ViolationSeverity.ETHICAL_CRITICAL
            elif violation.severity >= 0.5:
                return ViolationSeverity.ETHICAL_HIGH
        elif violation.violation_type == ViolationType.COMPLIANCE_BREACH:
            if violation.severity >= 0.9:
                return ViolationSeverity.COMPLIANCE_CRITICAL
            elif violation.severity >= 0.5:
                return ViolationSeverity.COMPLIANCE_HIGH
        elif violation.severity >= 0.8:
            return ViolationSeverity.OPERATIONAL_HIGH
        elif violation.severity >= 0.5:
            return ViolationSeverity.RECOVERABLE_MEDIUM

        return ViolationSeverity.RECOVERABLE_LOW

    def _classify_recoverability(self, violation) -> "RecoverabilityType":
        """Classify violation recoverability (GAP 5)."""
        from app.policy.models import RecoverabilityType

        if violation.violation_type in [ViolationType.ETHICAL_VIOLATION, ViolationType.COMPLIANCE_BREACH]:
            if violation.severity >= 0.9:
                return RecoverabilityType.NON_RECOVERABLE
            return RecoverabilityType.RECOVERABLE_MANUAL

        if violation.severity >= 0.8:
            return RecoverabilityType.RECOVERABLE_MANUAL

        return RecoverabilityType.RECOVERABLE_AUTO

    # =========================================================================
    # ISSUE 1: DAG Enforcement & Cycle Detection
    # =========================================================================

    async def validate_dependency_dag(self, db=None) -> Dict[str, Any]:
        """
        Validate that policy dependencies form a valid DAG (Directed Acyclic Graph).

        Returns:
            Dict with 'is_dag', 'cycles' (if any), and 'topological_order'
        """
        # Build adjacency list from dependencies
        graph = {}  # source -> [targets]
        all_nodes = set()

        if self._db_url:
            try:
                engine = create_engine(self._db_url)
                with engine.connect() as conn:
                    rows = conn.execute(
                        text(
                            """
                        SELECT source_policy, target_policy, dependency_type
                        FROM policy.policy_dependencies
                        WHERE is_active = true
                    """
                        )
                    )
                    for row in rows:
                        source, target = row[0], row[1]
                        all_nodes.add(source)
                        all_nodes.add(target)

                        if source not in graph:
                            graph[source] = []
                        graph[source].append((target, row[2]))
                engine.dispose()
            except Exception as e:
                logger.error(f"Failed to load dependencies for DAG validation: {e}")
                return {"is_dag": False, "error": str(e)}

        # Detect cycles using DFS with three-color marking
        # WHITE (0) = unvisited, GRAY (1) = in current path, BLACK (2) = fully processed
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {node: WHITE for node in all_nodes}
        parent = {node: None for node in all_nodes}
        cycles = []
        topological_order = []

        def dfs(node: str, path: List[str]) -> bool:
            """Returns True if cycle detected."""
            color[node] = GRAY

            for neighbor, dep_type in graph.get(node, []):
                if neighbor not in color:
                    color[neighbor] = WHITE

                if color[neighbor] == GRAY:
                    # Found cycle - extract it
                    cycle_start = path.index(neighbor) if neighbor in path else 0
                    cycle = path[cycle_start:] + [node, neighbor]
                    cycles.append(
                        {
                            "cycle": cycle,
                            "type": "back_edge",
                            "edge": f"{node} -> {neighbor}",
                            "dependency_type": dep_type,
                        }
                    )
                    return True

                elif color[neighbor] == WHITE:
                    parent[neighbor] = node
                    if dfs(neighbor, path + [node]):
                        return True  # Propagate cycle detection

            color[node] = BLACK
            topological_order.append(node)
            return False

        has_cycle = False
        for node in all_nodes:
            if color.get(node) == WHITE:
                if dfs(node, []):
                    has_cycle = True
                    # Continue to find all cycles, don't stop at first

        topological_order.reverse()  # Reverse for proper ordering

        return {
            "is_dag": not has_cycle,
            "cycles": cycles,
            "topological_order": topological_order if not has_cycle else None,
            "node_count": len(all_nodes),
            "edge_count": sum(len(v) for v in graph.values()),
        }

    async def add_dependency_with_dag_check(
        self,
        db,
        source_policy: str,
        target_policy: str,
        dependency_type: str,
        resolution_strategy: str = "source_wins",
        priority: int = 100,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Add a policy dependency with DAG validation.

        Blocks addition if it would create a cycle.
        """
        if not self._db_url:
            return {"success": False, "error": "No database configured"}

        try:
            engine = create_engine(self._db_url)
            with engine.connect() as conn:
                # First, simulate adding the edge and check for cycles
                # Get existing dependencies
                rows = conn.execute(
                    text(
                        """
                    SELECT source_policy, target_policy
                    FROM policy.policy_dependencies
                    WHERE is_active = true
                """
                    )
                )

                graph = {}
                all_nodes = set()
                for row in rows:
                    src, tgt = row[0], row[1]
                    all_nodes.add(src)
                    all_nodes.add(tgt)
                    if src not in graph:
                        graph[src] = []
                    graph[src].append(tgt)

                # Add proposed edge
                all_nodes.add(source_policy)
                all_nodes.add(target_policy)
                if source_policy not in graph:
                    graph[source_policy] = []
                graph[source_policy].append(target_policy)

                # Check for cycle using BFS reachability (can we reach source from target?)
                # If target can reach source, adding source->target creates cycle
                def can_reach(start: str, end: str) -> bool:
                    if start == end:
                        return True
                    visited = set()
                    queue = [start]
                    while queue:
                        node = queue.pop(0)
                        if node == end:
                            return True
                        if node in visited:
                            continue
                        visited.add(node)
                        queue.extend(graph.get(node, []))
                    return False

                # Check if target can reach source (would create cycle)
                if can_reach(target_policy, source_policy):
                    return {
                        "success": False,
                        "error": "Adding this dependency would create a cycle",
                        "cycle_path": f"{target_policy} -> ... -> {source_policy} -> {target_policy}",
                        "blocked": True,
                    }

                # Safe to add - insert the dependency
                conn.execute(
                    text(
                        """
                    INSERT INTO policy.policy_dependencies
                    (source_policy, target_policy, dependency_type, resolution_strategy, priority, description)
                    VALUES (:source, :target, :dtype, :strategy, :priority, :desc)
                """
                    ),
                    {
                        "source": source_policy,
                        "target": target_policy,
                        "dtype": dependency_type,
                        "strategy": resolution_strategy,
                        "priority": priority,
                        "desc": description,
                    },
                )
                conn.commit()

                return {
                    "success": True,
                    "source_policy": source_policy,
                    "target_policy": target_policy,
                    "dependency_type": dependency_type,
                }
            engine.dispose()
        except Exception as e:
            logger.error(f"Failed to add dependency: {e}")
            return {"success": False, "error": str(e)}

    def get_topological_evaluation_order(self, dependencies: List) -> List[str]:
        """
        Get topological order for policy evaluation based on dependencies.

        Policies that depend on others should be evaluated after their dependencies.
        """
        # Build graph
        graph = {}
        in_degree = {}
        all_nodes = set()

        for dep in dependencies:
            src = dep.source_policy if hasattr(dep, "source_policy") else dep["source_policy"]
            tgt = dep.target_policy if hasattr(dep, "target_policy") else dep["target_policy"]

            all_nodes.add(src)
            all_nodes.add(tgt)

            if src not in graph:
                graph[src] = []
            graph[src].append(tgt)

            if src not in in_degree:
                in_degree[src] = 0
            if tgt not in in_degree:
                in_degree[tgt] = 0
            in_degree[tgt] += 1

        # Kahn's algorithm for topological sort
        queue = [node for node in all_nodes if in_degree.get(node, 0) == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for neighbor in graph.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(all_nodes):
            # Cycle detected (shouldn't happen if we validated before)
            logger.error("Cycle detected in dependency graph during topological sort")
            return []

        return result

    # =========================================================================
    # ISSUE 2: Temporal Metric Retention & Compaction
    # =========================================================================

    async def prune_temporal_metrics(
        self,
        db=None,
        retention_hours: int = 168,  # 7 days default
        compact_older_than_hours: int = 24,
        max_events_per_policy: int = 10000,
    ) -> Dict[str, Any]:
        """
        Prune and compact temporal metric events to prevent storage explosion.

        Strategy:
        1. Delete events older than retention period
        2. Downsample events older than compact_older_than_hours to hourly aggregates
        3. Cap maximum events per policy

        Returns:
            Dict with pruning statistics
        """
        if not self._db_url:
            return {"success": False, "error": "No database configured"}

        stats = {
            "deleted_expired": 0,
            "compacted_hourly": 0,
            "capped_overflow": 0,
        }

        try:
            engine = create_engine(self._db_url)
            with engine.connect() as conn:
                # 1. Delete events older than retention period
                result = conn.execute(
                    text(
                        """
                    DELETE FROM policy.temporal_metric_events
                    WHERE occurred_at < NOW() - INTERVAL ':hours hours'
                """.replace(":hours", str(retention_hours))
                    )
                )
                stats["deleted_expired"] = result.rowcount

                # 2. Compact events older than threshold to hourly aggregates
                # First, insert aggregates into windows table
                conn.execute(
                    text(
                        """
                    INSERT INTO policy.temporal_metric_windows
                    (policy_id, agent_id, tenant_id, window_key, current_sum, current_count,
                     current_max, window_start, window_end, updated_at)
                    SELECT
                        policy_id,
                        agent_id,
                        tenant_id,
                        policy_id::text || ':' || COALESCE(agent_id, '') || ':' || date_trunc('hour', occurred_at)::text,
                        SUM(value),
                        COUNT(*),
                        MAX(value),
                        date_trunc('hour', occurred_at),
                        date_trunc('hour', occurred_at) + INTERVAL '1 hour',
                        NOW()
                    FROM policy.temporal_metric_events
                    WHERE occurred_at < NOW() - INTERVAL ':hours hours'
                        AND occurred_at >= NOW() - INTERVAL ':retention hours'
                    GROUP BY policy_id, agent_id, tenant_id, date_trunc('hour', occurred_at)
                    ON CONFLICT (window_key) DO UPDATE
                    SET current_sum = policy.temporal_metric_windows.current_sum + EXCLUDED.current_sum,
                        current_count = policy.temporal_metric_windows.current_count + EXCLUDED.current_count,
                        current_max = GREATEST(policy.temporal_metric_windows.current_max, EXCLUDED.current_max),
                        updated_at = NOW()
                """.replace(":hours", str(compact_older_than_hours)).replace(":retention", str(retention_hours))
                    )
                )

                # Delete the compacted events
                result = conn.execute(
                    text(
                        """
                    DELETE FROM policy.temporal_metric_events
                    WHERE occurred_at < NOW() - INTERVAL ':hours hours'
                        AND occurred_at >= NOW() - INTERVAL ':retention hours'
                """.replace(":hours", str(compact_older_than_hours)).replace(":retention", str(retention_hours))
                    )
                )
                stats["compacted_hourly"] = result.rowcount

                # 3. Cap events per policy (keep newest)
                result = conn.execute(
                    text(
                        """
                    WITH ranked AS (
                        SELECT id, policy_id,
                               ROW_NUMBER() OVER (PARTITION BY policy_id ORDER BY occurred_at DESC) as rn
                        FROM policy.temporal_metric_events
                    ),
                    to_delete AS (
                        SELECT id FROM ranked WHERE rn > :max_events
                    )
                    DELETE FROM policy.temporal_metric_events
                    WHERE id IN (SELECT id FROM to_delete)
                """
                    ),
                    {"max_events": max_events_per_policy},
                )
                stats["capped_overflow"] = result.rowcount

                conn.commit()

                # Get current counts for reporting
                counts = conn.execute(
                    text(
                        """
                    SELECT COUNT(*) as event_count,
                           (SELECT COUNT(*) FROM policy.temporal_metric_windows) as window_count
                    FROM policy.temporal_metric_events
                """
                    )
                ).fetchone()

                stats["remaining_events"] = counts[0] if counts else 0
                stats["total_windows"] = counts[1] if counts else 0
                stats["success"] = True

            engine.dispose()
        except Exception as e:
            logger.error(f"Temporal metric pruning failed: {e}")
            stats["success"] = False
            stats["error"] = str(e)

        return stats

    async def get_temporal_storage_stats(self, db=None) -> Dict[str, Any]:
        """Get storage statistics for temporal metrics."""
        if not self._db_url:
            return {"error": "No database configured"}

        try:
            engine = create_engine(self._db_url)
            with engine.connect() as conn:
                stats = conn.execute(
                    text(
                        """
                    SELECT
                        (SELECT COUNT(*) FROM policy.temporal_metric_events) as event_count,
                        (SELECT COUNT(*) FROM policy.temporal_metric_windows) as window_count,
                        (SELECT MIN(occurred_at) FROM policy.temporal_metric_events) as oldest_event,
                        (SELECT MAX(occurred_at) FROM policy.temporal_metric_events) as newest_event,
                        (SELECT COUNT(DISTINCT policy_id) FROM policy.temporal_metric_events) as policies_with_events,
                        (SELECT pg_size_pretty(pg_total_relation_size('policy.temporal_metric_events'))) as events_size,
                        (SELECT pg_size_pretty(pg_total_relation_size('policy.temporal_metric_windows'))) as windows_size
                """
                    )
                ).fetchone()

                return {
                    "event_count": stats[0],
                    "window_count": stats[1],
                    "oldest_event": stats[2].isoformat() if stats[2] else None,
                    "newest_event": stats[3].isoformat() if stats[3] else None,
                    "policies_with_events": stats[4],
                    "events_table_size": stats[5],
                    "windows_table_size": stats[6],
                }
            engine.dispose()
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {"error": str(e)}

    # =========================================================================
    # ISSUE 3: Version Activation with Pre-Activation Integrity Checks
    # =========================================================================

    async def activate_policy_version(
        self,
        db,
        version_id: str,
        activated_by: str,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Activate a policy version with comprehensive pre-activation integrity checks.

        Checks performed:
        1. Dependency closure - all dependencies exist
        2. Conflict scan - no unresolved critical conflicts
        3. DAG validation - no cycles
        4. Temporal policy integrity - valid window configurations
        5. Severity compatibility - ensure escalation paths exist
        6. Simulation - dry-run evaluation against test cases

        Args:
            version_id: The version to activate
            activated_by: Who is activating
            dry_run: If True, run checks but don't activate

        Returns:
            Dict with check results and activation status
        """
        checks = {
            "dependency_closure": {"passed": False, "issues": []},
            "conflict_scan": {"passed": False, "issues": []},
            "dag_validation": {"passed": False, "issues": []},
            "temporal_integrity": {"passed": False, "issues": []},
            "severity_compatibility": {"passed": False, "issues": []},
            "simulation": {"passed": False, "issues": []},
        }

        all_passed = True

        if not self._db_url:
            return {"success": False, "error": "No database configured"}

        try:
            engine = create_engine(self._db_url)
            with engine.connect() as conn:
                # Get version info
                version = conn.execute(
                    text(
                        """
                    SELECT id, version, policy_hash, is_active
                    FROM policy.policy_versions
                    WHERE id = CAST(:id AS UUID) OR version = :id
                """
                    ),
                    {"id": version_id},
                ).fetchone()

                if not version:
                    return {"success": False, "error": f"Version {version_id} not found"}

                # CHECK 1: Dependency Closure
                deps = conn.execute(
                    text(
                        """
                    SELECT source_policy, target_policy
                    FROM policy.policy_dependencies
                    WHERE is_active = true
                """
                    )
                ).fetchall()

                # Collect all referenced policies
                referenced = set()
                for src, tgt in deps:
                    referenced.add(src)
                    referenced.add(tgt)

                # Check if all referenced policies exist
                existing = set()
                for cat_table, name_col in [
                    ("ethical_constraints", "name"),
                    ("safety_rules", "name"),
                    ("risk_ceilings", "name"),
                    ("business_rules", "name"),
                ]:
                    rows = conn.execute(
                        text(
                            f"""
                        SELECT {name_col} FROM policy.{cat_table} WHERE is_active = true
                    """
                        )
                    )
                    for row in rows:
                        existing.add(row[0])
                        # Also add category-prefixed version
                        existing.add(f"{cat_table.rstrip('s').replace('_', '.')}.{row[0]}")

                missing = referenced - existing
                if missing:
                    checks["dependency_closure"]["issues"].append(
                        f"Missing policies referenced in dependencies: {list(missing)}"
                    )
                    all_passed = False
                else:
                    checks["dependency_closure"]["passed"] = True

                # CHECK 2: Conflict Scan
                unresolved = conn.execute(
                    text(
                        """
                    SELECT policy_a, policy_b, conflict_type, severity, description
                    FROM policy.policy_conflicts
                    WHERE resolved = false AND severity >= 0.7
                """
                    )
                ).fetchall()

                if unresolved:
                    for conflict in unresolved:
                        checks["conflict_scan"]["issues"].append(
                            f"Unresolved conflict: {conflict[0]} vs {conflict[1]} (severity {conflict[3]}): {conflict[4]}"
                        )
                    all_passed = False
                else:
                    checks["conflict_scan"]["passed"] = True

                # CHECK 3: DAG Validation
                dag_result = await self.validate_dependency_dag(db)
                if not dag_result.get("is_dag", False):
                    checks["dag_validation"]["issues"].extend(
                        [f"Cycle detected: {c['edge']}" for c in dag_result.get("cycles", [])]
                    )
                    all_passed = False
                else:
                    checks["dag_validation"]["passed"] = True

                # CHECK 4: Temporal Policy Integrity
                temporal = conn.execute(
                    text(
                        """
                    SELECT name, metric, max_value, window_seconds, breach_action
                    FROM policy.temporal_policies
                    WHERE is_active = true
                """
                    )
                ).fetchall()

                temporal_issues = []
                for tp in temporal:
                    if tp[2] <= 0:
                        temporal_issues.append(f"{tp[0]}: max_value must be positive (got {tp[2]})")
                    if tp[3] <= 0:
                        temporal_issues.append(f"{tp[0]}: window_seconds must be positive (got {tp[3]})")
                    if tp[4] not in ["block", "throttle", "alert", "escalate"]:
                        temporal_issues.append(f"{tp[0]}: invalid breach_action '{tp[4]}'")

                if temporal_issues:
                    checks["temporal_integrity"]["issues"] = temporal_issues
                    all_passed = False
                else:
                    checks["temporal_integrity"]["passed"] = True

                # CHECK 5: Severity Compatibility
                # Ensure ethical and compliance constraints have proper escalation paths
                ethical = conn.execute(
                    text(
                        """
                    SELECT name, enforcement_level, violation_action
                    FROM policy.ethical_constraints
                    WHERE is_active = true
                """
                    )
                ).fetchall()

                severity_issues = []
                for ec in ethical:
                    if ec[1] == "strict" and ec[2] not in ["block", "escalate"]:
                        severity_issues.append(
                            f"Ethical constraint '{ec[0]}' has strict enforcement but action is '{ec[2]}' (should be block/escalate)"
                        )

                if severity_issues:
                    checks["severity_compatibility"]["issues"] = severity_issues
                    # This is a warning, not a blocker
                    checks["severity_compatibility"]["passed"] = True
                    checks["severity_compatibility"]["warnings"] = severity_issues
                else:
                    checks["severity_compatibility"]["passed"] = True

                # CHECK 6: Simulation (basic test cases)
                simulation_passed = True
                test_cases = [
                    # Test that blocking patterns are blocked
                    {"action": "rm -rf /", "expected_block": True},
                    {"action": "send_email", "expected_block": False},
                ]

                sim_issues = []
                for tc in test_cases:
                    try:
                        test_req = PolicyEvaluationRequest(
                            action_type=ActionType.EXECUTE,
                            proposed_action=tc["action"],
                            agent_id="test-agent",
                        )
                        result = await self.evaluate(test_req, db, dry_run=True)
                        was_blocked = result.decision == PolicyDecision.BLOCK

                        if tc["expected_block"] and not was_blocked:
                            sim_issues.append(f"Action '{tc['action']}' should be blocked but wasn't")
                            simulation_passed = False
                        elif not tc["expected_block"] and was_blocked:
                            sim_issues.append(f"Action '{tc['action']}' should not be blocked but was")
                            simulation_passed = False
                    except Exception as e:
                        sim_issues.append(f"Simulation error for '{tc['action']}': {e}")
                        simulation_passed = False

                checks["simulation"]["passed"] = simulation_passed
                if sim_issues:
                    checks["simulation"]["issues"] = sim_issues
                    all_passed = False

                # If dry_run or checks failed, don't activate
                if dry_run:
                    return {
                        "success": True,
                        "dry_run": True,
                        "all_checks_passed": all_passed,
                        "checks": checks,
                        "version": version[1],
                    }

                if not all_passed:
                    return {
                        "success": False,
                        "error": "Pre-activation checks failed",
                        "checks": checks,
                    }

                # All checks passed - activate the version
                # Deactivate current version
                conn.execute(
                    text(
                        """
                    UPDATE policy.policy_versions SET is_active = false WHERE is_active = true
                """
                    )
                )

                # Activate new version
                conn.execute(
                    text(
                        """
                    UPDATE policy.policy_versions
                    SET is_active = true
                    WHERE id = CAST(:id AS UUID)
                """
                    ),
                    {"id": str(version[0])},
                )

                # Record provenance
                conn.execute(
                    text(
                        """
                    INSERT INTO policy.policy_provenance
                    (policy_id, policy_type, action, changed_by, policy_version, reason)
                    VALUES (CAST(:vid AS UUID), 'version', 'activate', :by, :version, 'Pre-activation checks passed')
                """
                    ),
                    {"vid": str(version[0]), "by": activated_by, "version": version[1]},
                )

                conn.commit()

                # Update internal state
                self._policy_version = version[1]
                await self.reload_policies(db)

                return {
                    "success": True,
                    "activated_version": version[1],
                    "all_checks_passed": all_passed,
                    "checks": checks,
                }

            engine.dispose()
        except Exception as e:
            logger.error(f"Version activation failed: {e}")
            return {"success": False, "error": str(e)}


# =============================================================================
# Singleton
# =============================================================================

_policy_engine: Optional[PolicyEngine] = None


def get_policy_engine() -> PolicyEngine:
    """Get singleton policy engine with M18 Governor integration."""
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = PolicyEngine()

        # Wire up M18 Governor for violation routing
        try:
            from app.routing import get_governor

            governor = get_governor()
            _policy_engine.set_governor(governor)
            logger.info("M19 Policy Engine connected to M18 Governor")
        except ImportError:
            logger.warning("M18 Governor not available - violation routing disabled")
        except Exception as e:
            logger.warning(f"Failed to connect M18 Governor: {e}")

    return _policy_engine
