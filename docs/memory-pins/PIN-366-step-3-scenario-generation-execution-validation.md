# PIN-366: STEP 3 — Scenario Generation, Execution & Validation

**Status:** 🔒 FROZEN + CI GATED
**Created:** 2026-01-08
**Category:** Governance / Validation Pipeline
**Scope:** Scenario-based validation of bound capabilities, surfaces, and slots
**Prerequisites:** PIN-363 (STEP 1B-R), PIN-365 (STEP 2A)

---

## Definition (Precise)

> STEP 3 validates that **bound capabilities + surfaces + slots** actually behave correctly under realistic system conditions — both **headless** and **UI-visible** — without changing any prior artifacts.

**STEP 3 is a consumer of truth, never a producer of truth.**

---

## What STEP 3 Is NOT

- **NOT** UI design
- **NOT** capability binding
- **NOT** L2.1 mutation
- **NOT** slot mutation
- **NOT** product roadmap work

Those are already done or future steps.

---

## STEP 3 Inputs (Immutable)

STEP 3 consumes only **frozen artifacts**:

### System Truth

| Artifact | Source | Purpose |
|----------|--------|---------|
| `capability_directional_metadata.xlsx` | STEP 0B | Capability definitions |
| `capability_applicability_matrix.xlsx` | STEP 1 | Domain applicability |
| `l2_supertable_v3_rebased_surfaces.xlsx` | STEP 1B-R | Mechanical surfaces |
| `ui_slot_registry.xlsx` | STEP 2A | Slot definitions |
| `surface_to_ui_slot_map.xlsx` | STEP 2A | Surface → Slot mappings |

### UI Truth

| Artifact | Source | Purpose |
|----------|--------|---------|
| `ui_projection_lock.json` | L2.1 Pipeline | Locked UI projection |

### Scenario Truth (STEP 3 Owned)

| Artifact | Purpose |
|----------|---------|
| `scenario_spec.yaml` | Scenario definitions |
| `scenario_fixtures/` | Synthetic test data |

---

## STEP 3 Outputs (Additive Only)

STEP 3 **never edits upstream files**.

| Output | Purpose |
|--------|---------|
| `scenario_run_results.json` | Execution results |
| `scenario_assertions.xlsx` | Assertion outcomes |
| `scenario_failures.xlsx` | Failure records (if any) |
| `scenario_evidence/` | Logs, snapshots |
| `STEP_3_LEDGER.csv` | Append-only institutional memory |

---

## STEP 3 Architecture (Pipeline View)

```
Scenario Spec
      ↓
Scenario Generator
      ↓
Synthetic Data Injector
      ↓
Scenario Runner
      ↓
Assertions Engine
      ├── Headless Validation (mandatory)
      └── UI Slot Validation (optional but enabled)
      ↓
Results Recorder (Ledger)
```

---

## STEP 3.1 — Scenario Specification

### Purpose

Define **what you are testing**, not how.

### Key Rules

- Scenario declares **required surfaces**
- Scenario declares **expected slots**
- Scenario **never references capabilities directly**

### Schema

```yaml
scenario_id: string        # Unique identifier
domain: string             # ACTIVITY | INCIDENTS | POLICIES | LOGS
intent: string             # Human-readable description
surfaces_required: list    # Surface IDs from STEP 1B-R
slots_expected: list       # Slot IDs from STEP 2A
assertions: list           # Assertion types to evaluate
fixtures: object           # Synthetic data requirements
```

---

## STEP 3.2 — Scenario Generator

### Purpose

Turn declarative scenario specs into **executable test plans**.

### Responsibilities

- Resolve surfaces → slots (read-only)
- Determine required data fixtures
- Generate execution plan

### Output

- `generated_scenario_plan.json`

No execution yet.

---

## STEP 3.3 — Synthetic Data Injector

### Purpose

Create **controlled, deterministic system state**.

### Examples

- Fake executions (RUNNING / FAILED)
- Fake incidents
- Fake policy blocks
- Fake replay traces

### Rules

- No production data
- Deterministic seeds
- Re-runnable

---

## STEP 3.4 — Scenario Runner

### Two Execution Modes (Both Required)

#### Mode A — Headless (Mandatory)

Validates:
- Surface availability
- Authority correctness
- Determinism
- API responses
- Policy enforcement

Answers: **"Does the system actually work?"**

#### Mode B — UI Slot Aware (Enabled via STEP 2A)

Validates:
- Slot visibility
- Slot presence
- Slot grouping
- Slot enable/disable state

Answers: **"Does the product expose the system correctly?"**

**Note:** UI rendering itself is NOT asserted — only contract-level visibility.

---

## STEP 3.5 — Assertion Engine

Assertions are **typed and mechanical**.

### Core Assertion Types

| Assertion | Meaning |
|-----------|---------|
| `surface_available` | Surface exists and is bound |
| `surface_authority_ok` | Authority matches scenario |
| `slot_visible` | Slot appears in projection |
| `slot_hidden` | Slot correctly hidden |
| `control_disabled` | UI control exists but disabled |
| `no_slot_leakage` | No unexpected slots appear |
| `action_blocked` | Mutating action prevented |
| `evidence_loads` | Replay/logs retrievable |

Assertions are evaluated **post-run**, not inline.

---

## STEP 3.6 — Results & Ledger

### Ledger Schema (Append-Only)

`STEP_3_LEDGER.csv` columns:

| Column | Description |
|--------|-------------|
| `scenario_id` | Scenario identifier |
| `domain` | Target domain |
| `surfaces` | Surfaces tested |
| `slots` | Slots validated |
| `status` | PASS / FAIL |
| `failure_type` | Failure code (if any) |
| `timestamp` | Run timestamp |
| `pipeline_version` | STEP 3 version |

---

## Acceptance Criteria

A scenario **passes** only if:

1. All required surfaces are available
2. No authority violations occur
3. All expected slots are visible
4. No unexpected slots appear
5. All assertions pass
6. UI projection remains unchanged

Any failure is **recorded, categorized, and never silently ignored**.

---

## Failure Taxonomy (Authoritative)

### A. SURFACE FAILURES (System Layer)

| Code | Name | Meaning | Fix Location |
|------|------|---------|--------------|
| SF-01 | Surface Missing | Required surface not bound | Capability metadata or L2.1 binding |
| SF-02 | Surface Authority Mismatch | Authority insufficient | Capability metadata or L2.1 binding |
| SF-03 | Surface Determinism Violation | Advisory used where strict required | Capability metadata or L2.1 binding |
| SF-04 | Surface Mutability Violation | Write/control allowed when read expected | Capability metadata or L2.1 binding |

### B. SLOT FAILURES (Product Layer)

| Code | Name | Meaning | Fix Location |
|------|------|---------|--------------|
| SL-01 | Slot Missing | Expected slot not visible | surface_to_slot_map or ui_slot_registry |
| SL-02 | Unexpected Slot Visible | Slot appeared without declaration | surface_to_slot_map or ui_slot_registry |
| SL-03 | Slot Visibility Violation | Slot visible when should be hidden | surface_to_slot_map or ui_slot_registry |
| SL-04 | Slot Authority Leak | Slot exposes actions beyond allowed authority | surface_to_slot_map or ui_slot_registry |

### C. UI CONTRACT FAILURES (Pipeline Integrity)

| Code | Name | Meaning | Fix Location |
|------|------|---------|--------------|
| UI-01 | Projection Mismatch | Slot resolved but missing in projection lock | STEP 2A resolver or projection builder |
| UI-02 | Control Shape Drift | Control differs from locked contract | STEP 2A resolver or projection builder |
| UI-03 | Ordering Violation | Panel/control order differs from lock | STEP 2A resolver or projection builder |

### D. SCENARIO FAILURES (Test Definition)

| Code | Name | Meaning | Fix Location |
|------|------|---------|--------------|
| SC-01 | Invalid Scenario | Scenario references unknown surface/slot | scenario_spec.yaml |
| SC-02 | Fixture Incomplete | Required synthetic data missing | scenario_spec.yaml |
| SC-03 | Assertion Invalid | Assertion incompatible with surface type | scenario_spec.yaml |

### E. SYSTEM VIOLATIONS (Hard Stop)

| Code | Name | Meaning | Fix Location |
|------|------|---------|--------------|
| SYS-01 | L2.1 Mutation Detected | Any write to L2.1 | Human process breach |
| SYS-02 | Projection Lock Modified | ui_projection_lock.json changed | Human process breach |
| SYS-03 | Capability Drift | Capability metadata modified | Human process breach |

---

## Hard Rule (Non-Negotiable)

> **STEP 3 may expose problems, but it may not fix them.**

Fixes happen:
- In capability metadata
- In surface binding
- In slot mapping
- Or later roadmap steps

**STEP 3 only reveals truth.**

---

## Implementation Checklist

| Task | Status | Notes |
|------|--------|-------|
| Create PIN-366 | COMPLETE | This document |
| Create scenario_spec.yaml | COMPLETE | 4 baseline + 1 negative |
| Create scenario directory structure | COMPLETE | design/l2_1/step_3/ |
| Create slot alias mapping | COMPLETE | 38 aliases |
| Implement scenario generator | COMPLETE | Integrated in runner |
| Implement synthetic data injector | COMPLETE | In-memory fixtures |
| Implement scenario runner | COMPLETE | Headless + UI-aware |
| Implement assertion engine | COMPLETE | 11 assertion types + authority check |
| Implement results recorder | COMPLETE | CSV ledger + JSON |
| Add baseline column to ledger | COMPLETE | true/false tracking |
| Add negative CONTROL-path scenario | COMPLETE | ACTIVITY-NEG-001 (SL-04) |
| Add symmetric negative scenarios | COMPLETE | INCIDENTS/POLICIES/LOGS-NEG-001 |
| Freeze scenario coverage | COMPLETE | 8 scenarios (4 baseline, 4 negative) |
| Add CI integration | COMPLETE | `.github/workflows/step3-ui-contract.yml` |
| Add exit-code logic | COMPLETE | 0=pass, 1=regression, 2=breach |

---

## References

| PIN | Topic | Status |
|-----|-------|--------|
| PIN-360 | STEP 0B Directional Capability Normalization | COMPLETE |
| PIN-361 | STEP 1 Domain Applicability Matrix | COMPLETE |
| PIN-362 | STEP 1B L2.1 Compatibility Scan | COMPLETE |
| PIN-363 | STEP 1B-R L2.1 Surface Rebaselining | FROZEN |
| PIN-365 | STEP 2A UI Slot Population | COMPLETE |

---

## Updates

### 2026-01-08: PIN Created

- STEP 3 specification locked
- Failure taxonomy defined
- Ready for implementation

### Update (2026-01-08)

### 2026-01-08: STEP 3 Implementation Complete

**Artifacts Created:**

| Artifact | Path |
|----------|------|
| Slot Aliases | `design/l2_1/step_3/slot_aliases.yaml` |
| Scenario Spec | `design/l2_1/step_3/scenarios/scenario_spec.yaml` |
| Runner Script | `scripts/ops/step3_scenario_runner.py` |
| Ledger | `design/l2_1/step_3/STEP_3_LEDGER.csv` |
| Results Dir | `design/l2_1/step_3/results/` |

**Baseline Scenarios:**

| Scenario | Domain | Status |
|----------|--------|--------|
| ACTIVITY-001 | Activity | PASS |
| INCIDENTS-001 | Incidents | PASS |
| POLICIES-001 | Policies | PASS |
| LOGS-001 | Logs | PASS |

**Implementation Details:**

- Slot alias system: 38 human-readable aliases → actual slot IDs
- In-memory fixtures: Executions, incidents, policies, logs
- Assertion engine: 11 assertion types
- Results recorder: CSV ledger + JSON per-scenario

**Command:** `python3 scripts/ops/step3_scenario_runner.py`

**Status:** 🔒 FROZEN + CI GATED

### 2026-01-08: Baseline Column & Freeze

**Enhancement:** Added `baseline` column to `STEP_3_LEDGER.csv`

| Column | Values | Purpose |
|--------|--------|---------|
| `baseline` | `true` / `false` | Marks scenarios that must never fail |

**Baseline Scenarios (FROZEN):**

All 4 domain scenarios are marked `baseline: true`:

- `ACTIVITY-001` - Activity domain evidence/replay
- `INCIDENTS-001` - Incidents domain evidence inspection
- `POLICIES-001` - Policies domain view-only controls
- `LOGS-001` - Logs domain replay window

**Regression Invariant:** If a baseline scenario fails, it indicates a regression in the system, not a test issue.

**Ledger Schema (v1.0.0):**

```csv
scenario_id,domain,surfaces,slots,status,failure_codes,baseline,timestamp,pipeline_version
```

**Status:** 🔒 FROZEN + CI GATED

### 2026-01-08: Negative Scenario Added (CONTROL-path)

**Purpose:** Prove the assertion engine can fail correctly, loudly, and classifiably.

**Scenario Added:**

| ID | Domain | Intent | Baseline | Expected Status |
|----|--------|--------|----------|-----------------|
| `ACTIVITY-NEG-001` | Activity | User attempts write/control action on read-only surface | false | FAIL |

**Scenario Details:**

```yaml
scenario_id: ACTIVITY-NEG-001
surfaces_required: [L21-EVD-R]
slots_expected: [ACTIVITY_RUN_LIST]
attempted_actions:
  - type: EXECUTE
    target: REPLAY_EXPORT
assertions: [surface_available, slot_visible, action_blocked]
expected_failure:
  category: SLOT
  code: SL-04
```

**Execution Result:**

| Assertion | Result |
|-----------|--------|
| `surface_available` | PASS |
| `slot_visible` | PASS |
| `action_blocked` | FAIL (SL-04) |

**Failure Recorded:**

```
SL-04: Authority violation: EXECUTE action on 'REPLAY_EXPORT'
       attempted on read-only surface L21-EVD-R
```

**Ledger Entry:**

```csv
ACTIVITY-NEG-001,Activity,L21-EVD-R,SLOT-ACT-EX-AR-O2,FAIL,SL-04,false,2026-01-08T19:48:18,1.0.0
```

**What This Proves:**

1. Assertion engine is **bi-directional** (detects both PASS and FAIL)
2. Failure taxonomy (SL-04) is **real**, not theoretical
3. Ledger correctly distinguishes `baseline=true` from `baseline=false`
4. Negative scenarios produce **deterministic, classifiable failures**
5. CI gating can now trust the ledger

**Invariants Verified:**

- All 4 baseline scenarios remain PASS (no regression)
- Negative scenario fails as designed
- No system state mutation occurred
- No UI projection mutation occurred

**Status:** 🔒 FROZEN + CI GATED

### 2026-01-09: Symmetric Coverage Complete — FROZEN

**Purpose:** Achieve 1:1 baseline-to-negative scenario coverage for all domains.

**Scenarios Added:**

| ID | Domain | Intent | Baseline | Expected Status |
|----|--------|--------|----------|-----------------|
| `INCIDENTS-NEG-001` | Incidents | User attempts to close/mitigate incident on read-only surface | false | FAIL (SL-04) |
| `POLICIES-NEG-001` | Policies | User attempts to toggle policy on read-only surface | false | FAIL (SL-04) |
| `LOGS-NEG-001` | Logs | User attempts to delete/export logs on read-only surface | false | FAIL (SL-04) |

**Final Ledger (FROZEN):**

```
scenario_id         | domain     | status | baseline | failure_code
--------------------|------------|--------|----------|-------------
ACTIVITY-001        | Activity   | PASS   | true     | -
INCIDENTS-001       | Incidents  | PASS   | true     | -
POLICIES-001        | Policies   | PASS   | true     | -
LOGS-001            | Logs       | PASS   | true     | -
ACTIVITY-NEG-001    | Activity   | FAIL   | false    | SL-04
INCIDENTS-NEG-001   | Incidents  | FAIL   | false    | SL-04
POLICIES-NEG-001    | Policies   | FAIL   | false    | SL-04
LOGS-NEG-001        | Logs       | FAIL   | false    | SL-04
```

**Freeze Conditions Met:**

| Condition | Status |
|-----------|--------|
| Every domain has 1 baseline PASS | ✅ |
| Every domain has 1 negative FAIL | ✅ |
| All failures are deterministic | ✅ |
| All failures use same class (SL-04) | ✅ |
| No baseline scenario affected | ✅ |
| UI projection unchanged | ✅ |

**What This Proves:**

1. **Authority boundaries are enforced** — read-only surfaces block mutating actions
2. **Assertion engine is bidirectional** — detects both PASS and FAIL correctly
3. **Failure taxonomy is real** — SL-04 (Slot Authority Leak) applies to all domains
4. **CI can gate on symmetry** — if any baseline fails OR any negative passes, something is broken

---

### Update (2026-01-09)

### Update (2026-01-09)

### Update (2026-01-09)

## 2026-01-09: Phase-2A.1 Affordance Surfacing Complete

Added 14 blocked action controls to ui_projection_lock.json:
- Activity: STOP, RETRY, REPLAY_EXPORT
- Incidents: MITIGATE, CLOSE, ESCALATE
- Policies: TOGGLE (x3), EDIT
- Logs: ARCHIVE (x3), DELETE

All controls are visible but disabled with disabled_reason explaining the read-only surface.

Artifacts:
- design/l2_1/step_3/phase_2a1_affordance_spec.yaml
- scripts/ops/apply_phase2a1_affordances.py

Scenarios verified: 4/4 baseline PASS, 4/4 negative FAIL (SL-04)


## 2026-01-09: Phase-A CI Gating Complete

### Deliverables

| Component | Path | Status |
|-----------|------|--------|
| Scenario Runner | `scripts/ops/step3_scenario_runner.py` | Exit codes updated |
| CI Workflow | `.github/workflows/step3-ui-contract.yml` | Created |

### Exit Code Semantics

| Exit Code | Meaning | CI Behavior |
|-----------|---------|-------------|
| 0 | All baselines pass, negatives fail as expected | PASS |
| 1 | Baseline failure OR negative passed unexpectedly | HARD FAIL |
| 2 | SYS-* contract breach | CRITICAL FAIL |

### CI Workflow Features

- Triggers: Push to main, PR to main, manual dispatch
- Path filters: design/l2_1/**, step3_scenario_runner.py, website/app-shell/src/**
- Outputs: Scenario summary, ledger diff, PR comment, artifacts

### Governance Statement

> STEP-3 UI-level scenarios are frozen.
> Any change affecting baseline scenarios requires explicit UX approval.
> Negative scenarios must continue to fail with SL-04.

**Status:** 🔒 FROZEN + CI GATED


## 2026-01-09: Symmetric Coverage Complete — FROZEN

### Scenarios Added (3 negative scenarios)

| ID | Domain | Intent | Expected Status |
|----|--------|--------|-----------------|
| INCIDENTS-NEG-001 | Incidents | User attempts to close/mitigate incident on read-only surface | FAIL (SL-04) |
| POLICIES-NEG-001 | Policies | User attempts to toggle policy on read-only surface | FAIL (SL-04) |
| LOGS-NEG-001 | Logs | User attempts to delete/export logs on read-only surface | FAIL (SL-04) |

### Final Ledger (8 scenarios)

- 4 baseline scenarios: PASS (Activity, Incidents, Policies, Logs)
- 4 negative scenarios: FAIL with SL-04 (symmetric coverage)

### Freeze Conditions Met

- Every domain has 1 baseline PASS
- Every domain has 1 negative FAIL  
- All failures deterministic (SL-04)
- UI projection unchanged

**Status:** 🔒 FROZEN + CI GATED


## 🔒 FREEZE STATEMENT

**STEP 3 UI-Level Scenario Coverage is hereby FROZEN.**

**Effective:** 2026-01-09
**Authority:** PIN-366

**Frozen Artifacts:**

| Artifact | Path | Status |
|----------|------|--------|
| Scenario Spec | `design/l2_1/step_3/scenarios/scenario_spec.yaml` | FROZEN |
| Slot Aliases | `design/l2_1/step_3/slot_aliases.yaml` | FROZEN |
| Ledger Schema | `design/l2_1/step_3/STEP_3_LEDGER.csv` | FROZEN |

**Immutability Rules:**

1. **No new scenarios** may be added without explicit governance approval
2. **No scenario modification** — existing scenarios are immutable
3. **No baseline changes** — baseline status cannot be toggled
4. **Ledger is append-only** — past runs cannot be modified

**Regression Invariant:**

> If a baseline scenario FAILs → system regression
> If a negative scenario PASSes → authority boundary breach

**Next Steps:**

- [x] Phase-A CI gating design — COMPLETE
- [x] Integrate scenario runner into CI pipeline — COMPLETE
- [x] Add exit-code logic for baseline-only failures — COMPLETE

---

## Phase-A CI Gating (COMPLETE)

**Effective:** 2026-01-09
**Workflow:** `.github/workflows/step3-ui-contract.yml`

### Exit Code Semantics

| Exit Code | Meaning | CI Behavior |
|-----------|---------|-------------|
| 0 | All baselines pass, negatives fail as expected | PASS |
| 1 | Baseline failure OR negative passed unexpectedly | HARD FAIL |
| 2 | SYS-* contract breach | CRITICAL FAIL |

### Trigger Conditions

- Push to `main` (paths: `design/l2_1/**`, `scripts/ops/step3_scenario_runner.py`, `website/app-shell/src/**`)
- Pull request to `main` (same paths)
- Manual workflow dispatch

### What CI Does

1. Runs `step3_scenario_runner.py`
2. Publishes scenario summary
3. Generates ledger diff from previous run
4. Uploads results as artifacts
5. Comments on PR with status

### What CI Does NOT Do

- Block on negative scenarios (they are expected to fail)
- Enforce performance or timing
- Touch DB or persistence
- Block non-baseline failures

### Governance Statement

> **STEP-3 UI-level scenarios are frozen.**
> Any change affecting baseline scenarios requires explicit UX approval.
> Negative scenarios must continue to fail with SL-04.
> If a negative scenario passes, this indicates an authority boundary breach.

**Status:** 🔒 FROZEN + CI GATED

---

## Phase-2A.1: Affordance Surfacing (COMPLETE)

**Effective:** 2026-01-09

### Purpose

Add **blocked action controls** to ui_projection_lock.json so users can see what actions exist but understand why they're unavailable on read-only surfaces.

### Artifacts Created

| Artifact | Path | Purpose |
|----------|------|---------|
| Affordance Spec | `design/l2_1/step_3/phase_2a1_affordance_spec.yaml` | Control definitions |
| Apply Script | `scripts/ops/apply_phase2a1_affordances.py` | Applies controls to projection |

### Controls Added (14 total)

| Domain | Controls Added | Panels Modified |
|--------|---------------|-----------------|
| **Activity** | STOP, RETRY, REPLAY_EXPORT | 2 |
| **Incidents** | MITIGATE, CLOSE, ESCALATE | 2 |
| **Policies** | TOGGLE (x3), EDIT | 4 |
| **Logs** | ARCHIVE (x3), DELETE | 3 |

**Total:** 14 blocked action controls across 11 panels

### Blocked State Schema

All added controls share this state:

```json
{
  "type": "STOP",
  "order": 4,
  "icon": "stop-circle",
  "category": "action",
  "enabled": false,
  "visibility": "ALWAYS",
  "disabled_reason": "Action unavailable on read-only surface L21-EVD-R"
}
```

### Key Properties

| Property | Value | Meaning |
|----------|-------|---------|
| `enabled` | `false` | Control is visible but non-interactive |
| `visibility` | `ALWAYS` | Control appears even when blocked |
| `disabled_reason` | Surface-specific | Explains why action is unavailable |

### Graduation Path

When surfaces are upgraded from `L21-EVD-R` to `L21-CTL-RW`:

1. **Phase-3 Simulation:** Controls enter SIMULATED state (onClick logs, doesn't execute)
2. **Phase-4 Activation:** Controls set `enabled: true`, remove `disabled_reason`

### Validation Results

After applying Phase-2A.1:

```
Baseline: 4/4 PASS
Negative: 4/4 FAIL (SL-04)
```

All scenarios continue to work correctly.

### Command

```bash
# Apply affordances
python3 scripts/ops/apply_phase2a1_affordances.py

# Dry run (preview changes)
python3 scripts/ops/apply_phase2a1_affordances.py --dry-run
```

**Status:** COMPLETE

