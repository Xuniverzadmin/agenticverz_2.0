# Layer: L2.1 — Panel Adapter Layer
# Product: ai-console
# Role: Shared type primitives for Panel Adapter
# Reference: L2_1_PANEL_ADAPTER_SPEC.yaml

"""
Panel Types — Shared primitives for AI Console Panel Adapter

All type definitions used across the panel adapter system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# =============================================================================
# ENUMS — Canonical values from spec
# =============================================================================


class TruthClass(str, Enum):
    """What type of truth this slot represents."""
    INTERPRETATION = "interpretation"
    EVIDENCE = "evidence"
    EXECUTION = "execution"


class TruthLens(str, Enum):
    """The perspective through which data is viewed."""
    RISK = "risk"
    COST = "cost"
    RELIABILITY = "reliability"
    COMPLIANCE = "compliance"
    AUDIT = "audit"
    OPERATIONAL = "operational"


class SlotState(str, Enum):
    """Data availability state."""
    AVAILABLE = "available"
    PARTIAL = "partial"
    MISSING = "missing"


class Authority(str, Enum):
    """Whether the answer is definitively yes, definitively no, or unknown."""
    AFFIRMATIVE = "affirmative"
    NEGATIVE = "negative"
    INDETERMINATE = "indeterminate"


class NegativeAuthorityValue(str, Enum):
    """Explicit negative authority values — these prove absence."""
    NO_VIOLATION = "NO_VIOLATION"
    NO_DRIFT = "NO_DRIFT"
    NO_INCIDENT = "NO_INCIDENT"
    NO_POLICY_IMPACT = "NO_POLICY_IMPACT"
    NO_THRESHOLD_BREACH = "NO_THRESHOLD_BREACH"
    NO_ANOMALY = "NO_ANOMALY"
    NO_NEAR_THRESHOLD = "NO_NEAR_THRESHOLD"
    NO_ACTIVE_RISK = "NO_ACTIVE_RISK"


# =============================================================================
# DATACLASSES — Core types
# =============================================================================


@dataclass
class PanelSlotContext:
    """Context for slot evaluation."""
    adapter_version: str
    panel_id: str
    slot_id: str
    slot_contract_id: str
    determinism_test_id: Optional[str] = None
    tenant_id: Optional[str] = None
    window: str = "24h"


@dataclass
class VerificationSignals:
    """Verification signals computed during evaluation."""
    missing_input_count: int = 0
    stale_input_count: int = 0
    contradictory_signal_count: int = 0
    unverified_signal_refs: List[str] = field(default_factory=list)


@dataclass
class TruthMetadata:
    """Truth metadata for a slot."""
    truth_class: TruthClass
    lens: TruthLens
    capability: str
    state: SlotState
    authority: Authority
    actionable: bool
    negative_authority_value: Optional[NegativeAuthorityValue] = None


@dataclass
class TimeSemantics:
    """Time semantics for a slot."""
    as_of: datetime
    evaluation_window: str
    data_cutoff_time: datetime
    staleness_threshold: str
    baseline_window: Optional[str] = None


@dataclass
class SlotProvenance:
    """Provenance tracking for a slot."""
    derived_from: List[str]
    aggregation: str
    generated_at: datetime
    adapter_version: str


@dataclass
class PanelSlotResult:
    """Complete result of slot evaluation."""
    slot_id: str
    slot_contract_id: str
    output_signals: Dict[str, Any]
    truth_metadata: TruthMetadata
    time_semantics: TimeSemantics
    verification: VerificationSignals
    provenance: SlotProvenance


@dataclass
class PanelResult:
    """Complete result of panel evaluation."""
    adapter_version: str
    panel_id: str
    panel_contract_id: str
    domain: str
    subdomain: str
    topic: str
    slots: Dict[str, PanelSlotResult]
    evaluated_at: datetime
    dependency_chain: List[str]


# =============================================================================
# SPEC TYPES — For loader
# =============================================================================


@dataclass
class InputSignalSpec:
    """Input signal definition from spec."""
    signal_id: str
    source_api: str
    type: str
    required: bool


@dataclass
class OutputSignalSpec:
    """Output signal definition from spec."""
    signal_id: str
    type: str
    customer_facing: bool
    deterministic: bool
    values: Optional[List[str]] = None


@dataclass
class APISpec:
    """API consumed by a slot (V1 legacy)."""
    path: str
    method: str
    domain: str
    signals_used: List[str]


@dataclass
class ConsumedCapabilitySpec:
    """Capability consumed by a slot (V2)."""
    capability_id: str
    signals: List[str]
    required: bool = True


@dataclass
class InputSignalsSpec:
    """Structured input signals specification (V2)."""
    raw: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SlotSpec:
    """Slot specification from YAML.

    V2.0 Changes:
    - Added consumed_capabilities for capability-bound model
    - Added input_signals structured spec
    - Added capability_binding for single-capability slots
    - APIs retained for backward compatibility
    """
    slot_id: str
    slot_contract_id: str
    slot_question: str
    truth_class: TruthClass
    lens: TruthLens
    capability: str
    state_binding: str
    apis: List[APISpec]
    required_inputs: List[str]
    output_signals: List[OutputSignalSpec]
    evaluation_window: str
    staleness_threshold: str
    # V2 capability-bound fields
    consumed_capabilities: List[ConsumedCapabilitySpec] = field(default_factory=list)
    input_signals: Optional[InputSignalsSpec] = None
    capability_binding: Optional[str] = None


@dataclass
class PanelSpec:
    """Panel specification from YAML."""
    panel_id: str
    panel_contract_id: str
    domain: str
    subdomain: str
    topic: str
    description: str
    slots: Dict[str, SlotSpec]


@dataclass
class DependencySpec:
    """Panel dependency from graph."""
    panel_id: str
    depends_on: List[str]
    evaluation_order: int
    can_short_circuit: bool


@dataclass
class DeterminismRule:
    """Determinism rule from matrix."""
    slot_id: str
    panel_id: str
    required_input: str
    missing_effect_state: str
    missing_effect_authority: str
    stale_effect_state: str
    contradictory_rule: str
    expected_negative: str
    test_id: str
