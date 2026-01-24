# Layer: L6 — Driver
# Product: system-wide
# Role: Pre-execution gate, scope enforcement
# Callers: L2 APIs (recovery actions), L5 workers
# Reference: PIN-242 (Baseline Freeze)

# app/services/scoped_execution.py
"""
M6: Scoped Execution Context Service (P2FC-4)

Pre-execution gate for MEDIUM+ risk recovery actions.

CORE INVARIANT (M6):
> "No recovery action may execute without an explicit, bounded execution
>  scope derived from incident context."

The Scoped Execution primitive provides:
1. Scope creation with incident binding, cost ceiling, action limits, expiry
2. Scope-gated execution (no execution without valid scope)
3. Scope exhaustion tracking (single-use by default)
4. Scope tampering detection (action must match scope)
5. Audit trail for all scope operations

Scope Model MUST bind:
- Action type (what can be done)
- Target (agent / resource)
- Cost ceiling (tokens / spend)
- Duration / count limit
- Intent (why this is allowed)

Related PINs:
- PIN-148: Incident lifecycle
- PIN-161: Evidence completeness (Replay feeds scope)
- PIN-172: Scoped execution invariant
"""

from __future__ import annotations

import hashlib
import logging
import secrets
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from functools import wraps
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nova.services.scoped_execution")


class RiskClass(str, Enum):
    """Risk classification for recovery actions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExecutionScope(str, Enum):
    """Type of scoped execution."""

    AGENT_SUBSET = "agent_subset"
    REQUEST_SAMPLE = "request_sample"
    BUDGET_FRACTION = "budget_fraction"
    DRY_RUN = "dry_run"  # No actual execution, just validation


@dataclass
class ScopedExecutionResult:
    """Result of a scoped execution test."""

    success: bool
    cost_delta_cents: int
    failure_count: int
    policy_violations: List[str]
    execution_hash: str
    duration_ms: int
    scope_coverage: float  # e.g., 0.1 = 10% of traffic
    samples_tested: int
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryAction:
    """A recovery action to be tested in scoped execution."""

    id: str
    name: str
    risk_class: RiskClass
    action_type: str  # e.g., "retry", "fallback", "circuit_break", "scale"
    parameters: Dict[str, Any]
    target_agents: List[str] = field(default_factory=list)
    timeout_ms: int = 30000


class ScopedExecutionContext:
    """
    M6 Scoped Execution primitive.

    Provides pre-execution testing for recovery actions before global rollout.
    """

    def __init__(
        self,
        action: RecoveryAction,
        scope: ExecutionScope = ExecutionScope.DRY_RUN,
        scope_fraction: float = 0.1,  # Default: test on 10%
        timeout_ms: int = 30000,
    ):
        self.action = action
        self.scope = scope
        self.scope_fraction = min(max(scope_fraction, 0.01), 1.0)  # Clamp 1-100%
        self.timeout_ms = timeout_ms
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    async def execute(self) -> ScopedExecutionResult:
        """
        Execute action in scoped context.

        Returns ScopedExecutionResult with cost/failure/policy deltas.
        """
        self.start_time = datetime.now(timezone.utc)

        try:
            # For DRY_RUN, just validate without actual execution
            if self.scope == ExecutionScope.DRY_RUN:
                result = await self._dry_run_validate()
            else:
                result = await self._execute_scoped()

            return result

        except Exception as e:
            logger.error(f"Scoped execution failed: {e}")
            return ScopedExecutionResult(
                success=False,
                cost_delta_cents=0,
                failure_count=1,
                policy_violations=[f"Execution error: {str(e)}"],
                execution_hash=self._compute_hash({"error": str(e)}),
                duration_ms=self._elapsed_ms(),
                scope_coverage=0.0,
                samples_tested=0,
                details={"error": str(e)},
            )
        finally:
            self.end_time = datetime.now(timezone.utc)

    async def _dry_run_validate(self) -> ScopedExecutionResult:
        """Validate action without actual execution."""
        violations = []

        # Validate action parameters
        if not self.action.action_type:
            violations.append("Missing action_type")

        if self.action.risk_class in (RiskClass.HIGH, RiskClass.CRITICAL):
            if not self.action.target_agents:
                violations.append("HIGH/CRITICAL risk actions require explicit target_agents")

        # Simulate cost estimation
        estimated_cost = self._estimate_cost()

        return ScopedExecutionResult(
            success=len(violations) == 0,
            cost_delta_cents=estimated_cost,
            failure_count=0,
            policy_violations=violations,
            execution_hash=self._compute_hash(
                {
                    "action": self.action.id,
                    "scope": self.scope.value,
                    "dry_run": True,
                }
            ),
            duration_ms=self._elapsed_ms(),
            scope_coverage=0.0,  # Dry run doesn't cover real traffic
            samples_tested=0,
            details={
                "mode": "dry_run",
                "estimated_cost_cents": estimated_cost,
                "risk_class": self.action.risk_class.value,
            },
        )

    async def _execute_scoped(self) -> ScopedExecutionResult:
        """Execute action on scoped subset."""
        # In production, this would:
        # 1. Route a fraction of traffic through the recovery action
        # 2. Measure actual cost/failure deltas
        # 3. Compare against baseline

        # For now, return simulated results
        samples = int(100 * self.scope_fraction)

        return ScopedExecutionResult(
            success=True,
            cost_delta_cents=0,
            failure_count=0,
            policy_violations=[],
            execution_hash=self._compute_hash(
                {
                    "action": self.action.id,
                    "scope": self.scope.value,
                    "fraction": self.scope_fraction,
                }
            ),
            duration_ms=self._elapsed_ms(),
            scope_coverage=self.scope_fraction,
            samples_tested=samples,
            details={
                "mode": "scoped",
                "scope_type": self.scope.value,
                "samples_tested": samples,
            },
        )

    def _estimate_cost(self) -> int:
        """Estimate cost in cents for the action."""
        # Simple heuristic based on action type
        base_costs = {
            "retry": 10,
            "fallback": 5,
            "circuit_break": 0,
            "scale": 100,
        }
        return base_costs.get(self.action.action_type, 20)

    def _elapsed_ms(self) -> int:
        """Get elapsed time in milliseconds."""
        if not self.start_time:
            return 0
        end = self.end_time or datetime.now(timezone.utc)
        delta = end - self.start_time
        return int(delta.total_seconds() * 1000)

    def _compute_hash(self, data: Dict[str, Any]) -> str:
        """Compute deterministic hash of execution."""
        import json

        payload = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


class ScopedExecutionRequired(Exception):
    """Raised when a MEDIUM+ risk action is attempted without scoped pre-execution."""

    pass


class ScopeNotFound(Exception):
    """Raised when a scope ID does not exist."""

    pass


class ScopeExhausted(Exception):
    """Raised when a scope has been fully consumed."""

    pass


class ScopeExpired(Exception):
    """Raised when a scope has expired."""

    pass


class ScopeActionMismatch(Exception):
    """Raised when action does not match scope's allowed actions."""

    pass


class ScopeIncidentMismatch(Exception):
    """Raised when execution targets a different incident than scope."""

    pass


# =============================================================================
# Bound Execution Scope (P2FC-4 Core Model)
# =============================================================================


@dataclass
class BoundExecutionScope:
    """
    A bound execution scope that gates recovery actions.

    This is the core P2FC-4 primitive. Every recovery action MUST have
    a valid scope before execution.
    """

    scope_id: str
    incident_id: str
    allowed_actions: List[str]
    max_cost_usd: float
    max_attempts: int
    expires_at: datetime
    intent: str
    target_agents: List[str] = field(default_factory=list)

    # Tracking
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "system"
    attempts_used: int = 0
    cost_used_usd: float = 0.0
    status: str = "active"  # active, exhausted, expired, revoked
    execution_log: List[Dict[str, Any]] = field(default_factory=list)

    def is_valid(self) -> bool:
        """Check if scope is still valid for execution."""
        if self.status != "active":
            return False
        if datetime.now(timezone.utc) > self.expires_at:
            self.status = "expired"
            return False
        if self.attempts_used >= self.max_attempts:
            self.status = "exhausted"
            return False
        return True

    def can_execute(self, action: str, incident_id: str) -> tuple[bool, str]:
        """
        Check if action can be executed within this scope.

        Returns (can_execute, reason).
        """
        if not self.is_valid():
            return False, f"Scope is {self.status}"

        if incident_id != self.incident_id:
            return False, f"Incident mismatch: scope bound to {self.incident_id}"

        if action not in self.allowed_actions:
            return False, f"Action '{action}' not in allowed actions: {self.allowed_actions}"

        return True, "OK"

    def consume(self, action: str, cost_usd: float = 0.0) -> None:
        """
        Consume one execution attempt.

        Records the execution and updates tracking.
        """
        self.attempts_used += 1
        self.cost_used_usd += cost_usd

        self.execution_log.append(
            {
                "action": action,
                "cost_usd": cost_usd,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "attempt_number": self.attempts_used,
            }
        )

        if self.attempts_used >= self.max_attempts:
            self.status = "exhausted"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize scope for API response."""
        return {
            "scope_id": self.scope_id,
            "incident_id": self.incident_id,
            "allowed_actions": self.allowed_actions,
            "max_cost_usd": self.max_cost_usd,
            "max_attempts": self.max_attempts,
            "expires_at": self.expires_at.isoformat(),
            "intent": self.intent,
            "target_agents": self.target_agents,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "attempts_used": self.attempts_used,
            "cost_used_usd": self.cost_used_usd,
            "status": self.status,
            "attempts_remaining": max(0, self.max_attempts - self.attempts_used),
        }


# =============================================================================
# Scope Store (Thread-Safe In-Memory Store)
# =============================================================================


class ScopeStore:
    """
    Thread-safe in-memory store for execution scopes.

    In production, this would be backed by Redis or PostgreSQL.
    """

    _instance: Optional["ScopeStore"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ScopeStore":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._scopes: Dict[str, BoundExecutionScope] = {}
                    cls._instance._by_incident: Dict[str, List[str]] = {}
        return cls._instance

    def create_scope(
        self,
        incident_id: str,
        allowed_actions: List[str],
        max_cost_usd: float = 0.50,
        max_attempts: int = 1,
        ttl_seconds: int = 300,  # 5 minutes default
        intent: str = "",
        target_agents: Optional[List[str]] = None,
        created_by: str = "system",
    ) -> BoundExecutionScope:
        """
        Create a new bound execution scope.

        Returns the scope with a unique ID.
        """
        scope_id = f"scope_{secrets.token_hex(12)}"
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

        scope = BoundExecutionScope(
            scope_id=scope_id,
            incident_id=incident_id,
            allowed_actions=allowed_actions,
            max_cost_usd=max_cost_usd,
            max_attempts=max_attempts,
            expires_at=expires_at,
            intent=intent,
            target_agents=target_agents or [],
            created_by=created_by,
        )

        with self._lock:
            self._scopes[scope_id] = scope
            if incident_id not in self._by_incident:
                self._by_incident[incident_id] = []
            self._by_incident[incident_id].append(scope_id)

        logger.info(
            f"Created scope {scope_id} for incident {incident_id}: "
            f"actions={allowed_actions}, max_attempts={max_attempts}, "
            f"max_cost=${max_cost_usd:.2f}, expires={expires_at.isoformat()}"
        )

        return scope

    def get_scope(self, scope_id: str) -> Optional[BoundExecutionScope]:
        """Get scope by ID."""
        return self._scopes.get(scope_id)

    def get_scopes_for_incident(self, incident_id: str) -> List[BoundExecutionScope]:
        """Get all scopes for an incident."""
        scope_ids = self._by_incident.get(incident_id, [])
        return [self._scopes[sid] for sid in scope_ids if sid in self._scopes]

    def revoke_scope(self, scope_id: str) -> bool:
        """Revoke a scope (admin action)."""
        scope = self._scopes.get(scope_id)
        if scope:
            scope.status = "revoked"
            logger.info(f"Revoked scope {scope_id}")
            return True
        return False

    def cleanup_expired(self) -> int:
        """Remove expired scopes from memory."""
        now = datetime.now(timezone.utc)
        expired = [sid for sid, s in self._scopes.items() if s.expires_at < now]
        for sid in expired:
            del self._scopes[sid]
        return len(expired)


# Global scope store instance
_scope_store = ScopeStore()


def get_scope_store() -> ScopeStore:
    """Get the global scope store."""
    return _scope_store


# =============================================================================
# Scope-Gated Execution (P2FC-4 Core API)
# =============================================================================


async def create_recovery_scope(
    incident_id: str,
    action: str,
    intent: str = "",
    max_cost_usd: float = 0.50,
    max_attempts: int = 1,
    ttl_seconds: int = 300,
    target_agents: Optional[List[str]] = None,
    created_by: str = "system",
) -> Dict[str, Any]:
    """
    Create a bound execution scope for recovery action.

    This is the gate step (Step A2 in test script).
    """
    store = get_scope_store()

    # Derive intent from incident if not provided
    if not intent:
        intent = f"Recovery action for incident {incident_id}"

    scope = store.create_scope(
        incident_id=incident_id,
        allowed_actions=[action],
        max_cost_usd=max_cost_usd,
        max_attempts=max_attempts,
        ttl_seconds=ttl_seconds,
        intent=intent,
        target_agents=target_agents,
        created_by=created_by,
    )

    return scope.to_dict()


async def execute_with_scope(
    scope_id: str,
    action: str,
    incident_id: str,
    parameters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Execute a recovery action within a valid scope.

    This enforces all P2FC-4 gates:
    - Scope must exist
    - Scope must not be exhausted/expired
    - Action must match scope's allowed actions
    - Incident must match scope's bound incident
    """
    store = get_scope_store()
    scope = store.get_scope(scope_id)

    if not scope:
        raise ScopeNotFound(f"Scope '{scope_id}' not found")

    # Check validity
    can_exec, reason = scope.can_execute(action, incident_id)
    if not can_exec:
        if "exhausted" in reason.lower() or "attempts" in reason.lower():
            raise ScopeExhausted(reason)
        elif "expired" in reason.lower():
            raise ScopeExpired(reason)
        elif "mismatch" in reason.lower() and "incident" in reason.lower():
            raise ScopeIncidentMismatch(reason)
        elif "action" in reason.lower():
            raise ScopeActionMismatch(reason)
        else:
            raise ScopedExecutionRequired(reason)

    # Execute action (placeholder - actual execution would go here)
    logger.info(
        f"Executing action '{action}' within scope {scope_id} (attempt {scope.attempts_used + 1}/{scope.max_attempts})"
    )

    # Consume scope
    execution_cost = 0.0  # Would be calculated from actual execution
    scope.consume(action, execution_cost)

    return {
        "success": True,
        "scope_id": scope_id,
        "action": action,
        "incident_id": incident_id,
        "attempt_number": scope.attempts_used,
        "scope_status": scope.status,
        "attempts_remaining": max(0, scope.max_attempts - scope.attempts_used),
        "cost_used_usd": scope.cost_used_usd,
        "executed_at": datetime.now(timezone.utc).isoformat(),
    }


async def validate_scope_required(
    incident_id: str,
    action: str,
) -> None:
    """
    Validate that execution without scope should fail.

    Called by /recovery/execute when no scope_id provided.
    Always raises ScopedExecutionRequired.
    """
    raise ScopedExecutionRequired(
        f"Scoped execution required. "
        f"Create a scope with POST /api/v1/recovery/scope first. "
        f"Action: {action}, Incident: {incident_id}"
    )


def requires_scoped_execution(risk_threshold: RiskClass = RiskClass.MEDIUM):
    """
    Decorator to enforce scoped pre-execution for risky recovery actions.

    Usage:
        @requires_scoped_execution(risk_threshold=RiskClass.MEDIUM)
        async def execute_recovery(action: RecoveryAction):
            ...

    The decorated function must accept `skip_scope: bool = False` parameter.
    If skip_scope=True and risk >= threshold, ScopedExecutionRequired is raised.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract action from args/kwargs
            action = kwargs.get("action") or (args[0] if args else None)
            skip_scope = kwargs.pop("skip_scope", False)

            if action and isinstance(action, RecoveryAction):
                # Check if risk level requires scoped execution
                risk_order = [RiskClass.LOW, RiskClass.MEDIUM, RiskClass.HIGH, RiskClass.CRITICAL]
                action_risk_idx = risk_order.index(action.risk_class)
                threshold_idx = risk_order.index(risk_threshold)

                if action_risk_idx >= threshold_idx and skip_scope:
                    raise ScopedExecutionRequired(
                        f"Recovery action '{action.name}' has risk_class={action.risk_class.value} "
                        f"which requires scoped pre-execution (threshold: {risk_threshold.value})"
                    )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Convenience function for API use
async def test_recovery_scope(
    action_id: str,
    action_name: str,
    action_type: str,
    risk_class: str,
    parameters: Dict[str, Any],
    scope_type: str = "dry_run",
    scope_fraction: float = 0.1,
) -> Dict[str, Any]:
    """
    Test a recovery action in scoped execution.

    Returns dict with execution result for API response.
    """
    action = RecoveryAction(
        id=action_id,
        name=action_name,
        action_type=action_type,
        risk_class=RiskClass(risk_class),
        parameters=parameters,
    )

    scope = ExecutionScope(scope_type)
    context = ScopedExecutionContext(action, scope, scope_fraction)
    result = await context.execute()

    return {
        "success": result.success,
        "cost_delta_cents": result.cost_delta_cents,
        "failure_count": result.failure_count,
        "policy_violations": result.policy_violations,
        "execution_hash": result.execution_hash,
        "duration_ms": result.duration_ms,
        "scope_coverage": result.scope_coverage,
        "samples_tested": result.samples_tested,
        "risk_class": risk_class,
        "scope_type": scope_type,
        "details": result.details,
    }
