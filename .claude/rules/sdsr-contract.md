---
paths:
  - "backend/scripts/sdsr/**"
  - "backend/aurora_l2/**"
---

# SDSR System Contract Rules

**Status:** LOCKED
**Reference:** docs/governance/SDSR_SYSTEM_CONTRACT.md, PIN-370, PIN-379

## Core Principle

> Scenarios inject causes. Engines create effects. UI reveals truth.

## Claude MUST:
- Reference the SDSR pipeline, never re-derive it
- Treat inject_synthetic.py contract as immutable
- Never create new tables or APIs without explicit user approval
- Fix canonical structures, not fork them

## Claude MUST NOT:
- Simulate system behavior in scripts
- Create shortcut UI-only flows
- Invent transitional or "temporary" paths
- Write to engine-owned tables from any script
- Bypass L2.1 → projection → UI pipeline

## Engine-Owned Tables (FORBIDDEN to write from scripts)
- aos_traces, aos_trace_steps → TraceStore
- incidents → IncidentEngine
- policy_proposals → PolicyProposalEngine
- prevention_records, policy_rules → PolicyEngine

## Capability Status Gate (CAP-E2E-001)

Capabilities MUST remain DECLARED until E2E validation passes.

```
DECLARED → OBSERVED → TRUSTED → DEPRECATED
```

Transition DECLARED → OBSERVED requires:
1. SDSR scenario exists and was executed
2. All assertions passed
3. Observation JSON emitted
4. AURORA_L2_apply_sdsr_observations.py applied

## E2E Testing Protocol (BL-SDSR-E2E-001)

### Hard Guardrails (GR-1 through GR-6)

| Guardrail | Rule |
|-----------|------|
| GR-1 | No Direct DB Mutation Outside Alembic |
| GR-2 | No Trigger/Constraint Changes Without Approval |
| GR-3 | Canonical Tables Only (no *sdsr* copies) |
| GR-4 | No Silent Compatibility Fallbacks |
| GR-5 | No "Fix While Investigating" |
| GR-6 | UI Never Drives State |

### Execution Discipline (GR-5)
1. Diagnose → 2. Summarize root cause → 3. Propose fix → 4. Wait for approval → 5. Implement → 6. Verify

## Cross-Domain Propagation Rules

| Rule ID | Name |
|---------|------|
| SDSR-PROP-001 | Scenarios Inject Causes Not Consequences |
| SDSR-PROP-002 | One Scenario One Domain |
| SDSR-PROP-003 | Expectations Not Cross-Domain Writes |
| SDSR-PROP-004 | Backend Owns Propagation |

Scenarios must NEVER simulate cross-domain behavior. Cross-domain reflection emerges ONLY from backend capabilities.
