# HISAR: Human Intent → SDSR → Aurora → Rendering

**Status:** ACTIVE
**Effective:** 2026-01-15
**Authority:** Governance Document
**Reference:** PIN-422

---

## Definition

> **HISAR** is the canonical execution doctrine for the AURORA L2 pipeline.

HISAR governs how human intent becomes rendered UI through verified system truth.

> **HISAR = Human Intent → SDSR → Aurora → Rendering**

This is not a script name. This is a **governed execution doctrine**.

---

## Execution Contract

```
1. Human Intent is the ONLY source of meaning.
2. SDSR is the ONLY source of truth.
3. Aurora may ONLY run AFTER SDSR success.
4. Rendering may ONLY reflect OBSERVED or TRUSTED capabilities.
```

### Forbidden Actions

| Action | Why Forbidden |
|--------|---------------|
| Inventing endpoints | Reality must be discovered, not assumed |
| Skipping coherency | Wiring truth must precede behavior truth |
| Running Aurora before SDSR | Unverified capabilities cannot be rendered |
| Forcing state transitions | Trust is earned, not assigned |

### Failure Semantics

- Any failure **MUST** stop execution
- Report the exact phase and invariant that blocked progress
- Exit 0 → rendered UI reflects proven reality
- Exit non-zero → NOTHING downstream is allowed to run

---

## The 8 Phases (+ Sync)

```
[H] Phase 1    Human Intent Validation
[H] Phase 2    Intent Specification
[A] Phase 3    Capability Declaration
[S] Phase 3.5  Coherency Gate (BLOCKING)
[S] Phase 4    SDSR Verification
[S] Phase 5    Observation Application
[S] Phase 5.5  Trust Evaluation
[A] Phase 6    Aurora Compilation
[A] Phase 6.5  UI Plan Bind
[A] Phase 7    Projection Diff Guard
[R] Phase 8    Rendering
```

### Phase Legend

| Letter | Meaning | Owner |
|--------|---------|-------|
| **H** | Human | Intent declaration, approval |
| **S** | SDSR | Verification, observation, trust |
| **A** | Aurora | Compilation, projection |
| **R** | Rendering | UI output |

---

## Canonical Runner

```bash
./scripts/tools/run_hisar.sh <PANEL_ID>
./scripts/tools/run_hisar.sh --all
./scripts/tools/run_hisar.sh --dry-run <PANEL_ID>
```

### Examples

```bash
# Run HISAR for a single panel
./scripts/tools/run_hisar.sh OVR-SUM-HL-O2

# Run HISAR for all panels
./scripts/tools/run_hisar.sh --all

# Preview what would run (no execution)
./scripts/tools/run_hisar.sh --dry-run OVR-SUM-HL-O2
```

---

## Phase Details

### Phase 0: Intent Ledger Sync (Pre-Phase)

**Owner:** Automation
**Script:** `sync_from_intent_ledger.py`

- **Source of Truth:** `design/l2_1/INTENT_LEDGER.md`
- Generates all downstream artifacts:
  - `design/l2_1/ui_plan.yaml`
  - `design/l2_1/intents/AURORA_L2_INTENT_*.yaml`
  - `backend/AURORA_L2_CAPABILITY_REGISTRY/*.yaml`
- **Naming Convention:** `AURORA_L2_INTENT_{panel_id}.yaml`
- Run this before any panel work to ensure artifacts are in sync

### Phase 1: Human Intent Validation

**Owner:** Human
**Script:** `aurora_intent_scaffold.py`

- Check if intent YAML exists for panel
- Scaffold new intent if missing (uses new naming: `AURORA_L2_INTENT_*.yaml`)
- Human fills TODO fields
- **Note:** For new panels, add to `INTENT_LEDGER.md` first, then run sync

### Phase 2: Intent Specification

**Owner:** Human
**Script:** `aurora_intent_registry_sync.py`

- Sync intent to registry (status: DRAFT)
- Human reviews and approves (DRAFT → APPROVED)
- Intent hash frozen at APPROVED time
- **Note:** Intent YAMLs support both legacy (`{panel_id}.yaml`) and new (`AURORA_L2_INTENT_{panel_id}.yaml`) naming

### Phase 3: Capability Declaration

**Owner:** Aurora
**Script:** `aurora_capability_scaffold.py`

- Create capability YAML (status: DECLARED)
- Extract endpoint/method from intent
- Capability exists but is not yet proven

### Phase 3.5: Coherency Gate (BLOCKING)

**Owner:** SDSR
**Script:** `aurora_coherency_check.py`

- Validates COH-001 to COH-010 invariants
- **BLOCKING** — SDSR cannot run if coherency fails
- Ensures wiring truth before behavior truth

| Check | Validates |
|-------|-----------|
| COH-001 | Panel exists in ui_plan.yaml |
| COH-002 | Intent YAML exists |
| COH-003 | Capability ID matches |
| COH-004 | Endpoints match |
| COH-005 | Methods match |
| COH-006 | Domains match |
| COH-007 | Capability status valid |
| COH-008 | SDSR verification consistent |
| COH-009 | Backend route exists |
| COH-010 | Route method matches |

### Phase 4: SDSR Verification

**Owner:** SDSR
**Scripts:** `aurora_sdsr_synth.py`, `aurora_sdsr_runner.py`

- Generate SDSR scenario from intent
- Execute scenario against live backend
- Check invariants (response shape, auth, provenance)
- Emit observation JSON

### Phase 5: Observation Application

**Owner:** SDSR
**Script:** `aurora_apply_observation.py`

- Apply observation to capability
- DECLARED → OBSERVED transition
- Update intent with verification trace

### Phase 5.5: Trust Evaluation

**Owner:** SDSR
**Script:** `aurora_trust_evaluator.py`

- Evaluate eligibility for TRUSTED promotion
- Requires: 10 runs, 98% pass rate, invariant stability
- OBSERVED → TRUSTED is machine-only

### Phase 6: Aurora Compilation

**Owner:** Aurora
**Script:** `SDSR_UI_AURORA_compiler.py`

- Compile intents + capabilities into projection
- Only APPROVED intents with OBSERVED capabilities → BOUND
- Output: `ui_projection_lock.json`

### Phase 6.5: UI Plan Bind

**Owner:** Aurora
**Script:** `aurora_ui_plan_bind.py`

- Sync `ui_plan.yaml` with observed capability state
- Updates panel state: EMPTY → BOUND
- Sets `intent_spec` and `expected_capability` fields
- Closes the loop between SDSR observation and UI plan source of truth

**Why This Exists:**

Before Phase 6.5, HISAR would update everything except `ui_plan.yaml`, creating
a sync gap where the source of truth showed EMPTY while the panel was actually BOUND.
This phase ensures `ui_plan.yaml` accurately reflects pipeline state.

### Phase 7: Projection Diff Guard

**Owner:** Aurora
**Script:** `projection_diff_guard.py`

- Prevent silent UI drift
- Check PDG-001 to PDG-005 rules
- Audit logging for traceability

### Phase 8: Rendering

**Owner:** Rendering
**Action:** Copy projection to public/

- `ui_projection_lock.json` → `public/projection/`
- Frontend reads projection verbatim
- No inference, no bypass

---

## State Transitions

```
Intent:     (new) → DRAFT → APPROVED
Capability: (new) → DECLARED → OBSERVED → TRUSTED
Panel:      EMPTY → UNBOUND → DRAFT → BOUND
```

### Binding Status Matrix

| Intent Status | Capability Status | Panel State |
|---------------|-------------------|-------------|
| DRAFT | - | EMPTY |
| APPROVED | DECLARED | DRAFT |
| APPROVED | OBSERVED | BOUND |
| APPROVED | TRUSTED | BOUND |

---

## How to Instruct Claude

This is now enough:

```
Act as run_hisar.sh for OVR-SUM-HL-O2.
```

Claude will:
- Stop on coherency failure
- Stop on SDSR failure
- Never invoke Aurora prematurely
- Report where and why it stopped

---

## Scheduling

### GitHub Action (Nightly)

```yaml
# .github/workflows/aurora-sdsr-nightly.yml
# Runs at 03:00 UTC daily
```

### Manual/Cron

```bash
# Run all SDSR scenarios
python3 aurora_sdsr_schedule.py --all

# Cron (nightly at 3am)
0 3 * * * ./scripts/tools/run_hisar.sh --all
```

---

## Golden Failure Tests

Tests that prove safety rails work:

| Test | What It Proves |
|------|----------------|
| `test_coh009_blocks_sdsr_when_endpoint_missing` | Missing endpoint → BLOCKED |
| `test_reality_mismatch_prevents_trust_promotion` | REALITY_MISMATCH → Can't reach TRUSTED |
| `test_consecutive_failures_block_promotion` | 3 failures → No promotion |

Run: `python3 backend/aurora_l2/tests/test_golden_failure.py`

---

## Files

| File | Purpose |
|------|---------|
| `scripts/tools/run_hisar.sh` | Canonical HISAR runner |
| `scripts/tools/sync_from_intent_ledger.py` | **Phase 0**: Intent Ledger → YAML sync (SOURCE OF TRUTH) |
| `design/l2_1/INTENT_LEDGER.md` | **SOURCE OF TRUTH** for all panel intents |
| `backend/aurora_l2/tools/aurora_*.py` | Phase automation scripts |
| `backend/aurora_l2/tools/aurora_ui_plan_bind.py` | Phase 6.5: UI Plan sync |
| `design/l2_1/TRUST_POLICY.md` | Trust demotion policy |
| `.github/workflows/aurora-sdsr-nightly.yml` | Nightly SDSR runs |
| `backend/aurora_l2/tests/test_golden_failure.py` | Safety rail tests |

### Generated Artifacts (from sync_from_intent_ledger.py)

| Artifact | Naming Convention |
|----------|-------------------|
| Intent YAMLs | `design/l2_1/intents/AURORA_L2_INTENT_{panel_id}.yaml` |
| Capability YAMLs | `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_{cap_id}.yaml` |
| UI Plan | `design/l2_1/ui_plan.yaml` |

---

## Invariants

1. **Human Intent is the only source of meaning** — machines execute, not interpret
2. **SDSR is the only source of truth** — capabilities must be proven
3. **Aurora runs only after SDSR success** — no unverified rendering
4. **Rendering reflects only OBSERVED/TRUSTED** — no speculation
5. **Failure stops execution** — no silent continuation
6. **Invariants are immutable** — SDSR reveals gaps, it does not hide them

---

## The Invariant Immutability Law

> **SDSR's job is to REVEAL backend gaps, not work around them.**

### The Correct Flow

```
Human Intent (what SHOULD exist)
        ↓
SDSR runs with standard invariants
        ↓
SDSR FAILS if backend doesn't match
        ↓
Backend is FIXED to satisfy intent
        ↓
SDSR re-runs and PASSES
```

### What Is FORBIDDEN

| Action | Why Forbidden |
|--------|---------------|
| Changing invariants to match backend | Hides the gap, inverts authority |
| Softening assertions | Weakens the contract |
| Removing failed checks | Destroys signal |
| "Legacy endpoint" exceptions | Creates two classes of truth |

### What Is REQUIRED

| Action | Why Required |
|--------|--------------|
| Run SDSR with standard invariants | Reveals true state |
| Report failures as backend gaps | Surfaces work needed |
| Fix backend to satisfy intent | Backend serves intent |
| Re-run SDSR after fix | Proves the fix worked |

### The Law

```
INVARIANT IMMUTABILITY LAW

Human Intent is the constraint.
Backend is the implementation.
SDSR is the verifier.

When SDSR fails:
  - The backend is wrong, not the invariant.
  - The gap is real, not a false positive.
  - The fix goes in backend, not SDSR.

Changing invariants to "make tests pass" is a governance violation.
```

---

## The One-Paragraph HISAR Doctrine

> HISAR is the execution doctrine that governs how human intent becomes rendered UI. Human intent defines what should exist. SDSR proves what actually exists. Aurora compiles proven reality into projection. Rendering displays only what has been verified. No phase may run before its predecessor succeeds. No capability may be rendered until observed. No state transition may be forced. If any phase fails, execution stops and reports exactly where and why. The UI is not a design artifact — it is a machine-verified reflection of system truth.

---

## Observation Scope Semantics (Addendum)

**Added:** 2026-01-15

### Problem

Not all panels observe the same scope of data. Some observe system-wide data, some observe tenant-specific data, some observe user-specific data. Without explicit scope declaration, SDSR cannot correctly inject context for verification.

### Solution: observation_scope in Intent YAML

Every intent YAML declares an `observation_scope` block:

```yaml
observation_scope:
  type: SYSTEM | TENANT | USER
  semantic_alias: <optional vocabulary mapping>
  source: SERVICE_CONTEXT | USER_SESSION | SYSTEM_GLOBAL
```

### Scope Types

| Type | Description | SDSR Injection |
|------|-------------|----------------|
| **SYSTEM** | Global/infrastructure | No tenant context |
| **TENANT** | Tenant-specific | `tenant_id` added |
| **USER** | User-specific | `user_id` added |

### Critical Vocabulary Rule

> **TENANT = CUSTOMER** — same entity, different vocabularies.

| Layer | Uses | Example |
|-------|------|---------|
| Infrastructure | TENANT | tenant_id, multi-tenant |
| UX/Console | CUSTOMER | customer dashboard |
| Database | TENANT | tenant_id column |

When a panel is TENANT-scoped, use `semantic_alias: CUSTOMER` to clarify it's customer-facing.

### Panel Class and Provenance

| Panel Class | Returns | Provenance |
|-------------|---------|------------|
| **evidence** | List | No provenance |
| **interpretation** | Dict | **REQUIRED** — aggregation, data_source, computed_at |

If an interpretation panel doesn't return provenance, SDSR will fail INV-004/INV-005.

### Auth Mode Mapping

| Scope Type | Auth Mode |
|------------|-----------|
| SYSTEM | OBSERVER |
| TENANT | SERVICE |
| USER | SESSION |

### Example: Cost Intelligence Panels

All OVR-SUM-CI panels are TENANT-scoped:

```yaml
observation_scope:
  type: TENANT
  semantic_alias: CUSTOMER
  source: SERVICE_CONTEXT
```

---

## References

### Core Governance (SDSR/HISAR/Aurora)

- [SDSR.md](SDSR.md) — **Scenario-Driven System Realization** (companion doc)
- [SDSR_SYSTEM_CONTRACT.md](SDSR_SYSTEM_CONTRACT.md) — System contract
- [SDSR_PIPELINE_CONTRACT.md](SDSR_PIPELINE_CONTRACT.md) — Pipeline contract

### Scripts & Tools

- `scripts/tools/run_hisar.sh` — Canonical HISAR runner
- `backend/aurora_l2/tools/aurora_*.py` — Phase automation scripts
- `design/l2_1/TRUST_POLICY.md` — Trust demotion rules

### Memory PINs

- PIN-370 — SDSR System Contract
- PIN-379 — E2E Pipeline
- PIN-407 — Observation Scope Architecture
- PIN-421 — AURORA L2 Automation Suite
- PIN-422 — HISAR Execution Doctrine (this document)
- PIN-425 — UI Plan Sync Closure
