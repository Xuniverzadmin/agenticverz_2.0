# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Runtime domain commands and query logic (pure logic)
# Callers: runtime_adapter.py (L3)
# Allowed Imports: L6, L7
# Forbidden Imports: L1, L2, L3, L4, sqlalchemy, sqlmodel
# Reference: PIN-258 Phase F-3 Runtime Cluster
# Contract: PHASE_F_FIX_DESIGN (L4 Command = Data)
# NOTE: Reclassified L6→L5 (2026-01-24) - no Session imports, pure logic
#
# GOVERNANCE NOTE: This L4 engine provides domain decisions for runtime operations.
# It must NOT execute skills or import L5 workers.
# All domain knowledge about skills, contracts, and queries lives here.
# L5 Runtime is for execution only.

"""
Runtime Domain Commands (L4)

Domain engine for runtime-related decisions. Provides authoritative answers for:
1. Skill descriptions - what skills exist and their metadata
2. Runtime queries - budget, history, capability information
3. Resource contracts - budget, rate limits, constraints

This is an L4 domain engine. It makes decisions based on domain facts.
It does NOT execute skills. Execution is L5's responsibility.

Reference: PIN-258 Phase F-3 Runtime Cluster
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# =============================================================================
# L4 Domain Constants (System Truth)
# =============================================================================

# Default budget for runtime operations (in cents)
DEFAULT_BUDGET_CENTS: int = 1000

# Default rate limit (requests per minute)
DEFAULT_RATE_LIMIT_PER_MINUTE: int = 100

# Default max concurrent operations
DEFAULT_MAX_CONCURRENT: int = 5

# Supported query types (L4 domain knowledge)
SUPPORTED_QUERY_TYPES: List[str] = [
    "remaining_budget_cents",
    "what_did_i_try_already",
    "allowed_skills",
    "last_step_outcome",
    "skills_available_for_goal",
]


# =============================================================================
# L4 Domain Result Types
# =============================================================================


@dataclass
class QueryResult:
    """Result from a runtime query command."""

    query_type: str
    result: Dict[str, Any]
    supported_queries: List[str] = field(default_factory=lambda: SUPPORTED_QUERY_TYPES.copy())


@dataclass
class SkillInfo:
    """Domain information about a skill."""

    skill_id: str
    name: str
    version: str
    description: str
    cost_model: Dict[str, Any]
    latency_ms: int
    failure_modes: List[Dict[str, Any]]
    constraints: Dict[str, Any]
    composition_hints: Dict[str, Any]
    inputs_schema: Optional[Dict[str, Any]] = None
    outputs_schema: Optional[Dict[str, Any]] = None


@dataclass
class ResourceContractInfo:
    """Domain information about a resource contract."""

    resource_id: str
    budget_cents: int
    rate_limit_per_minute: int
    max_concurrent: int


@dataclass
class CapabilitiesInfo:
    """Domain information about available capabilities."""

    agent_id: Optional[str]
    skills: Dict[str, Dict[str, Any]]
    budget: Dict[str, Any]
    rate_limits: Dict[str, Dict[str, Any]]
    permissions: List[str]


# =============================================================================
# L4 Default Skill Metadata (Domain Knowledge)
# =============================================================================
# This is the authoritative source for skill metadata when no runtime is available.
# It defines what the system knows about each skill's cost, latency, and failure modes.

DEFAULT_SKILL_METADATA: Dict[str, Dict[str, Any]] = {
    "http_call": {
        "cost_cents": 0,
        "latency_ms": 500,
        "failure_modes": [
            {"code": "TIMEOUT", "category": "TRANSIENT", "probability": 0.1},
            {"code": "DNS_FAILURE", "category": "TRANSIENT", "probability": 0.02},
            {"code": "HTTP_4XX", "category": "PERMANENT", "probability": 0.05},
            {"code": "HTTP_5XX", "category": "TRANSIENT", "probability": 0.03},
        ],
        "constraints": {"max_timeout_ms": 30000, "blocked_hosts": ["localhost", "169.254.169.254"]},
        "composition_hints": {
            "often_followed_by": ["json_transform", "llm_invoke"],
            "often_preceded_by": ["cache_lookup"],
            "anti_patterns": ["calling same URL repeatedly without cache"],
        },
    },
    "llm_invoke": {
        "cost_cents": 5,
        "latency_ms": 2000,
        "failure_modes": [
            {"code": "RATE_LIMITED", "category": "TRANSIENT", "probability": 0.05},
            {"code": "CONTEXT_OVERFLOW", "category": "PERMANENT", "probability": 0.02},
            {"code": "TIMEOUT", "category": "TRANSIENT", "probability": 0.03},
        ],
        "constraints": {"max_tokens": 100000, "models_allowed": ["claude-3-haiku", "claude-sonnet-4-20250514"]},
        "composition_hints": {
            "often_followed_by": ["json_transform", "http_call"],
            "often_preceded_by": ["http_call", "fs_read"],
            "anti_patterns": ["chaining multiple LLM calls without caching"],
        },
    },
    "json_transform": {
        "cost_cents": 0,
        "latency_ms": 10,
        "failure_modes": [
            {"code": "SCHEMA_VALIDATION_FAILED", "category": "PERMANENT", "probability": 0.01},
            {"code": "TRANSFORM_ERROR", "category": "PERMANENT", "probability": 0.01},
        ],
        "constraints": {"max_input_size_bytes": 10485760},
        "composition_hints": {
            "often_followed_by": ["http_call", "llm_invoke"],
            "often_preceded_by": ["http_call", "llm_invoke"],
            "anti_patterns": [],
        },
    },
    "fs_read": {
        "cost_cents": 0,
        "latency_ms": 50,
        "failure_modes": [
            {"code": "FILE_NOT_FOUND", "category": "PERMANENT", "probability": 0.05},
            {"code": "PERMISSION_DENIED", "category": "PERMISSION", "probability": 0.02},
        ],
        "constraints": {"max_file_size_bytes": 10485760},
        "composition_hints": {
            "often_followed_by": ["llm_invoke", "json_transform"],
            "often_preceded_by": ["fs_write"],
            "anti_patterns": ["reading same file multiple times without caching"],
        },
    },
    "fs_write": {
        "cost_cents": 0,
        "latency_ms": 100,
        "failure_modes": [
            {"code": "PERMISSION_DENIED", "category": "PERMISSION", "probability": 0.05},
            {"code": "DISK_FULL", "category": "RESOURCE", "probability": 0.01},
        ],
        "constraints": {"max_file_size_bytes": 10485760},
        "composition_hints": {
            "often_followed_by": ["fs_read"],
            "often_preceded_by": ["llm_invoke", "http_call"],
            "anti_patterns": [],
        },
    },
    "webhook_send": {
        "cost_cents": 0,
        "latency_ms": 300,
        "failure_modes": [
            {"code": "TIMEOUT", "category": "TRANSIENT", "probability": 0.1},
            {"code": "HTTP_5XX", "category": "TRANSIENT", "probability": 0.05},
        ],
        "constraints": {"max_payload_bytes": 1048576},
        "composition_hints": {"often_followed_by": [], "often_preceded_by": ["json_transform"], "anti_patterns": []},
    },
    "email_send": {
        "cost_cents": 1,
        "latency_ms": 500,
        "failure_modes": [
            {"code": "DELIVERY_FAILED", "category": "TRANSIENT", "probability": 0.05},
            {"code": "RATE_LIMITED", "category": "TRANSIENT", "probability": 0.02},
        ],
        "constraints": {"max_recipients": 10, "max_body_size_bytes": 1048576},
        "composition_hints": {
            "often_followed_by": [],
            "often_preceded_by": ["llm_invoke", "json_transform"],
            "anti_patterns": ["sending same email multiple times"],
        },
    },
}


# =============================================================================
# L4 Domain Query Commands
# =============================================================================


def get_supported_query_types() -> List[str]:
    """
    Get list of supported query types.

    This is an L4 domain decision - defining what queries the system supports.

    Returns:
        List of supported query type strings
    """
    return SUPPORTED_QUERY_TYPES.copy()


def query_remaining_budget(
    spent_cents: int = 0,
    total_cents: int = DEFAULT_BUDGET_CENTS,
) -> QueryResult:
    """
    Query remaining budget.

    L4 domain decision: How to calculate and present budget information.

    Args:
        spent_cents: Amount already spent
        total_cents: Total budget available

    Returns:
        QueryResult with budget information
    """
    return QueryResult(
        query_type="remaining_budget_cents",
        result={
            "remaining_cents": total_cents - spent_cents,
            "spent_cents": spent_cents,
            "total_cents": total_cents,
        },
    )


def query_execution_history(history: Optional[List[Dict[str, Any]]] = None) -> QueryResult:
    """
    Query execution history.

    L4 domain decision: How to present execution history.

    Args:
        history: Execution history records

    Returns:
        QueryResult with history
    """
    return QueryResult(
        query_type="what_did_i_try_already",
        result={"history": history or []},
    )


def query_allowed_skills() -> QueryResult:
    """
    Query list of allowed skills.

    L4 domain decision: What skills are available.

    Returns:
        QueryResult with skill list
    """
    skills = list(DEFAULT_SKILL_METADATA.keys())
    return QueryResult(
        query_type="allowed_skills",
        result={
            "skills": skills,
            "count": len(skills),
        },
    )


def query_last_step_outcome(outcome: Optional[Dict[str, Any]] = None) -> QueryResult:
    """
    Query last step outcome.

    L4 domain decision: How to present last outcome.

    Args:
        outcome: Last execution outcome

    Returns:
        QueryResult with outcome
    """
    return QueryResult(
        query_type="last_step_outcome",
        result={"outcome": outcome},
    )


def query_skills_for_goal(goal: str) -> QueryResult:
    """
    Query skills available for a goal.

    L4 domain decision: Deterministic skill matching based on goal.

    Args:
        goal: Goal description

    Returns:
        QueryResult with matched skills
    """
    # Deterministic pseudo-matching based on goal hash
    seed = sum(ord(c) for c in goal) % 997
    all_skills = list(DEFAULT_SKILL_METADATA.keys())
    # Deterministic sort using seed
    matched = sorted(all_skills, key=lambda s: (hash(s) + seed) % 1000)
    return QueryResult(
        query_type="skills_available_for_goal",
        result={
            "goal": goal,
            "skills": matched[:5],
            "seed": seed,
        },
    )


def execute_query(query_type: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
    """
    Execute a runtime query.

    L4 domain command: Routes query to appropriate handler.

    Args:
        query_type: Type of query
        params: Query parameters

    Returns:
        QueryResult with query response
    """
    params = params or {}

    if query_type == "remaining_budget_cents":
        return query_remaining_budget()
    elif query_type == "what_did_i_try_already":
        return query_execution_history()
    elif query_type == "allowed_skills":
        return query_allowed_skills()
    elif query_type == "last_step_outcome":
        return query_last_step_outcome()
    elif query_type == "skills_available_for_goal":
        goal = params.get("goal", "")
        return query_skills_for_goal(goal)
    else:
        return QueryResult(
            query_type=query_type,
            result={
                "error": f"Unknown query type: {query_type}",
                "supported": SUPPORTED_QUERY_TYPES,
            },
        )


# =============================================================================
# L4 Skill Information Commands
# =============================================================================


def get_skill_info(skill_id: str) -> Optional[SkillInfo]:
    """
    Get domain information about a skill.

    L4 domain decision: Skill metadata and capabilities.

    Args:
        skill_id: Skill identifier

    Returns:
        SkillInfo if skill exists, None otherwise
    """
    if skill_id not in DEFAULT_SKILL_METADATA:
        return None

    meta = DEFAULT_SKILL_METADATA[skill_id]
    return SkillInfo(
        skill_id=skill_id,
        name=skill_id,
        version="0.1.0",
        description=f"{skill_id} skill for AOS runtime",
        cost_model={"base_cents": meta.get("cost_cents", 0), "per_kb_cents": 0},
        latency_ms=meta.get("latency_ms", 100),
        failure_modes=meta.get("failure_modes", []),
        constraints=meta.get("constraints", {}),
        composition_hints=meta.get("composition_hints", {}),
    )


def list_skills() -> List[str]:
    """
    List all available skill IDs.

    L4 domain decision: What skills are known to the system.

    Returns:
        List of skill IDs
    """
    return list(DEFAULT_SKILL_METADATA.keys())


def get_all_skill_descriptors() -> Dict[str, Dict[str, Any]]:
    """
    Get descriptors for all skills.

    L4 domain decision: Comprehensive skill information.

    Returns:
        Dict mapping skill_id to descriptor dict
    """
    descriptors = {}
    for skill_id in DEFAULT_SKILL_METADATA:
        meta = DEFAULT_SKILL_METADATA[skill_id]
        descriptors[skill_id] = {
            "skill_id": skill_id,
            "name": skill_id,
            "version": "0.1.0",
            "description": f"{skill_id} skill",
            "cost_model": {"base_cents": meta.get("cost_cents", 0)},
            "latency_ms": meta.get("latency_ms", 100),
        }
    return descriptors


# =============================================================================
# L4 Resource Contract Commands
# =============================================================================


def get_resource_contract(resource_id: str) -> ResourceContractInfo:
    """
    Get resource contract information.

    L4 domain decision: Default resource constraints.

    Args:
        resource_id: Resource identifier

    Returns:
        ResourceContractInfo with contract details
    """
    return ResourceContractInfo(
        resource_id=resource_id,
        budget_cents=DEFAULT_BUDGET_CENTS,
        rate_limit_per_minute=DEFAULT_RATE_LIMIT_PER_MINUTE,
        max_concurrent=DEFAULT_MAX_CONCURRENT,
    )


# =============================================================================
# L4 Capability Commands
# =============================================================================


def get_capabilities(
    agent_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> CapabilitiesInfo:
    """
    Get capabilities for an agent/tenant.

    L4 domain decision: What capabilities are available.

    Args:
        agent_id: Optional agent ID
        tenant_id: Optional tenant ID

    Returns:
        CapabilitiesInfo with capability details
    """
    skills_caps = {}
    for skill_id, meta in DEFAULT_SKILL_METADATA.items():
        skills_caps[skill_id] = {
            "available": True,
            "cost_estimate_cents": meta.get("cost_cents", 0),
            "avg_latency_ms": meta.get("latency_ms", 100),
            "rate_limit_remaining": 95,  # Default
            "known_failure_patterns": [
                fm.get("code") for fm in meta.get("failure_modes", []) if fm.get("probability", 0) > 0.05
            ],
        }

    return CapabilitiesInfo(
        agent_id=agent_id,
        skills=skills_caps,
        budget={
            "total_cents": DEFAULT_BUDGET_CENTS,
            "remaining_cents": DEFAULT_BUDGET_CENTS,
            "per_step_max_cents": 100,
        },
        rate_limits={
            "http_call": {"remaining": 95, "resets_in_seconds": 60},
            "llm_invoke": {"remaining": 50, "resets_in_seconds": 60},
        },
        permissions=["read", "write", "execute"],
    )


# =============================================================================
# Exports
# =============================================================================

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
]
