# PIN-495: Policies Domain — Canonical Consolidation

**Created:** 2026-01-31
**Status:** COMPLETE
**Category:** Architecture / Domain Consolidation
**Related PINs:** PIN-470 (HOC Layer Inventory), PIN-484 (HOC Topology V2.0.0), PIN-493 (Incidents), PIN-494 (Activity)

---

## Summary

Completed full consolidation of the policies domain (largest domain, 77 files): two-pass analysis, naming violation fixes, layer header corrections, legacy import disconnection, canonical registration, and deterministic tally verification. Third domain after incidents pilot and activity.

## Scope

- **Physical files:** 77 (62 L5_engines + 15 L6_drivers)
- **Active scripts:** 75 (excluding 2 __init__.py)
- **L4 Operations:** 9 (policies.query, policies.enforcement, policies.governance, policies.lessons, policies.policy_facade, policies.limits, policies.rules, policies.rate_limits, policies.simulate)
- **Stub engines:** 0 (fully implemented domain, but 3 files were legacy re-export shims → now stubbed after disconnection)

## Key Decisions

### 1. Zero Duplicates Confirmed
All apparent overlaps classified:
| Group | Verdict | Reason |
|-------|---------|--------|
| Policy read (L5 vs L6) | L5_L6_SEPARATION | Business logic vs data access |
| Conflict resolution (3 files) | FALSE_POSITIVE | Prevention, optimization, runtime arbitration |
| Proposals (5 files) | FACADE_PATTERN | Read/write separation, lifecycle vs query |
| Rules (4 files) | FACADE_PATTERN | CRUD + query engines, each with own driver |
| Facades (3 files) | FALSE_POSITIVE | Governance, policies, limits — distinct concerns |
| Recovery (3 files) | L5_L6_SEPARATION | Decision engine + matcher + persistence |

### 2. All 75 Active Scripts Declared Canonical
Every script has a unique purpose. Full registry in `POLICIES_CANONICAL_SOFTWARE_LITERATURE.md`.

### 3. Two Naming Violations Fixed
| ID | Old Name | New Name | Status |
|----|----------|----------|--------|
| N1 | cus_enforcement_service.py | cus_enforcement_engine.py | FIXED — legacy disconnected, stubbed |
| N2 | limits_simulation_service.py | limits_simulation_engine.py | FIXED — legacy disconnected, stubbed |

### 4. Four Layer Headers Corrected
| File | Was | Now | Reason |
|------|-----|-----|--------|
| governance_facade.py | L6 — Driver | L5 — Domain Engine (Facade) | File is in L5_engines/ |
| policy_command.py | L4 — Command Facade | L5 — Domain Engine (Command Facade) | File is in L5_engines/ |
| worker_execution_command.py | L4 — Command Facade | L5 — Domain Engine (Command Facade) | File is in L5_engines/ |
| claim_decision_engine.py | L4 — System Truth | L5 — Domain Engine (System Truth) | File is in L5_engines/ |

### 5. Four Legacy Connections DISCONNECTED
| Direction | File | Was Importing | Action |
|-----------|------|---------------|--------|
| HOC→legacy | cus_enforcement_engine.py | app.services.cus_enforcement_engine | Stubbed with TODO |
| HOC→legacy | limits_simulation_engine.py | app.services.limits.simulation_engine | Stubbed with TODO |
| HOC→legacy | policies_facade.py | app.services.policies_facade | Stubbed with TODO |
| Legacy→HOC | app/services/policy/lessons_engine.py | app.hoc.cus.policies.L5_engines.lessons_engine | File emptied, disconnected |

All stubs marked: `TODO: Rewire to HOC equivalent candidate during rewiring phase`

### 6. Architecture Violations (deferred to rewiring phase)
Correct cross-domain pattern per V2.0.0: L6 policy driver → L5 policy engine → L4 runtime orchestrator → L5 target engine → L6 target driver → feedback return same route.

| ID | File | Violation | Target |
|----|------|-----------|--------|
| V1 | policy_proposal_engine.py (L5) | L5→L6 cross-domain | logs/audit_ledger |
| V2 | policy_rules_engine.py (L5) | L5→L6 cross-domain | logs/audit_ledger |
| V3 | policy_limits_engine.py (L5) | L5→L6 cross-domain | logs/audit_ledger |
| V4 | recovery_evaluation_engine.py (L5) | L5→L5 cross-domain | incidents/recovery_rule_engine |
| V5 | lessons_engine.py (L5) | L5→L6 cross-domain | incidents/lessons_driver |

## Artifacts Produced

| Artifact | Path |
|----------|------|
| Full Literature | `literature/hoc_domain/policies/POLICIES_CANONICAL_SOFTWARE_LITERATURE.md` |
| Tally Script | `scripts/ops/hoc_policies_tally.py` |
| Memory PIN | `docs/memory-pins/PIN-495-policies-domain-canonical-consolidation.md` |

## Lessons Applied from Previous Domains

| # | Lesson | Applied |
|---|--------|---------|
| L1 (PIN-493) | Overlap detection must consider role | Yes — 6 groups classified |
| L6 (PIN-493) | Naming violations break classification | Yes — fixed 2 naming violations first |
| A2 (PIN-494) | Don't compare with legacy | Yes — disconnected instead |
| A4 (PIN-494) | Legacy caller paths need migration | Yes — disconnected legacy↔HOC |

## New Lessons (for subsequent domains)

| # | Lesson | Impact |
|---|--------|--------|
| P1 | Layer header mismatches are common in large domains — check every file | Automated tally catches these |
| P2 | Legacy re-export shims should be disconnected, not deferred | Prevents accidental coupling |
| P3 | Cross-domain audit logging (V1-V3) is the most common violation pattern | L4 needs audit operation |
| P4 | 3 legacy disconnections create stubs that need rewiring — track in rewiring manifest | Add to post-all-domain work |

## Verification Commands

```bash
python3 scripts/ops/hoc_policies_tally.py    # All checks PASS expected
```
