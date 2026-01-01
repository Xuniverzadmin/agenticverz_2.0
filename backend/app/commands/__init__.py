# Layer: L4 — Domain Commands
# Product: system-wide
# Role: Package for L4 domain command facades
# Reference: PIN-258 Phase F

"""
L4 Domain Commands Package

This package contains L4 domain command facades that:
- Receive domain facts (not execution context)
- Make domain decisions
- Produce command specs or rejections
- Delegate to L5 for execution (L4 → L5 is allowed)

Commands must:
- Only import from L4, L5, and L6 (L4 → L5 allowed per layer rules)
- Never import from L1, L2, L3
- Authorize and delegate, not contain execution logic
- Return result types, not raw L5 objects
"""

from app.commands.policy_command import (
    ApprovalConfig,
    PolicyEvaluationResult,
    PolicyViolation,
    check_policy_violations,
    evaluate_policy,
    record_approval_created,
    record_approval_outcome,
    record_escalation,
    record_webhook_used,
    simulate_cost,
)
from app.commands.runtime_command import (
    DEFAULT_BUDGET_CENTS,
    DEFAULT_MAX_CONCURRENT,
    DEFAULT_RATE_LIMIT_PER_MINUTE,
    DEFAULT_SKILL_METADATA,
    SUPPORTED_QUERY_TYPES,
    CapabilitiesInfo,
    QueryResult,
    ResourceContractInfo,
    SkillInfo,
    execute_query,
    get_all_skill_descriptors,
    get_capabilities,
    get_resource_contract,
    get_skill_info,
    get_supported_query_types,
    list_skills,
    query_allowed_skills,
    query_execution_history,
    query_last_step_outcome,
    query_remaining_budget,
    query_skills_for_goal,
)
from app.commands.worker_execution_command import (
    ReplayResult,
    WorkerExecutionResult,
    calculate_cost_cents,
    convert_brand_request,
    execute_worker,
    get_brand_schema_types,
    replay_execution,
)

__all__ = [
    # Constants
    "DEFAULT_BUDGET_CENTS",
    "DEFAULT_RATE_LIMIT_PER_MINUTE",
    "DEFAULT_MAX_CONCURRENT",
    "SUPPORTED_QUERY_TYPES",
    "DEFAULT_SKILL_METADATA",
    # Result types
    "QueryResult",
    "SkillInfo",
    "ResourceContractInfo",
    "CapabilitiesInfo",
    # Query commands
    "get_supported_query_types",
    "query_remaining_budget",
    "query_execution_history",
    "query_allowed_skills",
    "query_last_step_outcome",
    "query_skills_for_goal",
    "execute_query",
    # Skill commands
    "get_skill_info",
    "list_skills",
    "get_all_skill_descriptors",
    # Contract commands
    "get_resource_contract",
    # Capability commands
    "get_capabilities",
    # Worker execution commands (Phase F-3)
    "WorkerExecutionResult",
    "ReplayResult",
    "calculate_cost_cents",
    "convert_brand_request",
    "execute_worker",
    "get_brand_schema_types",
    "replay_execution",
    # Policy commands (Phase F-3)
    "PolicyViolation",
    "PolicyEvaluationResult",
    "ApprovalConfig",
    "simulate_cost",
    "check_policy_violations",
    "evaluate_policy",
    "record_approval_created",
    "record_approval_outcome",
    "record_escalation",
    "record_webhook_used",
]
