# Layered Semantic Coherency Completion Contract

**Status:** ACTIVE
**Effective:** 2025-12-31
**Version:** 2.1 (Phase C′ Architectural Closure added)
**Scope:** L7 → L2 bidirectional coherency
**Reference:** PIN-253 (Layer Flow Coherency Verification)

---

## 1. Objective (Non-Negotiable)

> **Complete a bidirectional, coherent, closed-loop architecture from L7 to L2 such that:**
>
> - Every bottom-up flow (L7 → L2) is explainable, justified, and intentional
> - Every top-down flow (L2 → L7) maps to real execution and state
> - Domain semantics are authoritative, not accidental
> - APIs expose truth, not convenience
> - Missing pieces are identified explicitly before any product or CI hardening

### Completion Condition (All Must Be True)

- [ ] L7 → L6 → L5 → L4 → L3 → L2 flows documented
- [ ] L2 → L3 → L4 → L5 → L6 → L7 reconciliation documented
- [ ] No silent domain logic exists outside L4
- [ ] No API exists without a real execution path
- [ ] Drift is detected and corrected automatically during analysis

---

## 2. Core Invariants (Claude Must Enforce These)

Claude must **pause and flag** if any invariant is violated.

### I1. Domain Authority Direction

| Layer | May Do | May NOT Do |
|-------|--------|------------|
| L4 | Define domain meaning | — |
| L5 | Enforce L4 rules | Invent domain rules |
| L3 | Translate data/context | Reinterpret meaning |
| L2 | Expose domain actions | Decide domain logic |

**Violation Response:** If domain rules appear outside L4 → **STOP and flag**

### I2. Layer Purity

- No layer may bypass an adjacent layer
- Cross-layer shortcuts must be explicitly documented as violations or legacy debt

**Violation Response:** If L5 touches L3/L2 directly → **STOP**

### I3. Bottom-Up ≠ Top-Down Equivalence

| Direction | Shows |
|-----------|-------|
| Bottom-up (L7 → L2) | What happens |
| Top-down (L2 → L7) | What is promised |

Asymmetry must be **explicitly documented**, not "fixed" silently.

### I4. Evidence-Based Reasoning Only

**Allowed:**
- Code paths
- Persistence patterns
- Guards/validations
- Reuse patterns
- Stability evidence

**Forbidden:**
- Assumed intent
- "Probably" statements
- Naming-based inference

### I5. Scope Discipline

**Out of scope until explicitly allowed:**
- Performance tuning
- UX/product semantics
- CI enforcement
- Refactors

**Violation Response:** If these appear → **DEFER and park**

---

## 3. Execution Plan (Authoritative Path)

Work must follow **this order only**. Claude must refuse out-of-order requests.

### Phase A — L5 → L4 (Domain Semantics Extraction)

**Goal:** Prove that all execution behavior in L5 is authorized by domain semantics in L4.

**Tasks:**
1. Enumerate L5 actions (workers, jobs, orchestrations)
2. For each action:
   - Identify corresponding L4 rule / engine / invariant
   - Classify:
     - ✔ Authorized by L4
     - ⚠ Enforced redundantly
     - ❌ Shadow domain logic

**Artifact:** `docs/architecture/L5_L4_SEMANTIC_MAPPING.md`

**Constraint:** Claude must **not fix** violations, only record them.

---

### Phase B — L4 → L3 (Translation Integrity)

**Goal:** Ensure adapters translate data and context without altering domain meaning.

**Guardrails (MANDATORY):**
1. **L4 is authoritative** — treat as ground truth, even where shadow logic exists
2. **Descriptive only** — no adapter redesign, no optimization, no "improvements"
3. **Translation definition (FROZEN):** shape, transport, protocol, context binding — never rules, thresholds, or classification

**Tasks:**
1. Enumerate L3 adapters
2. For each adapter:
   - Identify what it transforms (shape, transport, protocol, context)
   - Verify no domain logic is introduced or dropped
   - Flag adapters that contain rules, thresholds, or classification

**Artifact:** `docs/architecture/L4_L3_TRANSLATION_INTEGRITY.md`

**Constraint:** If L3 makes decisions → **flag as violation** (do NOT fix)

---

### Phase C — L3 → L2 (API Truthfulness)

**Goal:** Ensure APIs expose real, complete, and truthful domain actions and state.

**Tasks:**
1. Enumerate L2 endpoints
2. For each endpoint:
   - Map to L3 adapter
   - Map to L4 domain rule
   - Map to L5 execution path
3. Classify:
   - ✔ Truthful
   - ⚠ Partial abstraction
   - ❌ Decorative / misleading

**Artifact:** `docs/architecture/L3_L2_API_TRUTH_TABLE.md`

---

### Phase C′ — Architectural Closure & L8 Hygiene (MANDATORY)

**Goal:** Ensure all bottom-up discoveries are resolved and L8 contains no runtime/domain/execution semantics.

**Hard Rule (Non-Negotiable):**
> No top-down validation (Phase D) may begin unless Phase C′ passes with zero open items.

**Purpose:** Answer one question only:
> "Is the system now clean enough that a top-down pass can be trusted?"

If the answer is no → **Phase D is BLOCKED**.

---

#### C′-1. Bottom-Up Discovery Closure

For every previously identified issue (shadow logic, adapter violations, API mismatches):

| Resolution Type | Allowed? |
|-----------------|----------|
| ✅ Fixed | YES |
| 🚫 Explicitly excluded (documented, justified) | YES |
| 🔁 Relocated to correct layer | YES |
| ⏳ Deferred | **NO** |
| 📋 Tech debt | **NO** |
| 🔜 Later | **NO** |

If any item is unresolved → **STOP**

---

#### C′-2. L8 Containment Audit (Critical)

**L8 must contain ZERO of the following:**

| Forbidden in L8 | Action if Found |
|-----------------|-----------------|
| Runtime decision logic | Move to L7 |
| Domain rules | Move to L4 |
| Execution orchestration | Move to L5 |
| Feature gating | Move to L4/L5 |
| Persistence semantics | Move to L6 |
| State mutation | Move to L5/L6 |

**Allowed in L8 ONLY:**
- CI/CD pipelines
- Test harnesses
- Static validators
- Code generation
- Linters
- Documentation tools

---

#### C′-3. L7 Boundary Re-assertion

Claude must verify:
- All runtime-affecting logic below L8 is owned by L7 or lower
- No CI job mutates runtime state directly
- No test harness is relied upon for production behavior

If CI/test code is *implicitly relied on* → **BLOCKER**

---

#### C′-4. Zero-Leak Guarantee

| Leak Type | Allowed? |
|-----------|----------|
| L8 → L7 runtime | ❌ |
| L8 → L6 state | ❌ |
| L8 → L5 execution | ❌ |
| L8 → L4 domain | ❌ |

If any are detected → fix or relocate.

---

**Artifact:** `docs/architecture/ARCHITECTURAL_CLOSURE_REPORT.md`

Claude may **NOT** proceed to Phase D without this artifact.

---

### Phase D — Bidirectional Reconciliation (Top-Down Validation)

**Goal:** Ensure bottom-up reality and top-down promise converge.

**Tasks:**
1. Select representative flows
2. Walk:
   - L7 → … → L2
   - L2 → … → L7
3. Identify:
   - Symmetry
   - Intentional asymmetry
   - Missing links

**Artifact:** `docs/architecture/END_TO_END_CONSISTENCY.md`

---

## 4. Drift Detection & Correction Protocol

Claude must actively enforce this **at every step**.

### Drift Signals

Claude must pause and notify if:

| Signal | Example |
|--------|---------|
| Layer jump | L2 analysis before L4 complete |
| Product concern | UI/UX consideration introduced |
| Premature CI | Enforcement rules suggested early |
| Assumed intent | "Probably" or naming-based reasoning |
| Fix proposal | Suggesting changes instead of documenting |

### Correction Action

When drift is detected, Claude must:

1. **State the drift explicitly**
2. **Restate the current phase**
3. **Redirect work to the correct task**
4. **Refuse to proceed until alignment is restored**

**Standard Response Format:**

```
DRIFT DETECTED

Type: [layer jump | product concern | premature CI | assumed intent | fix proposal]
Current Phase: [A | B | C | D]
Expected Work: [description]
Requested Work: [description]

Action: Parking this request. Returning to [correct task].
```

---

## 5. Fix-After-Phase Protocol (v2 RULE)

**Critical Change:** Violations must be fixed after each upward phase completes, NOT deferred to post-Phase D.

### Rationale

> Running top-down reconciliation (Phase D) on a knowingly impure system would produce false negatives.
> Phase D must operate on a clean foundation.

### Execution Sequence (Canonical)

```
BOTTOM-UP (Discovery + Fix)
═══════════════════════════
Phase A Discovery → Phase A Fixes → Phase A Re-Verify (clean)
    ↓
Phase B Discovery → Phase B Fixes → Phase B Re-Verify (clean)
    ↓
Phase C Discovery → Phase C Fixes → Phase C Re-Verify (clean)
    ↓
CLOSURE GATE
═══════════════════════════
Phase C′ — Architectural Closure & L8 Hygiene
    ↓
TOP-DOWN (Credibility Validation)
═══════════════════════════
Phase D (on certified clean system, zero violations)
```

**Claude must STOP if Phase C′ fails.**

### Fix Rules

| Rule | Description |
|------|-------------|
| F1 | Fix ONLY violations from the CURRENT phase |
| F2 | Re-verify phase is clean before proceeding |
| F3 | If fix introduces NEW violation → immediate correction |
| F4 | Phase D BLOCKED until Phases A, B, C have zero open violations |

### Phase-Specific Fix Authority

| Phase | Violation Type | Fix Target |
|-------|---------------|------------|
| A | Shadow domain logic in L5 | Move rules to L4 domain engines |
| B | Domain logic in L3 adapters | Move policy to L4, reduce L3 to translation |
| C | Decorative/misleading APIs | Remove or document as intentional abstraction |

### Phase B Acceptance Condition (EXPLICIT)

**After Phase B fixes, L3 adapters must contain ZERO of the following:**

| Forbidden in L3 | Relocation Target |
|-----------------|-------------------|
| Thresholds | L4 PolicyEngine / Domain Engine |
| Classification logic | L4 Domain Engine |
| Policy branching | L4 PolicyEngine |
| Role/level mapping | L4 RBACEngine |
| Model/provider selection rules | L4 PolicyEngine |

**Enforcement:** Phase B is NOT clean until all adapters pass this check.

---

## 6. Completion Gate

Claude may only declare completion when:

- [ ] Phase A artifact exists and is CLEAN
- [ ] Phase B artifact exists and is CLEAN
- [ ] Phase C artifact exists and is CLEAN
- [ ] **Phase C′ ARCHITECTURAL_CLOSURE_REPORT.md exists and is CERTIFIED**
- [ ] Phase D artifact exists
- [ ] **All violations FIXED (not just listed)**
- [ ] Bidirectional consistency is documented
- [ ] Missing pieces are explicitly enumerated
- [ ] **Phase D ran on certified clean system (C′ passed)**

**Only after completion may Claude:**
- Suggest CI enforcement
- Suggest refactors
- Suggest product/L1 implications

---

## 7. Phase Status Tracker

| Phase | Artifact | Discovery | Fixes | Status |
|-------|----------|-----------|-------|--------|
| A | L5_L4_SEMANTIC_MAPPING.md | ✅ COMPLETE | ✅ COMPLETE (3/3) | **CLEAN** (2025-12-31) |
| B | L4_L3_TRANSLATION_INTEGRITY.md | ✅ COMPLETE | ⏳ PENDING (5 items) | **FIX REQUIRED** |
| C | L3_L2_API_TRUTH_TABLE.md | NOT STARTED | — | BLOCKED (awaits B clean) |
| **C′** | **ARCHITECTURAL_CLOSURE_REPORT.md** | — | — | **BLOCKED** (awaits C clean) |
| D | END_TO_END_CONSISTENCY.md | NOT STARTED | — | BLOCKED (awaits C′ certified) |

### Phase A Results

- **L5 Actions Enumerated:** 56
- **L4 Domain Authorities:** 31
- **Authorized:** 48 (85.7%)
- **Redundant:** 5 (8.9%)
- **Shadow Logic:** 3 (5.4%)

**Shadow Logic Fixed (2025-12-31):**
1. ~~SHADOW-001: Auto-execute confidence threshold~~ → Moved to L4 `should_auto_execute()`
2. ~~SHADOW-002: Failure category heuristics~~ → Moved to L4 `classify_error_category()`
3. ~~SHADOW-003: Recovery mode heuristics~~ → Moved to L4 `suggest_recovery_mode()`

**All shadow logic now delegated to L4 RecoveryRuleEngine. Phase A CLEAN.**

### Phase B Results

- **L3 Adapters Enumerated:** 13
- **Valid Translators:** 8 (61.5%)
- **Domain Logic Violations:** 5 (38.5%)
- **Violation LOC:** ~550 (13% of L3 code)

**Translation Violations Identified:**
1. B01: OpenAI Adapter — safety limits, budget enforcement (HIGH)
2. B02: CostSim V2 Adapter — cost modeling, risk classification (HIGH)
3. B03: Clerk Auth Provider — role mapping, tenant isolation (MEDIUM)
4. B04: OIDC Provider — role extraction, role mapping (MEDIUM)
5. B05: Tenant LLM Config — model selection policy (MEDIUM)

---

## 8. Related Documents

| Document | Relationship |
|----------|--------------|
| INDEX.md | Architecture document index |
| AUTHORITY_BOUNDARIES.md | Layer intent authority |
| IMPLIED_INTENT_ANALYSIS.md | L7→L6→L5 chain classification |
| L7_L6_L5_COHERENCY_PASS.md | Upstream coherency verification |

---

**Contract Authority:** This contract governs all L5→L2 analysis work.
**Violation Protocol:** Work that violates this contract must be parked and redirected.
**Amendment:** Requires explicit human approval to modify.
