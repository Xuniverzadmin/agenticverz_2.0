# PIN-306: Capability Registry Governance

**Status:** ACTIVE
**Created:** 2026-01-05
**Category:** Governance / System Truth
**Scope:** ALL capabilities, ALL planes

---

## Summary

Established the Capability Registry as the single source of truth for system capabilities. Replaces H1/H2/H3 free-text classification with registry-derived gaps. Enables drift-proof surveys and mechanical enforcement.

---

## Problem Statement

Prior surveys (PIN-303, PIN-304, PIN-305) used free-text classification:
- **H1:** "Partially Implemented"
- **H2:** "Suspected but Unverified"
- **H3:** "Messy / Transitional"

This caused:
1. Gaps being missed (M12 in PIN-303)
2. No mechanical enforcement
3. Survey drift over time
4. No linkage between code and capability status

---

## Solution: Capability Registry

### Registry Location

```
/docs/capabilities/CAPABILITY_REGISTRY.yaml
```

### Registry Structure

```yaml
capabilities:
  <capability_name>:
    capability_id: CAP-XXX
    name: "Human readable name"

    planes:
      engine: true/false       # L4 domain logic
      l2_api: true/false       # L2 API endpoints
      client: true/false       # Frontend API client
      ui: true/false           # Frontend UI pages
      authority: true/false    # Governance/permission wiring
      audit_replay: true/false # Audit trail and replay

    lifecycle:
      state: PLANNED|PARTIAL|READ_ONLY|CLOSED|FROZEN|QUARANTINED
      closure_requirements:
        engine_complete: true/false
        api_complete: true/false
        ...

    governance:
      ui_expansion_allowed: true/false
      promotion_blocked_by: [...]
      founder_approval_required: true/false

    evidence:
      engine: [paths]
      l2_api: [paths]
      ...

    gaps:
      - type: <gap_type>
        detail: "description"
```

---

## Allowed Enums (LOCKED)

### Lifecycle States

| State | Meaning |
|-------|---------|
| PLANNED | Intent declared, no code |
| PARTIAL | Code exists, not all planes complete |
| READ_ONLY | Can read/query, cannot mutate |
| CLOSED | All planes complete, all requirements met |
| FROZEN | Closed + no changes without founder approval |
| QUARANTINED | Disabled, pending decision |

### Capability Planes

| Plane | Meaning |
|-------|---------|
| engine | L4 domain logic exists |
| l2_api | L2 API endpoints exist |
| client | Frontend API client exists |
| ui | Frontend UI pages exist |
| authority | Governance/permission wiring exists |
| audit_replay | Audit trail and replay support exists |

### Gap Types

| Type | Meaning |
|------|---------|
| UNREGISTERED_CODE | Code exists without registry entry |
| PLANE_ASYMMETRY | Some planes true, others false |
| LIFECYCLE_INCOMPLETE | Closure requirements not met |
| MISSING_AUTHORITY | UI/API exists without governance |
| MISSING_AUDIT | Mutations without audit trail |
| STUBBED_INFRA | Infrastructure code not wired |
| INTENTIONALLY_ABSENT | Explicitly not implemented |

---

## Registered Capabilities (17)

### By State

| State | Count | Capabilities |
|-------|-------|--------------|
| PLANNED | 1 | cross_project |
| PARTIAL | 5 | replay, cost_simulation, prediction_plane, founder_console, authentication |
| READ_ONLY | 1 | policy_proposals |
| CLOSED | 10 | authorization, multi_agent, policy_engine, care_routing, governance_orchestration, workflow_engine, learning_pipeline, memory_system, optimization_engine, skill_system |

### Blocking Gaps

| Capability | Gap Type | Detail |
|------------|----------|--------|
| authentication | STUBBED_INFRA | Clerk not wired to main.py |
| replay | MISSING_AUTHORITY | No RBAC on replay |
| prediction_plane | MISSING_AUTHORITY | No governance gate |
| cost_simulation | PLANE_ASYMMETRY | Client exists, no UI |
| policy_proposals | LIFECYCLE_INCOMPLETE | Read-only, no creation |
| founder_console | LIFECYCLE_INCOMPLETE | Routing unverified |

### UI Expansion Status

**BLOCKED (10):**
- replay, authentication, prediction_plane, cross_project
- care_routing, authorization, workflow_engine, learning_pipeline, optimization_engine, skill_system

**ALLOWED (6):**
- cost_simulation, policy_proposals, founder_console
- memory_system, policy_engine, governance_orchestration

---

## Enforcement Rules

### Rule E1: Code → Registry Linkage

```
Any PR touching:
  - /backend/**
  - /frontend/**
Must reference:
  capability_id: <id>

CI fails if capability_id not in registry.
```

### Rule E2: UI Expansion Guard

```
If governance.ui_expansion_allowed = false:
  UI PR touching that capability → FAIL
```

### Rule E3: Promotion Gate

```
Lifecycle promotion to CLOSED/FROZEN requires:
  - All closure_requirements = true
  - Founder approval recorded
  - Registry version bumped
```

---

## Claude Invariants

Claude MUST:
- Treat Capability Registry as single source of truth
- Never infer capability existence from UI or APIs alone
- Never use H1/H2/H3 free-text classification
- Fail fast when code exists without registry linkage

Claude MUST NOT:
- Assume UI == capability
- Assume API == capability
- Invent lifecycle states
- Proceed without evidence links

---

## Migration from H1/H2/H3

| Old Classification | New Mapping |
|--------------------|-------------|
| H1 Partially Implemented | state: PARTIAL + specific gaps |
| H2 Suspected Unverified | state: PARTIAL + UNREGISTERED_CODE gap |
| H3 Messy/Transitional | state: QUARANTINED or PARTIAL + gaps |

---

## Capability Truth Report (Derived)

| Capability | State | Missing Planes | Blocking Gaps |
|------------|-------|----------------|---------------|
| replay | PARTIAL | client, authority | MISSING_AUTHORITY |
| cost_simulation | PARTIAL | ui | PLANE_ASYMMETRY |
| prediction_plane | PARTIAL | client, ui, authority | MISSING_AUTHORITY |
| policy_proposals | READ_ONLY | client, ui, audit | LIFECYCLE_INCOMPLETE |
| authentication | PARTIAL | client, ui | STUBBED_INFRA |
| founder_console | PARTIAL | - | LIFECYCLE_INCOMPLETE |
| authorization | CLOSED | - | - |
| multi_agent | CLOSED | - | - |
| policy_engine | CLOSED | - | - |
| care_routing | CLOSED | - | - |
| governance_orchestration | CLOSED | - | - |
| workflow_engine | CLOSED | - | - |
| learning_pipeline | CLOSED | - | - |
| memory_system | CLOSED | - | - |
| optimization_engine | CLOSED | - | - |
| skill_system | CLOSED | - | - |
| cross_project | PLANNED | all | INTENTIONALLY_ABSENT |

---

## Files

- `/docs/capabilities/CAPABILITY_REGISTRY.yaml` — Registry (source of truth)
- This PIN — Governance rules

## References

- PIN-303 — Frontend Constitution Survey (superseded by registry)
- PIN-304 — M12 Gap Correction (incorporated into registry)
- PIN-305 — System-Complete Survey (registry-aligned)

---

## Implementation (COMPLETE)

All enforcement mechanisms have been implemented:

### Enforcement Script

**Path:** `scripts/ops/capability_registry_enforcer.py`

**Commands:**

```bash
# Validate registry structure
python scripts/ops/capability_registry_enforcer.py validate-registry

# Check PR files for capability linkage (CI)
python scripts/ops/capability_registry_enforcer.py check-pr --files file1.py file2.py

# Check UI expansion rules (CI)
python scripts/ops/capability_registry_enforcer.py ui-guard --files page.tsx

# Scan for unregistered capabilities
python scripts/ops/capability_registry_enforcer.py scan-unregistered --generate-drafts

# Generate gap heatmap
python scripts/ops/capability_registry_enforcer.py heatmap --format md --output docs/capabilities/GAP_HEATMAP.md
```

### GitHub Actions Workflow

**Path:** `.github/workflows/capability-registry.yml`

**Jobs:**

| Job | Trigger | Purpose |
|-----|---------|---------|
| capability-linkage | PR | Verify capability_id in code or PR body |
| ui-expansion-guard | PR | Block UI changes for blocked capabilities |
| validate-registry | PR | Validate registry YAML structure |
| update-heatmap | Push to main | Auto-generate GAP_HEATMAP.md |
| full-scan | Manual | Detect unregistered capabilities |

### Gap Heatmap

**Path:** `docs/capabilities/GAP_HEATMAP.md`

Auto-generated on every push to main. Shows:
- Capability state distribution
- Missing planes matrix
- Gap types per capability
- UI expansion status (blocked/allowed)

### Capability Annotation Standard

Every code file touching a capability must include:

**Option A (file comment):**
```python
# capability_id: CAP-XXX
```

**Option B (PR description):**
```
capability_id: CAP-XXX
```

### UI Non-Expansion Exception

For bug fixes or CSS-only changes to blocked capabilities:
- Add PR label: `ui-non-expansion`
- CI will pass with warning instead of failure

---

## Files

- `/docs/capabilities/CAPABILITY_REGISTRY.yaml` — Registry (source of truth)
- `/docs/capabilities/GAP_HEATMAP.md` — Auto-generated gap visualization
- `/.github/workflows/capability-registry.yml` — CI enforcement
- `/scripts/ops/capability_registry_enforcer.py` — Enforcement script
- This PIN — Governance rules

## References

- PIN-303 — Frontend Constitution Survey (superseded by registry)
- PIN-304 — M12 Gap Correction (incorporated into registry)
- PIN-305 — System-Complete Survey (registry-aligned)

---

## Updates

### 2026-01-05: PIN-311 Gap Resolution

**Reference:** PIN-311 (System Resurvey Registry-Aligned)

PIN-311 identified 15 unmapped L2 API files. This session resolved all of them:

**File Classifications:**

| File | Assigned To | Reason |
|------|-------------|--------|
| customer_activity.py | CAP-001 (replay) | Run activity tracking |
| guard_logs.py | CAP-001 (replay) | Guard execution logs |
| status_history.py | CAP-001 (replay) | Status change history |
| replay.py | CAP-001 (replay) | Replay UX API |
| traces.py | CAP-001 (replay) | Trace storage/indexing |
| cost_guard.py | CAP-002 (cost_simulation) | Cost guard enforcement |
| cost_intelligence.py | CAP-002 (cost_simulation) | Cost analytics |
| scenarios.py | CAP-002 (cost_simulation) | H2 cost scenarios |
| v1_proxy.py | CAP-002 (cost_simulation) | M22 KillSwitch proxy |
| cost_ops.py | CAP-005 (founder_console) | Founder cost visibility |
| founder_explorer.py | CAP-005 (founder_console) | H3 Explorer mode |
| platform.py | CAP-005 (founder_console) | Platform health |
| onboarding.py | CAP-006 (authentication) | Tenant onboarding |
| auth_helpers.py | CAP-006 (authentication) | Console auth helpers |
| authz_status.py | CAP-007 (authorization) | Auth status endpoint |
| rbac_api.py | CAP-007 (authorization) | RBAC management |
| discovery.py | CAP-011 (governance) | Discovery signals |
| feedback.py | CAP-013 (learning) | PB-S3 Pattern Feedback |
| embedding.py | CAP-014 (memory) | Embedding quota/config |
| integration.py | CAP-018 (PENDING) | M25 Integration API |
| recovery.py | CAP-018 (PENDING) | M10 Recovery API |
| recovery_ingest.py | CAP-018 (PENDING) | Recovery ingest |
| customer_visibility.py | LEGACY | Superseded API |
| legacy_routes.py | LEGACY | 410 Gone handlers |
| health.py | PLATFORM | System health |
| tenants.py | PLATFORM | Tenant management |

**State Promotions:**

| Capability | Old State | New State | Reason |
|------------|-----------|-----------|--------|
| CAP-001 (replay) | PARTIAL | CLOSED | replay.ts client exists |
| CAP-005 (founder_console) | PARTIAL | CLOSED | Routes wired in main.py |

**Gap Summary:**

| Category | Count |
|----------|-------|
| Unmapped API files | 0 (was 15) |
| CLOSED capabilities | 13 (was 11) |
| PARTIAL capabilities | 1 (was 3) |
| Stale gaps removed | 2 |

**Pending:**

- CAP-018 (M25 Integration) requires founder approval before registration

---

## Related PINs

- [PIN-303](PIN-303-frontend-constitution-alignment-system-survey.md) — Frontend survey
- [PIN-304](PIN-304-m12-multi-agent-survey-gap-correction.md) — M12 gap
- [PIN-305](PIN-305-system-complete-survey.md) — System survey
- [PIN-311](PIN-311-system-resurvey-registry-aligned.md) — Registry-aligned resurvey

---

## Updates

### 2026-01-05: CAP-018 Approval

**Reference:** PIN-311 Gap Resolution

**Decision:** CAP-018 (M25 Integration Platform) approved as first-class capability.

| Field | Value |
|-------|-------|
| Capability ID | CAP-018 |
| Name | M25 Integration Platform |
| State | CLOSED |
| Approval Date | 2026-01-05 |
| Founder Approval | ✅ Granted |

**Evidence Files:**
- Engine: `/backend/app/integrations/` (dispatcher, graduation_engine, learning_proof, bridges)
- L2 API: `/backend/app/api/integration.py`, `/backend/app/api/recovery.py`, `/backend/app/api/recovery_ingest.py`

**Registry Changes:**
- Total capabilities: 17 → 18
- CLOSED capabilities: 13 → 14
- No structural changes pending

**Blocking Gaps Remaining (4):**
- CAP-002 (cost_simulation): PARTIAL
- CAP-003 (policy_proposals): READ_ONLY
- CAP-004 (prediction_plane): READ_ONLY
- CAP-017 (cross_project): PLANNED

---

### 2026-01-05: PIN-313 Governance Hardening

**Reference:** PIN-313 (Governance Hardening & Gap Closure)

**Changes:**

1. **Session Playbook v2.33** — Added Section 35: Capability Registry Governance
   - Capability Surveyor added to bootstrap sequence (step 3)
   - Registry validation required at session start
   - Unregistered Code Response Matrix (BLOCKING enforcement)
   - Promotion Gate Rules (no asymmetry, no missing authority)

2. **Gap Closure:**
   - cost_simulation: PARTIAL → CLOSED (ProvenanceLog provides audit)
   - policy_proposals: READ_ONLY confirmed (origination semantics exist)
   - prediction_plane: READ_ONLY confirmed (visibility-only RBAC)
   - cross_project: Governance assertion added (P0 violation invariant)

**Registry State:**
- Total capabilities: 18
- CLOSED: 15 (was 14)
- PARTIAL: 0 (was 1)
- READ_ONLY: 2
- PLANNED: 1
- Blocking gaps: 0 (was 4)

**Enforcement:**
- Capability Surveyor enforced at bootstrap + session
- Promotion Gate prevents lifecycle advancement without closure requirements
