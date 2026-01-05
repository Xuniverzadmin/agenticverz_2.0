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

## Next Steps (BLOCKED UNTIL ASKED)

1. **CI Enforcement** — Implement capability-linkage workflow
2. **UI Expansion Guard** — Implement PR check for ui_expansion_allowed
3. **Auto-Registration** — Generate entries from code scan
4. **Gap Heatmap** — Visualize capability gaps

---

## Related PINs

- [PIN-303](PIN-303-frontend-constitution-alignment-system-survey.md) — Frontend survey
- [PIN-304](PIN-304-m12-multi-agent-survey-gap-correction.md) — M12 gap
- [PIN-305](PIN-305-system-complete-survey.md) — System survey
