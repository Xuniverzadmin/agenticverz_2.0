# Layer: L2 — API
# AUDIENCE: INTERNAL
# Role: Policy Domain Driver - Internal orchestration for policy operations
# Product: system-wide
# Temporal:
#   Trigger: api/worker
#   Execution: sync/async
# Callers: policy_layer API, governance services, worker runtime
# Allowed Imports: L4 policy engine, L5, L6 (models, db)
# Forbidden Imports: L1, L2, L3
# Reference: FACADE_CONSOLIDATION_PLAN.md, API-001 Guardrail
#
# GOVERNANCE NOTE:
# This is the INTERNAL driver for policy evaluation operations.
# CUSTOMER-facing CRUD operations use policies_facade.py (L2 API projection).
# Internal evaluation and governance services use this driver directly.


"""
Policy Domain Driver (INTERNAL)

This driver provides the internal interface for policy evaluation operations.
Used by policy_layer API, governance services, and worker runtime.

For CUSTOMER policy CRUD operations, use policies_facade.py instead.

Why Drivers (not Facades for internal use):
- Facades are API projection layers (CUSTOMER-facing)
- Drivers are orchestration layers (INTERNAL)
- Clear separation prevents confusion
- Import rules become enforceable

Usage:
    from app.services.policy.policy_driver import get_policy_driver

    driver = get_policy_driver()
    result = await driver.evaluate(eval_request, db)
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nova.services.policy.driver")

# Singleton instance
_policy_driver: Optional["PolicyDriver"] = None


class PolicyDriver:
    """
    Driver for Policy domain operations (INTERNAL).

    This is the entry point for internal code (policy_layer, governance)
    to interact with policy evaluation services.

    CUSTOMER-facing CRUD code should use policies_facade.py instead.
    """

    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize driver with optional database URL.

        Args:
            db_url: Optional database URL override. If not provided,
                    uses DATABASE_URL environment variable.
        """
        self._db_url = db_url
        self._policy_engine = None

    @property
    def _engine(self):
        """Lazy-load policy engine."""
        if self._policy_engine is None:
            from app.policy.engine import PolicyEngine
            self._policy_engine = PolicyEngine(database_url=self._db_url)
        return self._policy_engine

    # =========================================================================
    # Core Evaluation Operations
    # =========================================================================

    async def evaluate(self, request, db=None, dry_run: bool = False):
        """
        Evaluate a request against all applicable policies.

        This is the central evaluation point that every agent action
        must pass through.

        Args:
            request: PolicyEvaluationRequest with action details
            db: Database session
            dry_run: If True, don't persist or update counters

        Returns:
            PolicyEvaluationResult with decision and details
        """
        logger.debug("driver.evaluate", extra={"action_type": str(request.action_type)})
        return await self._engine.evaluate(request, db, dry_run=dry_run)

    async def pre_check(
        self,
        request_id: str,
        agent_id: str,
        goal: str,
        tenant_id: str = "default",
    ) -> Dict[str, Any]:
        """
        Pre-check policy constraints before run creation.

        Lighter weight than evaluate() - just checks basic viability.
        """
        logger.debug("driver.pre_check", extra={"agent_id": agent_id, "goal": goal})
        return await self._engine.pre_check(request_id, agent_id, goal, tenant_id)

    async def get_state(self, db=None):
        """Get the current state of the policy layer."""
        return await self._engine.get_state(db)

    async def reload_policies(self, db=None):
        """Hot-reload policies from database."""
        logger.info("driver.reload_policies")
        return await self._engine.reload_policies(db)

    # =========================================================================
    # Violation Operations
    # =========================================================================

    async def get_violations(
        self,
        db,
        violation_type=None,
        agent_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        severity_min: Optional[float] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ):
        """Get policy violations with filtering."""
        return await self._engine.get_violations(
            db,
            violation_type=violation_type,
            agent_id=agent_id,
            tenant_id=tenant_id,
            severity_min=severity_min,
            since=since,
            limit=limit,
        )

    async def get_violation(self, db, violation_id: str):
        """Get a specific violation by ID."""
        return await self._engine.get_violation(db, violation_id)

    async def acknowledge_violation(self, db, violation_id: str, notes: Optional[str] = None) -> bool:
        """Acknowledge a violation (mark as reviewed)."""
        return await self._engine.acknowledge_violation(db, violation_id, notes)

    # =========================================================================
    # Risk Ceiling Operations
    # =========================================================================

    async def get_risk_ceilings(
        self,
        db,
        tenant_id: Optional[str] = None,
        include_inactive: bool = False,
    ):
        """List all risk ceilings."""
        return await self._engine.get_risk_ceilings(db, tenant_id=tenant_id, include_inactive=include_inactive)

    async def get_risk_ceiling(self, db, ceiling_id: str):
        """Get a specific risk ceiling."""
        return await self._engine.get_risk_ceiling(db, ceiling_id)

    async def update_risk_ceiling(self, db, ceiling_id: str, updates: Dict[str, Any]):
        """Update a risk ceiling configuration."""
        return await self._engine.update_risk_ceiling(db, ceiling_id, updates)

    async def reset_risk_ceiling(self, db, ceiling_id: str) -> bool:
        """Reset a risk ceiling's current value to 0."""
        return await self._engine.reset_risk_ceiling(db, ceiling_id)

    # =========================================================================
    # Safety Rule Operations
    # =========================================================================

    async def get_safety_rules(
        self,
        db,
        tenant_id: Optional[str] = None,
        include_inactive: bool = False,
    ):
        """List all safety rules."""
        return await self._engine.get_safety_rules(db, tenant_id=tenant_id, include_inactive=include_inactive)

    async def update_safety_rule(self, db, rule_id: str, updates: Dict[str, Any]):
        """Update a safety rule configuration."""
        return await self._engine.update_safety_rule(db, rule_id, updates)

    # =========================================================================
    # Ethical Constraint Operations
    # =========================================================================

    async def get_ethical_constraints(self, db, include_inactive: bool = False):
        """List all ethical constraints."""
        return await self._engine.get_ethical_constraints(db, include_inactive=include_inactive)

    # =========================================================================
    # Cooldown Operations
    # =========================================================================

    async def get_active_cooldowns(self, db=None, agent_id: Optional[str] = None):
        """List all active cooldowns."""
        return await self._engine.get_active_cooldowns(db, agent_id=agent_id)

    async def clear_cooldowns(self, db, agent_id: str, rule_name: Optional[str] = None) -> int:
        """Clear cooldowns for an agent."""
        return await self._engine.clear_cooldowns(db, agent_id, rule_name)

    # =========================================================================
    # Metrics Operations
    # =========================================================================

    async def get_metrics(self, db=None, hours: int = 24):
        """Get policy engine metrics for the specified time window."""
        return await self._engine.get_metrics(db, hours=hours)

    # =========================================================================
    # Version Operations (GAP 1)
    # =========================================================================

    async def get_policy_versions(self, db=None, limit: int = 20, include_inactive: bool = False):
        """List all policy versions."""
        return await self._engine.get_policy_versions(db, limit=limit, include_inactive=include_inactive)

    async def get_current_version(self, db=None):
        """Get the currently active policy version."""
        return await self._engine.get_current_version(db)

    async def create_policy_version(self, db, description: str, created_by: str = "system"):
        """Create a new policy version snapshot."""
        return await self._engine.create_policy_version(db, description=description, created_by=created_by)

    async def rollback_to_version(self, db, target_version: str, reason: str, rolled_back_by: str):
        """Rollback to a previous policy version."""
        return await self._engine.rollback_to_version(
            db, target_version=target_version, reason=reason, rolled_back_by=rolled_back_by
        )

    async def get_version_provenance(self, db, version_id: str):
        """Get the provenance (change history) for a policy version."""
        return await self._engine.get_version_provenance(db, version_id)

    async def activate_policy_version(
        self, db, version_id: str, activated_by: str = "system", dry_run: bool = False
    ):
        """Activate a policy version with pre-activation integrity checks."""
        return await self._engine.activate_policy_version(
            db, version_id=version_id, activated_by=activated_by, dry_run=dry_run
        )

    # =========================================================================
    # Dependency Graph Operations (GAP 2)
    # =========================================================================

    async def get_dependency_graph(self, db=None):
        """Get the policy dependency graph."""
        return await self._engine.get_dependency_graph(db)

    async def get_policy_conflicts(self, db=None, include_resolved: bool = False):
        """List policy conflicts."""
        return await self._engine.get_policy_conflicts(db, include_resolved=include_resolved)

    async def resolve_conflict(self, db, conflict_id: str, resolution: str, resolved_by: str) -> bool:
        """Resolve a policy conflict."""
        return await self._engine.resolve_conflict(
            db, conflict_id=conflict_id, resolution=resolution, resolved_by=resolved_by
        )

    async def validate_dependency_dag(self, db=None):
        """Validate that policy dependencies form a valid DAG."""
        return await self._engine.validate_dependency_dag(db)

    async def add_dependency_with_dag_check(
        self,
        db,
        source_policy: str,
        target_policy: str,
        dependency_type: str,
        resolution_strategy: str = "source_wins",
        priority: int = 100,
        description: Optional[str] = None,
    ):
        """Add a policy dependency with DAG validation."""
        return await self._engine.add_dependency_with_dag_check(
            db,
            source_policy=source_policy,
            target_policy=target_policy,
            dependency_type=dependency_type,
            resolution_strategy=resolution_strategy,
            priority=priority,
            description=description,
        )

    def get_topological_evaluation_order(self, dependencies: List):
        """Get the topological evaluation order for policies."""
        return self._engine.get_topological_evaluation_order(dependencies)

    # =========================================================================
    # Temporal Policy Operations (GAP 3)
    # =========================================================================

    async def get_temporal_policies(
        self, db, metric: Optional[str] = None, include_inactive: bool = False
    ):
        """List temporal (sliding window) policies."""
        return await self._engine.get_temporal_policies(db, metric=metric, include_inactive=include_inactive)

    async def create_temporal_policy(self, db, data: Dict):
        """Create a new temporal policy."""
        return await self._engine.create_temporal_policy(db, data)

    async def get_temporal_utilization(
        self, db, policy_id: str, agent_id: Optional[str] = None
    ):
        """Get current utilization for a temporal policy."""
        return await self._engine.get_temporal_utilization(db, policy_id=policy_id, agent_id=agent_id)

    async def prune_temporal_metrics(
        self,
        db,
        retention_hours: int = 168,
        compact_older_than_hours: int = 24,
        max_events_per_policy: int = 10000,
    ):
        """Prune and compact temporal metric events."""
        return await self._engine.prune_temporal_metrics(
            db,
            retention_hours=retention_hours,
            compact_older_than_hours=compact_older_than_hours,
            max_events_per_policy=max_events_per_policy,
        )

    async def get_temporal_storage_stats(self, db=None):
        """Get storage statistics for temporal metrics."""
        return await self._engine.get_temporal_storage_stats(db)

    # =========================================================================
    # Context-Aware Evaluation (GAP 4)
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
        context: Optional[Dict[str, Any]] = None,
    ):
        """Context-aware policy evaluation."""
        return await self._engine.evaluate_with_context(
            db,
            action_type=action_type,
            policy_context=policy_context,
            proposed_action=proposed_action,
            target_resource=target_resource,
            estimated_cost=estimated_cost,
            data_categories=data_categories,
            context=context or {},
        )


def get_policy_driver(db_url: Optional[str] = None) -> PolicyDriver:
    """
    Get the PolicyDriver singleton.

    This is the recommended way to access policy evaluation from
    internal code (policy_layer, governance services).

    For CUSTOMER API CRUD operations, use get_policies_facade() instead.

    Args:
        db_url: Optional database URL override

    Returns:
        PolicyDriver singleton instance
    """
    global _policy_driver
    if _policy_driver is None:
        _policy_driver = PolicyDriver(db_url=db_url)
    return _policy_driver


def reset_policy_driver() -> None:
    """Reset the driver singleton (for testing)."""
    global _policy_driver
    _policy_driver = None


# Backward compatibility aliases (DEPRECATED - will be removed)
# This allows gradual migration from facade to driver
PolicyFacade = PolicyDriver
get_policy_facade = get_policy_driver
reset_policy_facade = reset_policy_driver
