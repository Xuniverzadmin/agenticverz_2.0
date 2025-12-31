# Phase G — Steady-State Governance

**Status:** ACTIVE (Permanent)
**Effective:** 2025-12-31
**Authority:** Hard Rules, No Drift Allowed

---

## Purpose

Phase G exists to prevent **architecture regression**, **authority erosion**, and **governance decay** after Phase F completion.

This phase is **permanent**.

---

## G-1. BLCA Supremacy Rule

BLCA **must run**:

- At the start of every Claude session
- After any code change touching L2–L5
- After adding any new external integration

BLCA output is **authoritative**.

A non-CLEAN status **halts all forward work**.

**Command:** `python3 scripts/ops/layer_validator.py --backend --ci`

---

## G-2. Zero-Tolerance Rule

The following are **never allowed**:

| Forbidden | Reason |
|-----------|--------|
| "Acceptable" bypasses | Violations are defects, not preferences |
| "Temporary" direct calls | Temporary = permanent in practice |
| "Just this once" imports | Precedent destroys governance |
| "We'll fix it later" exceptions | Later never comes |

Any of the above is treated as a **BLOCKING violation**.

---

## G-3. Change Classification Rule

| Change Type | Required Action |
|-------------|-----------------|
| New API endpoint | L3 adapter + L4 command **before** implementation |
| New worker capability | L4 decision engine **before** execution |
| Policy change | L4 only; L3/L5 forbidden |
| Execution optimization | Allowed only inside L5 |
| Refactor | BLCA must remain CLEAN |

---

## G-4. Human Acknowledgment Rule

- BLCA findings **must be acknowledged explicitly**
- Silence ≠ acceptance
- CLEAN status must be reaffirmed periodically (cadence defined by owner)

---

## G-5. Override Rule (Emergency Only)

Overrides are allowed **only** if **all** conditions are true:

1. Written justification exists
2. A governance PIN is created
3. A remediation path is defined
4. BLCA re-run is scheduled

There is **no silent override**.

---

## G-6. Decay Prevention Clause

If BLCA is not actively enforced, the system is considered **governance-invalid**, regardless of runtime behavior.

---

## G-7. Import Direction Law (Immutable)

| Source | May Import |
|--------|------------|
| L1 | L2, L3 |
| L2 | L3, L4, L6 |
| L3 | L4, L6 |
| L4 | L5, L6 |
| L5 | L6 |
| L6 | L6 only (peers) |
| L7 | Any (operational) |

**Note:** L4 → L5 is authorized. This is delegation, not bypass.

---

## G-8. Layer Freeze Rule

The seven-layer model is **frozen**:

| Layer | Name | Status |
|-------|------|--------|
| L1 | Product Experience | FROZEN |
| L2 | Product APIs | FROZEN |
| L3 | Boundary Adapters | FROZEN |
| L4 | Domain Engines | FROZEN |
| L5 | Execution & Workers | FROZEN |
| L6 | Platform Substrate | FROZEN |
| L7 | Ops & Scripts | FROZEN |

Layers cannot be added, removed, renamed, or reordered without constitutional amendment.

---

## G-9. Extraction-First Resolution

When a file violates layer boundaries:

1. **Extraction** is the default fix
2. **Reclassification** is allowed only for historical labeling errors
3. **Suppression** is forbidden
4. **Documentation-as-fix** is forbidden

---

## G-10. Amendment Protocol

These rules may only be changed by **constitutional amendment**:

1. Create a PIN proposing the amendment
2. Document rationale with evidence
3. Require explicit human ratification
4. Update this document with amendment reference

**Forbidden:**
- Silent rule changes
- "Pragmatic" exceptions
- "Just this once" bypasses

---

## Enforcement Summary

| Violation | Response |
|-----------|----------|
| BLCA violation | Merge blocked |
| Bypass attempt | Work halted |
| Silent override | Governance invalid |
| Layer breach | Extraction required |

---

## Reference

- PIN-258: Phase F Application Boundary Completion
- PIN-259: Phase G Steady-State Governance
- PHASE_F_CLOSURE_DECLARATION.md
