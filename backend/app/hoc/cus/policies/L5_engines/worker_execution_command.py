# Layer: L5 — Domain Engine (Command Facade)
# NOTE: Header corrected L4→L5 (2026-01-31) — file is in L5_engines/
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async (delegates to L5)
# Role: Worker execution authorization and delegation
# Callers: workers_adapter.py (L3)
# Allowed Imports: L4, L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: PIN-258 Phase F-3 Workers Cluster
# Contract: PHASE_F_FIX_DESIGN (F-W-RULE-1 to F-W-RULE-5)
#
# GOVERNANCE NOTE (F-W-RULE-3):
# This L4 command takes facts, makes authorization decisions, and delegates
# to L5 for execution. It does NOT contain execution logic itself.
# L4 → L5 import is allowed per layer rules.
#
# F-W-RULE-1: No semantic changes - all logic stays where it is.
# F-W-RULE-2: Workers are blind executors - L5 executes, L4 authorizes.
# F-W-RULE-3: This command produces authorization, not execution.

"""
Worker Execution Command (L4)

Domain command for Business Builder Worker execution. This L4 command:
1. Takes domain facts (task, brand, budget, etc.)
2. Provides authorization for execution
3. Delegates to L5 workers (since L4 → L5 is allowed)
4. Returns results

This is NOT an execution layer. It authorizes and delegates.
All execution logic remains in L5 workers.

Reference: PIN-258 Phase F-3 Workers Cluster
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# =============================================================================
# L4 Command Result Types
# =============================================================================


@dataclass
class WorkerExecutionResult:
    """Result from worker execution command."""

    success: bool
    run_id: str
    status: str
    artifacts: Optional[Dict[str, Any]] = None
    replay_token: Optional[str] = None
    cost_report: Optional[Dict[str, Any]] = None
    policy_violations: Optional[List[Dict[str, Any]]] = None
    recovery_log: Optional[List[Dict[str, Any]]] = None
    drift_metrics: Optional[Dict[str, Any]] = None
    execution_trace: Optional[List[Dict[str, Any]]] = None
    routing_decisions: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    total_tokens_used: Optional[int] = None
    total_latency_ms: Optional[int] = None


@dataclass
class ReplayResult:
    """Result from replay command."""

    success: bool
    run_id: str
    status: str
    artifacts: Optional[Dict[str, Any]] = None
    replay_token: Optional[str] = None
    cost_report: Optional[Dict[str, Any]] = None
    policy_violations: Optional[List[Dict[str, Any]]] = None
    recovery_log: Optional[List[Dict[str, Any]]] = None
    drift_metrics: Optional[Dict[str, Any]] = None
    execution_trace: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    total_tokens_used: Optional[int] = None
    total_latency_ms: Optional[int] = None


# =============================================================================
# L4 Domain Decisions: Cost Calculation
# =============================================================================
# L4 → L5 import is allowed. This exposes L5 cost calculation through L4.


def calculate_cost_cents(model: str, input_tokens: int, output_tokens: int) -> int:
    """
    Calculate LLM cost in cents.

    This L4 command delegates to L5 cost calculation.
    L4 → L5 is an allowed import per layer rules.

    Args:
        model: Model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Cost in cents

    Reference: PIN-258 Phase F-3 (F-W-RULE-1: No semantic changes)
    """
    from app.worker.runner import calculate_llm_cost_cents

    return calculate_llm_cost_cents(model, input_tokens, output_tokens)


# =============================================================================
# L4 Domain Decisions: Schema Conversion
# =============================================================================
# L4 → L5 import is allowed. This exposes L5 schemas through L4.


def get_brand_schema_types():
    """
    Get brand schema types from L5.

    L4 → L5 is an allowed import per layer rules.
    Returns the schema types needed for brand conversion.

    Reference: PIN-258 Phase F-3 (F-W-RULE-1: No semantic changes)
    """
    from app.workers.business_builder.schemas.brand import (
        AudienceSegment,
        BrandSchema,
        ForbiddenClaim,
        ToneLevel,
        ToneRule,
        VisualIdentity,
    )

    return {
        "AudienceSegment": AudienceSegment,
        "BrandSchema": BrandSchema,
        "ForbiddenClaim": ForbiddenClaim,
        "ToneLevel": ToneLevel,
        "ToneRule": ToneRule,
        "VisualIdentity": VisualIdentity,
    }


def convert_brand_request(brand_req) -> Any:
    """
    Convert API brand request to BrandSchema.

    This L4 command handles the conversion logic using L5 schemas.
    L4 → L5 is an allowed import per layer rules.

    Args:
        brand_req: Brand request from API

    Returns:
        BrandSchema instance

    Reference: PIN-258 Phase F-3 (F-W-RULE-1: No semantic changes)
    """
    types = get_brand_schema_types()
    AudienceSegment = types["AudienceSegment"]
    BrandSchema = types["BrandSchema"]
    ForbiddenClaim = types["ForbiddenClaim"]
    ToneLevel = types["ToneLevel"]
    ToneRule = types["ToneRule"]
    VisualIdentity = types["VisualIdentity"]

    # Convert tone
    tone = ToneRule(
        primary=ToneLevel(brand_req.tone.primary),
        avoid=[ToneLevel(t) for t in brand_req.tone.avoid if t in [e.value for e in ToneLevel]],
        examples_good=brand_req.tone.examples_good,
        examples_bad=brand_req.tone.examples_bad,
    )

    # Convert forbidden claims
    forbidden = [
        ForbiddenClaim(
            pattern=fc.pattern,
            reason=fc.reason,
            severity=fc.severity,
        )
        for fc in brand_req.forbidden_claims
    ]

    # Convert visual
    visual = VisualIdentity(
        primary_color=brand_req.visual.primary_color,
        secondary_color=brand_req.visual.secondary_color,
        font_heading=brand_req.visual.font_heading,
        font_body=brand_req.visual.font_body,
        logo_placement=brand_req.visual.logo_placement,
    )

    # Convert audience
    audience = []
    for a in brand_req.target_audience:
        try:
            audience.append(AudienceSegment(a))
        except ValueError:
            pass
    if not audience:
        audience = [AudienceSegment.B2B_SMB]

    return BrandSchema(
        company_name=brand_req.company_name,
        tagline=brand_req.tagline,
        mission=brand_req.mission,
        vision=brand_req.vision,
        value_proposition=brand_req.value_proposition,
        target_audience=audience,
        audience_pain_points=brand_req.audience_pain_points,
        tone=tone,
        voice_attributes=brand_req.voice_attributes,
        forbidden_claims=forbidden,
        required_disclosures=brand_req.required_disclosures,
        visual=visual,
        budget_tokens=brand_req.budget_tokens,
    )


# =============================================================================
# L4 Commands: Worker Execution (Delegates to L5)
# =============================================================================
# L4 → L5 import is allowed. L4 authorizes and delegates execution to L5.


async def execute_worker(
    task: str,
    brand: Optional[Any] = None,
    budget: Optional[int] = None,
    strict_mode: bool = False,
    depth: int = 2,
    run_id: Optional[str] = None,
    event_bus: Optional[Any] = None,
) -> WorkerExecutionResult:
    """
    Execute Business Builder Worker.

    This L4 command authorizes and delegates execution to L5.
    L4 → L5 is an allowed import per layer rules.

    F-W-RULE-2: Worker is a blind executor. This command delegates to it.
    F-W-RULE-3: This command authorizes, L5 executes.

    Args:
        task: Business/product idea
        brand: Optional brand schema
        budget: Optional budget
        strict_mode: Whether to use strict mode
        depth: Execution depth
        run_id: Optional run ID
        event_bus: Optional event bus

    Returns:
        WorkerExecutionResult with execution outcome

    Reference: PIN-258 Phase F-3 Workers Cluster
    """
    from app.workers.business_builder.worker import BusinessBuilderWorker

    # Create worker (with optional event bus)
    if event_bus is not None:
        worker = BusinessBuilderWorker(event_bus=event_bus)
    else:
        worker = BusinessBuilderWorker()

    # Delegate execution to L5 worker
    result = await worker.run(
        task=task,
        brand=brand,
        budget=budget,
        strict_mode=strict_mode,
        depth=depth,
        run_id=run_id,
    )

    # Return L4 result type
    return WorkerExecutionResult(
        success=result.success,
        run_id=run_id or "",
        status="completed" if result.success else "failed",
        artifacts=result.artifacts,
        replay_token=result.replay_token,
        cost_report=result.cost_report,
        policy_violations=result.policy_violations,
        recovery_log=result.recovery_log,
        drift_metrics=result.drift_metrics,
        execution_trace=result.execution_trace,
        routing_decisions=getattr(result, "routing_decisions", None),
        error=result.error,
        total_tokens_used=result.total_tokens_used,
        total_latency_ms=result.total_latency_ms,
    )


async def replay_execution(replay_token: str, run_id: str) -> ReplayResult:
    """
    Replay a previous execution.

    This L4 command authorizes and delegates replay to L5.
    L4 → L5 is an allowed import per layer rules.

    Args:
        replay_token: Token from previous execution
        run_id: New run ID for this replay

    Returns:
        ReplayResult with replay outcome

    Reference: PIN-258 Phase F-3 Workers Cluster
    """
    from app.workers.business_builder.worker import replay

    # Delegate replay to L5
    result = await replay(replay_token)

    # Return L4 result type
    return ReplayResult(
        success=result.success,
        run_id=run_id,
        status="completed" if result.success else "failed",
        artifacts=result.artifacts,
        replay_token=result.replay_token,
        cost_report=result.cost_report,
        policy_violations=result.policy_violations,
        recovery_log=result.recovery_log,
        drift_metrics=result.drift_metrics,
        execution_trace=result.execution_trace,
        error=result.error,
        total_tokens_used=result.total_tokens_used,
        total_latency_ms=result.total_latency_ms,
    )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Result types
    "WorkerExecutionResult",
    "ReplayResult",
    # Cost calculation
    "calculate_cost_cents",
    # Schema conversion
    "get_brand_schema_types",
    "convert_brand_request",
    # Execution commands
    "execute_worker",
    "replay_execution",
]
