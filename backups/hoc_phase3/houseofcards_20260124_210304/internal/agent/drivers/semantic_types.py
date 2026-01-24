# Layer: L2.1 — Panel Adapter Layer
# Product: ai-console
# Role: Type definitions for semantic validation
# Reference: PIN-420, L2_1_PANEL_ADAPTER_SPEC.yaml

"""
Semantic Types — Core structures for two-phase semantic validation.

Two-Phase Architecture:
    Phase A: Intent Guardrails (design-time, human-facing)
    Phase B: Semantic Reality (proof-time, system-facing)

Key Invariant:
    - Intent rules must never depend on SDSR or APIs
    - Semantic rules must never judge human intent quality

These types enforce semantic authority in the panel pipeline.
Semantics are declared in intent, validated mechanically, enforced everywhere.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ViolationClass(str, Enum):
    """Class of violation — determines ownership and fix path."""
    INTENT = "INTENT_VIOLATION"      # Phase A: Human/design-time
    SEMANTIC = "SEMANTIC_VIOLATION"  # Phase B: System/proof-time


class SemanticSeverity(str, Enum):
    """Severity of semantic violations."""
    BLOCKING = "BLOCKING"  # Pipeline must stop
    WARNING = "WARNING"    # Pipeline continues but flags issue


class IntentFailureCode(str, Enum):
    """Phase A failure codes — Intent Guardrails (design-time)."""
    INT_001 = "INT-001"  # Signal not provable
    INT_002 = "INT-002"  # Capability cardinality exceeded
    INT_003 = "INT-003"  # Semantic duplication
    INT_004 = "INT-004"  # Contradictory intents
    INT_005 = "INT-005"  # Missing evolution path
    INT_006 = "INT-006"  # Unbounded intent scope
    INT_007 = "INT-007"  # Missing semantic contract
    INT_008 = "INT-008"  # Invalid capability reference


class SemanticFailureCode(str, Enum):
    """Phase B failure codes — Semantic Reality (proof-time)."""
    SEM_001 = "SEM-001"  # Signal not translated
    SEM_002 = "SEM-002"  # Capability not observed
    SEM_003 = "SEM-003"  # API field missing
    SEM_004 = "SEM-004"  # Signal type mismatch
    SEM_005 = "SEM-005"  # Semantic contract missing
    SEM_006 = "SEM-006"  # Cross-panel inconsistency
    SEM_007 = "SEM-007"  # Required signal missing default
    SEM_008 = "SEM-008"  # Computed signal function missing


# Union type for both failure code types
FailureCode = SemanticFailureCode | IntentFailureCode


@dataclass
class SemanticContext:
    """Context for a semantic validation check."""
    panel_id: str = ""
    slot_id: str = ""
    signal: str = ""
    capability_id: str = ""
    source: str = ""  # Where this binding was declared


@dataclass
class SemanticViolation:
    """A single semantic violation (Phase A or Phase B)."""
    code: FailureCode
    severity: SemanticSeverity
    message: str
    context: SemanticContext
    vclass: ViolationClass = ViolationClass.SEMANTIC
    evidence: Dict[str, Any] = field(default_factory=dict)
    fix_owner: str = ""
    fix_action: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "code": self.code.value,
            "class": self.vclass.value,
            "severity": self.severity.value,
            "message": self.message,
            "panel_id": self.context.panel_id,
            "slot_id": self.context.slot_id,
            "signal": self.context.signal,
            "capability_id": self.context.capability_id,
            "source": self.context.source,
            "evidence": self.evidence,
            "fix_owner": self.fix_owner,
            "fix_action": self.fix_action,
        }

    @property
    def is_intent_violation(self) -> bool:
        """True if this is a Phase A (intent) violation."""
        return self.vclass == ViolationClass.INTENT

    @property
    def is_semantic_violation(self) -> bool:
        """True if this is a Phase B (semantic) violation."""
        return self.vclass == ViolationClass.SEMANTIC


@dataclass
class SemanticReport:
    """Complete two-phase semantic validation report."""
    validated_at: datetime
    panels_checked: int = 0
    signals_checked: int = 0
    capabilities_checked: int = 0
    intents_checked: int = 0
    phase_a_complete: bool = False
    phase_b_complete: bool = False
    violations: List[SemanticViolation] = field(default_factory=list)

    def add(self, violation: Optional[SemanticViolation]) -> None:
        """Add a violation if not None."""
        if violation:
            self.violations.append(violation)

    def blocking(self) -> List[SemanticViolation]:
        """Get all blocking violations."""
        return [v for v in self.violations if v.severity == SemanticSeverity.BLOCKING]

    def warnings(self) -> List[SemanticViolation]:
        """Get all warning violations."""
        return [v for v in self.violations if v.severity == SemanticSeverity.WARNING]

    def intent_violations(self) -> List[SemanticViolation]:
        """Get Phase A (intent guardrail) violations."""
        return [v for v in self.violations if v.vclass == ViolationClass.INTENT]

    def semantic_violations(self) -> List[SemanticViolation]:
        """Get Phase B (semantic reality) violations."""
        return [v for v in self.violations if v.vclass == ViolationClass.SEMANTIC]

    def phase_a_blocking(self) -> List[SemanticViolation]:
        """Get blocking Phase A violations."""
        return [v for v in self.intent_violations() if v.severity == SemanticSeverity.BLOCKING]

    def phase_b_blocking(self) -> List[SemanticViolation]:
        """Get blocking Phase B violations."""
        return [v for v in self.semantic_violations() if v.severity == SemanticSeverity.BLOCKING]

    def is_valid(self) -> bool:
        """Report is valid if no blocking violations."""
        return len(self.blocking()) == 0

    def phase_a_valid(self) -> bool:
        """Phase A is valid if no blocking intent violations."""
        return len(self.phase_a_blocking()) == 0

    def phase_b_valid(self) -> bool:
        """Phase B is valid if no blocking semantic violations."""
        return len(self.phase_b_blocking()) == 0

    def summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        by_code: Dict[str, int] = {}
        for v in self.violations:
            by_code[v.code.value] = by_code.get(v.code.value, 0) + 1

        by_class: Dict[str, int] = {}
        for v in self.violations:
            by_class[v.vclass.value] = by_class.get(v.vclass.value, 0) + 1

        return {
            "valid": self.is_valid(),
            "validated_at": self.validated_at.isoformat(),
            "panels_checked": self.panels_checked,
            "signals_checked": self.signals_checked,
            "capabilities_checked": self.capabilities_checked,
            "intents_checked": self.intents_checked,
            "phase_a_complete": self.phase_a_complete,
            "phase_b_complete": self.phase_b_complete,
            "phase_a_valid": self.phase_a_valid(),
            "phase_b_valid": self.phase_b_valid(),
            "total_violations": len(self.violations),
            "blocking_count": len(self.blocking()),
            "warning_count": len(self.warnings()),
            "intent_violations": len(self.intent_violations()),
            "semantic_violations": len(self.semantic_violations()),
            "by_code": by_code,
            "by_class": by_class,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to full dictionary."""
        return {
            **self.summary(),
            "violations": [v.to_dict() for v in self.violations],
        }


@dataclass
class SemanticBinding:
    """A validated semantic binding between panel signal and capability field."""
    panel_id: str
    slot_id: str
    signal: str
    capability_id: str
    api_field: str
    default_value: Any
    is_computed: bool = False
    compute_function: Optional[str] = None
    validated: bool = False
    validation_errors: List[str] = field(default_factory=list)
