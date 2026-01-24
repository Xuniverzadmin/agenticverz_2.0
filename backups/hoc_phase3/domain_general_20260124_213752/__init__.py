# Layer: L4 — Domain Services
# AUDIENCE: CUSTOMER
# Role: General domain - Runtime orchestration, lifecycle management, cross-domain governance
# Reference: docs/architecture/HOC_general_domain_constitution_v1.md

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
   - governance_orchestrator.py, contract_service.py, cross_domain.py
   - Invariants: GOV-001, GOV-002, CON-001 to CON-007

2. Lifecycle Plane - "Where is this entity in its life?"
   - lifecycle/engines/*, knowledge_lifecycle_manager.py
   - Invariants: LCY-001 (stage handlers are dumb plugins)

3. Projection Plane - "What is true right now?"
   - rollout_projection.py, facades/*
   - Invariants: SEP-003 (read-only, never mutate)

FROZEN INVARIANTS:
- GOV-001: MAY_NOT is un-overridable
- GOV-002: Governance must throw
- SEP-001: Orchestrators decide, never execute
- SEP-002: Executors execute, never decide
- SEP-003: Projections read, never mutate
- LCY-001: Stage handlers are dumb plugins
- CON-001 to CON-007: Contract state machine rules

KNOWN ISSUES:
1. knowledge_sdk.py is L2 in engines (layer violation) - Phase 3 deadline
2. guard_write_service.py is temporary (split pending Phase 3)
3. Facades are extraction candidates (Phase 4+)

ENTRY RULE:
New code requires completed Entry Checklist (see constitution Article IV).

EXIT RULE:
Extracted code must complete Exit Checklist (see constitution Article IV).

GRAVITY CONTROL:
This domain attracts responsibility. Every PR touching general/ must answer:
- Can this live in a dedicated domain instead?
- If yes, it MUST be placed there (not here)
"""
