# Activity Domain DTO Rules

**Status:** ENFORCED
**Effective:** 2026-01-23
**Scope:** `houseofcards/customer/activity/`
**Reference:** HOC_activity_deep_audit_report.md

---

## Purpose

This document codifies DTO ownership and composition rules for the Activity domain.
These rules prevent the semantic indecision and duplication that erodes domain clarity.

---

## Core Invariants

### 1. Engine Ownership Rule

> **Engines own canonical state DTOs. Facades only compose or extend. No facade may redefine engine state.**

| Owner | Responsibility |
|-------|----------------|
| **Engines** | Define canonical dataclasses for domain state |
| **Facades** | Compose, extend, or project engine DTOs |

**Violations:**
- Facade redefines a dataclass that exists in an engine
- Facade creates state DTO that should be owned by engine

**Example:**
```python
# ❌ WRONG - Facade redefines engine state
# facades/activity_facade.py
@dataclass
class SignalFeedbackResult:  # Duplicate of engine's SignalFeedbackStatus
    acknowledged: bool = False
    ...

# ✅ CORRECT - Facade imports from engine
from app.services.activity.signal_feedback_service import SignalFeedbackStatus
```

---

### 2. Feedback State Ownership

> **Feedback state is owned by engines, never redefined by facades.**

The canonical feedback state is `SignalFeedbackStatus` in `signal_feedback_service.py`.
No facade may create an alternative representation.

---

### 3. Detail Extends Summary Rule

> **Detail DTOs must extend summary DTOs, never re-declare shared fields.**

This prevents field drift and guarantees backward compatibility.

**Example:**
```python
# ❌ WRONG - 91% field duplication
@dataclass
class RunSummaryResult:
    run_id: str
    tenant_id: str | None
    # ... 20 more fields

@dataclass
class RunDetailResult:  # Duplicates all 22 fields!
    run_id: str
    tenant_id: str | None
    # ... 20 more fields
    goal: str | None
    error_message: str | None

# ✅ CORRECT - Inheritance
@dataclass
class RunDetailResult(RunSummaryResult):
    goal: str | None = None
    error_message: str | None = None
```

---

### 4. Structural Identity Rule

> **If structures are identical today, they will diverge accidentally tomorrow.**

When two DTOs have 100% structural overlap with only semantic name differences,
they MUST be consolidated into a single type.

**Example:**
```python
# ❌ WRONG - 100% identical structure
@dataclass
class LiveRunsResult:
    items: list[RunSummaryV2Result]
    total: int
    has_more: bool
    generated_at: datetime

@dataclass
class CompletedRunsResult:  # Identical!
    items: list[RunSummaryV2Result]
    total: int
    has_more: bool
    generated_at: datetime

# ✅ CORRECT - Unified with discriminator
@dataclass
class RunsResult:
    state: str  # "LIVE" or "COMPLETED"
    items: list[RunSummaryV2Result]
    total: int
    has_more: bool
    generated_at: datetime
```

---

### 5. Derived Projection Rule

> **Derived views must be explicitly labeled as such.**

When a DTO is a subset or projection of another, document the relationship
to prevent "why don't these numbers match?" confusion.

**Example:**
```python
@dataclass
class RiskSignalsResult:
    """
    NOTE: This is a DERIVED PROJECTION of MetricsResult.
    If you need full metrics, use MetricsResult directly.
    """
    at_risk_count: int  # Subset of MetricsResult
    ...
```

---

### 6. No Free-Text Categorical Fields

> **Signals are governance inputs — they must be enumerable.**

All categorical fields (signal types, severity, risk types) must use
canonical enums defined in `engines/activity_enums.py`.

**Canonical Enums:**
- `SignalType` - Types of signals
- `SeverityLevel` - Display severity (HIGH/MEDIUM/LOW)
- `RunState` - LIVE/COMPLETED
- `RiskType` - COST/TIME/TOKENS/RATE
- `EvidenceHealth` - FLOWING/DEGRADED/MISSING

---

### 7. Severity Representation Rule

> **Engines speak numbers, facades speak labels.**

| Layer | Representation | Example |
|-------|----------------|---------|
| Engine | `severity_score: float` | 0.0 - 1.0 |
| Facade | `severity_level: str` | "HIGH", "MEDIUM", "LOW" |

Use `SeverityLevel.from_score()` for conversion at facade boundaries.

---

## File Ownership Matrix

| File | Owns | Imports From |
|------|------|--------------|
| `engines/activity_enums.py` | `SignalType`, `SeverityLevel`, `RunState`, `RiskType`, `EvidenceHealth` | — |
| `engines/signal_feedback_service.py` | `SignalFeedbackStatus`, `AcknowledgeResult`, `SuppressResult` | — |
| `engines/attention_ranking_service.py` | `AttentionSignal`, `AttentionQueueResult` | — |
| `engines/cost_analysis_service.py` | `CostAnomaly`, `CostAnalysisResult` | — |
| `engines/pattern_detection_service.py` | `DetectedPattern`, `PatternDetectionResult` | — |
| `facades/activity_facade.py` | Composed/extended DTOs only | All engines |

---

## Audit Checklist

Before adding a new DTO, verify:

- [ ] Is this state owned by an engine? → Define in engine, import in facade
- [ ] Does a similar DTO already exist? → Extend or compose, don't duplicate
- [ ] Are there shared fields with an existing DTO? → Use inheritance
- [ ] Is this a categorical field? → Use or extend canonical enums
- [ ] Is this a derived view? → Document the source relationship

---

## References

- `HOC_activity_deep_audit_report.md` - Original audit findings
- `ACT-DUP-001` through `ACT-DUP-006` - Issue IDs

---

*These rules exist because semantic indecision quietly rots a domain.
Fix it now, cheaply — or fix it later, expensively.*
