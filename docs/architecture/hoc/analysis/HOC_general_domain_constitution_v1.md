# General Domain Constitution v1

**Domain:** `app/houseofcards/customer/general/`
**Status:** RATIFIED
**Effective:** 2026-01-22
**Authority:** Architectural Governance

---

## Preamble

General is not a domain. **General is a constitution.**

It exists to hold code that must never be wrong, must never be bypassed, and must never be owned by a single product concern. This document defines what may enter General, what must leave, and how to prevent it from becoming a god-domain.

---

## Article I: Purpose and Scope

### Section 1.1 — What General Exists For

General exists **ONLY** for:

| Category | Description |
|----------|-------------|
| **Cross-domain invariants** | Rules that span multiple domains and cannot be owned by one |
| **Irreversible decisions** | Actions that cannot be undone once committed |
| **Lifecycle state machines** | Entity lifecycles that affect system-wide behavior |
| **Projections of audited truth** | Read-only views derived from authoritative sources |

### Section 1.2 — What General Does NOT Exist For

General is **FORBIDDEN** from holding:

| Anti-Pattern | Why Forbidden |
|--------------|---------------|
| Product-specific features | Creates audience confusion |
| Convenience utilities | Attracts more utilities |
| "Important but homeless" code | Turns General into a dumping ground |
| Experimental features | Contaminates governance code |
| Temporary hacks (beyond 1 phase) | Temporary becomes permanent |

### Section 1.3 — The Prime Directive

> **If a feature can live elsewhere safely, it MUST.**

Code enters General only when placement elsewhere would:
- Fragment enforcement
- Create split-brain state management
- Violate cross-domain integrity
- Risk silent governance failures

---

## Article II: Sub-Constitutions

General is divided into three **sub-constitutions**. Every file in General must belong to exactly one.

### Section 2.1 — Control Plane

**Question Answered:** "Is this allowed to happen?"

**Owns:**
- `runtime/engines/governance_orchestrator.py`
- `runtime/engines/transaction_coordinator.py`
- `runtime/engines/phase_status_invariants.py`
- `workflow/contracts/engines/contract_service.py`
- `cross-domain/engines/cross_domain.py`

**Characteristics:**
- Makes decisions, never executes
- Enforces invariants mechanically
- Throws on governance failure (never silent)
- Audit trail is mandatory

**Entry Criteria:**
- Code decides whether operations proceed
- Code enforces cross-domain rules
- Code manages irreversible state transitions

---

### Section 2.2 — Lifecycle Plane

**Question Answered:** "Where is this entity in its life?"

**Owns:**
- `lifecycle/engines/base.py`
- `lifecycle/engines/onboarding.py`
- `lifecycle/engines/offboarding.py`
- `lifecycle/engines/pool_manager.py`
- `lifecycle/engines/knowledge_plane.py`
- `lifecycle/engines/execution.py`
- `facades/lifecycle_facade.py`

**Characteristics:**
- Manages entity state through defined stages
- Stage handlers are dumb plugins (no decisions)
- Orchestrator owns state, handlers own actions
- Destructive actions require explicit approval

**Entry Criteria:**
- Code manages entity lifecycle state
- Code implements stage handler protocol
- Code coordinates lifecycle transitions

---

### Section 2.3 — Projection Plane

**Question Answered:** "What is true right now?"

**Owns:**
- `ui/engines/rollout_projection.py`
- Future: Overview-like projections for General

**Characteristics:**
- Read-only (never mutates)
- Derived from authoritative sources
- No execution authority
- No approval authority

**Entry Criteria:**
- Code projects truth without modifying it
- Code computes views from existing data
- Code serves UI or API consumers with facts

---

### Section 2.4 — Unclassified (Requires Resolution)

Files that do not fit cleanly into a sub-constitution:

| File | Current State | Resolution Path |
|------|---------------|-----------------|
| `facades/monitors_facade.py` | Customer facade | Candidate for extraction to dedicated Monitors domain |
| `facades/alerts_facade.py` | Customer facade | Candidate for extraction to dedicated Alerts domain |
| `facades/scheduler_facade.py` | Customer facade | Candidate for extraction to dedicated Scheduler domain |
| `facades/compliance_facade.py` | Customer facade | Candidate for extraction to dedicated Compliance domain |
| `controls/engines/guard_write_service.py` | TEMPORARY | Must split or extract by Phase 3 |
| `engines/knowledge_sdk.py` | L2 MISPLACED | Must move to L2 location or reclassify |

---

## Article III: Frozen Invariants

These invariants are **constitutional** and cannot be relaxed, abstracted, or bypassed.

### Section 3.1 — Governance Invariants

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| **GOV-001** | MAY_NOT verdicts are mechanically un-overridable | `MayNotVerdictError` in ContractService |
| **GOV-002** | Governance must throw on failure (no silent failures) | `GovernanceError` in cross_domain.py |
| **GOV-003** | Terminal states are immutable | `ContractImmutableError` in state machine |
| **GOV-004** | Cross-domain functions have no optional dependencies | Doctrine in cross_domain.py |

### Section 3.2 — Separation Invariants

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| **SEP-001** | Orchestrators decide, never execute | Code review + architecture |
| **SEP-002** | Executors execute, never decide | Code review + architecture |
| **SEP-003** | Projections read, never mutate | Code review + architecture |
| **SEP-004** | Cross-domain governance enforces, never learns | Doctrine in cross_domain.py |

### Section 3.3 — Lifecycle Invariants

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| **LCY-001** | Stage handlers are dumb plugins | Protocol in base.py |
| **LCY-002** | Stage handlers do NOT manage state | Protocol in base.py |
| **LCY-003** | Stage handlers do NOT emit events | Protocol in base.py |
| **LCY-004** | Stage handlers do NOT check policies | Protocol in base.py |
| **LCY-005** | Destructive actions require explicit approval | `purge_approved` check |

### Section 3.4 — Projection Invariants

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| **PRJ-001** | Projection is read-only | RolloutProjectionService design |
| **PRJ-002** | Stage advancement requires audit PASS | `can_advance_stage()` |
| **PRJ-003** | Stage advancement requires stabilization | `StabilizationWindow` |
| **PRJ-004** | No health degradation during rollout | `can_advance_stage()` |
| **PRJ-005** | Stages are monotonic | `STAGE_ORDER` enforcement |
| **PRJ-006** | Customer sees only current stage facts | `CustomerRolloutView` |

### Section 3.5 — Contract Invariants

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| **CON-001** | Status transitions must follow state machine | `VALID_TRANSITIONS` |
| **CON-002** | APPROVED requires approved_by | `validate_transition()` |
| **CON-003** | ACTIVE requires job exists | `validate_transition()` |
| **CON-004** | COMPLETED requires audit_verdict = PASS | `validate_transition()` |
| **CON-005** | Terminal states are immutable | `TERMINAL_STATES` check |
| **CON-006** | proposed_changes must validate schema | Input validation |
| **CON-007** | confidence_score range [0,1] | Input validation |

---

## Article IV: Entry and Exit Rules

### Section 4.1 — Entry Criteria (Must ALL Be True)

Before adding code to General, answer these questions:

| # | Question | Required Answer |
|---|----------|-----------------|
| 1 | Can this code live in a product domain? | **NO** |
| 2 | Does this code enforce cross-domain rules? | **YES** |
| 3 | Would placing this elsewhere fragment enforcement? | **YES** |
| 4 | Which sub-constitution does this belong to? | **Must have answer** |
| 5 | Does this code maintain decision/execution separation? | **YES** |

If any answer is wrong, the code **MUST NOT** enter General.

### Section 4.2 — Entry Checklist

```
GENERAL DOMAIN ENTRY CHECKLIST

File: _______________
Author: _______________
Date: _______________

[ ] Code cannot live in a product domain (explain why)
[ ] Sub-constitution identified: Control / Lifecycle / Projection
[ ] Invariants identified and documented
[ ] No product-specific logic included
[ ] Decision/execution separation maintained
[ ] Layer classification correct (L4 for engines)
[ ] AUDIENCE header present and correct

Justification:
_________________________________________________
_________________________________________________

Approved by: _______________
```

### Section 4.3 — Exit Criteria (Extraction Triggers)

Code MUST be extracted from General when:

| Trigger | Action |
|---------|--------|
| Code becomes product-specific | Extract to product domain |
| Code no longer enforces cross-domain rules | Extract to appropriate domain |
| A dedicated domain is created for the concern | Migrate code to new domain |
| Code was temporary and deadline passed | Remove or formalize |

### Section 4.4 — Exit Checklist

```
GENERAL DOMAIN EXIT CHECKLIST

File: _______________
Destination: _______________
Date: _______________

[ ] Target domain identified
[ ] All callers updated
[ ] No invariant violations introduced
[ ] Cross-domain contracts preserved (or explicitly transferred)
[ ] Tests migrated
[ ] Documentation updated

Extraction rationale:
_________________________________________________

Approved by: _______________
```

---

## Article V: Gravity Control

### Section 5.1 — The Gravity Problem

General attracts code because:
- It's "safe" (high governance)
- It's "important" (contains critical systems)
- It's "convenient" (already has patterns)

This creates a god-domain over time.

### Section 5.2 — Gravity Countermeasures

| Countermeasure | Implementation |
|----------------|----------------|
| **Entry friction** | Require checklist approval for new files |
| **Periodic audit** | Quarterly review of all General code |
| **Extraction pressure** | Track candidates and set deadlines |
| **Sub-constitution enforcement** | Every file must belong to exactly one |
| **Temporary time-bombs** | Temporary code must have explicit expiry |

### Section 5.3 — Quarterly Audit Template

```
GENERAL DOMAIN QUARTERLY AUDIT

Quarter: _______________
Auditor: _______________

1. Total files in General: _____
2. Files added this quarter: _____
3. Files extracted this quarter: _____

4. Extraction candidates identified:
   - _______________
   - _______________

5. Temporary code status:
   - guard_write_service.py: Phase ___ / Deadline: ___

6. Invariant violations found: _____
7. Layer violations found: _____

8. Recommendation:
   [ ] No action needed
   [ ] Extraction required (list files)
   [ ] Constitution amendment needed (describe)

Signed: _______________
```

---

## Article VI: Future Extraction Map

### Section 6.1 — Planned Extractions

| Current Location | Target Domain | Timeline | Trigger |
|------------------|---------------|----------|---------|
| `facades/monitors_facade.py` | `customer/monitors/` | Phase 4+ | Monitors domain creation |
| `facades/alerts_facade.py` | `customer/alerts/` | Phase 4+ | Alerts domain creation |
| `facades/scheduler_facade.py` | `customer/scheduler/` | Phase 4+ | Scheduler domain creation |
| `facades/compliance_facade.py` | `customer/compliance/` | Phase 4+ | Compliance domain creation |
| `controls/engines/guard_write_service.py` | Split: KillSwitch + Incident | Phase 3 | **MANDATORY** |
| `runtime/engines/*` | `customer/runtime/` | Phase 5+ | Runtime domain creation |
| `lifecycle/engines/*` | `customer/lifecycle/` | Phase 5+ | Lifecycle domain creation |
| `workflow/contracts/*` | `customer/contracts/` | Phase 5+ | Contracts domain creation |

### Section 6.2 — What Remains in General

After all extractions, General should contain ONLY:

| Component | Reason to Remain |
|-----------|------------------|
| `cross-domain/engines/cross_domain.py` | Cross-domain governance by definition |
| Future: Cross-domain projections | Projections spanning domains |
| Future: System-wide invariant checkers | Invariants that no single domain can own |

### Section 6.3 — Extraction Dependencies

```
Phase 3:
  └── guard_write_service.py split (MANDATORY)

Phase 4:
  ├── Monitors domain created
  ├── Alerts domain created
  ├── Scheduler domain created
  └── Compliance domain created

Phase 5:
  ├── Runtime domain created
  ├── Lifecycle domain created
  └── Contracts domain created

Phase 6:
  └── General reduced to cross-domain core only
```

---

## Article VII: Immediate Actions

### Section 7.1 — Required Before Phase 4

| Action | Owner | Deadline |
|--------|-------|----------|
| Fix `knowledge_sdk.py` layer violation | Architecture | Phase 3 end |
| Add Phase 3 deadline to `guard_write_service.py` | Architecture | Immediate |
| Add this constitution to `general/__init__.py` | Architecture | Immediate |
| Classify all files into sub-constitutions | Architecture | Phase 3 end |

### Section 7.2 — Governance Contract for `__init__.py`

Add to `general/__init__.py`:

```python
"""
General Domain

CONSTITUTION: docs/architecture/HOC_general_domain_constitution_v1.md

PURPOSE:
General exists ONLY for:
- Cross-domain invariants
- Irreversible decisions
- Lifecycle state machines
- Projections of audited truth

If a feature can live elsewhere safely, it MUST.

SUB-CONSTITUTIONS:
1. Control Plane - "Is this allowed to happen?"
2. Lifecycle Plane - "Where is this entity in its life?"
3. Projection Plane - "What is true right now?"

FROZEN INVARIANTS:
- GOV-001: MAY_NOT is un-overridable
- GOV-002: Governance must throw
- SEP-001: Orchestrators decide, never execute
- SEP-002: Executors execute, never decide
- SEP-003: Projections read, never mutate
- LCY-001: Stage handlers are dumb plugins

KNOWN ISSUES:
1. knowledge_sdk.py is L2 in engines (layer violation)
2. guard_write_service.py is temporary (split pending Phase 3)
3. Facades are extraction candidates (Phase 4+)

ENTRY RULE:
New code requires completed Entry Checklist (see constitution).
"""
```

---

## Article VIII: Amendments

### Section 8.1 — Amendment Process

This constitution may be amended when:

1. A new sub-constitution is needed
2. An invariant must be added or modified
3. Extraction map changes
4. Entry/exit criteria evolve

### Section 8.2 — Amendment Record

| Version | Date | Change | Ratified By |
|---------|------|--------|-------------|
| v1 | 2026-01-22 | Initial constitution | Architecture |

---

## Signatures

```
RATIFIED

Domain: General
Constitution Version: 1.0
Date: 2026-01-22

This constitution is now in effect.
All code entering General must comply.
All existing code must be classified by Phase 3 end.
```

---

## Appendix A: Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                 GENERAL DOMAIN CONSTITUTION                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PRIME DIRECTIVE:                                           │
│  If it can live elsewhere safely, it MUST.                  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  SUB-CONSTITUTIONS:                                         │
│                                                             │
│  CONTROL PLANE      "Is this allowed to happen?"            │
│  LIFECYCLE PLANE    "Where is this entity in its life?"     │
│  PROJECTION PLANE   "What is true right now?"               │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  FROZEN RULES:                                              │
│                                                             │
│  • MAY_NOT is un-overridable                                │
│  • Governance must throw                                    │
│  • Orchestrators decide, never execute                      │
│  • Executors execute, never decide                          │
│  • Projections read, never mutate                           │
│  • Stage handlers are dumb                                  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  BEFORE ADDING CODE:                                        │
│                                                             │
│  1. Can it live elsewhere? → If YES, put it there           │
│  2. Which sub-constitution? → Must have answer              │
│  3. Entry checklist complete? → Required                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Appendix B: Invariant Reference Table

| ID | Name | Location | Enforcement |
|----|------|----------|-------------|
| GOV-001 | MAY_NOT un-overridable | contract_service.py | MayNotVerdictError |
| GOV-002 | Governance must throw | cross_domain.py | GovernanceError |
| GOV-003 | Terminal states immutable | contract_service.py | ContractImmutableError |
| GOV-004 | No optional dependencies | cross_domain.py | Doctrine |
| SEP-001 | Orchestrators decide only | Architecture | Code review |
| SEP-002 | Executors execute only | Architecture | Code review |
| SEP-003 | Projections read only | rollout_projection.py | Design |
| SEP-004 | Governance enforces only | cross_domain.py | Doctrine |
| LCY-001 | Stage handlers are dumb | base.py | Protocol |
| LCY-002 | Handlers don't manage state | base.py | Protocol |
| LCY-003 | Handlers don't emit events | base.py | Protocol |
| LCY-004 | Handlers don't check policies | base.py | Protocol |
| LCY-005 | Destructive requires approval | offboarding.py | purge_approved |
| PRJ-001 | Projection is read-only | rollout_projection.py | Design |
| PRJ-002 | Advancement requires PASS | rollout_projection.py | can_advance_stage |
| PRJ-003 | Advancement requires stabilization | rollout_projection.py | StabilizationWindow |
| PRJ-004 | No health degradation | rollout_projection.py | can_advance_stage |
| PRJ-005 | Stages are monotonic | rollout_projection.py | STAGE_ORDER |
| PRJ-006 | Customer sees facts only | rollout_projection.py | CustomerRolloutView |
| CON-001 | Follow state machine | contract_service.py | VALID_TRANSITIONS |
| CON-002 | APPROVED needs approved_by | contract_service.py | validate_transition |
| CON-003 | ACTIVE needs job | contract_service.py | validate_transition |
| CON-004 | COMPLETED needs PASS | contract_service.py | validate_transition |
| CON-005 | Terminal is immutable | contract_service.py | TERMINAL_STATES |
| CON-006 | Schema validation | contract_service.py | Input validation |
| CON-007 | Confidence [0,1] | contract_service.py | Input validation |
