# Layer: L2.1 — Panel Adapter Layer
# Product: ai-console
# Role: Module exports for AI Console Panel Adapter
# Reference: L2_1_PANEL_ADAPTER_SPEC.yaml

"""
AI Console Panel Adapter — L2.1 Panel Evaluation Layer

This module transforms raw backend API responses into spec-compliant
panel responses with truth metadata, verification signals, and provenance.

Main Entry Points:
    - AIConsolePanelEngine: Main orchestration engine
    - get_panel_engine(): Get singleton engine instance
    - create_panel_engine(): Factory for custom instances

Architecture (Option A: Spec Interpreter):
    1. Load YAML spec (panel definitions, dependencies, determinism rules)
    2. Resolve evaluation order from dependency graph
    3. Collect raw signals from backend APIs
    4. Verify inputs against determinism rules
    5. Evaluate slots with truth metadata
    6. Check cross-slot consistency
    7. Assemble spec-compliant response envelope
    8. Emit Prometheus metrics

Components:
    - PanelSpecLoader: Load YAML spec files
    - PanelDependencyResolver: Resolve evaluation order
    - PanelSignalCollector: Collect signals from APIs
    - PanelVerificationEngine: Verify inputs, enforce determinism
    - PanelSlotEvaluator: Evaluate individual slots
    - PanelConsistencyChecker: Check cross-slot consistency
    - PanelResponseAssembler: Assemble response envelope
    - PanelMetricsEmitter: Emit Prometheus metrics
"""

# Main engine
from .ai_console_panel_engine import (
    AIConsolePanelEngine,
    create_panel_engine,
    get_panel_engine,
)

# Components (for testing and custom usage)
from .panel_spec_loader import (
    PanelSpecLoader,
    get_panel_spec_loader,
)
from .panel_dependency_resolver import (
    PanelDependencyResolver,
)
from .panel_capability_resolver import (
    PanelCapabilityResolver,
    ResolvedCapability,
    CapabilityStatus,
    CapabilityRegistryEntry,
    get_capability_resolver,
)
from .panel_signal_translator import (
    PanelSignalTranslator,
    TranslatedSignal,
    TranslationOutcome,
    get_signal_translator,
)
from .panel_signal_collector import (
    PanelSignalCollector,
    CollectedSignal,
    CollectedSignals,
    CapabilityResolutionTrace,
    create_signal_collector,
)
from .panel_verification_engine import (
    PanelVerificationEngine,
)
from .panel_slot_evaluator import (
    PanelSlotEvaluator,
)
from .panel_consistency_checker import (
    PanelConsistencyChecker,
    ConsistencyViolation,
    ConsistencyCheckResult,
    create_consistency_checker,
)
from .panel_response_assembler import (
    PanelResponseAssembler,
    create_response_assembler,
)
from .panel_metrics_emitter import (
    PanelMetricsEmitter,
    get_panel_metrics_emitter,
)

# Semantic Validator (V2 - semantic authority enforcement)
from .semantic_validator import (
    SemanticValidator,
    get_semantic_validator,
    create_semantic_validator,
)
from .semantic_types import (
    # Core types
    SemanticContext,
    SemanticViolation,
    SemanticReport,
    SemanticBinding,
    SemanticSeverity,
    # Failure codes (Phase A + Phase B)
    FailureCode,
    IntentFailureCode,
    SemanticFailureCode,
    ViolationClass,
)
from .semantic_failures import (
    FAILURE_TAXONOMY,
    SEMANTIC_FAILURE_TAXONOMY,
    INTENT_FAILURE_TAXONOMY,
    get_failure_info,
    get_fix_owner,
    get_fix_action,
    get_violation_class,
)

# Two-Phase Validator (V2.1 - intent guardrails + semantic reality)
from .intent_guardrails import (
    run_intent_guardrails,
    # Configuration
    MAX_CAPABILITIES_PER_PANEL,
    MAX_SIGNALS_PER_CAPABILITY,
    MAX_SIGNALS_PER_PANEL,
)
from .validator_engine import (
    TwoPhaseValidator,
    validate_intent,
    validate_panel,
    validate_full,
)

# Types
from .panel_types import (
    # Enums
    TruthClass,
    TruthLens,
    SlotState,
    Authority,
    NegativeAuthorityValue,
    # Data classes
    TruthMetadata,
    TimeSemantics,
    VerificationSignals,
    SlotProvenance,
    PanelSlotResult,
    # Spec types
    APISpec,
    InputSignalSpec,
    OutputSignalSpec,
    SlotSpec,
    PanelSpec,
    DependencySpec,
    DeterminismRule,
    # V2 Capability-bound types
    ConsumedCapabilitySpec,
    InputSignalsSpec,
)

__all__ = [
    # Main engine
    "AIConsolePanelEngine",
    "create_panel_engine",
    "get_panel_engine",
    # Loader
    "PanelSpecLoader",
    "get_panel_spec_loader",
    # Dependency Resolver
    "PanelDependencyResolver",
    # Capability Resolver (V2)
    "PanelCapabilityResolver",
    "ResolvedCapability",
    "CapabilityStatus",
    "CapabilityRegistryEntry",
    "get_capability_resolver",
    # Signal Translator (V2)
    "PanelSignalTranslator",
    "TranslatedSignal",
    "TranslationOutcome",
    "get_signal_translator",
    # Signal Collector
    "PanelSignalCollector",
    "CollectedSignal",
    "CollectedSignals",
    "CapabilityResolutionTrace",
    "create_signal_collector",
    # Verification
    "PanelVerificationEngine",
    # Evaluator
    "PanelSlotEvaluator",
    # Consistency
    "PanelConsistencyChecker",
    "ConsistencyViolation",
    "ConsistencyCheckResult",
    "create_consistency_checker",
    # Assembler
    "PanelResponseAssembler",
    "create_response_assembler",
    # Metrics
    "PanelMetricsEmitter",
    "get_panel_metrics_emitter",
    # Types - Enums
    "TruthClass",
    "TruthLens",
    "SlotState",
    "Authority",
    "NegativeAuthorityValue",
    # Types - Data classes
    "TruthMetadata",
    "TimeSemantics",
    "VerificationSignals",
    "SlotProvenance",
    "PanelSlotResult",
    # Types - Spec
    "APISpec",
    "InputSignalSpec",
    "OutputSignalSpec",
    "SlotSpec",
    "PanelSpec",
    "DependencySpec",
    "DeterminismRule",
    # Types - V2 Capability-bound
    "ConsumedCapabilitySpec",
    "InputSignalsSpec",
    # Semantic Validator (V2)
    "SemanticValidator",
    "get_semantic_validator",
    "create_semantic_validator",
    "SemanticContext",
    "SemanticViolation",
    "SemanticReport",
    "SemanticBinding",
    "SemanticSeverity",
    # Failure codes (Phase A + Phase B)
    "FailureCode",
    "IntentFailureCode",
    "SemanticFailureCode",
    "ViolationClass",
    # Failure taxonomy
    "FAILURE_TAXONOMY",
    "SEMANTIC_FAILURE_TAXONOMY",
    "INTENT_FAILURE_TAXONOMY",
    "get_failure_info",
    "get_fix_owner",
    "get_fix_action",
    "get_violation_class",
    # Two-Phase Validator (V2.1)
    "TwoPhaseValidator",
    "validate_intent",
    "validate_panel",
    "validate_full",
    "run_intent_guardrails",
    "MAX_CAPABILITIES_PER_PANEL",
    "MAX_SIGNALS_PER_CAPABILITY",
    "MAX_SIGNALS_PER_PANEL",
]

__version__ = "2.2.0"
