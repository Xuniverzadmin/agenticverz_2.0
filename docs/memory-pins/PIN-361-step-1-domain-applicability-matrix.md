# PIN-361: STEP 1 — Domain Applicability Matrix

**Status:** ✅ COMPLETE
**Created:** 2026-01-08
**Category:** Governance / Capability Intelligence
**Scope:** 4 Domains x 41 Capabilities = 164 Evaluations
**Prerequisites:** PIN-360 (STEP 0B Directional Normalization)

---

## Purpose (single sentence, no drift)

> Determine **which domains are even allowed to attempt a capability**, based on *questions*, not UI, not architecture.

This step answers **"may we try?"**, not **"does it work?"**.

---

## Executive Summary

| Metric | Value | Status |
|--------|-------|--------|
| Domains in scope | 4 | LOCKED |
| Capabilities to evaluate | 41 | FROM STEP 0B |
| Total evaluations | 164 | COMPLETE |
| Domain intent spec | YES | COMPLETE |
| Script implemented | YES | COMPLETE |
| Applicability matrix generated | YES | COMPLETE |

### Decision Distribution

| Decision | Count | Percentage |
|----------|-------|------------|
| CONSUME | 26 | 15.9% |
| DEFER | 7 | 4.3% |
| REVIEW | 0 | 0.0% |
| REJECT | 131 | 79.9% |

### Per-Domain Results

| Domain | CONSUME | DEFER | REJECT |
|--------|---------|-------|--------|
| ACTIVITY | 9 | 5 | 27 |
| INCIDENTS | 5 | 0 | 36 |
| POLICIES | 6 | 2 | 33 |
| LOGS | 6 | 0 | 35 |

### Cross-Domain Capabilities (applicable to 2+ domains)

| Capability | Domains |
|------------|---------|
| CAP-001 | ACTIVITY, INCIDENTS, LOGS, POLICIES (all 4) |
| CAP-011 | ACTIVITY, LOGS, POLICIES |
| CAP-002 | ACTIVITY, INCIDENTS, LOGS |
| CAP-021 | ACTIVITY, INCIDENTS, LOGS |
| CAP-016 | ACTIVITY, POLICIES |
| CAP-012 | ACTIVITY, LOGS |
| CAP-020 | ACTIVITY, LOGS |
| CAP-019 | ACTIVITY, POLICIES |
| CAP-003 | ACTIVITY, POLICIES |
| CAP-005 | INCIDENTS, POLICIES |
| CAP-009 | INCIDENTS, POLICIES |

---

## Inputs (Locked)

### Mandatory

| Input | Authority | Purpose |
|-------|-----------|---------|
| `capability_directional_metadata.xlsx` | HIGH | Directional truth from STEP 0B |
| `domain_intent_spec.yaml` | HIGH | Domain → questions → intent map |

### Optional (recommended)

| Input | Authority | Purpose |
|-------|-----------|---------|
| `CAPABILITY_REGISTRY_UNIFIED.yaml` | MEDIUM | Lifecycle guard (planned/deprecated) |

**No Claude here. No code scanning here. This is semantic + intent matching.**

---

## Domains in Scope (Locked)

| Domain | Core Question |
|--------|---------------|
| **Activity** | What ran / is running? |
| **Incidents** | What went wrong? |
| **Policies** | How is behavior defined? |
| **Logs** | What is the raw truth? |

**Explicitly excluded:** Overview (deferred to later phase)

---

## Domain Intent Specification (v1.0)

**File:** `docs/domains/domain_intent_spec.yaml`

### Design Rules (Non-Negotiable)

| Rule | Description |
|------|-------------|
| D1 | Question-first (no capabilities, no UI) |
| D2 | Questions must be answerable (observable, user language) |
| D3 | IDs are mandatory and stable |
| D4 | Overview is excluded (derived later) |

### Question Summary

| Domain | Questions | HIGH Criticality |
|--------|-----------|------------------|
| ACTIVITY | 6 | 5 |
| INCIDENTS | 5 | 4 |
| POLICIES | 4 | 3 |
| LOGS | 3 | 2 |
| **Total** | **18** | **14** |

### Question Types

| Type | Count | Description |
|------|-------|-------------|
| state | 6 | Current system state |
| performance | 4 | How well things performed |
| explanation | 5 | Why something happened |
| action | 3 | What can be done |

### Evolution Rules

| Allowed | Forbidden |
|---------|-----------|
| Add new questions | Rename question IDs |
| Refine question text | Delete bound questions |
| Change criticality | Add Overview questions |

---

## Core Rule (Non-Negotiable)

> A capability is **applicable to a domain only if it unambiguously answers at least one domain question**.

No question → no applicability → hard NO.

---

## Applicability Dimensions

Each capability × domain pair is evaluated along **four axes**:

### 1. Question Coverage

- Does the capability answer ≥1 question from that domain?
- Questions are exact strings or IDs, not vibes

### 2. Capability Role Fit

Derived from STEP 0B fields:
- `claimed_role`
- `claimed_exposure_type`
- `mutability_claim`
- `determinism_claim`

### 3. Console Scope Compatibility

Soft constraint, not a blocker:
- CUSTOMER / FOUNDER / SDK / NONE

### 4. Trust Weight Modifier

Trust does **not decide**, but it **modulates confidence**.

---

## Decisions (Finite Set)

Each capability × domain results in exactly one decision:

| Decision | Meaning | Next Action |
|----------|---------|-------------|
| `CONSUME` | Proceed to L2.1 compatibility scan | STEP 1B |
| `DEFER` | Conceptually fits, but weak/ambiguous | Review later |
| `REJECT` | Does not answer any domain question | No further action |
| `REVIEW` | Conflicts or overlaps multiple domains | Human decision |

**No "partial", no "tentative".**

---

## Confidence Computation (Deterministic)

This is **not trust weight**. Different thing.

```
base = 0.4

+0.3 if >=2 questions answered
+0.2 if claimed_role matches domain intent
+0.1 if trust_weight == HIGH
-0.2 if exposure is advisory-only
-0.2 if console scope mismatched

clamp to [0.0, 1.0]
```

**Rule:** Confidence < 0.5 cannot be CONSUME.

---

## Output Artifacts

### Primary Table (Authoritative)

**`capability_applicability_matrix.xlsx`**

| Column | Description |
|--------|-------------|
| `domain` | Activity / Incidents / Policies / Logs |
| `capability_id` | CAP-XXX or SUB-XXX |
| `applicable` | TRUE only if CONSUME or DEFER |
| `questions_answered` | Explicit question IDs |
| `decision` | CONSUME / DEFER / REJECT / REVIEW |
| `confidence` | Computed score [0.0, 1.0] |
| `notes` | Justification |

### Derived (Never Edited Manually)

- `capability_applicability_matrix.csv`
- `capability_applicability_matrix.yaml`

---

## Implementation

### Script

**File:** `scripts/ops/capability_applicability.py`

**Responsibilities:**
1. Load directional metadata from STEP 0B
2. Load domain intent spec
3. Evaluate applicability mechanically
4. Emit tables

No heuristics without explanation in `notes`.

---

## Failure Modes (Why They're Good)

| Outcome | Interpretation |
|---------|----------------|
| Many `REJECT`s | Domain intent is sharp (good) |
| Many `DEFER`s | Ambiguity exposed early (good) |
| Few `CONSUME`s | Protects L2.1 from overload (very good) |

**If STEP 1 feels "harsh", it's working.**

---

## Explicit NON-GOALS

STEP 1 must NOT:

- Bind to L2.1 rows
- Assign UI slots
- Execute scenario logic
- Implement kill switches
- Make acceptance decisions

That's why STEP 1 is fast, repeatable, and safe.

---

## Progress Tracker

| Task | Status | Notes |
|------|--------|-------|
| Create PIN-361 | COMPLETE | This document |
| Create domain_intent_spec.yaml | COMPLETE | 4 domains, 18 questions |
| Implement capability_applicability.py | COMPLETE | `scripts/ops/capability_applicability.py` |
| Run script | COMPLETE | 164 evaluations generated |
| Generate matrix | COMPLETE | xlsx, csv, yaml outputs |
| Review results | COMPLETE | 80% REJECT rate (expected) |

## Generated Artifacts

| Artifact | Path |
|----------|------|
| Applicability Matrix (Excel) | `docs/capabilities/applicability/capability_applicability_matrix.xlsx` |
| Applicability Matrix (CSV) | `docs/capabilities/applicability/capability_applicability_matrix.csv` |
| Applicability Matrix (YAML) | `docs/capabilities/applicability/capability_applicability_matrix.yaml` |
| Domain Intent Spec | `docs/domains/domain_intent_spec.yaml` |
| Applicability Script | `scripts/ops/capability_applicability.py` |

---

## Next Steps (User Choice)

| Option | Description |
|--------|-------------|
| **1** | Tighten `domain_intent_spec.yaml` (questions → IDs) |
| **2** | Expand applicability rules per domain (Activity first) |
| **3** | Move to STEP 1B – L2.1 compatibility scan using this matrix |

---

## References

- PIN-360: STEP 0B Directional Capability Normalization
- PIN-329: Capability Promotion & Merge Report
- CAPABILITY_REGISTRY_UNIFIED.yaml
- CUSTOMER_CONSOLE_V1_CONSTITUTION.md (frozen domains)

---

## Updates

### 2026-01-08: STEP 1 Complete

**Results:**
- 164 evaluations (41 capabilities x 4 domains)
- 26 CONSUME (15.9%) — proceed to L2.1
- 7 DEFER (4.3%) — review later
- 131 REJECT (79.9%) — no domain fit

**Key Findings:**
- CAP-001 (Execution Replay & Activity) is applicable to ALL 4 domains
- 11 capabilities are cross-domain (applicable to 2+ domains)
- ACTIVITY domain has highest applicability (9 CONSUME)
- INCIDENTS has most restrictive matching (5 CONSUME)
- 80% rejection rate confirms domain intent is sharp

**Artifacts Generated:**
- `capability_applicability_matrix.xlsx`
- `capability_applicability_matrix.csv`
- `capability_applicability_matrix.yaml`

### 2026-01-08: Domain Intent Spec Created

- Created `domain_intent_spec.yaml` with 18 questions
- 4 domains: ACTIVITY, INCIDENTS, POLICIES, LOGS
- Question types: state, performance, explanation, action

### 2026-01-08: PIN Created

- Purpose defined
- Applicability dimensions locked
- Confidence computation formalized
- Decision categories defined

### Update (2026-01-08)

STEP 1 COMPLETE - 164 evaluations, 26 CONSUME, 7 DEFER, 131 REJECT

