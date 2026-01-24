# Layer: L6 — Driver
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: SBA schema definitions
# Callers: agents/sba/*
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: M18 SBA

# M15.1 SBA Schema
# Canonical Strategy Cascade definition for Strategy-Bound Agents
#
# Every agent MUST satisfy this schema before spawn.
# Missing or malformed cascade = spawn blocked.
#
# M15.1.1 Updates:
# - Structured dependencies (tool/agent types)
# - Version negotiation support
# - Semantic validation hooks

from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field, field_validator, model_validator

# Schema version - must be checked at spawn time
SBA_VERSION = "1.0"

# Supported SBA versions for version negotiation
SUPPORTED_SBA_VERSIONS: Set[str] = {"1.0"}
MIN_SUPPORTED_VERSION = "1.0"
MAX_SUPPORTED_VERSION = "1.0"
DEPRECATED_VERSIONS: Set[str] = set()  # Versions that work but emit warnings


class GovernanceProvider(str, Enum):
    """Supported governance providers."""

    BUDGETLLM = "BudgetLLM"
    NONE = "None"  # Only for testing/dev


class DependencyType(str, Enum):
    """Types of dependencies an agent can have."""

    TOOL = "tool"  # Skill/tool dependency
    AGENT = "agent"  # Another agent dependency
    API = "api"  # External API dependency
    SERVICE = "service"  # Internal service dependency


class Dependency(BaseModel):
    """
    Structured dependency declaration.

    M15.1.1: Dependencies are now typed for semantic validation.
    """

    type: DependencyType = Field(..., description="Type of dependency (tool, agent, api, service)")
    name: str = Field(..., min_length=1, description="Dependency identifier")
    version: Optional[str] = Field(default=None, description="Version constraint (e.g., '>=1.0')")
    required: bool = Field(default=True, description="Whether this dependency is required")
    fallback: Optional[str] = Field(default=None, description="Fallback dependency name if primary unavailable")

    def __hash__(self):
        return hash((self.type, self.name))

    def __eq__(self, other):
        if isinstance(other, Dependency):
            return self.type == other.type and self.name == other.name
        return False


class EnvironmentRequirements(BaseModel):
    """Environment requirements for agent execution."""

    cpu: Optional[str] = Field(default="0.5", description="CPU requirement (cores or millicores)")
    memory: Optional[str] = Field(default="256Mi", description="Memory requirement (Mi/Gi)")
    budget_tokens: Optional[int] = Field(default=None, description="Maximum tokens budget for LLM calls")
    timeout_seconds: Optional[int] = Field(default=300, description="Maximum execution time")


class HowToWin(BaseModel):
    """
    How the agent will achieve its aspiration.

    Contains:
    - tasks: What the agent will do
    - tests: How to validate success
    - fulfillment_metric: Target success rate (0.0-1.0)
    """

    tasks: List[str] = Field(..., min_length=1, description="List of task descriptors the agent will execute")
    tests: List[str] = Field(
        default_factory=list, description="Validation tests mapped to tasks (can be empty for retrofitted agents)"
    )
    fulfillment_metric: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Target fulfillment score (0.0-1.0), computed by orchestrator"
    )

    @field_validator("tasks")
    @classmethod
    def validate_tasks_not_empty(cls, v: List[str]) -> List[str]:
        """Ensure tasks list is not empty and contains non-empty strings."""
        if not v:
            raise ValueError("tasks cannot be empty")
        for i, task in enumerate(v):
            if not task or not task.strip():
                raise ValueError(f"task at index {i} cannot be empty")
        return v


class CapabilitiesCapacity(BaseModel):
    """
    What the agent needs to operate.

    Contains:
    - dependencies: Structured dependencies (tool, agent, api, service)
    - legacy_dependencies: String list for backward compatibility
    - env: Runtime environment requirements

    M15.1.1: Now supports typed dependencies for semantic validation.
    """

    # Structured dependencies (preferred)
    dependencies: List[Dependency] = Field(
        default_factory=list, description="Typed dependencies (tool/agent/api/service)"
    )

    # Legacy support - plain string list
    legacy_dependencies: List[str] = Field(
        default_factory=list, description="Legacy: List of dependency names (use 'dependencies' instead)"
    )

    env: EnvironmentRequirements = Field(
        default_factory=EnvironmentRequirements, description="Environment requirements"
    )

    def get_all_dependency_names(self) -> List[str]:
        """Get all dependency names (structured + legacy)."""
        names = [d.name for d in self.dependencies]
        names.extend(self.legacy_dependencies)
        return list(set(names))

    def get_tool_dependencies(self) -> List[Dependency]:
        """Get only tool dependencies."""
        return [d for d in self.dependencies if d.type == DependencyType.TOOL]

    def get_agent_dependencies(self) -> List[Dependency]:
        """Get only agent dependencies."""
        return [d for d in self.dependencies if d.type == DependencyType.AGENT]

    def get_required_dependencies(self) -> List[Dependency]:
        """Get only required dependencies."""
        return [d for d in self.dependencies if d.required]


class EnablingManagementSystems(BaseModel):
    """
    Management systems that govern this agent.

    Contains:
    - orchestrator: The orchestrator that owns this agent
    - governance: The governance provider (MUST be BudgetLLM for production)
    """

    orchestrator: str = Field(..., min_length=1, description="Orchestrator agent name/ID that owns this worker")
    governance: GovernanceProvider = Field(
        default=GovernanceProvider.BUDGETLLM, description="Governance provider (must be BudgetLLM for production)"
    )


class WinningAspiration(BaseModel):
    """
    Why the agent exists.

    This is NOT a task list - it describes the agent's PURPOSE.
    """

    description: str = Field(
        ..., min_length=10, description="Clear statement of why this agent exists and what it aims to achieve"
    )

    @field_validator("description")
    @classmethod
    def validate_not_task_list(cls, v: str) -> str:
        """Ensure aspiration is a purpose statement, not a task list."""
        # Check for common task-list patterns
        task_indicators = [
            "1.",
            "2.",
            "3.",
            "- ",
            "* ",
            "step 1",
            "step 2",
            "first,",
            "second,",
            "third,",
        ]
        lower_v = v.lower()
        for indicator in task_indicators:
            if indicator in lower_v:
                raise ValueError(
                    "winning_aspiration should describe WHY the agent exists, "
                    "not a task list. Use how_to_win.tasks for tasks."
                )
        return v


class WhereToPlay(BaseModel):
    """
    Boundaries and scope of the agent's operation.

    Defines:
    - domain: What domain/area the agent operates in
    - input_constraints: What inputs are valid
    - allowed_tools: What tools the agent can use
    - allowed_contexts: What contexts the agent can operate in
    """

    domain: str = Field(
        ..., min_length=3, description="Domain/area of operation (e.g., 'web-scraping', 'data-analysis')"
    )
    input_constraints: Optional[Dict[str, Any]] = Field(
        default=None, description="JSON schema or constraints for valid inputs"
    )
    allowed_tools: List[str] = Field(
        default_factory=list, description="List of tools/skills the agent is allowed to use"
    )
    allowed_contexts: List[str] = Field(
        default_factory=lambda: ["job"], description="Contexts where agent can operate: job, p2p, blackboard"
    )
    boundaries: Optional[str] = Field(
        default=None, description="Natural language description of what the agent should NOT do"
    )


class SBASchema(BaseModel):
    """
    Strategy-Bound Agent (SBA) Schema.

    The canonical 5-element Strategy Cascade that every agent MUST satisfy
    before being allowed to spawn.

    Elements:
    1. winning_aspiration - WHY the agent exists
    2. where_to_play - Boundaries and scope
    3. how_to_win - Tasks, tests, fulfillment metric
    4. capabilities_capacity - Dependencies and runtime needs
    5. enabling_management_systems - Orchestrator and governance

    Version: 1.0
    """

    # Schema version for forward compatibility
    sba_version: str = Field(default=SBA_VERSION, description="SBA schema version")

    # The 5 Strategy Cascade elements
    winning_aspiration: WinningAspiration = Field(..., description="Why the agent exists (not a task list)")

    where_to_play: WhereToPlay = Field(..., description="Boundaries and scope of operation")

    how_to_win: HowToWin = Field(..., description="Tasks, tests, and fulfillment metric")

    capabilities_capacity: CapabilitiesCapacity = Field(
        default_factory=CapabilitiesCapacity, description="Dependencies and environment requirements"
    )

    enabling_management_systems: EnablingManagementSystems = Field(
        ..., description="Orchestrator and governance configuration"
    )

    # Metadata
    agent_id: Optional[str] = Field(default=None, description="Agent identifier (filled by registry)")
    created_at: Optional[str] = Field(default=None, description="ISO timestamp of creation")
    updated_at: Optional[str] = Field(default=None, description="ISO timestamp of last update")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSONB storage."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SBASchema":
        """Create from dictionary (e.g., from JSONB)."""
        return cls.model_validate(data)

    @model_validator(mode="after")
    def validate_version_supported(self) -> "SBASchema":
        """Validate that the SBA version is supported."""
        if self.sba_version not in SUPPORTED_SBA_VERSIONS:
            raise ValueError(
                f"SBA version '{self.sba_version}' is not supported. Supported versions: {SUPPORTED_SBA_VERSIONS}"
            )
        return self

    def is_version_deprecated(self) -> bool:
        """Check if this SBA version is deprecated."""
        return self.sba_version in DEPRECATED_VERSIONS

    def get_cascade_summary(self) -> str:
        """Get a human-readable summary of the strategy cascade."""
        dep_count = len(self.capabilities_capacity.dependencies) + len(self.capabilities_capacity.legacy_dependencies)
        return f"""
Strategy Cascade for {self.agent_id or "agent"}:
  Aspiration: {self.winning_aspiration.description[:80]}...
  Domain: {self.where_to_play.domain}
  Tasks: {len(self.how_to_win.tasks)} task(s)
  Dependencies: {dep_count} dep(s)
  Orchestrator: {self.enabling_management_systems.orchestrator}
  Governance: {self.enabling_management_systems.governance.value}
  Version: {self.sba_version} {"(DEPRECATED)" if self.is_version_deprecated() else ""}
""".strip()


# Convenience function for creating minimal valid SBA
def create_minimal_sba(
    agent_id: str,
    aspiration: str,
    domain: str,
    tasks: List[str],
    orchestrator: str,
) -> SBASchema:
    """
    Create a minimal valid SBA schema.

    Args:
        agent_id: Agent identifier
        aspiration: Why the agent exists
        domain: What domain it operates in
        tasks: List of tasks it performs
        orchestrator: Orchestrator that owns it

    Returns:
        Valid SBASchema
    """
    return SBASchema(
        agent_id=agent_id,
        winning_aspiration=WinningAspiration(description=aspiration),
        where_to_play=WhereToPlay(domain=domain),
        how_to_win=HowToWin(tasks=tasks),
        capabilities_capacity=CapabilitiesCapacity(),
        enabling_management_systems=EnablingManagementSystems(
            orchestrator=orchestrator,
        ),
    )


# =============================================================================
# Version Negotiation Helpers
# =============================================================================


class SBAVersionError(Exception):
    """Raised when SBA version is not supported."""

    def __init__(self, version: str, supported: Set[str]):
        self.version = version
        self.supported = supported
        super().__init__(f"SBA version '{version}' is not supported. Supported: {supported}")


def check_version_supported(version: str) -> bool:
    """Check if an SBA version is supported."""
    return version in SUPPORTED_SBA_VERSIONS


def check_version_deprecated(version: str) -> bool:
    """Check if an SBA version is deprecated."""
    return version in DEPRECATED_VERSIONS


def negotiate_version(requested: str) -> str:
    """
    Negotiate SBA version.

    Args:
        requested: Requested version string

    Returns:
        Best matching supported version

    Raises:
        SBAVersionError: If version not supported
    """
    if requested in SUPPORTED_SBA_VERSIONS:
        return requested

    # Try to find closest match (for future use)
    # For now, just reject unsupported
    raise SBAVersionError(requested, SUPPORTED_SBA_VERSIONS)


def get_version_info() -> Dict[str, Any]:
    """Get version negotiation info for API responses."""
    return {
        "current": SBA_VERSION,
        "supported": list(SUPPORTED_SBA_VERSIONS),
        "min_supported": MIN_SUPPORTED_VERSION,
        "max_supported": MAX_SUPPORTED_VERSION,
        "deprecated": list(DEPRECATED_VERSIONS),
    }


# =============================================================================
# Dependency Helpers
# =============================================================================


def create_tool_dependency(name: str, required: bool = True) -> Dependency:
    """Create a tool dependency."""
    return Dependency(type=DependencyType.TOOL, name=name, required=required)


def create_agent_dependency(name: str, required: bool = True) -> Dependency:
    """Create an agent dependency."""
    return Dependency(type=DependencyType.AGENT, name=name, required=required)


def create_api_dependency(name: str, required: bool = True) -> Dependency:
    """Create an API dependency."""
    return Dependency(type=DependencyType.API, name=name, required=required)
