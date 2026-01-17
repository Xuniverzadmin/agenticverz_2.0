# SEMANTIC_VALIDATOR: Semantic Authority Enforcement Gate

**Status:** ACTIVE
**Effective:** 2026-01-16
**Authority:** Governance Document
**Reference:** PIN-420 (Semantic Authority), HISAR.md, SDSR.md, AURORA_L2.md
**Version:** 2.1

---

## Definition

> **Semantic Validator** is the mechanical gate that enforces semantic authority between SDSR observation and HISAR binding.

The Semantic Validator answers the question:

> **SDSR proved the API works. But is the data semantically correct for THIS panel?**

SDSR proves operational truth (API responds, data flows).
Semantic Validator proves **semantic truth** (correct data, correct panel, correct meaning).

---

## Two-Phase Architecture (V2.0)

The Semantic Validator uses a **two-phase architecture**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE A: Intent Guardrails (Design-time, Human-facing)                     │
│                                                                             │
│  Question: Is this idea allowed to exist?                                   │
│  Fix Owners: Product, Architecture                                          │
│  Trigger: Intent YAML creation/modification                                 │
│                                                                             │
│  MUST NEVER depend on SDSR or APIs.                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    Phase A passes → Continue to Phase B
                    Phase A blocks → STOP (design issue)
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE B: Semantic Reality (Proof-time, System-facing)                      │
│                                                                             │
│  Question: Does reality match declared meaning?                             │
│  Fix Owners: Panel Adapter, Backend, SDSR, Intent, System                   │
│  Trigger: Signal collection, API response validation                        │
│                                                                             │
│  MUST NEVER judge human intent quality.                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Invariant

> **Phase A rules must NEVER depend on SDSR or APIs.**
> **Phase B rules must NEVER judge human intent quality.**

This separation ensures:
- Intent issues are caught at design-time (before wasting SDSR resources)
- System issues are caught at proof-time (when reality is observable)
- Fix ownership is clear and actionable

---

## Position in Pipeline

```
                        HISAR Pipeline
                        ═════════════════════════════════════════════════

Human Intent → SDSR → [SEMANTIC VALIDATOR] → Aurora Bind → Rendering
                 │              │                    │
                 │              │                    │
                 │              │                    └─► BOUND (success)
                 │              │
                 │              └─► BLOCKED + Report (semantic failure)
                 │
                 └─► FAILED + Report (operational failure)
```

### Phase Position in HISAR

The Semantic Validator sits between Phase 5 (Observation Application) and Phase 6 (Aurora Compilation):

```
Phase 4:   SDSR Verification        → API works?
Phase 5:   Observation Application  → DECLARED → OBSERVED
Phase 5.5: Trust Evaluation         → Eligible for TRUSTED?

┌─────────────────────────────────────────────────────────────┐
│  Phase 5.7: SEMANTIC VALIDATION (NEW)                       │
│                                                             │
│  • Signal completeness check                                │
│  • Capability reality check                                 │
│  • API field presence check                                 │
│  • Type validation check                                    │
│  • Cross-panel consistency check                            │
│                                                             │
│  BLOCKING violations → Panel stays DRAFT                    │
│  WARNING violations → Logged, panel proceeds                │
└─────────────────────────────────────────────────────────────┘

Phase 6:   Aurora Compilation       → Build projection
Phase 6.5: UI Plan Bind             → Update ui_plan.yaml
Phase 7:   Projection Diff Guard    → Prevent silent drift
Phase 8:   Rendering                → UI output
```

---

## The Problem Solved

### Gap: SDSR ≠ Semantic Correctness

SDSR proves:
- ✅ API responds with 200
- ✅ Data flows through the system
- ✅ Synthetic data reaches the endpoint

SDSR does NOT prove:
- ❌ Signal names match spec
- ❌ Capability is appropriate for panel
- ❌ API fields exist for all declared signals
- ❌ Data types are correct
- ❌ Cross-panel data is consistent

**Without Semantic Validator:**
- A panel could bind to the wrong capability
- A signal could be missing its translation
- An API could return incompatible field names
- Cross-panel data could contradict

**With Semantic Validator:**
- Every signal is validated before binding
- Every capability is verified as appropriate
- Every API field is confirmed present
- Type mismatches surface immediately

---

## Core Principle

> **Semantics must be declared once, validated mechanically, enforced everywhere.**

---

## Failure Taxonomy

The validator enforces two classes of failures:

### Phase A: Intent Guardrails (INT-*)

| Check | What It Validates | Failure Mode | Fix Owner |
|-------|-------------------|--------------|-----------|
| INT-001 | Signal is provable (observable or computed) | BLOCKING | Product |
| INT-002 | Capability cardinality ≤ 5 per panel | BLOCKING | Architecture |
| INT-003 | No semantic duplication across panels | WARNING | Product |
| INT-004 | No contradictory intents in same domain | BLOCKING | Product |
| INT-005 | Evolution/maturity path declared | WARNING | Product |
| INT-006 | Intent scope is bounded (≤ 20 signals) | WARNING | Architecture |
| INT-007 | Semantic contract exists in registry | BLOCKING | Product |
| INT-008 | Capability reference is valid | BLOCKING | Architecture |

### Phase B: Semantic Reality (SEM-*)

| Check | What It Validates | Failure Mode | Fix Owner |
|-------|-------------------|--------------|-----------|
| SEM-001 | Signal has translation or compute function | BLOCKING | Panel Adapter |
| SEM-002 | Capability is OBSERVED or TRUSTED | BLOCKING | SDSR |
| SEM-003 | API field exists in response | BLOCKING/WARNING | Backend |
| SEM-004 | Signal type matches expected | WARNING | Backend |
| SEM-005 | Semantic contract exists (INTENT_LEDGER) | BLOCKING | Intent |
| SEM-006 | Cross-panel data is consistent | WARNING | System |
| SEM-007 | Required signal has default defined | WARNING | Panel Adapter |
| SEM-008 | Computed signal has compute function | BLOCKING | Panel Adapter |

---

## Intent Guardrail Details (Phase A)

### INT-001: Signal Not Provable

**Severity:** BLOCKING
**Fix Owner:** Product
**Fix Action:** Make signal observable or add `computed_from` declaration

A signal is declared but is neither observable nor computable. Every signal must have a source of truth.

### INT-002: Capability Cardinality Exceeded

**Severity:** BLOCKING
**Fix Owner:** Architecture
**Fix Action:** Split intent into multiple panels or reduce capability dependencies

A panel depends on too many capabilities (max 5). This creates excessive coupling and failure modes.

### INT-003: Semantic Duplication

**Severity:** WARNING
**Fix Owner:** Product
**Fix Action:** Unify meaning or rename signal to avoid collision

The same signal name is used with different meanings across panels.

### INT-004: Contradictory Intents

**Severity:** BLOCKING
**Fix Owner:** Product
**Fix Action:** Resolve contradiction between intents

Two intents make mutually exclusive assertions in the same scope. They cannot both be true.

### INT-005: Missing Evolution Path

**Severity:** WARNING
**Fix Owner:** Product
**Fix Action:** Declare maturity stage and prerequisites

An intent lacks evolution/maturity declaration. The system cannot track readiness or dependencies.

### INT-006: Unbounded Intent Scope

**Severity:** WARNING
**Fix Owner:** Architecture
**Fix Action:** Bound the intent scope (max signals, pagination)

An intent can grow without limit. Unbounded intents are unmanageable.

### INT-007: Missing Semantic Contract

**Severity:** BLOCKING
**Fix Owner:** Product
**Fix Action:** Declare semantic contract in INTENT_LEDGER.md

A panel is referenced but has no semantic contract. Every panel must be declared in the intent registry.

### INT-008: Invalid Capability Reference

**Severity:** BLOCKING
**Fix Owner:** Architecture
**Fix Action:** Reference a valid capability ID from registry

An intent references a capability that doesn't exist. Every capability must be registered.

---

## Semantic Reality Details (Phase B)

### SEM-001: Signal Not Translated

**Severity:** BLOCKING
**Fix Owner:** Panel Adapter
**Fix Action:** Add signal translation to `SIGNAL_TRANSLATIONS` in `panel_signal_translator.py`

```python
# Example fix
SIGNAL_TRANSLATIONS = {
    "activity.summary": {
        "active_run_count": ("active_runs", 0),  # ← Add this
    },
}
```

### SEM-002: Capability Not Observed

**Severity:** BLOCKING
**Fix Owner:** SDSR
**Fix Action:** Run SDSR scenario to observe capability, OR downgrade panel to DRAFT

```bash
# Run SDSR scenario
python3 backend/scripts/sdsr/inject_synthetic.py --scenario SDSR-E2E-XXX --wait

# Apply observation
python3 scripts/tools/AURORA_L2_apply_sdsr_observations.py --observation SDSR_OBSERVATION_XXX.json
```

### SEM-003: API Field Missing

**Severity:** BLOCKING (no default) / WARNING (has default)
**Fix Owner:** Backend
**Fix Action:** Add field to API response OR correct the translation mapping

### SEM-004: Signal Type Mismatch

**Severity:** WARNING
**Fix Owner:** Backend
**Fix Action:** Fix API response schema OR update expected type in spec

### SEM-005: Semantic Contract Missing

**Severity:** BLOCKING
**Fix Owner:** Intent
**Fix Action:** Declare signal in `INTENT_LEDGER.md` OR remove usage from panel

### SEM-006: Cross-Panel Inconsistency

**Severity:** WARNING
**Fix Owner:** System
**Fix Action:** Resolve semantic contradiction between panels

### SEM-007: Required Signal No Default

**Severity:** WARNING
**Fix Owner:** Panel Adapter
**Fix Action:** Add appropriate default value in `SIGNAL_TRANSLATIONS`

### SEM-008: Computed Signal No Function

**Severity:** BLOCKING
**Fix Owner:** Panel Adapter
**Fix Action:** Add compute function to `COMPUTED_SIGNALS` in `panel_signal_translator.py`

```python
# Example fix
COMPUTED_SIGNALS = {
    "activity.summary": {
        "system_state": _compute_system_state,  # ← Add this
    },
}
```

---

## Architecture

### Components

```
backend/app/services/ai_console_panel_adapter/
├── validator_engine.py        # Two-phase orchestrator (NEW in V2.0)
├── intent_guardrails.py       # Phase A rules (NEW in V2.0)
├── semantic_validator.py      # Phase B validator class
├── semantic_types.py          # Type definitions (ViolationClass, FailureCode)
├── semantic_failures.py       # Combined failure taxonomy (INT-* + SEM-*)
├── panel_signal_translator.py # Signal translation mappings
├── panel_signal_collector.py  # Integration point (calls validator)
└── panel_capability_resolver.py # Capability resolution
```

### Two-Phase Flow

```
TwoPhaseValidator
        │
        ├── Phase A: run_intent_guardrails()
        │       │
        │       ├── INT-001: check_signal_provable()
        │       ├── INT-002: check_capability_cardinality()
        │       ├── INT-003: check_semantic_duplication()
        │       ├── INT-004: check_contradictory_intents()
        │       ├── INT-005: check_missing_evolution_path()
        │       ├── INT-006: check_unbounded_intent_scope()
        │       ├── INT-007: check_missing_semantic_contract()
        │       └── INT-008: check_invalid_capability_reference()
        │
        │   Phase A BLOCKING → STOP (return violations)
        │   Phase A PASS → Continue to Phase B
        │
        └── Phase B: SemanticValidator.validate_panel()
                │
                ├── SEM-001: check_signal_has_translation()
                ├── SEM-002: check_capability_is_observed()
                ├── SEM-003: check_api_field_present()
                ├── SEM-004: check_signal_type()
                └── ... (other SEM-* checks)
```

### Data Flow

```
SlotSpec (from YAML)
        ↓
SemanticValidator.validate_slot()
        │
        ├── For each capability_id:
        │       │
        │       ├── check_capability_is_observed()  → SEM-002
        │       │
        │       └── For each signal:
        │               │
        │               └── check_signal_has_translation() → SEM-001
        │
        └── Return SemanticReport
                │
                ├── is_valid() → True: proceed to binding
                │
                └── is_valid() → False: BLOCK, return violations
```

### Integration with Signal Collector

The Semantic Validator is integrated into `PanelSignalCollector`:

```python
async def collect_for_slot(self, slot_spec, params=None, panel_id=""):
    # V2.1: Run semantic validation FIRST
    if self._enforce_semantics:
        semantic_report = self._semantic_validator.validate_slot(slot_spec, panel_id)

        if not semantic_report.is_valid():
            # Log blocking violations
            for v in semantic_report.blocking():
                logger.error(f"Semantic violation {v.code.value}: {v.message}")

            # Return early with semantic errors
            return CollectedSignals(
                slot_id=slot_spec.slot_id,
                signals={},
                missing=list(slot_spec.required_inputs),
                errors=[f"SEMANTIC: {v.code.value}" for v in semantic_report.blocking()],
                semantic_valid=False,
            )

    # Proceed with signal collection...
```

---

## Usage

### Two-Phase Validation (Recommended)

```python
from app.services.ai_console_panel_adapter import (
    TwoPhaseValidator,
    validate_intent,
    validate_full,
)

# Create validator with known registries
validator = TwoPhaseValidator(
    registered_panels={"OVR-SUM-HL-O1", "ACT-RUN-LS-O2"},
    known_capabilities={"activity.summary", "activity.runs"},
)

# Validate intent YAML (Phase A only)
intent = {
    "panel_id": "OVR-SUM-HL-O1",
    "consumed_capabilities": [
        {"capability_id": "activity.summary", "signals": ["active_run_count"]}
    ],
    "panel_state": "BOUND",
}
report = validator.validate_intent(intent)

if not report.phase_a_valid():
    for v in report.phase_a_blocking():
        print(f"PHASE A BLOCKED: {v.code.value} - {v.message}")
        print(f"  Fix Owner: {v.fix_owner}")

# Full two-phase validation (Phase A + Phase B)
api_response = {"active_runs": 5, "failed_runs": 2}
report = validator.validate_full(intent, api_response)

print(f"Phase A valid: {report.phase_a_valid()}")
print(f"Phase B valid: {report.phase_b_valid()}")
print(f"Overall valid: {report.is_valid()}")
```

### Convenience Functions

```python
from app.services.ai_console_panel_adapter import (
    validate_intent,
    validate_panel,
    validate_full,
)

# Phase A only
report = validate_intent(
    intent=intent,
    registered_panels={"OVR-SUM-HL-O1"},
    known_capabilities={"activity.summary"},
)

# Phase B only
report = validate_panel(
    panel_id="OVR-SUM-HL-O1",
    api_response={"active_runs": 5},
)

# Full two-phase
report = validate_full(
    intent=intent,
    api_response=api_response,
)
```

### Legacy Usage (Phase B Only)

```python
from app.services.ai_console_panel_adapter import (
    SemanticValidator,
    get_semantic_validator,
)

validator = get_semantic_validator()
report = validator.validate_slot(slot_spec, panel_id="OVR-SUM-HL-O1")

if not report.is_valid():
    for violation in report.blocking():
        print(f"BLOCKED: {violation.code.value} - {violation.message}")
        print(f"  Fix Owner: {violation.fix_owner}")
        print(f"  Fix Action: {violation.fix_action}")
```

### Get Missing Translations

```python
validator = get_semantic_validator()
missing = validator.get_missing_translations()

for m in missing:
    print(f"Panel: {m['panel_id']}, Capability: {m['capability_id']}, Signal: {m['signal']}")
```

### Get Unobserved Capabilities

```python
validator = get_semantic_validator()
unobserved = validator.get_unobserved_capabilities()

for u in unobserved:
    print(f"Capability: {u['capability_id']}, Status: {u['status']}")
```

---

## CLI Integration

### Run Semantic Validation

```bash
# Validate all panels
python3 -c "
from app.services.ai_console_panel_adapter import get_semantic_validator
validator = get_semantic_validator()
report = validator.validate_all_panels()
print(f'Valid: {report.is_valid()}')
print(f'Blocking: {len(report.blocking())}')
print(f'Warnings: {len(report.warnings())}')
"
```

### In HISAR Pipeline

The semantic validator is invoked automatically in Phase 5.7 of the HISAR pipeline:

```bash
# run_hisar.sh invokes semantic validation after SDSR
./scripts/tools/run_hisar.sh OVR-SUM-HL-O1

# Phase 5.7 output:
# [SEMANTIC] Validating slot OVR-SUM-HL-O1...
# [SEMANTIC] Signals checked: 5
# [SEMANTIC] Capabilities checked: 1
# [SEMANTIC] Status: VALID
```

### In Aurora L2 Pipeline (RECOMMENDED)

Phase A validation is wired into the Aurora L2 pipeline as the **single gate** for all downstream UI activities:

```bash
# Run the full pipeline (Phase A → Aurora → Copy)
DB_AUTHORITY=neon ./scripts/tools/run_aurora_l2_pipeline.sh

# Dry-run mode (show what would happen)
DB_AUTHORITY=neon ./scripts/tools/run_aurora_l2_pipeline.sh --dry-run

# Skip Phase A (DANGEROUS - debugging only)
DB_AUTHORITY=neon ./scripts/tools/run_aurora_l2_pipeline.sh --skip-phase-a
```

**Pipeline Flow:**

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE A: Intent Guardrails (BLOCKING GATE)                 │
│  Script: scripts/tools/validate_all_intents.py              │
│                                                             │
│  Checks: INT-001 to INT-008                                 │
│  Output: design/l2_1/ui_contract/phase_a_validation.json    │
│                                                             │
│  If BLOCKING violations → EXIT 1 (pipeline stops)           │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼ (only if Phase A passes)
┌─────────────────────────────────────────────────────────────┐
│  AURORA COMPILATION                                          │
│  Script: backend/aurora_l2/SDSR_UI_AURORA_compiler.py        │
│                                                             │
│  Reads: intents + capabilities                              │
│  Output: design/l2_1/ui_contract/ui_projection_lock.json    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  COPY TO PUBLIC                                              │
│  website/app-shell/public/projection/ui_projection_lock.json │
└─────────────────────────────────────────────────────────────┘
```

**Exit Codes:**

| Code | Meaning |
|------|---------|
| 0 | Pipeline completed successfully |
| 1 | Phase A blocked (design-time violations) |
| 2 | Aurora compilation failed |
| 3 | Configuration error |

### Validate All Intents (Standalone)

Run Phase A validation without Aurora compilation:

```bash
cd backend
python3 ../scripts/tools/validate_all_intents.py --blocking --verbose
```

**Options:**

| Option | Description |
|--------|-------------|
| `--blocking` | Exit with code 1 if any blocking violations |
| `--output PATH` | Write validation report to JSON file |
| `--verbose` | Print detailed violation information |

---

## Enforcement Modes

### Mode 1: BLOCKING (Default)

All blocking violations stop the pipeline:

```python
collector = PanelSignalCollector(enforce_semantics=True)  # Default
```

### Mode 2: WARNING (Audit Only)

Violations are logged but don't stop the pipeline:

```python
collector = PanelSignalCollector(enforce_semantics=False)
```

### When to Use Each Mode

| Mode | Use Case |
|------|----------|
| BLOCKING | Production, CI, HISAR pipeline |
| WARNING | Development, debugging, gap analysis |

---

## Outputs

### SemanticReport

```python
@dataclass
class SemanticReport:
    violations: List[SemanticViolation]
    validated_at: datetime
    panels_checked: int = 0
    signals_checked: int = 0
    capabilities_checked: int = 0
    intents_checked: int = 0       # NEW in V2.0
    phase_a_complete: bool = False  # NEW in V2.0
    phase_b_complete: bool = False  # NEW in V2.0

    def is_valid(self) -> bool:
        """True if no BLOCKING violations."""
        return len(self.blocking()) == 0

    def phase_a_valid(self) -> bool:
        """True if no Phase A BLOCKING violations."""
        return len(self.phase_a_blocking()) == 0

    def phase_b_valid(self) -> bool:
        """True if no Phase B BLOCKING violations."""
        return len(self.phase_b_blocking()) == 0

    def blocking(self) -> List[SemanticViolation]:
        """Return BLOCKING violations only."""

    def warnings(self) -> List[SemanticViolation]:
        """Return WARNING violations only."""

    def intent_violations(self) -> List[SemanticViolation]:
        """Return Phase A (INT-*) violations only."""

    def semantic_violations(self) -> List[SemanticViolation]:
        """Return Phase B (SEM-*) violations only."""

    def phase_a_blocking(self) -> List[SemanticViolation]:
        """Return Phase A BLOCKING violations."""

    def phase_b_blocking(self) -> List[SemanticViolation]:
        """Return Phase B BLOCKING violations."""
```

### SemanticViolation

```python
@dataclass
class SemanticViolation:
    code: FailureCode               # INT-* or SEM-*
    vclass: ViolationClass          # INTENT or SEMANTIC (NEW in V2.0)
    severity: SemanticSeverity      # BLOCKING or WARNING
    message: str                    # Human-readable message
    context: SemanticContext        # Panel, slot, signal, capability
    evidence: Dict[str, Any]        # Supporting data
    fix_owner: str                  # Who fixes this
    fix_action: str                 # How to fix it

    @property
    def is_intent_violation(self) -> bool:
        """True if Phase A violation."""

    @property
    def is_semantic_violation(self) -> bool:
        """True if Phase B violation."""
```

### ViolationClass (NEW in V2.0)

```python
class ViolationClass(str, Enum):
    INTENT = "INTENT_VIOLATION"      # Phase A: Human/design-time
    SEMANTIC = "SEMANTIC_VIOLATION"  # Phase B: System/proof-time
```

---

## Relationship to Other Pipeline Components

### SDSR (Upstream)

```
SDSR proves: "API works" (operational truth)
Semantic Validator proves: "Data is correct for panel" (semantic truth)
```

SDSR must pass BEFORE Semantic Validator runs.

### HISAR (Container)

```
HISAR Phase 5.7 = Semantic Validation
```

Semantic Validator is Phase 5.7 in the HISAR execution doctrine.

### AURORA L2 (Downstream)

```
Semantic Validator → VALID → Aurora Compilation
Semantic Validator → INVALID → Panel stays DRAFT
```

Aurora Compilation only runs for semantically valid slots.

### Panel Adapter Layer (Host)

```
panel_signal_collector.py
        │
        ├── _semantic_validator.validate_slot()  # Check first
        │
        └── _call_capability()  # Only if valid
```

The Semantic Validator is hosted in the Panel Adapter Layer (L2.1).

---

## Invariants

1. **No binding without semantic validation** — Every slot must pass semantic validation before signals are collected.

2. **BLOCKING violations stop execution** — The pipeline cannot proceed if semantic validation fails.

3. **Fix ownership is explicit** — Every violation identifies who must fix it (Panel Adapter, Backend, SDSR, Intent).

4. **Evidence is captured** — Every violation includes supporting data for debugging.

5. **Mechanical enforcement** — No human judgment required; validation is fully automated.

6. **Single source of truth** — Signal translations live in `panel_signal_translator.py`, nowhere else.

---

## Files & Locations

### Core Implementation

| File | Purpose |
|------|---------|
| `backend/app/services/ai_console_panel_adapter/validator_engine.py` | Two-phase orchestrator (NEW V2.0) |
| `backend/app/services/ai_console_panel_adapter/intent_guardrails.py` | Phase A rules (NEW V2.0) |
| `backend/app/services/ai_console_panel_adapter/semantic_validator.py` | Phase B validator class |
| `backend/app/services/ai_console_panel_adapter/semantic_types.py` | Type definitions |
| `backend/app/services/ai_console_panel_adapter/semantic_failures.py` | Combined failure taxonomy |
| `backend/app/services/ai_console_panel_adapter/panel_signal_translator.py` | Signal translations |

### Integration Points

| File | Integration |
|------|-------------|
| `backend/app/services/ai_console_panel_adapter/panel_signal_collector.py` | Calls validator before collecting |
| `backend/app/services/ai_console_panel_adapter/__init__.py` | Module exports (V2.2.0) |
| `scripts/tools/run_hisar.sh` | Invokes Phase 5.7 |

### Pipeline Scripts (V2.1)

| File | Purpose |
|------|---------|
| `scripts/tools/validate_all_intents.py` | Phase A batch validation for all intents |
| `scripts/tools/run_aurora_l2_pipeline.sh` | Pipeline orchestrator (Phase A → Aurora → Copy) |

### Documentation

| File | Purpose |
|------|---------|
| `docs/architecture/pipeline/SEMANTIC_VALIDATOR.md` | This document |
| `docs/governance/HISAR.md` | Execution doctrine (references this) |
| `docs/governance/SDSR.md` | SDSR methodology (references this) |
| `design/l2_1/AURORA_L2.md` | Pipeline specification (references this) |

---

## Memory PINs

- PIN-420 — Semantic Authority and First SDSR Binding
- PIN-370 — SDSR System Contract
- PIN-422 — HISAR Execution Doctrine

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-01-16 | 2.1 | Added pipeline wiring (Phase A as single gate before Aurora) |
| 2026-01-16 | 2.1 | Created `validate_all_intents.py` for batch Phase A validation |
| 2026-01-16 | 2.1 | Created `run_aurora_l2_pipeline.sh` as pipeline orchestrator |
| 2026-01-16 | 2.0 | Two-phase architecture (Phase A: Intent Guardrails, Phase B: Semantic Reality) |
| 2026-01-16 | 2.0 | Added INT-001 to INT-008 failure codes for Phase A |
| 2026-01-16 | 2.0 | Added TwoPhaseValidator orchestrator |
| 2026-01-16 | 2.0 | Added ViolationClass enum (INTENT/SEMANTIC) |
| 2026-01-16 | 2.0 | Updated SemanticReport with phase-specific methods |
| 2026-01-16 | 1.0 | Initial creation — Semantic Validator governance document |
