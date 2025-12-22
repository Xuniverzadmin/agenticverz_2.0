# M15.1 Strategy-Bound Agents (SBA)
# Governance layer enforcing Strategy Cascade compliance before spawn
#
# Key Components:
# - SBA Schema: Canonical 5-element strategy cascade
# - SBA Validator: Spawn-time enforcement
# - SBA Generator: Auto-generate boilerplate for existing agents
# - SBA Service: Database operations and enforcement
# - M18: SBA Evolution (drift detection, boundary tracking, strategy adjustment)
#
# Based on: PIN-071 M15 BudgetLLM A2A Integration

from .evolution import (
    DRIFT_WINDOW,
    LATENCY_DRIFT_THRESHOLD,
    STRATEGY_ADJUSTMENT_COOLDOWN,
    # Configuration
    SUCCESS_RATE_DRIFT_THRESHOLD,
    VIOLATION_SPIKE_THRESHOLD,
    # Strategy adjustments
    AdjustmentType,
    BoundaryViolation,
    DriftSignal,
    # Drift detection
    DriftType,
    # M18: SBA Evolution
    SBAEvolutionEngine,
    StrategyAdjustment,
    # Boundary violations
    ViolationType,
    get_evolution_engine,
)
from .generator import (
    STRICT_MODE_REQUIREMENTS,
    # M15.1.1: Strict mode
    GenerationQuality,
    GenerationReport,
    SBAGenerator,
    generate_sba_from_agent,
    generate_sba_from_spawn_input,
    retrofit_existing_agents,
)
from .schema import (
    DEPRECATED_VERSIONS,
    MAX_SUPPORTED_VERSION,
    MIN_SUPPORTED_VERSION,
    SBA_VERSION,
    # M15.1.1: Version negotiation
    SUPPORTED_SBA_VERSIONS,
    CapabilitiesCapacity,
    Dependency,
    # M15.1.1: Structured dependencies
    DependencyType,
    EnablingManagementSystems,
    EnvironmentRequirements,
    GovernanceProvider,
    HowToWin,
    SBASchema,
    SBAVersionError,
    WhereToPlay,
    WinningAspiration,
    check_version_deprecated,
    check_version_supported,
    create_agent_dependency,
    create_api_dependency,
    create_minimal_sba,
    create_tool_dependency,
    get_version_info,
    negotiate_version,
)
from .service import (
    AgentDefinition,
    SBAService,
    get_sba_service,
)
from .validator import (
    SBAValidationError,
    SBAValidationErrorCode,
    SBAValidationResult,
    SBAValidator,
    validate_at_spawn,
    validate_sba,
)

__all__ = [
    # Schema
    "SBASchema",
    "WinningAspiration",
    "WhereToPlay",
    "HowToWin",
    "CapabilitiesCapacity",
    "EnablingManagementSystems",
    "EnvironmentRequirements",
    "GovernanceProvider",
    "SBA_VERSION",
    "create_minimal_sba",
    # M15.1.1: Structured dependencies
    "DependencyType",
    "Dependency",
    "create_tool_dependency",
    "create_agent_dependency",
    "create_api_dependency",
    # M15.1.1: Version negotiation
    "SUPPORTED_SBA_VERSIONS",
    "MIN_SUPPORTED_VERSION",
    "MAX_SUPPORTED_VERSION",
    "DEPRECATED_VERSIONS",
    "SBAVersionError",
    "check_version_supported",
    "check_version_deprecated",
    "negotiate_version",
    "get_version_info",
    # Validator
    "SBAValidator",
    "SBAValidationResult",
    "SBAValidationError",
    "SBAValidationErrorCode",
    "validate_sba",
    "validate_at_spawn",
    # Generator
    "SBAGenerator",
    "generate_sba_from_agent",
    "generate_sba_from_spawn_input",
    "retrofit_existing_agents",
    # M15.1.1: Strict mode
    "GenerationQuality",
    "GenerationReport",
    "STRICT_MODE_REQUIREMENTS",
    # Service
    "SBAService",
    "AgentDefinition",
    "get_sba_service",
    # M18: SBA Evolution
    "SBAEvolutionEngine",
    "get_evolution_engine",
    # Drift detection
    "DriftType",
    "DriftSignal",
    # Boundary violations
    "ViolationType",
    "BoundaryViolation",
    # Strategy adjustments
    "AdjustmentType",
    "StrategyAdjustment",
    # Configuration
    "SUCCESS_RATE_DRIFT_THRESHOLD",
    "LATENCY_DRIFT_THRESHOLD",
    "VIOLATION_SPIKE_THRESHOLD",
    "DRIFT_WINDOW",
    "STRATEGY_ADJUSTMENT_COOLDOWN",
]
