# PIN-447: Policy Domain V2 Design

**Status:** APPROVED
**Created:** 2026-01-19
**Category:** Architecture / Domain Design

---

## Summary

Approved the Policy Domain V2 design that introduces a clean facade layer while preserving O1-O5 depth, subdomains, and the existing panel structure. The design ensures Policy participates in cross-domain feedback loops only via artifacts, never via control flow.

---

## Key Decisions

### 1. Facade Layer (5 Authority Endpoints)

```
GET /api/v1/policy/active      → What governs execution now?
GET /api/v1/policy/library     → What patterns are available?
GET /api/v1/policy/lessons     → What governance emerged?
GET /api/v1/policy/thresholds  → What limits are enforced?
GET /api/v1/policy/violations  → What enforcement occurred?
```

### 2. Capability Architecture

**Facade (cross-domain visible):**
- `policy.active`
- `policy.library`
- `policy.lessons`
- `policy.thresholds`
- `policy.violations`

**Internal (policy domain only):**
- `internal.policy.governance.*`
- `internal.policy.limits.*`

### 3. Preserved Structure

- ✅ GOVERNANCE / LIMITS subdomains
- ✅ DRAFTS separate from LESSONS
- ✅ O1-O5 depth model
- ✅ All 30 existing panels

### 4. Feedback Loop Invariants

- Policy participates only via **artifacts**, never control flow
- **Human gate mandatory**: No policy change without DRAFT state
- Activity uses **cached** policy_context for resilience
- Violations must exist **before** incidents

---

## Architecture Documents

| Document | Purpose |
|----------|---------|
| `docs/architecture/policies/POLICY_DOMAIN_V2_DESIGN.md` | Complete V2 design |
| `docs/contracts/CROSS_DOMAIN_POLICY_CONTRACT.md` | Cross-domain binding rules |

---

## SDSR Loop Assertions

1. **SDSR-LOOP-001**: Violation before incident
2. **SDSR-LOOP-002**: Lesson references source
3. **SDSR-LOOP-003**: Active policy has origin
4. **SDSR-LOOP-004**: Activity resilience

---

## Migration Phases

1. **Phase 1**: Add V2 facade (non-breaking)
2. **Phase 2**: Add detail endpoints
3. **Phase 3**: Capability registry update
4. **Phase 4**: Cross-domain rebind
5. **Phase 5**: Deprecation (optional)

---

## Cross-Domain Rules

### Activity → Policy
- READ policy_context
- NAVIGATE via facade_ref
- CACHE for resilience
- NO synchronous evaluation

### Incidents → Policy
- READ violations
- PROPOSE lessons
- NO creating violations

### Policy → Incidents
- READ for lessons
- NO creating incidents

---

## Related PINs

- PIN-446: Attention Feedback Loop Implementation
- PIN-445: Incidents Domain V2 Migration
- PIN-370: SDSR System Contract

---

## Review Notes

Design reviewed and approved by GPT-4 architecture review with specific guidance:

1. Facade is a **governance firewall**, not API convenience
2. Capability split is the **load-bearing wall**
3. O-levels are **views**, not surfaces
4. Loops must be **implicit**, not forced integrations

