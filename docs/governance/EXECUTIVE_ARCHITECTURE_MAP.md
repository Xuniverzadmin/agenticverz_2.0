# Executive Architecture Map

**Version:** 1.0
**Date:** 2025-12-31
**Status:** Truthful, Compressed, No Hand-Waving

---

## What This System Guarantees

- No action executes without explicit authority
- No authority is implied
- No execution path is invisible
- No frontend, CI, or ops system can silently influence runtime behavior

---

## The Only Valid Execution Shape

```
Actors
  └─ Human / Client / Scheduler
        ↓
L2 — API INTENT
  (What is being requested)
        ↓
L3 — TRANSLATION
  (Normalize, validate, map intent)
        ↓
L4 — DECISION AUTHORITY
  (Is this allowed? What should happen?)
        ↓
L5 — EXECUTION
  (Do the work, touch systems, emit effects)
        ↓
STATE / METRICS / SIDE EFFECTS
```

---

## Where Power Lives (Non-Negotiable)

| Power | Layer | Others Forbidden |
|-------|-------|------------------|
| Authority | L4 only | L2, L3, L5 cannot decide |
| Translation | L3 only | L2 cannot normalize |
| Execution | L5 only | L4 cannot execute |
| Observation | Telemetry | No control path |
| Governance | BLCA / CI | Explicit, logged |

---

## Hard Stops (System Kill Switches)

| Switch | Entry | Authorization | Execution | Audit |
|--------|-------|---------------|-----------|-------|
| Tenant freeze | L2 | L4 | L5 | Full |
| API key revoke | L2 | L4 | L5 | Full |
| Runtime halt | L2 | L4 | L5 | Full |
| Policy lockout | L2 | L4 | L5 | Full |

All kill switches are auditable end-to-end.

---

## What Cannot Happen Anymore

| Forbidden | Why |
|-----------|-----|
| APIs calling workers directly | Bypasses authority |
| Workers deciding policy | Role violation |
| Adapters enforcing rules | Translation ≠ decision |
| CI implicitly changing behavior | Governance violation |
| "Just code" bypassing architecture | Structure enforced |

---

## ASCII Architecture Poster

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AOS ARCHITECTURE                               │
│                          Steady-State (Phase G)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ACTORS ────────────────────────────────────────────────────────────────   │
│   Human │ Client │ Scheduler │ External System                              │
│         │                                                                   │
│         ▼                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ L2 — API INTENT                                                     │   │
│   │ "What is being requested"                                           │   │
│   │                                                                     │   │
│   │ runtime.py │ workers.py │ policy.py │ runs.py │ agents.py           │   │
│   └─────────────────────────────┬───────────────────────────────────────┘   │
│                                 │                                           │
│                                 ▼                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ L3 — TRANSLATION                                                    │   │
│   │ "Normalize, validate, map intent"                                   │   │
│   │                                                                     │   │
│   │ runtime_adapter │ workers_adapter │ policy_adapter                  │   │
│   │ (< 200 LOC each, zero branching, translation only)                  │   │
│   └─────────────────────────────┬───────────────────────────────────────┘   │
│                                 │                                           │
│                                 ▼                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ L4 — DECISION AUTHORITY                                             │   │
│   │ "Is this allowed? What should happen?"                              │   │
│   │                                                                     │   │
│   │ ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐   │   │
│   │ │ Command Facades   │ │ Domain Engines    │ │ Classification    │   │   │
│   │ │ runtime_command   │ │ simulate.py       │ │ pattern_detect    │   │   │
│   │ │ worker_exec_cmd   │ │ graduation_engine │ │ recovery_rule     │   │   │
│   │ │ policy_command    │ │ claim_decision    │ │ cost_anomaly      │   │   │
│   │ └───────────────────┘ └───────────────────┘ └───────────────────┘   │   │
│   │                                                                     │   │
│   │ SYSTEM TRUTH LIVES HERE — ALL DECISIONS MADE AT THIS LAYER          │   │
│   └─────────────────────────────┬───────────────────────────────────────┘   │
│                                 │                                           │
│                                 ▼                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ L5 — EXECUTION                                                      │   │
│   │ "Do the work, touch systems, emit effects"                          │   │
│   │                                                                     │   │
│   │ Runtime │ BusinessBuilderWorker │ workflow/* │ cost_sim │ metrics   │   │
│   │ (Blind executors — consume specs, report outcomes, never decide)    │   │
│   └─────────────────────────────┬───────────────────────────────────────┘   │
│                                 │                                           │
│                                 ▼                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ L6 — PLATFORM SUBSTRATE                                             │   │
│   │ PostgreSQL │ Redis │ Auth │ Models │ Event Emitter                  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ L7 — OPS (Orthogonal)                                               │   │
│   │ layer_validator.py │ memory_trail.py │ session_start.sh             │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                          IMPORT DIRECTION LAW                               │
│                                                                             │
│     L2 → L3, L4, L6      (APIs call adapters, commands, platform)           │
│     L3 → L4, L6          (Adapters call commands, platform)                 │
│     L4 → L5, L6          (Commands delegate to execution)    ← AUTHORIZED   │
│     L5 → L6              (Workers use platform only)                        │
│                                                                             │
│     FORBIDDEN: L2 → L5 (APIs cannot call workers directly)                  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                          ENFORCEMENT (MECHANICAL)                           │
│                                                                             │
│     Tool: layer_validator.py (BLCA)                                         │
│     Gate: CI blocks merge on violations                                     │
│     Status: 0 violations (CLEAN)                                            │
│                                                                             │
│     If BLCA is not CLEAN → ALL WORK HALTS                                   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                          GOVERNANCE REGIME                                  │
│                                                                             │
│     Phase A    Foundation                                                   │
│     Phase A.5  Truth-Grade (S1-S6)                                          │
│     Phase B    Resilience                                                   │
│     Phase C    Learning                                                     │
│     Phase D    Visibility                                                   │
│     Phase E    Semantic Closure                                             │
│     Phase F    Structural Closure ─────────────────────────── COMPLETE      │
│     Phase G    Steady-State Governance ─────────────────────── ACTIVE       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Why This Matters

This architecture does not rely on discipline or memory.
It relies on **structure + enforcement**.

If someone tries to cheat:

1. BLCA catches it
2. Governance halts progress
3. The system protects itself

---

## Final Truth

> **This system does not merely work — it cannot lie about how it works.**

---

## Reference

- PIN-258: Phase F Application Boundary Completion
- PIN-259: Phase G Steady-State Governance
- PHASE_F_CLOSURE_DECLARATION.md
- PHASE_G_STEADY_STATE_GOVERNANCE.md
