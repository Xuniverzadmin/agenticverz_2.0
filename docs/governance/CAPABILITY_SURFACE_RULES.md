# Capability Surface Rules

**Status:** ACTIVE
**Effective:** 2026-01-18
**Authority:** Governance
**Reference:** INTENT_LEDGER Policy TOPIC-SCOPED-ENDPOINT-001

---

## Purpose

This document defines **do/don't rules** for capability surfaces in the L2.1 pipeline.
These rules prevent control-plane violations where topic semantics are bypassed or misconfigured.

---

## Definitions

| Term | Definition |
|------|------------|
| **Capability** | A semantic contract describing what the system can do (e.g., `activity.runs_by_dimension`) |
| **Surface** | An API endpoint that exposes a capability to a panel |
| **Topic** | A UI grouping within a subdomain (e.g., LIVE, COMPLETED, SIGNALS) |
| **Implicit Binding** | State/scope injected by endpoint, not caller-controlled |
| **Explicit Binding** | State/scope passed by caller via query param or header |

---

## Do/Don't Rules

### RULE-CAP-001: Topic Scope Enforcement

| DO | DON'T |
|----|-------|
| Create topic-scoped endpoints with hardcoded state | Expose optional state filter to panels |
| Inject state at the endpoint boundary | Accept state from query params for panel use |
| Name endpoints to reflect topic: `/runs/live/...` | Use generic endpoints for topic-bound panels |

**Rationale:** Topic determines what data a panel sees. Caller-controlled filtering creates data leakage risk.

---

### RULE-CAP-002: Capability Reuse

| DO | DON'T |
|----|-------|
| Share one capability across multiple topic-scoped endpoints | Duplicate capabilities per topic |
| Document which endpoint serves which topic | Leave endpoint-topic mapping implicit |
| Keep semantic contract unified | Fragment capability semantics by topic |

**Rationale:** Capability semantics should remain orthogonal to topic binding.

---

### RULE-CAP-003: Generic Endpoint Disposition

| DO | DON'T |
|----|-------|
| Mark generic endpoints as internal/admin-only | Bind generic endpoints to panels |
| Deprecate generic endpoints if unused | Keep generic endpoints "just in case" |
| Document why generic endpoint exists | Leave generic endpoint purpose ambiguous |

**Rationale:** Generic endpoints with optional filters are admin tools, not panel surfaces.

---

### RULE-CAP-004: Frontend Simplicity

| DO | DON'T |
|----|-------|
| Call topic-scoped endpoint directly | Add conditional logic to select state |
| Trust endpoint to return correct scope | Validate/filter response on frontend |
| Keep panel code stateless regarding scope | Store topic state in frontend for API calls |

**Rationale:** Frontend should be a dumb consumer. Topic logic belongs at API boundary.

---

### RULE-CAP-005: Multi-Topic Capability Declaration

| DO | DON'T |
|----|-------|
| Declare all topics the capability serves | Leave topic coverage undocumented |
| List endpoint-to-topic mapping explicitly | Assume "obvious" mappings |
| Confirm implicit binding in capability YAML | Rely on caller behavior for correctness |

**Example:**
```yaml
capability_id: activity.runs_by_dimension
topics_served:
  - topic: LIVE
    endpoint: /api/v1/activity/runs/live/by-dimension
    state_binding: implicit (LIVE hardcoded)
  - topic: COMPLETED
    endpoint: /api/v1/activity/runs/completed/by-dimension
    state_binding: implicit (COMPLETED hardcoded)
```

---

### RULE-CAP-006: Violation Classification

| Violation Type | Description | Severity |
|----------------|-------------|----------|
| **CONTROL-PLANE** | Caller can override topic scope | CRITICAL |
| **BINDING** | Panel calls generic endpoint instead of topic-scoped | HIGH |
| **NOISE** | Frontend implements conditional state logic | MEDIUM |
| **DOCUMENTATION** | Topic-endpoint mapping not declared | LOW |
| **ATTRIBUTION** | Dimension declared but not backed by schema | CRITICAL |

---

### RULE-CAP-007: Attribution Dimension Integrity

| DO | DON'T |
|----|-------|
| Declare dimensions only if schema projects them | Declare dimensions that don't exist in views |
| Ensure `agent_id`, `actor_type` exist in views before declaring | Assume attribution fields will be backfilled |
| Fail explicitly if dimension is missing | Return empty results masking schema gaps |
| Validate dimension-to-schema mapping at capability registration | Hide missing dimensions with UI suppression |

**Rationale:** Claim ≠ Truth unless enforced by schema. A capability declaring "By Agent" must have `agent_id` in all underlying views.

**Reference:** `docs/contracts/SDSR_ATTRIBUTION_INVARIANT.md` (Clause SDSR-ATTRIBUTION-INVARIANT-001)

**Required Attribution Fields for Dimension Capabilities:**

| Dimension | Required In |
|-----------|-------------|
| `agent_id` | `runs`, `v_runs_o2` |
| `actor_type` | `runs`, `v_runs_o2` |
| `actor_id` | `runs`, `v_runs_o2` |
| `source` | `runs`, `v_runs_o2` |

---

## Audit Checklist

For any capability serving multiple topics:

- [ ] Each topic has a dedicated endpoint
- [ ] State binding is implicit (hardcoded in endpoint)
- [ ] Generic endpoint (if exists) is not panel-bound
- [ ] Capability YAML declares topics_served
- [ ] Frontend code has no topic-conditional logic
- [ ] INTENT_LEDGER panel references topic-scoped endpoint

For any capability declaring dimensions:

- [ ] All declared dimensions exist in base table (`runs`)
- [ ] All declared dimensions are projected in analytical view (`v_runs_o2`)
- [ ] Attribution fields (`agent_id`, `actor_type`, `source`) are present if dimension capability
- [ ] No dimension is "planned but not yet projected"
- [ ] Missing dimension causes explicit error, not empty result

---

## Applies To

| Domain | Example Capability | Topics |
|--------|-------------------|--------|
| ACTIVITY | `activity.runs_by_dimension` | LIVE, COMPLETED |
| ACTIVITY | `activity.summary_by_status` | LIVE, COMPLETED |
| INCIDENTS | `incidents.list` | ACTIVE, RESOLVED, HISTORICAL |
| POLICIES | `policies.list` | ACTIVE, DRAFTS |

---

## Enforcement

| Phase | Enforcement |
|-------|-------------|
| Design | INTENT_LEDGER review |
| Implementation | Code review against rules |
| Runtime | Endpoint audit (no panel calling generic endpoints) |
| SDSR | Scenario validates topic isolation |

---

## References

- `design/l2_1/INTENT_LEDGER.md` - Policy Clause TOPIC-SCOPED-ENDPOINT-001
- `docs/governance/CAPABILITY_LIFECYCLE.yaml` - Capability state machine
- `backend/AURORA_L2_CAPABILITY_REGISTRY/` - Capability definitions
- `docs/contracts/AOS_SDK_ATTRIBUTION_CONTRACT.md` - SDK ingress enforcement
- `docs/contracts/RUN_VALIDATION_RULES.md` - Structural completeness definition
- `docs/contracts/SDSR_ATTRIBUTION_INVARIANT.md` - Clause SDSR-ATTRIBUTION-INVARIANT-001

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-01-18 | Initial creation | Governance |
| 2026-01-18 | Added RULE-CAP-007 (Attribution Dimension Integrity) | Governance |
| 2026-01-18 | Added ATTRIBUTION violation type to RULE-CAP-006 | Governance |
| 2026-01-18 | Added dimension audit checklist | Governance |
