# Capability Review Gate Template

**Status:** RATIFIED
**Effective:** 2026-01-18
**Purpose:** Mandatory PR checklist for dimension capabilities
**Reference:** SDSR_ATTRIBUTION_INVARIANT.md, CAPABILITY_SURFACE_RULES.md

---

## Purpose

This template defines the **mandatory checklist** for any PR that adds or modifies a capability declaring dimensions. No checkbox → no merge.

---

## Capability PR Gate — REQUIRED

### A. Capability Declaration

- [ ] Capability ID defined and unique
- [ ] All declared dimensions listed explicitly
- [ ] Topic scope stated (LIVE / COMPLETED / SIGNALS / etc.)
- [ ] Panel binding documented
- [ ] Endpoint(s) specified

**Example:**
```yaml
capability_id: activity.runs_by_dimension
dimensions:
  - agent_id
  - provider_type
  - risk_level
topics_served:
  - LIVE
  - COMPLETED
```

---

### B. Schema Proof (Non-Negotiable)

For **each declared dimension**, verify:

| Dimension | Base Table Column | View Column | Verified |
|-----------|-------------------|-------------|----------|
| `{dim1}` | `runs.{dim1}` | `v_runs_o2.{dim1}` | [ ] |
| `{dim2}` | `runs.{dim2}` | `v_runs_o2.{dim2}` | [ ] |

**Checklist:**

- [ ] Column exists in base table (`runs`)
- [ ] Column projected in **all** analytical views used by capability
- [ ] Column is non-derived (or derivation documented and stable)
- [ ] Column type matches expected query patterns

> **BLOCKING:** If any box fails → PR BLOCKED
>
> Error: `SDSR-ATTRIBUTION-INVARIANT-001 VIOLATION: Dimension {dim} not backed by schema`

---

### C. Attribution Compliance (If Applicable)

If dimension ∈ { `agent_id`, `actor_id`, `actor_type`, `origin_system_id` }:

- [ ] SDK enforces field presence (reference: AOS_SDK_ATTRIBUTION_CONTRACT)
- [ ] Validation rules R1-R8 apply (reference: RUN_VALIDATION_RULES)
- [ ] Null semantics documented
- [ ] Legacy handling specified

**Attribution Field Requirements:**

| Field | SDK Requirement | Schema Requirement |
|-------|-----------------|-------------------|
| `agent_id` | REQUIRED | NOT NULL |
| `actor_type` | REQUIRED | NOT NULL |
| `actor_id` | Conditional (HUMAN only) | NULLABLE |
| `origin_system_id` | REQUIRED | NOT NULL |

---

### D. Endpoint Binding

- [ ] Endpoint is topic-scoped (per TOPIC-SCOPED-ENDPOINT-001)
- [ ] No caller-controlled state filters exposed to panels
- [ ] No generic endpoints used by panels
- [ ] State binding is implicit (hardcoded in endpoint)

**Endpoint Pattern:**
```
/api/v1/{domain}/{resource}/{topic}/by-{dimension}
```

**Examples:**
- `/api/v1/activity/runs/live/by-dimension` → state=LIVE hardcoded
- `/api/v1/activity/runs/completed/by-dimension` → state=COMPLETED hardcoded

---

### E. Legacy Handling

- [ ] Legacy marker value defined (e.g., `legacy-unknown`)
- [ ] UI behavior specified for legacy values
- [ ] Analytics disclaimer text approved
- [ ] Legacy bucket visible (not hidden or merged)

**Legacy Display Rules:**

| Value | Display | Tooltip |
|-------|---------|---------|
| Known value | Normal label | None |
| `legacy-unknown` | "Legacy (pre-attribution)" | "Runs created before attribution enforcement" |

---

### F. SDSR Scenario

- [ ] SDSR scenario exists for capability validation
- [ ] Scenario tests all declared dimensions
- [ ] Scenario verifies topic isolation
- [ ] Observation JSON emitted on success

**Scenario Reference:**
```
backend/scripts/sdsr/scenarios/SDSR-{PANEL_ID}-001.yaml
```

---

### G. Documentation

- [ ] INTENT_LEDGER updated with capability definition
- [ ] CAPABILITY_REGISTRY updated (if applicable)
- [ ] Endpoint documented in OpenAPI spec
- [ ] Panel notes reference correct endpoint

---

## Final Gate

### Reviewer Attestation (REQUIRED)

```
CAPABILITY REVIEW ATTESTATION

Reviewer: _______________
Date: _______________

I attest that:
- [ ] All declared dimensions exist in schema
- [ ] All views project required columns
- [ ] Attribution fields comply with contracts
- [ ] Endpoint binding is topic-scoped
- [ ] Legacy handling is explicit
- [ ] SDSR scenario validates capability

Signature: "Capability claim is schema-true"
```

> **No attestation → No merge**

---

## Violation Response

If this checklist is incomplete at PR review:

```
CAPABILITY_REVIEW_GATE_VIOLATION

Missing: {section}
Capability: {capability_id}
Dimension: {dimension_name}

Status: PR BLOCKED
Action: Complete checklist before re-review

Reference: docs/governance/CAPABILITY_REVIEW_GATE_TEMPLATE.md
```

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `SDSR_ATTRIBUTION_INVARIANT.md` | Control-plane law |
| `CAPABILITY_SURFACE_RULES.md` | Topic-scoped rules |
| `AOS_SDK_ATTRIBUTION_CONTRACT.md` | SDK enforcement |
| `RUN_VALIDATION_RULES.md` | Structural invariants |
| `ATTRIBUTION_FAILURE_MODE_MATRIX.md` | Blast radius |

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-01-18 | Initial creation | Governance |
