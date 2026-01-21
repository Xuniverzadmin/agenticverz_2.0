# Layer: L2 — Product APIs
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Policy Layer API - Constitutional governance for multi-agent systems
# Callers: Customer Console, SDSR validation, agent runtime
# Allowed Imports: L3, L4 (via facade), L6 (models only)
# Forbidden Imports: L4 engine directly (use facade)
# Reference: API-001 Guardrail (Domain Facade Required), M19 Policy Engine
#
# These endpoints allow agents and subsystems to:
# 1. Evaluate proposed actions against policies
# 2. Query policy state and violations
# 3. Simulate policy evaluation for testing
# 4. Manage risk ceilings and safety rules
#
# NOTE: This file uses PolicyFacade per API-001 governance.
# Direct imports of PolicyEngine are forbidden.

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_async import get_async_session
from app.schemas.response import wrap_dict
from app.policy import (
    ActionType,
    PolicyEvaluationRequest,
    PolicyEvaluationResult,
    PolicyState,
    PolicyViolation,
    ViolationType,
)
from app.services.policy.facade import get_policy_facade

router = APIRouter(prefix="/policy-layer", tags=["policy-layer"])


# =============================================================================
# Request/Response Models
# =============================================================================


class EvaluateRequest(BaseModel):
    """Request to evaluate an action against policies."""

    action_type: ActionType
    agent_id: Optional[str] = None
    tenant_id: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    proposed_action: Optional[str] = None
    target_resource: Optional[str] = None
    estimated_cost: Optional[float] = None
    data_categories: Optional[List[str]] = None
    external_endpoints: Optional[List[str]] = None
    current_sba: Optional[Dict[str, Any]] = None
    proposed_modification: Optional[Dict[str, Any]] = None


class SimulateRequest(BaseModel):
    """Request to simulate policy evaluation (dry run)."""

    action_type: ActionType
    agent_id: Optional[str] = None
    tenant_id: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    proposed_action: Optional[str] = None
    target_resource: Optional[str] = None
    estimated_cost: Optional[float] = None
    # Additional simulation options
    ignore_cooldowns: bool = False
    assume_risk_ceiling_headroom: float = 1.0  # 1.0 = current, 0.0 = empty


class ViolationQuery(BaseModel):
    """Query parameters for violations."""

    violation_type: Optional[ViolationType] = None
    agent_id: Optional[str] = None
    tenant_id: Optional[str] = None
    severity_min: Optional[float] = None
    since: Optional[datetime] = None
    limit: int = Field(default=100, le=1000)


class RiskCeilingUpdate(BaseModel):
    """Update for a risk ceiling."""

    max_value: Optional[float] = None
    window_seconds: Optional[int] = None
    breach_action: Optional[str] = None
    is_active: Optional[bool] = None


class SafetyRuleUpdate(BaseModel):
    """Update for a safety rule."""

    condition: Optional[Dict[str, Any]] = None
    action: Optional[str] = None
    cooldown_seconds: Optional[int] = None
    is_active: Optional[bool] = None


class CooldownInfo(BaseModel):
    """Information about an active cooldown."""

    agent_id: str
    rule_name: str
    started_at: datetime
    expires_at: datetime
    remaining_seconds: float


class PolicyMetrics(BaseModel):
    """Metrics from the policy engine."""

    total_evaluations: int
    total_blocks: int
    total_allows: int
    total_modifications: int
    block_rate: float
    avg_evaluation_ms: float
    violations_by_type: Dict[str, int]
    evaluations_by_action: Dict[str, int]


# =============================================================================
# Core Evaluation Endpoints
# =============================================================================


@router.post("/evaluate", response_model=PolicyEvaluationResult)
async def evaluate_action(
    request: EvaluateRequest,
    db: AsyncSession = Depends(get_async_session),
) -> PolicyEvaluationResult:
    """
    Evaluate a proposed action against all applicable policies.

    This is the primary endpoint that agents MUST call before:
    - Routing decisions (CARE)
    - Task/skill execution
    - Strategy adaptation (SBA)
    - Escalation to humans
    - Self-modification
    - Agent spawning/invocation
    - Data access
    - External API calls

    Returns ALLOW, BLOCK, or MODIFY with detailed reasoning.
    """
    facade = get_policy_facade()

    eval_request = PolicyEvaluationRequest(
        action_type=request.action_type,
        agent_id=request.agent_id,
        tenant_id=request.tenant_id,
        context=request.context,
        proposed_action=request.proposed_action,
        target_resource=request.target_resource,
        estimated_cost=request.estimated_cost,
        data_categories=request.data_categories,
        external_endpoints=request.external_endpoints,
        current_sba=request.current_sba,
        proposed_modification=request.proposed_modification,
    )

    result = await facade.evaluate(eval_request, db)
    return wrap_dict(result.model_dump())


@router.post("/simulate", response_model=PolicyEvaluationResult)
async def simulate_evaluation(
    request: SimulateRequest,
    db: AsyncSession = Depends(get_async_session),
) -> PolicyEvaluationResult:
    """
    Simulate policy evaluation without side effects.

    Useful for:
    - Testing policy configurations
    - Debugging why actions are blocked
    - Pre-flight checks before batch operations

    Does NOT:
    - Record the evaluation
    - Update risk ceiling counters
    - Create violation records
    - Route to governor
    """
    facade = get_policy_facade()

    eval_request = PolicyEvaluationRequest(
        action_type=request.action_type,
        agent_id=request.agent_id,
        tenant_id=request.tenant_id,
        context=request.context,
        proposed_action=request.proposed_action,
        target_resource=request.target_resource,
        estimated_cost=request.estimated_cost,
    )

    # Simulate with dry_run=True
    result = await facade.evaluate(eval_request, db, dry_run=True)
    return wrap_dict(result.model_dump())


@router.get("/state", response_model=PolicyState)
async def get_policy_state(
    db: AsyncSession = Depends(get_async_session),
) -> PolicyState:
    """
    Get the current state of the policy layer.

    Returns summary of:
    - Active policies by category
    - Evaluation statistics
    - Violation counts
    - Risk ceiling status
    """
    facade = get_policy_facade()
    state = await facade.get_state(db)
    return wrap_dict(state.model_dump())


@router.post("/reload")
async def reload_policies(
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Hot-reload policies from database.

    Use this after updating policies to apply changes immediately
    without restarting the service.
    """
    facade = get_policy_facade()
    result = await facade.reload_policies(db)
    return wrap_dict({
        "success": True,
        "policies_loaded": result.policies_loaded,
        "risk_ceilings_loaded": result.risk_ceilings_loaded,
        "safety_rules_loaded": result.safety_rules_loaded,
        "ethical_constraints_loaded": result.ethical_constraints_loaded,
        "business_rules_loaded": result.business_rules_loaded,
        "errors": result.errors,
        "loaded_at": result.loaded_at.isoformat(),
    })


# =============================================================================
# Violation Endpoints
# =============================================================================


@router.get("/violations")
async def list_violations(
    violation_type: Optional[ViolationType] = None,
    agent_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    severity_min: Optional[float] = Query(None, ge=0.0, le=1.0),
    hours: int = Query(24, ge=1, le=720),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    List policy violations with filtering.

    Default: violations from last 24 hours.
    """
    facade = get_policy_facade()

    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    violations = await facade.get_violations(
        db,
        violation_type=violation_type,
        agent_id=agent_id,
        tenant_id=tenant_id,
        severity_min=severity_min,
        since=since,
        limit=limit,
    )
    return wrap_dict({"items": [v.model_dump() for v in violations], "total": len(violations)})


@router.get("/violations/{violation_id}", response_model=PolicyViolation)
async def get_violation(
    violation_id: str,
    db: AsyncSession = Depends(get_async_session),
) -> PolicyViolation:
    """Get a specific violation by ID."""
    facade = get_policy_facade()
    violation = await facade.get_violation(db, violation_id)
    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")
    return wrap_dict(violation.model_dump())


@router.post("/violations/{violation_id}/acknowledge")
async def acknowledge_violation(
    violation_id: str,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Acknowledge a violation (mark as reviewed).

    This does NOT dismiss the violation - it records that
    a human has reviewed it.
    """
    facade = get_policy_facade()
    success = await facade.acknowledge_violation(db, violation_id, notes)
    if not success:
        raise HTTPException(status_code=404, detail="Violation not found")
    return wrap_dict({"acknowledged": True, "violation_id": violation_id})


# =============================================================================
# Risk Ceiling Endpoints
# =============================================================================


@router.get("/risk-ceilings")
async def list_risk_ceilings(
    tenant_id: Optional[str] = None,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """List all risk ceilings with current values."""
    facade = get_policy_facade()
    ceilings = await facade.get_risk_ceilings(db, tenant_id=tenant_id, include_inactive=include_inactive)
    items = [
        {
            "id": c.id,
            "name": c.name,
            "metric": c.metric,
            "max_value": c.max_value,
            "current_value": c.current_value,
            "utilization": c.current_value / c.max_value if c.max_value > 0 else 0.0,
            "window_seconds": c.window_seconds,
            "breach_action": c.breach_action,
            "breach_count": c.breach_count,
            "is_active": c.is_active,
        }
        for c in ceilings
    ]
    return wrap_dict({"items": items, "total": len(items)})


@router.get("/risk-ceilings/{ceiling_id}")
async def get_risk_ceiling(
    ceiling_id: str,
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """Get a specific risk ceiling with current utilization."""
    facade = get_policy_facade()
    ceiling = await facade.get_risk_ceiling(db, ceiling_id)
    if not ceiling:
        raise HTTPException(status_code=404, detail="Risk ceiling not found")

    return wrap_dict({
        "id": ceiling.id,
        "name": ceiling.name,
        "description": ceiling.description,
        "metric": ceiling.metric,
        "max_value": ceiling.max_value,
        "current_value": ceiling.current_value,
        "utilization": ceiling.current_value / ceiling.max_value if ceiling.max_value > 0 else 0.0,
        "window_seconds": ceiling.window_seconds,
        "breach_action": ceiling.breach_action,
        "breach_count": ceiling.breach_count,
        "last_breach_at": ceiling.last_breach_at.isoformat() if ceiling.last_breach_at else None,
        "is_active": ceiling.is_active,
    })


@router.patch("/risk-ceilings/{ceiling_id}")
async def update_risk_ceiling(
    ceiling_id: str,
    update: RiskCeilingUpdate,
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """Update a risk ceiling configuration."""
    facade = get_policy_facade()
    ceiling = await facade.update_risk_ceiling(db, ceiling_id, update.model_dump(exclude_none=True))
    if not ceiling:
        raise HTTPException(status_code=404, detail="Risk ceiling not found")

    return wrap_dict({
        "updated": True,
        "id": ceiling.id,
        "name": ceiling.name,
        "max_value": ceiling.max_value,
    })


@router.post("/risk-ceilings/{ceiling_id}/reset")
async def reset_risk_ceiling(
    ceiling_id: str,
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """Reset a risk ceiling's current value to 0."""
    facade = get_policy_facade()
    success = await facade.reset_risk_ceiling(db, ceiling_id)
    if not success:
        raise HTTPException(status_code=404, detail="Risk ceiling not found")

    return wrap_dict({"reset": True, "ceiling_id": ceiling_id})


# =============================================================================
# Safety Rule Endpoints
# =============================================================================


@router.get("/safety-rules")
async def list_safety_rules(
    tenant_id: Optional[str] = None,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_async_session),
) -> List[Dict[str, Any]]:
    """List all safety rules."""
    facade = get_policy_facade()
    rules = await facade.get_safety_rules(db, tenant_id=tenant_id, include_inactive=include_inactive)
    items = [
        {
            "id": r.id,
            "name": r.name,
            "rule_type": r.rule_type,
            "action": r.action,
            "cooldown_seconds": r.cooldown_seconds,
            "triggered_count": r.triggered_count,
            "last_triggered_at": r.last_triggered_at.isoformat() if r.last_triggered_at else None,
            "is_active": r.is_active,
        }
        for r in rules
    ]
    return wrap_dict({"items": items, "total": len(items)})


@router.patch("/safety-rules/{rule_id}")
async def update_safety_rule(
    rule_id: str,
    update: SafetyRuleUpdate,
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """Update a safety rule configuration."""
    facade = get_policy_facade()
    rule = await facade.update_safety_rule(db, rule_id, update.model_dump(exclude_none=True))
    if not rule:
        raise HTTPException(status_code=404, detail="Safety rule not found")

    return wrap_dict({
        "updated": True,
        "id": rule.id,
        "name": rule.name,
    })


# =============================================================================
# Ethical Constraint Endpoints
# =============================================================================


@router.get("/ethical-constraints")
async def list_ethical_constraints(
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_async_session),
) -> List[Dict[str, Any]]:
    """List all ethical constraints."""
    facade = get_policy_facade()
    constraints = await facade.get_ethical_constraints(db, include_inactive=include_inactive)
    items = [
        {
            "id": c.id,
            "name": c.name,
            "constraint_type": c.constraint_type,
            "enforcement_level": c.enforcement_level,
            "violation_action": c.violation_action,
            "violated_count": c.violated_count,
            "is_active": c.is_active,
        }
        for c in constraints
    ]
    return wrap_dict({"items": items, "total": len(items)})


# =============================================================================
# Cooldown Endpoints
# =============================================================================


@router.get("/cooldowns", response_model=List[CooldownInfo])
async def list_active_cooldowns(
    agent_id: Optional[str] = None,
    db: AsyncSession = Depends(get_async_session),
) -> List[CooldownInfo]:
    """List all active cooldowns."""
    facade = get_policy_facade()
    cooldowns = await facade.get_active_cooldowns(db, agent_id=agent_id)
    return wrap_dict({"items": [c.model_dump() for c in cooldowns], "total": len(cooldowns)})


@router.delete("/cooldowns/{agent_id}")
async def clear_cooldowns(
    agent_id: str,
    rule_name: Optional[str] = None,
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Clear cooldowns for an agent.

    Use with caution - bypasses safety cooldowns.
    """
    facade = get_policy_facade()
    count = await facade.clear_cooldowns(db, agent_id, rule_name)
    return wrap_dict({"cleared": count, "agent_id": agent_id})


# =============================================================================
# Metrics Endpoint
# =============================================================================


@router.get("/metrics", response_model=PolicyMetrics)
async def get_policy_metrics(
    hours: int = Query(24, ge=1, le=720),
    db: AsyncSession = Depends(get_async_session),
) -> PolicyMetrics:
    """Get policy engine metrics for the specified time window."""
    facade = get_policy_facade()
    metrics = await facade.get_metrics(db, hours=hours)
    return metrics


# =============================================================================
# Batch Operations
# =============================================================================


@router.post("/evaluate/batch")
async def evaluate_batch(
    requests: List[EvaluateRequest],
    db: AsyncSession = Depends(get_async_session),
) -> List[PolicyEvaluationResult]:
    """
    Evaluate multiple actions in a single call.

    Useful for pre-flight checks on batch operations.
    Limited to 50 requests per batch.
    """
    if len(requests) > 50:
        raise HTTPException(status_code=400, detail="Batch size limited to 50 requests")

    facade = get_policy_facade()
    results = []

    for req in requests:
        eval_request = PolicyEvaluationRequest(
            action_type=req.action_type,
            agent_id=req.agent_id,
            tenant_id=req.tenant_id,
            context=req.context,
            proposed_action=req.proposed_action,
            target_resource=req.target_resource,
            estimated_cost=req.estimated_cost,
            data_categories=req.data_categories,
            external_endpoints=req.external_endpoints,
        )
        result = await facade.evaluate(eval_request, db)
        results.append(result)

    return wrap_dict({"items": [r.model_dump() for r in results], "total": len(results)})


# =============================================================================
# GAP 1: Policy Versioning & Provenance Endpoints
# =============================================================================


class CreateVersionRequest(BaseModel):
    """Request to create a new policy version."""

    description: str
    created_by: str = "system"


class RollbackRequest(BaseModel):
    """Request to rollback to a previous version."""

    target_version: str
    reason: str
    rolled_back_by: str = "system"


@router.get("/versions")
async def list_policy_versions(
    limit: int = Query(20, ge=1, le=100),
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_async_session),
) -> List[Dict[str, Any]]:
    """
    List all policy versions.

    Returns version history for audit and rollback purposes.
    """
    facade = get_policy_facade()
    versions = await facade.get_policy_versions(db, limit=limit, include_inactive=include_inactive)
    return wrap_dict({"items": versions, "total": len(versions)})


@router.get("/versions/current")
async def get_current_version(
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get the currently active policy version.

    This is the version being used for all evaluations.
    """
    facade = get_policy_facade()
    version = await facade.get_current_version(db)
    if not version:
        return wrap_dict({"version": "1.0.0", "is_active": True, "description": "Default"})
    return wrap_dict(version)


@router.post("/versions")
async def create_policy_version(
    request: CreateVersionRequest,
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Create a new policy version snapshot.

    This captures the current state of all policies for audit
    and potential rollback.
    """
    facade = get_policy_facade()
    version = await facade.create_policy_version(
        db,
        description=request.description,
        created_by=request.created_by,
    )
    return wrap_dict({
        "created": True,
        "version": version.version,
        "policy_hash": version.policy_hash,
        "created_at": version.created_at.isoformat(),
    })


@router.post("/versions/rollback")
async def rollback_to_version(
    request: RollbackRequest,
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Rollback to a previous policy version.

    This restores all policies to the state captured in
    the specified version.
    """
    facade = get_policy_facade()
    result = await facade.rollback_to_version(
        db,
        target_version=request.target_version,
        reason=request.reason,
        rolled_back_by=request.rolled_back_by,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Rollback failed"))

    return wrap_dict(result)


@router.get("/versions/{version_id}/provenance")
async def get_version_provenance(
    version_id: str,
    db: AsyncSession = Depends(get_async_session),
) -> List[Dict[str, Any]]:
    """
    Get the provenance (change history) for a policy version.

    Shows what changes were made and by whom.
    """
    facade = get_policy_facade()
    provenance = await facade.get_version_provenance(db, version_id)
    return wrap_dict({"items": provenance, "total": len(provenance)})


# =============================================================================
# GAP 2: Policy Dependency Graph Endpoints
# =============================================================================


@router.get("/dependencies")
async def get_dependency_graph(
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get the policy dependency graph.

    Shows relationships and potential conflicts between policies.
    """
    facade = get_policy_facade()
    graph = await facade.get_dependency_graph(db)
    return wrap_dict({
        "nodes": len(graph.nodes),
        "edges": len(graph.edges),
        "conflicts": len(graph.conflicts),
        "computed_at": graph.computed_at.isoformat(),
        "dependencies": [
            {
                "source": e.source_policy,
                "target": e.target_policy,
                "type": e.dependency_type,
                "resolution": e.resolution_strategy,
            }
            for e in graph.edges
        ],
        "active_conflicts": [
            {
                "id": c.id,
                "policy_a": c.policy_a,
                "policy_b": c.policy_b,
                "conflict_type": c.conflict_type,
                "severity": c.severity,
                "description": c.description,
                "resolved": c.resolved,
            }
            for c in graph.conflicts
            if not c.resolved
        ],
    })


@router.get("/conflicts")
async def list_conflicts(
    include_resolved: bool = False,
    db: AsyncSession = Depends(get_async_session),
) -> List[Dict[str, Any]]:
    """
    List policy conflicts.

    Conflicts occur when policies have contradictory rules.
    """
    facade = get_policy_facade()
    conflicts = await facade.get_policy_conflicts(db, include_resolved=include_resolved)
    items = [
        {
            "id": c.id,
            "policy_a": c.policy_a,
            "policy_b": c.policy_b,
            "conflict_type": c.conflict_type,
            "severity": c.severity,
            "description": c.description,
            "affected_action_types": c.affected_action_types,
            "resolved": c.resolved,
            "resolution": c.resolution,
            "detected_at": c.detected_at.isoformat(),
        }
        for c in conflicts
    ]
    return wrap_dict({"items": items, "total": len(items)})


class ResolveConflictRequest(BaseModel):
    """Request to resolve a policy conflict."""

    resolution: str
    resolved_by: str = "system"


@router.post("/conflicts/{conflict_id}/resolve")
async def resolve_conflict(
    conflict_id: str,
    request: ResolveConflictRequest,
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Resolve a policy conflict.

    Documents how the conflict should be handled during evaluation.
    """
    facade = get_policy_facade()
    result = await facade.resolve_conflict(
        db,
        conflict_id=conflict_id,
        resolution=request.resolution,
        resolved_by=request.resolved_by,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Conflict not found")

    return wrap_dict({"resolved": True, "conflict_id": conflict_id})


# =============================================================================
# GAP 3: Temporal Policy Endpoints
# =============================================================================


class TemporalPolicyCreate(BaseModel):
    """Request to create a temporal policy."""

    name: str
    description: Optional[str] = None
    temporal_type: str  # sliding_window, cumulative_daily, etc.
    metric: str
    max_value: float
    window_seconds: int
    breach_action: str = "block"
    cooldown_on_breach: int = 0
    agent_id: Optional[str] = None
    tenant_id: Optional[str] = None


@router.get("/temporal-policies")
async def list_temporal_policies(
    metric: Optional[str] = None,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_async_session),
) -> List[Dict[str, Any]]:
    """
    List temporal (sliding window) policies.

    These policies track cumulative metrics over time windows.
    """
    facade = get_policy_facade()
    policies = await facade.get_temporal_policies(db, metric=metric, include_inactive=include_inactive)
    items = [
        {
            "id": p.id,
            "name": p.name,
            "temporal_type": p.temporal_type,
            "metric": p.metric,
            "max_value": p.max_value,
            "window_seconds": p.window_seconds,
            "breach_action": p.breach_action,
            "breach_count": p.breach_count,
            "is_active": p.is_active,
        }
        for p in policies
    ]
    return wrap_dict({"items": items, "total": len(items)})


@router.post("/temporal-policies")
async def create_temporal_policy(
    request: TemporalPolicyCreate,
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Create a new temporal policy.

    Temporal policies track cumulative metrics over sliding windows.
    """
    facade = get_policy_facade()
    policy = await facade.create_temporal_policy(db, request.model_dump())

    return wrap_dict({
        "created": True,
        "id": policy.id,
        "name": policy.name,
    })


@router.get("/temporal-policies/{policy_id}/utilization")
async def get_temporal_utilization(
    policy_id: str,
    agent_id: Optional[str] = None,
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get current utilization for a temporal policy.

    Shows how much of the limit has been consumed in the current window.
    """
    facade = get_policy_facade()
    utilization = await facade.get_temporal_utilization(db, policy_id=policy_id, agent_id=agent_id)
    return wrap_dict(utilization)


# =============================================================================
# GAP 4: Context-Aware Evaluation Endpoint
# =============================================================================


class ContextAwareEvaluateRequest(BaseModel):
    """Request for context-aware policy evaluation (GAP 4)."""

    action_type: ActionType

    # Agent context
    agent_id: Optional[str] = None
    agent_type: Optional[str] = None
    agent_capabilities: List[str] = Field(default_factory=list)

    # Tenant context
    tenant_id: Optional[str] = None
    customer_tier: Optional[str] = None

    # Action chain context
    action_chain_depth: int = 0
    action_chain_ids: List[str] = Field(default_factory=list)
    origin_trigger: Optional[str] = None

    # Action details
    proposed_action: Optional[str] = None
    target_resource: Optional[str] = None
    estimated_cost: Optional[float] = None
    data_categories: Optional[List[str]] = None

    # Additional context
    context: Dict[str, Any] = Field(default_factory=dict)


@router.post("/evaluate/context-aware")
async def evaluate_with_context(
    request: ContextAwareEvaluateRequest,
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Context-aware policy evaluation (GAP 4).

    Evaluates with full agent/tenant context, action chain tracking,
    and temporal policy awareness. Returns updated context for
    use in subsequent evaluations.
    """
    from app.policy import PolicyContext

    facade = get_policy_facade()

    # Build policy context
    policy_context = PolicyContext(
        agent_id=request.agent_id,
        agent_type=request.agent_type,
        agent_capabilities=request.agent_capabilities,
        tenant_id=request.tenant_id,
        customer_tier=request.customer_tier,
        action_chain_depth=request.action_chain_depth,
        action_chain_ids=request.action_chain_ids,
        origin_trigger=request.origin_trigger,
    )

    # Evaluate with context
    result = await facade.evaluate_with_context(
        db,
        action_type=request.action_type,
        policy_context=policy_context,
        proposed_action=request.proposed_action,
        target_resource=request.target_resource,
        estimated_cost=request.estimated_cost,
        data_categories=request.data_categories,
        context=request.context,
    )

    return wrap_dict({
        "decision": result.decision.value,
        "decision_reason": result.decision_reason,
        "policies_evaluated": result.policies_evaluated,
        "temporal_policies_evaluated": result.temporal_policies_evaluated,
        "dependencies_checked": result.dependencies_checked,
        "violations": [
            {
                "type": v.violation_type.value,
                "policy": v.policy_name,
                "severity": v.severity,
                "severity_class": v.severity_class.value,
                "recoverability": v.recoverability.value,
                "description": v.description,
                "is_temporal": v.is_temporal_violation,
            }
            for v in result.violations
        ],
        "temporal_utilization": result.temporal_utilization,
        "temporal_warnings": result.temporal_warnings,
        "conflicts_detected": [
            {"policy_a": c.policy_a, "policy_b": c.policy_b, "type": c.conflict_type} for c in result.conflicts_detected
        ],
        "policy_version": result.policy_version,
        "policy_hash": result.policy_hash,
        "updated_context": result.updated_context.model_dump() if result.updated_context else None,
    })


# =============================================================================
# ISSUE 1: DAG Enforcement & Cycle Detection Endpoints
# =============================================================================


@router.get("/dependencies/dag/validate")
async def validate_dependency_dag(
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Validate that policy dependencies form a valid DAG.

    Checks for cycles in the dependency graph. Cycles cause:
    - Infinite recursion in override resolution
    - Oscillation in dependency evaluation
    - Rule folding failures
    - MODIFY rule loops

    Returns:
    - is_dag: True if graph is acyclic
    - cycles: List of detected cycles (if any)
    - topological_order: Evaluation order (if DAG is valid)
    """
    facade = get_policy_facade()
    result = await facade.validate_dependency_dag(db)
    return wrap_dict(result)


class AddDependencyRequest(BaseModel):
    """Request to add a policy dependency with DAG validation."""

    source_policy: str
    target_policy: str
    dependency_type: str  # requires, conflicts_with, overrides, modifies
    resolution_strategy: str = "source_wins"  # source_wins, target_wins, merge, escalate
    priority: int = 100
    description: Optional[str] = None


@router.post("/dependencies/add")
async def add_dependency_with_dag_check(
    request: AddDependencyRequest,
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Add a policy dependency with DAG validation.

    Blocks the addition if it would create a cycle in the
    dependency graph. This ensures the graph remains a
    valid DAG (Directed Acyclic Graph).

    Returns:
    - success: True if added
    - error: Error message if blocked due to cycle
    - blocked: True if cycle detected
    - cycle_path: The path that would form a cycle
    """
    facade = get_policy_facade()
    result = await facade.add_dependency_with_dag_check(
        db,
        source_policy=request.source_policy,
        target_policy=request.target_policy,
        dependency_type=request.dependency_type,
        resolution_strategy=request.resolution_strategy,
        priority=request.priority,
        description=request.description,
    )

    if not result.get("success"):
        if result.get("blocked"):
            raise HTTPException(
                status_code=409,
                detail={
                    "error": result.get("error"),
                    "cycle_path": result.get("cycle_path"),
                },
            )
        raise HTTPException(status_code=400, detail=result.get("error"))

    return wrap_dict(result)


@router.get("/dependencies/evaluation-order")
async def get_evaluation_order(
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get the topological evaluation order for policies.

    Returns the order in which policies should be evaluated
    based on their dependencies. Policies that depend on
    others are evaluated after their dependencies.
    """
    facade = get_policy_facade()
    dag_result = await facade.validate_dependency_dag(db)

    if not dag_result.get("is_dag"):
        return wrap_dict({
            "success": False,
            "error": "Dependency graph contains cycles",
            "cycles": dag_result.get("cycles"),
        })

    return wrap_dict({
        "success": True,
        "evaluation_order": dag_result.get("topological_order", []),
        "node_count": dag_result.get("node_count", 0),
        "edge_count": dag_result.get("edge_count", 0),
    })


# =============================================================================
# ISSUE 2: Temporal Metric Retention & Compaction Endpoints
# =============================================================================


class PruneTemporalMetricsRequest(BaseModel):
    """Request to prune temporal metrics."""

    retention_hours: int = 168  # 7 days
    compact_older_than_hours: int = 24  # Compact to hourly after 24h
    max_events_per_policy: int = 10000


@router.post("/temporal-metrics/prune")
async def prune_temporal_metrics(
    request: PruneTemporalMetricsRequest,
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Prune and compact temporal metric events.

    This prevents storage explosion by:
    1. Deleting events older than retention period
    2. Downsampling older events to hourly aggregates
    3. Capping maximum events per policy

    Should be run periodically (e.g., via cron job).
    """
    facade = get_policy_facade()
    result = await facade.prune_temporal_metrics(
        db,
        retention_hours=request.retention_hours,
        compact_older_than_hours=request.compact_older_than_hours,
        max_events_per_policy=request.max_events_per_policy,
    )

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))

    return wrap_dict(result)


@router.get("/temporal-metrics/storage-stats")
async def get_temporal_storage_stats(
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get storage statistics for temporal metrics.

    Use this to monitor storage growth and determine
    when pruning is needed.
    """
    facade = get_policy_facade()
    stats = await facade.get_temporal_storage_stats(db)
    return wrap_dict(stats)


# =============================================================================
# ISSUE 3: Version Activation with Pre-Activation Integrity Checks
# =============================================================================


class ActivateVersionRequest(BaseModel):
    """Request to activate a policy version."""

    version_id: str
    activated_by: str = "system"
    dry_run: bool = False  # If True, run checks but don't activate


@router.post("/versions/activate")
async def activate_policy_version(
    request: ActivateVersionRequest,
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Activate a policy version with pre-activation integrity checks.

    Performs comprehensive checks before activation:
    1. Dependency closure - all dependencies exist
    2. Conflict scan - no unresolved critical conflicts
    3. DAG validation - no cycles
    4. Temporal integrity - valid window configurations
    5. Severity compatibility - escalation paths exist
    6. Simulation - dry-run against test cases

    Use dry_run=True to test without activating.

    Returns:
    - success: True if activated (or would be, for dry_run)
    - all_checks_passed: True if all integrity checks pass
    - checks: Detailed results of each check
    - activated_version: The version that was activated
    """
    facade = get_policy_facade()
    result = await facade.activate_policy_version(
        db,
        version_id=request.version_id,
        activated_by=request.activated_by,
        dry_run=request.dry_run,
    )

    if not result.get("success"):
        if "Pre-activation checks failed" in result.get("error", ""):
            # Return the check results for debugging
            raise HTTPException(
                status_code=400,
                detail={
                    "error": result.get("error"),
                    "checks": result.get("checks"),
                },
            )
        raise HTTPException(status_code=400, detail=result.get("error"))

    return wrap_dict(result)


@router.post("/versions/{version_id}/check")
async def check_version_integrity(
    version_id: str,
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Run integrity checks on a version without activating.

    Shortcut for activate with dry_run=True.
    Useful for validating a version before scheduling activation.
    """
    facade = get_policy_facade()
    result = await facade.activate_policy_version(
        db,
        version_id=version_id,
        activated_by="check-only",
        dry_run=True,
    )
    return wrap_dict(result)


# =============================================================================
# Lessons Learned Endpoints (PIN-411)
# =============================================================================


class LessonConvertRequest(BaseModel):
    """Request to convert a lesson to draft proposal."""

    converted_by: str = "system"


class LessonDeferRequest(BaseModel):
    """Request to defer a lesson."""

    defer_until: datetime


class LessonDismissRequest(BaseModel):
    """Request to dismiss a lesson."""

    dismissed_by: str
    reason: str


@router.get("/lessons")
async def list_lessons(
    tenant_id: Optional[str] = None,
    lesson_type: Optional[str] = Query(None, description="Filter: failure, near_threshold, critical_success"),
    status: Optional[str] = Query(None, description="Filter: pending, converted_to_draft, deferred, dismissed"),
    severity: Optional[str] = Query(None, description="Filter: CRITICAL, HIGH, MEDIUM, LOW"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    List lessons learned.

    Returns lessons with optional filtering by type, status, and severity.
    This endpoint is for the policy-layer (L3) - internal use.

    Reference: PIN-411, POLICIES_DOMAIN_AUDIT.md Section 11
    """
    from app.services.lessons_learned_engine import get_lessons_learned_engine

    if not tenant_id:
        return wrap_dict({"error": "tenant_id required", "items": [], "total": 0})

    engine = get_lessons_learned_engine()
    lessons = engine.list_lessons(
        tenant_id=tenant_id,
        lesson_type=lesson_type,
        status=status,
        severity=severity,
        limit=limit,
        offset=offset,
    )

    return wrap_dict({
        "items": lessons,
        "total": len(lessons),
        "has_more": len(lessons) == limit,
        "filters": {
            "tenant_id": tenant_id,
            "lesson_type": lesson_type,
            "status": status,
            "severity": severity,
        },
    })


@router.get("/lessons/stats")
async def get_lesson_stats(
    tenant_id: str,
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get lesson statistics for a tenant.

    Returns counts by type and status.

    Reference: PIN-411
    """
    from app.services.lessons_learned_engine import get_lessons_learned_engine

    engine = get_lessons_learned_engine()
    stats = engine.get_lesson_stats(tenant_id=tenant_id)

    return wrap_dict(stats)


@router.get("/lessons/{lesson_id}")
async def get_lesson(
    lesson_id: str,
    tenant_id: str,
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get a specific lesson by ID.

    Returns detailed lesson information.

    Reference: PIN-411
    """
    from uuid import UUID
    from app.services.lessons_learned_engine import get_lessons_learned_engine

    engine = get_lessons_learned_engine()
    lesson = engine.get_lesson(lesson_id=UUID(lesson_id), tenant_id=tenant_id)

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    return wrap_dict(lesson)


@router.post("/lessons/{lesson_id}/convert")
async def convert_lesson_to_draft(
    lesson_id: str,
    request: LessonConvertRequest,
    tenant_id: str = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Convert a lesson to a draft policy proposal.

    Creates a new draft proposal and updates the lesson status.
    PB-S4 compliant: drafts require human approval.

    Reference: PIN-411, PB-S4
    """
    from uuid import UUID
    from app.services.lessons_learned_engine import get_lessons_learned_engine

    engine = get_lessons_learned_engine()
    proposal_id = engine.convert_lesson_to_draft(
        lesson_id=UUID(lesson_id),
        tenant_id=tenant_id,
        converted_by=request.converted_by,
    )

    if not proposal_id:
        raise HTTPException(status_code=400, detail="Failed to convert lesson")

    return wrap_dict({
        "success": True,
        "lesson_id": lesson_id,
        "draft_proposal_id": str(proposal_id),
    })


@router.post("/lessons/{lesson_id}/defer")
async def defer_lesson(
    lesson_id: str,
    request: LessonDeferRequest,
    tenant_id: str = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Defer a lesson until a future date.

    The lesson will resurface for review after the defer date.

    Reference: PIN-411
    """
    from uuid import UUID
    from app.services.lessons_learned_engine import get_lessons_learned_engine

    engine = get_lessons_learned_engine()
    success = engine.defer_lesson(
        lesson_id=UUID(lesson_id),
        tenant_id=tenant_id,
        defer_until=request.defer_until,
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to defer lesson")

    return wrap_dict({
        "success": True,
        "lesson_id": lesson_id,
        "deferred_until": request.defer_until.isoformat(),
    })


@router.post("/lessons/{lesson_id}/dismiss")
async def dismiss_lesson(
    lesson_id: str,
    request: LessonDismissRequest,
    tenant_id: str = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Dismiss a lesson (mark as not actionable).

    Dismissed lessons are preserved for audit but won't resurface.

    Reference: PIN-411
    """
    from uuid import UUID
    from app.services.lessons_learned_engine import get_lessons_learned_engine

    engine = get_lessons_learned_engine()
    success = engine.dismiss_lesson(
        lesson_id=UUID(lesson_id),
        tenant_id=tenant_id,
        dismissed_by=request.dismissed_by,
        reason=request.reason,
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to dismiss lesson")

    return wrap_dict({
        "success": True,
        "lesson_id": lesson_id,
        "dismissed_by": request.dismissed_by,
    })
