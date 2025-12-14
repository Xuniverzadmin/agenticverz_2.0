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

from .schema import (
    SBASchema,
    WinningAspiration,
    WhereToPlay,
    HowToWin,
    CapabilitiesCapacity,
    EnablingManagementSystems,
    EnvironmentRequirements,
    GovernanceProvider,
    SBA_VERSION,
    create_minimal_sba,
    # M15.1.1: Structured dependencies
    DependencyType,
    Dependency,
    create_tool_dependency,
    create_agent_dependency,
    create_api_dependency,
    # M15.1.1: Version negotiation
    SUPPORTED_SBA_VERSIONS,
    MIN_SUPPORTED_VERSION,
    MAX_SUPPORTED_VERSION,
    DEPRECATED_VERSIONS,
    SBAVersionError,
    check_version_supported,
    check_version_deprecated,
    negotiate_version,
    get_version_info,
)
from .validator import (
    SBAValidator,
    SBAValidationResult,
    SBAValidationError,
    SBAValidationErrorCode,
    validate_sba,
    validate_at_spawn,
)
from .generator import (
    SBAGenerator,
    generate_sba_from_agent,
    generate_sba_from_spawn_input,
    retrofit_existing_agents,
    # M15.1.1: Strict mode
    GenerationQuality,
    GenerationReport,
    STRICT_MODE_REQUIREMENTS,
)
from .service import (
    SBAService,
    AgentDefinition,
    get_sba_service,
)
from .evolution import (
    # M18: SBA Evolution
    SBAEvolutionEngine,
    get_evolution_engine,
    # Drift detection
    DriftType,
    DriftSignal,
    # Boundary violations
    ViolationType,
    BoundaryViolation,
    # Strategy adjustments
    AdjustmentType,
    StrategyAdjustment,
    # Configuration
    SUCCESS_RATE_DRIFT_THRESHOLD,
    LATENCY_DRIFT_THRESHOLD,
    VIOLATION_SPIKE_THRESHOLD,
    DRIFT_WINDOW,
    STRATEGY_ADJUSTMENT_COOLDOWN,
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
