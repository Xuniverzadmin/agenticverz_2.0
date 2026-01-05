# PIN-302: Tier-2 Semantic Closure - Policies and AI Console Keys

**Status:** COMPLETE
**Created:** 2026-01-05
**Category:** Governance / L2 Promotion
**Milestone:** Tech Debt Clearance
**Continues:** PIN-301

---

## Summary

Completed Tier-2 semantic closure with L2_GUARD_POLICIES and L2_GUARD_AICONSOLE_KEYS intents. Fixed critical over-tightening issue (global vs surface-scoped prohibitions). Established terminology correction for AI Console Keys. Analytics domain remains unstarted by design.

---

## Details

### Session Context

This session continued from a previous conversation where:
- Tier-1 triangle was complete (Logs, Activity, Incidents)
- L2_GUARD_POLICIES was in DRAFT state with surface-scoping revision needed
- PIN-301 was tracking progress

### Work Completed

#### 1. L2_GUARD_POLICIES Freeze (Commit: 2ae34c24)

**Critical Fix Applied:** Surface-scoped prohibitions

The initial Policies intent had **globally-scoped** prohibitions that would have prevented an Analytics domain from existing. This was corrected:

| Before (Wrong) | After (Correct) |
|---------------|-----------------|
| "Never use effectiveness" | "Avoid effectiveness at this surface (Analytics may use)" |
| Global prohibition | Location-based prohibition |

**Founder Decisions:**
1. `percentage_used`: SHOW as neutral fact (freeze-safe)
2. `action_on_trigger`: SHOW RAW (block/warn/log)
3. Policy CRUD: SEPARATE surface (non-negotiable)

**Key Architectural Property:**
- Prohibitions are **surface-scoped**, not global
- Analytics domain explicitly permitted to exist separately
- No back-propagation of meaning into definition surfaces

#### 2. L2_GUARD_AICONSOLE_KEYS Freeze (Commit: 6fbc083e)

**Terminology Correction (BLOCKING):**

The `/guard/keys` surface required explicit object identity clarification:

| Property | Correct | NOT |
|----------|---------|-----|
| Object | Platform-issued AI Console keys | Third-party LLM provider keys |
| Nature | Operational credentials | Secrets vault |
| Scope | Access to AI Console/Agenticverz services | External API credentials |

**Intent ID:** `L2-GUARD-AICONSOLE-KEYS` (not `L2-GUARD-KEYS`)

**Authority Semantics:**
- Control surface (mutates state)
- Manual-only lifecycle (create/revoke/rotate)
- No automated rotation, revocation, or creation

**Founder Decisions (A/A/A):**
1. Developer visibility: METADATA ONLY (name, scope, status, timestamps)
2. Revocation semantics: TERMINAL (revoked means dead; new key required)
3. Rotation: MANUAL ONLY (no suggestions, no automation)

**Terminology Rules (Frozen):**
- Use "AI Console Key" (never "LLM key", "provider key", "secret")
- Use "scope" not "permissions"
- Use "revoked" not "deleted"

### Final Semantic Lattice

| Surface | Intent ID | Status | Interpretation |
|---------|-----------|--------|----------------|
| `/guard/logs` | L2-GUARD-LOGS | APPROVED | Forbidden |
| `/api/v1/customer/activity` | L2-GUARD-ACTIVITY | APPROVED | Forbidden |
| `/guard/incidents` | L2-GUARD-INCIDENTS | APPROVED | Forbidden |
| `/guard/policies` | L2-GUARD-POLICIES | APPROVED | Forbidden (surface-scoped) |
| `/guard/keys` | L2-GUARD-AICONSOLE-KEYS | FROZEN | Forbidden |
| Analytics (future) | — | NOT STARTED | Permitted |

**Invariant Preserved:** Interpretation exists only in Analytics domain, never in truth or definition surfaces.

### Key Insights Learned

1. **Surface-Scoped vs Global Prohibitions**
   - Prohibitions must say "not here" not "never anywhere"
   - Analytics is a derived interpretation layer, not a surface
   - Location-based prohibition, not existence-based

2. **Object Identity Before Freeze**
   - Keys surface required terminology correction before any semantic work
   - "AI Console Keys" disambiguates from external credentials
   - Terminology is frozen and cannot be modified

3. **Authority vs Projection**
   - Keys is a control surface (mutates state)
   - Policies is projection-only (read definitions)
   - Different authority semantics require explicit declaration

## Commits

| Commit | Description |
|--------|-------------|
| 2ae34c24 | Freeze L2_GUARD_POLICIES intent - Tier-2 surface approved |
| 6fbc083e | Freeze L2_GUARD_AICONSOLE_KEYS intent - Tier-2 complete |

## Files Modified

- `docs/intents/L2_GUARD_POLICIES_INTENT.yaml` — APPROVED
- `docs/intents/L2_GUARD_AICONSOLE_KEYS_INTENT.yaml` — FROZEN (new)
- `docs/memory-pins/PIN-301-l2-intent-declaration-progress---semantic-promotion-gate.md` — Updated

## Next Steps (Blocked Until Called)

1. **Define Analytics Domain Constitution** — Separate intent template, read-only, no back-propagation
2. **Bind Frontend (L1) to Frozen Intents** — UI contracts enforced, zero inference
3. **Tier-3 Surfaces** — `/guard/costs`, health endpoints

---

## Related PINs

- [PIN-300](PIN-300-semantic-promotion-gate.md) — Constitutional rule
- [PIN-301](PIN-301-l2-intent-declaration-progress---semantic-promotion-gate.md) — Progress tracker
- [PIN-298](PIN-298-.md) — Frontend Constitution Survey
- [PIN-299](PIN-299-.md) — Tech Debt Clearance
