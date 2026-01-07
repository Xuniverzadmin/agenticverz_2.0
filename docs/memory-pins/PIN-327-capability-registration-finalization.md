# PIN-327: Capability Registration Finalization (First-Class, Dormant, Substrate)

**Status:** COMPLETE
**Created:** 2026-01-06
**Category:** Governance / Capability Registration
**Scope:** Full System Registration
**Prerequisites:** PIN-326 (Dormant Capability Elicitation)

---

## Objective

Register ALL executable capabilities into a single, closed Capability Registry with explicit status, scope, and constraints, without changing system behavior.

**Operating Mode:** Registration ONLY — no promotion, no deletion, no behavior changes.

---

## Executive Summary

| Metric | Value | Status |
|--------|-------|--------|
| Total Capabilities Registered | 128 | COMPLETE |
| FIRST_CLASS | 18 | CAP-001 to CAP-018 |
| DORMANT | 103 | LCAP from PIN-326 |
| SUBSTRATE | 7 | SUB-001 to SUB-007 |
| Registry Schema Version | V2.0.0 | NEW |
| Negative Assertion | NO unregistered | COMPLETE |

---

## Key Achievement

**Before PIN-327:**
- 18 CAP in registry
- 103 LCAP unregistered
- No unified schema
- Mixed status tracking

**After PIN-327:**
- 128 capabilities registered
- 0 unregistered capabilities
- V2.0.0 schema enforced
- Explicit status for every capability

---

## Phase Execution Summary

| Phase | Task | Status |
|-------|------|--------|
| 1 | Extend Capability Registry Schema | COMPLETE |
| 2 | Register FIRST_CLASS (CAP-001 to CAP-018) | COMPLETE |
| 3 | Register DORMANT (103 LCAP) | COMPLETE |
| 4 | Register SUBSTRATE (7 SUB) | COMPLETE |
| 5 | Negative assertion (final) | COMPLETE |
| 6 | Produce registration report | COMPLETE |

---

## Capability Status Distribution

### By Status

| Status | Count | Description |
|--------|-------|-------------|
| FIRST_CLASS | 18 | Promoted, governed, surfaceable |
| DORMANT | 103 | Discovered, not promoted |
| SUBSTRATE | 7 | Foundational, never user-invokable |

### By Execution Vector

| Vector | Count |
|--------|-------|
| HTTP | 77 |
| SDK | 31 |
| CLI | 10 |
| Worker | 3 |
| None (SUBSTRATE) | 7 |

### By Authority Model

| Model | Count |
|-------|-------|
| DECLARED | 25 |
| UNCLASSIFIED | 103 |

---

## Registry Schema V2.0.0

### Status Enum
- **FIRST_CLASS:** Fully promoted, governed, and surfaceable
- **DORMANT:** Discovered but not yet promoted
- **SUBSTRATE:** Foundational, never user-invokable

### Execution Vectors
- `http`: HTTP API routes (L2)
- `worker`: Background workers/tasks (L5)
- `cli`: CLI commands (L7)
- `sdk`: SDK methods (L1)

### Authority Model
- **DECLARED:** Authority rules explicitly defined
- **UNCLASSIFIED:** Authority rules not yet defined

### Console Scope
- **CUSTOMER:** Visible in customer console
- **FOUNDER:** Visible in founder console
- **SDK:** SDK-only, not console visible
- **NONE:** Not visible in any console
- **UNDECIDED:** Scope not yet determined

---

## Invariants Established

1. **Status Invariant:** Every capability has exactly one status
2. **Registration Invariant:** Every executable path maps to a capability
3. **Permanence Invariant:** Registration is permanent (no silent removal)
4. **DORMANT Invariant:** DORMANT capabilities cannot be invoked from frontend
5. **SUBSTRATE Invariant:** SUBSTRATE capabilities are never user-invokable

---

## Negative Assertion Update

**Question:** Is there any executable capability NOT registered in this registry?

| PIN | Answer | Coverage |
|-----|--------|----------|
| PIN-325 | YES | 8% registered |
| PIN-326 | NO (undiscovered) | 100% discovered |
| PIN-327 | NO (unregistered) | 100% registered |

**Caveat:** Covers statically-discoverable capabilities only.

---

## Human Decisions Required

1. **DORMANT Promotion:** 103 capabilities need promotion decisions
2. **Authority Gaps:** 67 capabilities have authority_missing
3. **CLI/SDK Governance:** 41 capabilities are ungoverned
4. **Auto-Execute Gates:** LCAP-WKR-002 lacks capability gate

---

## Artifacts

| Artifact | Path |
|----------|------|
| Schema V2 | `docs/capabilities/CAPABILITY_REGISTRY_SCHEMA_V2.yaml` |
| Unified Registry | `docs/capabilities/CAPABILITY_REGISTRY_UNIFIED.yaml` |
| Registration Report | `l2_1/evidence/pin_327/REGISTRATION_REPORT.md` |
| Memory PIN | `docs/memory-pins/PIN-327-capability-registration-finalization.md` |

---

## References

- PIN-325: Shadow Capability Forensic Audit
- PIN-326: Dormant → Declared Capability Elicitation
- CAPABILITY_REGISTRY_SCHEMA_V2.yaml
- CAPABILITY_REGISTRY_UNIFIED.yaml

---

## Updates

### 2026-01-06: PIN Created and Completed

- All 6 phases executed successfully
- 128 capabilities registered (18 FIRST_CLASS, 103 DORMANT, 7 SUBSTRATE)
- V2.0.0 schema created and enforced
- Negative assertion: NO unregistered capabilities
- Ready for human decision on promotion actions
