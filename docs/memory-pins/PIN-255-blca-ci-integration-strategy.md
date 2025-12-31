# PIN-255: BLCA CI Integration Strategy

**Status:** PENDING (awaiting confirmation)
**Created:** 2025-12-31
**Category:** Infrastructure / CI / Governance
**Reference:** PIN-254, SESSION_PLAYBOOK.yaml v2.19 Section 29
**Predecessor:** PIN-254 (Layered Semantic Completion — COMPLETE)

---

## Summary

Strategy for integrating BLCA checks into CI pipeline. Defines what can be automated (blocking/warning) vs what must stay human-only.

**Core Principle:** Automate structural verification, keep semantic judgment human.

---

## Three-Tier CI Model

### Tier 1: CI-Enforced (Blocking PR Merge)

Mechanically verifiable with high confidence. PR cannot merge if any fail.

| Check | What CI Verifies | False Positive Risk | Implementation |
|-------|------------------|---------------------|----------------|
| **Endpoint Registration** | Every L2 route has BLCA registry entry | LOW | Script scans routes, compares to registry |
| **Import Boundary** | L3 doesn't import L4 internals, L5 doesn't import L2 | LOW | AST-based import checker |
| **L8 Containment** | Test files don't import `app.services.*` directly | LOW | Import pattern matcher |
| **F1 Entry Points** | Frontend API calls match registered L2 endpoints | LOW | TypeScript/static analysis |
| **Artifact Existence** | Required PINs/change records exist for PR | LOW | File existence check |

**Failure mode prevented:** Obvious structural drift merged without notice.

---

### Tier 2: CI-Warned (Non-Blocking, Logged)

Flags potential issues but requires human judgment. Merge requires explicit ACK.

| Check | What CI Flags | Why Non-Blocking | Implementation |
|-------|---------------|------------------|----------------|
| **New Transaction Detection** | PR introduces new mutation patterns | Could be legitimate | Pattern matching on POST/PUT/DELETE |
| **L3 Size Creep** | Adapter file exceeds 200 LOC | Could be justified | Line count check |
| **Unregistered Signal** | New event/signal without consumer mapping | May be in-progress | Signal pattern scan |
| **Domain Engine Touch** | PR modifies L4 engine | Requires semantic review | File path matching |

**Failure mode prevented:** Silent creep goes unnoticed, but humans decide.

---

### Tier 3: Human-Only (Never Automated)

Requires semantic judgment. Cannot be reliably automated.

| Check | Why Not Automatable | Human Trigger |
|-------|---------------------|---------------|
| **A2: API Truthfulness** | "Does this API do what it claims?" is semantic | Session start, PR review |
| **A3: Layer Semantic Purity** | "Does this logic belong here?" is judgment | Session start, architecture changes |
| **A5: Governance Escalation** | "Was this escalated correctly?" is contextual | Weekly ACK, incident review |
| **F2: Client-Side Authority** | "Is this a policy decision?" requires domain knowledge | Frontend PRs, session start |
| **F3: Silent Side Effects** | "Does this auto-fire?" requires understanding intent | Frontend PRs, session start |

**Failure mode prevented:** False confidence from green CI on semantic issues.

---

## BLCA Axis Analysis

| Axis | Mechanically Verifiable | Requires Semantic Judgment | CI Potential |
|------|------------------------|---------------------------|--------------|
| **A1: Bottom-Up** | Import graph, call patterns | Whether delegation is semantically correct | MEDIUM |
| **A2: Top-Down** | Endpoint registration exists | Whether API does what it claims | HIGH (registration) / LOW (truth) |
| **A3: Layer Purity** | Import boundaries, file locations | Whether logic belongs in layer | HIGH (structure) / LOW (semantic) |
| **A4: L8 Containment** | Test imports, CI file patterns | Whether test logic affects prod semantics | MEDIUM |
| **A5: Governance** | Artifact existence | Whether escalation was appropriate | LOW |
| **A6: Frontend** | F1 (API calls exist) | F2 (authority), F3 (side effects) | MEDIUM (F1) / LOW (F2/F3) |

---

## CI Workflow Design

```
┌─────────────────────────────────────────────────────────────────┐
│                     PR Opened / Updated                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  TIER 1: Structural Checks (BLOCKING)                           │
│                                                                  │
│  □ Endpoint registration verified                                │
│  □ Import boundaries clean                                       │
│  □ L8 containment verified                                       │
│  □ F1 entry points mapped                                        │
│  □ Required artifacts exist                                      │
│                                                                  │
│  ANY FAIL → PR blocked, cannot merge                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  TIER 2: Semantic Flags (WARNING)                                │
│                                                                  │
│  □ New transaction patterns? → flag for review                   │
│  □ L3 size creep? → flag for review                              │
│  □ Unregistered signals? → flag for review                       │
│  □ L4 engine touched? → flag for review                          │
│                                                                  │
│  FLAGS → logged, human must acknowledge before merge             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  TIER 3: Human Review (REQUIRED FOR FLAGGED)                     │
│                                                                  │
│  If Tier 2 flags present:                                        │
│    □ Reviewer must explicitly ACK each flag                      │
│    □ ACK recorded in PR comments                                 │
│                                                                  │
│  If no flags:                                                    │
│    □ Standard PR review process                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  MERGE                                                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Critical Design Decisions

### Why Tier 2 is Non-Blocking

If Tier 2 were blocking, teams would:
- Game the checks to avoid flags
- Treat all flags as false positives
- Lose trust in the system

Non-blocking with required ACK means:
- Flags are informational, not adversarial
- Human judgment is preserved
- Audit trail exists

### Why F2/F3 Stay Human

Automating authority detection would require:
- Understanding business rules
- Knowing what "eligible" means in context
- Distinguishing display logic from decision logic

This is beyond static analysis. Attempting it creates false confidence.

### The ACK Requirement for Flags

When Tier 2 produces flags, merge requires:
```
BLCA-CI-ACK: [reviewer]
- Flag: L4 engine modified (cost_model_engine.py)
  ACK: Reviewed. Change is additive function, no semantic modification.
- Flag: New transaction pattern detected (POST /ops/audit/export)
  ACK: Reviewed. Registered in BLCA. Scoped Phase C not required (read-export, not mutation).
```

---

## Implementation Priority

| Priority | Check | Effort | Risk Reduced |
|----------|-------|--------|--------------|
| **P0** | Endpoint registration | LOW | HIGH (shadow APIs) |
| **P0** | Import boundary | MEDIUM | HIGH (layer violations) |
| **P1** | L8 containment | LOW | MEDIUM (test pollution) |
| **P1** | F1 entry points | MEDIUM | MEDIUM (orphan calls) |
| **P2** | L4 engine touch flag | LOW | MEDIUM (semantic drift) |
| **P2** | New transaction flag | MEDIUM | MEDIUM (creep) |
| **P3** | L3 size creep | LOW | LOW (adapter bloat) |

---

## Pending Decisions (Awaiting Confirmation)

Before implementation can proceed:

1. **Confirm Tier 1 blocking list** — are these the right checks to block merge?
2. **Confirm Tier 2 flag list** — are these the right checks to warn (not block)?
3. **Confirm ACK format** — is the proposed PR comment format acceptable?
4. **Confirm priority order** — P0 first, then P1, etc.?

---

## Next Steps (When Resumed)

1. Receive confirmation on pending decisions
2. Draft CI workflow YAML (`.github/workflows/blca-ci.yml`)
3. Implement BLCA-CI validation scripts
4. Test on sample PRs
5. Document in SESSION_PLAYBOOK.yaml

---

## Related PINs

- PIN-254: Layered Semantic Completion (COMPLETE)
- PIN-245: Integration Integrity System
- PIN-248: Codebase Inventory & Layer System

---

**Contract Authority:** SESSION_PLAYBOOK.yaml v2.19 Section 29
**Baseline Reference:** Truthful Architecture v1 (2025-12-31)
