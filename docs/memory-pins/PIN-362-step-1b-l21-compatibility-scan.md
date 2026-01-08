# PIN-362: STEP 1B — L2.1 Capability Compatibility Scan

**Status:** COMPLETE
**Created:** 2026-01-08
**Category:** Governance / Capability Intelligence
**Scope:** 26 CONSUME + 7 DEFER capabilities from STEP 1
**Prerequisites:** PIN-361 (STEP 1 Domain Applicability Matrix)

---

## Purpose (single sentence)

> Given capability truth + domain admissibility + L2.1 surfaces, determine **where a capability can mechanically live** — and generate new surfaces **only when structurally required**.

**STEP 1 = semantic admissibility**
**STEP 1B = mechanical bindability**

---

## Executive Summary

| Metric | Value | Status |
|--------|-------|--------|
| Capabilities scanned | 33 | 26 CONSUME + 7 DEFER |
| L2.1 baseline rows | 300 | EXTRACTED |
| Bounded bindings | 33 | COMPLETE |
| Generated rows | 33 | ALL GENERATED |
| Bind failures | 0 | NONE |

### Key Finding

**All 33 capability-domain pairs required row generation** — none matched existing L2.1 baseline rows. This indicates:

1. Existing L2.1 rows were designed for UI panels, not capability bindings
2. Capabilities have different authority/determinism profiles than panel rows
3. Row generation is working correctly as a fallback mechanism

### Per-Domain Bindings

| Domain | Bindings | Generated | Capabilities |
|--------|----------|-----------|--------------|
| ACTIVITY | 14 | 14 | 14 |
| POLICIES | 8 | 8 | 8 |
| LOGS | 6 | 6 | 6 |
| INCIDENTS | 5 | 5 | 5 |

---

## Inputs (Locked)

| Input | Source | Purpose |
|-------|--------|---------|
| `capability_directional_metadata.xlsx` | STEP 0B | Capability truth |
| `capability_applicability_matrix.xlsx` | STEP 1 | Domain admissibility |
| `l2_supertable_v3_cap_expanded.xlsx` | L2.1 baseline | Existing surfaces |

---

## Outputs (Authoritative)

| Output | Purpose |
|--------|---------|
| `L21_supertable_v3_cap_bounded_v1.xlsx` | Extended + bounded supertable |
| `l21_bind_failures.xlsx` | Why binding failed |
| `l21_generated_rows.xlsx` | Audit trail of new rows |

---

## Enum Ordering (LOCKED)

These orderings define **what can bind to what**. A capability cannot bind to a row that requires MORE than it provides.

### Authority Class (lowest to highest)

```
OBSERVE < EXPLAIN < ACT < CONTROL < ADMIN
   0         1       2       3        4
```

| Level | Meaning |
|-------|---------|
| OBSERVE | Read-only, no side effects |
| EXPLAIN | Correlates / derives truth |
| ACT | Triggers system behavior |
| CONTROL | Enforces or blocks |
| ADMIN | Governance / irreversible |

**Rule:** `capability.authority >= row.authority_required`

### Determinism Level (lowest to highest)

```
ADVISORY < BOUNDED < STRICT
    0          1        2
```

| Level | Meaning |
|-------|---------|
| ADVISORY | Non-deterministic (ML, predictions) |
| BOUNDED | Allowed variance |
| STRICT | Same input → same output |

**Rule:** `capability.determinism >= row.determinism_required`

### Mutability (lowest to highest)

```
READ < WRITE < EXECUTE < GOVERN
  0      1        2         3
```

| Level | Meaning |
|-------|---------|
| READ | No state changes |
| WRITE | State changes |
| EXECUTE | Triggers actions |
| GOVERN | Policy/governance changes |

**Rule:** `capability.mutability >= row.mutability_required`

---

## L2.1 Row Schema

Each L2.1 row (existing or generated) must have:

| Field | Type | Description |
|-------|------|-------------|
| `row_id` | string | Stable identifier |
| `domain` | enum | ACTIVITY / INCIDENTS / POLICIES / LOGS |
| `surface_type` | enum | TIMELINE / DETAIL / ACTION / EVIDENCE / SUBSTRATE |
| `authority_required` | enum | OBSERVE / EXPLAIN / ACT / CONTROL / ADMIN |
| `determinism_required` | enum | STRICT / BOUNDED / ADVISORY |
| `mutability_required` | enum | READ / WRITE / EXECUTE / GOVERN |
| `ui_visibility` | enum | VISIBLE / COLLAPSIBLE / HIDDEN |
| `origin` | enum | BASELINE / GENERATED |

---

## Compatibility Rules (Hard Gates)

```python
def is_compatible(capability, row):
    # Authority check
    if capability.authority < row.authority_required:
        return False, "AUTHORITY_MISMATCH"

    # Determinism check
    if capability.determinism < row.determinism_required:
        return False, "DETERMINISM_MISMATCH"

    # Mutability check
    if capability.mutability < row.mutability_required:
        return False, "MUTABILITY_MISMATCH"

    return True, "OK"
```

**No heuristics. No exceptions.**

---

## Row Expansion Rules

A new row may be generated **only if ALL are true**:

1. Capability decision is `CONSUME` or `DEFER`
2. Capability fails **all existing rows** in that domain
3. Capability has valid authority + determinism + mutability
4. Generated row:
   - Does NOT exceed capability authority
   - Does NOT increase mutability
   - Defaults to `ui_visibility = COLLAPSIBLE` or `HIDDEN`
   - Has explicit surface semantics

**If any condition fails → HARD REJECT, no row creation.**

### Allowed Expansions

- New row types (e.g., `EVIDENCE_ONLY`, `SUBSTRATE_SIGNAL`)
- New sub-rows under existing domains
- New authority classes

### Forbidden Expansions

- Rows that exist only to "make a capability fit"
- Rows that imply user control where none exists
- Rows invented purely for UI grouping

---

## Surface Types

| Type | Description | Authority Range |
|------|-------------|-----------------|
| TIMELINE | Temporal sequence of events | OBSERVE - ACT |
| DETAIL | Deep dive into single item | OBSERVE - EXPLAIN |
| ACTION | User-triggered operations | ACT - CONTROL |
| EVIDENCE | Immutable proof / replay | OBSERVE only |
| SUBSTRATE | Internal system surface | OBSERVE - ADMIN |

---

## Algorithm

```
FOR each capability in STEP 1 where decision in (CONSUME, DEFER):
    domain = capability.applicable_domain
    bound = FALSE

    FOR each existing_row in L2.1 where row.domain == domain:
        IF is_compatible(capability, existing_row):
            BIND capability to existing_row
            bound = TRUE

    IF NOT bound:
        IF can_generate_row(capability):
            new_row = generate_row(capability, domain)
            BIND capability to new_row
            ADD new_row to generated_rows
        ELSE:
            ADD capability to bind_failures
```

---

## Implementation

### Script

**File:** `scripts/ops/l21_capability_bind_scan.py`

**Responsibilities:**
1. Load capability truth (STEP 0B)
2. Load domain applicability (STEP 1)
3. Load L2.1 baseline rows
4. For each applicable capability:
   - Try binding to existing rows
   - If none fit → attempt controlled row expansion
5. Emit bounded supertable + failures + generated rows

---

## Progress Tracker

| Task | Status | Notes |
|------|--------|-------|
| Create PIN-362 | COMPLETE | This document |
| Formalize enum ordering | COMPLETE | `docs/capabilities/l21_enums.yaml` |
| Create L2.1 baseline | COMPLETE | 300 rows extracted |
| Implement script | COMPLETE | `scripts/ops/l21_capability_bind_scan.py` |
| Run STEP 1B | COMPLETE | 33 bindings, all generated |
| Review results | COMPLETE | See findings below |

## Generated Artifacts

| Artifact | Path |
|----------|------|
| Bounded Supertable | `docs/capabilities/l21_bounded/L21_supertable_v3_cap_bounded_v1.xlsx` |
| Baseline Rows | `docs/capabilities/l21_bounded/l21_baseline_rows.xlsx` |
| Bind Failures | `docs/capabilities/l21_bounded/l21_bind_failures.xlsx` |
| Generated Rows | `docs/capabilities/l21_bounded/l21_generated_rows.xlsx` |
| Enum Definitions | `docs/capabilities/l21_enums.yaml` |
| Scan Script | `scripts/ops/l21_capability_bind_scan.py` |

---

## Constraints (Non-Negotiable)

### C1 — Authority is absolute
Capability cannot bind upward in authority.

### C2 — Determinism compatibility
Capability cannot bind to stricter determinism than it guarantees.

### C3 — Mutability compatibility
Capability cannot exceed its mutability claim from STEP 0B.

### C4 — Surface ≠ Domain
Rows are surfaces, not domains. Adding a surface-like row is allowed; adding a domain is not.

---

## What STEP 1B Does NOT Do

- Decide UI layout
- Decide product grouping
- Make acceptance decisions
- Override STEP 1 rejections

---

## References

- PIN-361: STEP 1 Domain Applicability Matrix
- PIN-360: STEP 0B Directional Capability Normalization
- PIN-329: Capability Promotion & Merge Report
- L2.1 Supertable baseline

---

## Updates

### 2026-01-08: PIN Created

- Purpose defined
- Enum ordering formalized (AUTHORITY/DETERMINISM/MUTABILITY)
- Compatibility rules locked
- Row expansion rules defined
- Implementation pending
