# M15.1 SBA Validator
# Spawn-time enforcement of Strategy Cascade compliance
#
# Rules:
# - Missing any of the 5 cascade elements → REJECT
# - Malformed elements → REJECT
# - Unknown dependencies → REJECT (validates against registry)
# - Missing BudgetLLM governance → REJECT (production only)
#
# M15.1.1 Updates:
# - Semantic validation (tool_catalog, agent_registry lookups)
# - Version negotiation
# - Structured dependency validation

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from pydantic import ValidationError

from .schema import (
    SUPPORTED_SBA_VERSIONS,
    DependencyType,
    GovernanceProvider,
    SBASchema,
    check_version_deprecated,
)

logger = logging.getLogger("nova.agents.sba.validator")


class SBAValidationErrorCode(str, Enum):
    """Error codes for SBA validation failures."""

    MISSING_FIELD = "MISSING_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    EMPTY_TASKS = "EMPTY_TASKS"
    UNKNOWN_DEPENDENCY = "UNKNOWN_DEPENDENCY"
    GOVERNANCE_REQUIRED = "GOVERNANCE_REQUIRED"
    VERSION_MISMATCH = "VERSION_MISMATCH"
    VERSION_DEPRECATED = "VERSION_DEPRECATED"
    ORCHESTRATOR_UNKNOWN = "ORCHESTRATOR_UNKNOWN"
    ASPIRATION_IS_TASK_LIST = "ASPIRATION_IS_TASK_LIST"
    # M15.1.1: Semantic validation errors
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    AGENT_NOT_FOUND = "AGENT_NOT_FOUND"
    CONTEXT_NOT_ALLOWED = "CONTEXT_NOT_ALLOWED"
    DEPENDENCY_TYPE_MISMATCH = "DEPENDENCY_TYPE_MISMATCH"
    EMPTY_BOUNDARIES = "EMPTY_BOUNDARIES"


# Valid contexts for agents
VALID_CONTEXTS: Set[str] = {"job", "p2p", "blackboard", "standalone"}


@dataclass
class SBAValidationError:
    """A single validation error."""

    code: SBAValidationErrorCode
    field: str
    message: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class SBAValidationResult:
    """Result of SBA validation."""

    valid: bool
    errors: List[SBAValidationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validated_sba: Optional[SBASchema] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "valid": self.valid,
            "errors": [
                {
                    "code": e.code.value,
                    "field": e.field,
                    "message": e.message,
                    "details": e.details,
                }
                for e in self.errors
            ],
            "warnings": self.warnings,
        }

    def get_error_summary(self) -> str:
        """Get human-readable error summary."""
        if self.valid:
            return "SBA validation passed"

        missing = [e.field for e in self.errors if e.code == SBAValidationErrorCode.MISSING_FIELD]
        invalid = [e.field for e in self.errors if e.code == SBAValidationErrorCode.INVALID_FORMAT]

        parts = []
        if missing:
            parts.append(f"missing: {', '.join(missing)}")
        if invalid:
            parts.append(f"invalid: {', '.join(invalid)}")

        return f"SBA validation failed - {'; '.join(parts)}" if parts else "SBA validation failed"


class SBAValidator:
    """
    Validator for Strategy-Bound Agent schemas.

    Enforces:
    1. All 5 cascade elements present
    2. Valid formats for each element
    3. Dependencies exist in registry (semantic validation)
    4. BudgetLLM governance required (production)
    5. Version compatibility and negotiation
    6. Context whitelist validation
    7. Tool permission map validation

    M15.1.1: Added semantic validation for runtime correctness.
    """

    def __init__(
        self,
        known_agents: Optional[Set[str]] = None,
        known_tools: Optional[Set[str]] = None,
        enforce_governance: bool = True,
        allowed_versions: Optional[List[str]] = None,
        # M15.1.1: Semantic validation options
        semantic_validation: bool = True,
        allowed_contexts: Optional[Set[str]] = None,
        tool_permission_map: Optional[Dict[str, Set[str]]] = None,
        agent_lookup_fn: Optional[Callable[[str], bool]] = None,
        tool_lookup_fn: Optional[Callable[[str], bool]] = None,
    ):
        """
        Initialize validator.

        Args:
            known_agents: Set of registered agent IDs (for dependency validation)
            known_tools: Set of registered tool/skill IDs
            enforce_governance: Require BudgetLLM governance (True in production)
            allowed_versions: List of allowed SBA versions
            semantic_validation: Enable semantic validation (tool/agent lookups)
            allowed_contexts: Override allowed contexts (default: job, p2p, blackboard, standalone)
            tool_permission_map: Map of orchestrator -> allowed tools for permission checking
            agent_lookup_fn: Custom function to check if agent exists
            tool_lookup_fn: Custom function to check if tool exists
        """
        self.known_agents = known_agents or set()
        self.known_tools = known_tools or set()
        self.enforce_governance = enforce_governance
        self.allowed_versions = allowed_versions or list(SUPPORTED_SBA_VERSIONS)

        # M15.1.1: Semantic validation
        self.semantic_validation = semantic_validation
        self.allowed_contexts = allowed_contexts or VALID_CONTEXTS
        self.tool_permission_map = tool_permission_map or {}
        self.agent_lookup_fn = agent_lookup_fn
        self.tool_lookup_fn = tool_lookup_fn

    def validate(self, sba_data: Dict[str, Any]) -> SBAValidationResult:
        """
        Validate SBA data against schema and rules.

        Args:
            sba_data: Dictionary containing SBA fields

        Returns:
            SBAValidationResult with validation outcome
        """
        errors: List[SBAValidationError] = []
        warnings: List[str] = []

        # 1. Try Pydantic validation first
        try:
            sba = SBASchema.model_validate(sba_data)
        except ValidationError as e:
            # Convert Pydantic errors to our format
            for error in e.errors():
                field_path = ".".join(str(loc) for loc in error["loc"])
                errors.append(
                    SBAValidationError(
                        code=SBAValidationErrorCode.INVALID_FORMAT,
                        field=field_path,
                        message=error["msg"],
                        details={"type": error["type"]},
                    )
                )
            return SBAValidationResult(valid=False, errors=errors)

        # 2. Check version compatibility
        if sba.sba_version not in self.allowed_versions:
            errors.append(
                SBAValidationError(
                    code=SBAValidationErrorCode.VERSION_MISMATCH,
                    field="sba_version",
                    message=f"Version {sba.sba_version} not supported. Allowed: {self.allowed_versions}",
                    details={"provided": sba.sba_version, "allowed": self.allowed_versions},
                )
            )

        # 3. Validate governance requirement
        if self.enforce_governance:
            if sba.enabling_management_systems.governance != GovernanceProvider.BUDGETLLM:
                errors.append(
                    SBAValidationError(
                        code=SBAValidationErrorCode.GOVERNANCE_REQUIRED,
                        field="enabling_management_systems.governance",
                        message="BudgetLLM governance is required for production agents",
                        details={"provided": sba.enabling_management_systems.governance.value},
                    )
                )

        # 4. Validate dependencies against known registries
        unknown_deps = self._validate_dependencies(sba)
        for dep in unknown_deps:
            errors.append(
                SBAValidationError(
                    code=SBAValidationErrorCode.UNKNOWN_DEPENDENCY,
                    field="capabilities_capacity.dependencies",
                    message=f"Unknown dependency: {dep}",
                    details={"dependency": dep},
                )
            )

        # 5. Validate orchestrator exists
        if self.known_agents and sba.enabling_management_systems.orchestrator not in self.known_agents:
            # Only warn if we have a registry to check against
            if len(self.known_agents) > 0:
                warnings.append(
                    f"Orchestrator '{sba.enabling_management_systems.orchestrator}' "
                    "not found in agent registry (may be registered later)"
                )

        # 6. Check for empty tests (warning, not error for retrofitted agents)
        if not sba.how_to_win.tests:
            warnings.append(
                "No tests defined in how_to_win.tests. " "Recommended to add validation tests for production agents."
            )

        # 7. Check allowed_tools against registry
        if sba.where_to_play.allowed_tools:
            unknown_tools = self._validate_tools(sba)
            for tool in unknown_tools:
                warnings.append(f"Tool '{tool}' in allowed_tools not found in tool catalog")

        # 8. M15.1.1: Semantic validation
        if self.semantic_validation:
            semantic_errors, semantic_warnings = self._validate_semantic(sba)
            errors.extend(semantic_errors)
            warnings.extend(semantic_warnings)

        # 9. Version deprecation warning
        if check_version_deprecated(sba.sba_version):
            warnings.append(f"SBA version '{sba.sba_version}' is deprecated. " "Consider upgrading to a newer version.")

        return SBAValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            validated_sba=sba if len(errors) == 0 else None,
        )

    def _validate_dependencies(self, sba: SBASchema) -> List[str]:
        """Check if dependencies exist in registries."""
        if not self.known_agents and not self.known_tools:
            # No registry to validate against
            return []

        unknown = []

        # Check structured dependencies
        for dep in sba.capabilities_capacity.dependencies:
            dep_name = dep.name
            dep_type = dep.type

            # Use type-specific validation
            if dep_type == DependencyType.AGENT:
                if self.agent_lookup_fn:
                    if not self.agent_lookup_fn(dep_name):
                        unknown.append(f"agent:{dep_name}")
                elif dep_name not in self.known_agents:
                    unknown.append(f"agent:{dep_name}")
            elif dep_type == DependencyType.TOOL:
                if self.tool_lookup_fn:
                    if not self.tool_lookup_fn(dep_name):
                        unknown.append(f"tool:{dep_name}")
                elif dep_name not in self.known_tools:
                    unknown.append(f"tool:{dep_name}")
            # API and SERVICE types are not validated against local registry

        # Check legacy dependencies (untyped strings)
        for dep in sba.capabilities_capacity.legacy_dependencies:
            if dep not in self.known_agents and dep not in self.known_tools:
                unknown.append(dep)

        return unknown

    def _validate_tools(self, sba: SBASchema) -> List[str]:
        """Check if allowed tools exist in tool catalog."""
        if not self.known_tools and not self.tool_lookup_fn:
            return []

        unknown = []
        for tool in sba.where_to_play.allowed_tools:
            if self.tool_lookup_fn:
                if not self.tool_lookup_fn(tool):
                    unknown.append(tool)
            elif tool not in self.known_tools:
                unknown.append(tool)

        return unknown

    def _validate_semantic(self, sba: SBASchema) -> tuple[List[SBAValidationError], List[str]]:
        """
        M15.1.1: Semantic validation.

        Validates:
        - Context whitelist
        - Tool permission map (orchestrator -> allowed tools)
        - Agent/tool existence via lookup functions
        """
        errors: List[SBAValidationError] = []
        warnings: List[str] = []

        # 1. Validate contexts
        for ctx in sba.where_to_play.allowed_contexts:
            if ctx not in self.allowed_contexts:
                errors.append(
                    SBAValidationError(
                        code=SBAValidationErrorCode.CONTEXT_NOT_ALLOWED,
                        field="where_to_play.allowed_contexts",
                        message=f"Context '{ctx}' is not allowed. Valid: {self.allowed_contexts}",
                        details={"context": ctx, "allowed": list(self.allowed_contexts)},
                    )
                )

        # 2. Validate tool permissions if permission map exists
        orchestrator = sba.enabling_management_systems.orchestrator
        if self.tool_permission_map and orchestrator in self.tool_permission_map:
            allowed_by_orch = self.tool_permission_map[orchestrator]
            for tool in sba.where_to_play.allowed_tools:
                if tool not in allowed_by_orch:
                    errors.append(
                        SBAValidationError(
                            code=SBAValidationErrorCode.TOOL_NOT_FOUND,
                            field="where_to_play.allowed_tools",
                            message=f"Tool '{tool}' not permitted by orchestrator '{orchestrator}'",
                            details={
                                "tool": tool,
                                "orchestrator": orchestrator,
                                "permitted": list(allowed_by_orch),
                            },
                        )
                    )

        # 3. Validate agent dependencies exist
        if self.agent_lookup_fn:
            for dep in sba.capabilities_capacity.get_agent_dependencies():
                if dep.required and not self.agent_lookup_fn(dep.name):
                    errors.append(
                        SBAValidationError(
                            code=SBAValidationErrorCode.AGENT_NOT_FOUND,
                            field="capabilities_capacity.dependencies",
                            message=f"Required agent dependency '{dep.name}' not found",
                            details={"agent": dep.name, "required": True},
                        )
                    )

        # 4. Validate tool dependencies exist
        if self.tool_lookup_fn:
            for dep in sba.capabilities_capacity.get_tool_dependencies():
                if dep.required and not self.tool_lookup_fn(dep.name):
                    errors.append(
                        SBAValidationError(
                            code=SBAValidationErrorCode.TOOL_NOT_FOUND,
                            field="capabilities_capacity.dependencies",
                            message=f"Required tool dependency '{dep.name}' not found",
                            details={"tool": dep.name, "required": True},
                        )
                    )

        # 5. Warn if boundaries not defined
        if not sba.where_to_play.boundaries:
            warnings.append(
                "No boundaries defined in where_to_play.boundaries. " "Consider defining what the agent should NOT do."
            )

        return errors, warnings


# =============================================================================
# Convenience Functions
# =============================================================================


def validate_sba(
    sba_data: Dict[str, Any],
    known_agents: Optional[Set[str]] = None,
    known_tools: Optional[Set[str]] = None,
    enforce_governance: bool = True,
) -> SBAValidationResult:
    """
    Convenience function to validate SBA data.

    Args:
        sba_data: Dictionary containing SBA fields
        known_agents: Optional set of known agent IDs
        known_tools: Optional set of known tool IDs
        enforce_governance: Require BudgetLLM governance

    Returns:
        SBAValidationResult
    """
    validator = SBAValidator(
        known_agents=known_agents,
        known_tools=known_tools,
        enforce_governance=enforce_governance,
    )
    return validator.validate(sba_data)


def validate_at_spawn(
    agent_id: str,
    sba_data: Optional[Dict[str, Any]],
    registry_service=None,
) -> SBAValidationResult:
    """
    Validate SBA at spawn time.

    This is the ENFORCEMENT POINT - called by orchestrator before
    allowing any agent to spawn.

    Args:
        agent_id: Agent being spawned
        sba_data: SBA data from agent definition (can be None)
        registry_service: Optional registry service for dependency validation

    Returns:
        SBAValidationResult - if not valid, spawn MUST be blocked
    """
    # If no SBA data, immediate rejection
    if sba_data is None:
        return SBAValidationResult(
            valid=False,
            errors=[
                SBAValidationError(
                    code=SBAValidationErrorCode.MISSING_FIELD,
                    field="sba",
                    message=f"Agent '{agent_id}' has no SBA schema defined. "
                    "All agents must have a valid Strategy Cascade.",
                )
            ],
        )

    # Get known agents/tools from registry if available
    known_agents: Set[str] = set()
    known_tools: Set[str] = set()

    if registry_service:
        try:
            # Try to get known agents
            instances = registry_service.list_instances(include_stale=True)
            known_agents = {i.agent_id for i in instances}
        except Exception as e:
            logger.warning(f"Could not load agent registry: {e}")

    # Determine if governance should be enforced
    # Can be disabled via environment variable for dev/testing
    enforce_governance = os.environ.get("SBA_ENFORCE_GOVERNANCE", "true").lower() == "true"

    # Validate
    validator = SBAValidator(
        known_agents=known_agents,
        known_tools=known_tools,
        enforce_governance=enforce_governance,
    )

    result = validator.validate(sba_data)

    # Log the validation result
    if result.valid:
        logger.info(
            "sba_validation_passed",
            extra={
                "agent_id": agent_id,
                "warnings": len(result.warnings),
            },
        )
    else:
        logger.warning(
            "sba_validation_failed",
            extra={
                "agent_id": agent_id,
                "error_count": len(result.errors),
                "errors": [e.code.value for e in result.errors],
            },
        )

    return result
