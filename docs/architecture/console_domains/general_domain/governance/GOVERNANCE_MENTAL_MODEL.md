# Governance Mental Model

**Status:** REQUIRED READING
**Audience:** New Engineers
**Time to Read:** 5 minutes
**Reference:** PIN-454 (Cross-Domain Orchestration Audit)

---

## The Four Roles

Every operation in the system involves four distinct roles:

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   DECIDES          EXECUTES         OBSERVES        AUDITS     │
│   ───────          ────────         ────────        ──────     │
│                                                                 │
│   PolicyChecker    RunRunner        TraceFacade     RAC        │
│   ROK              Workers          EventReactor    Reconciler │
│   RBAC             Engines          Prometheus                 │
│                                                                 │
│   "Should this     "Do the          "Record what    "Did what  │
│    happen?"         work"            happened"       was       │
│                                                      promised  │
│                                                      happen?"  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Who Decides?

**PolicyChecker** and **ROK (Run Orchestration Kernel)** decide.

- PolicyChecker: "Is this run allowed? Does it violate budget/rate limits?"
- ROK: "What phase should this run be in? Can it transition?"
- RBAC: "Does this actor have permission?"

**Rule:** Deciders never execute. They return yes/no/pause.

### Who Executes?

**RunRunner** and **Workers** execute.

- RunRunner: Orchestrates LLM calls, skill execution
- Workers: Process jobs from the queue
- Engines: IncidentEngine, PolicyEngine, TraceStore

**Rule:** Executors don't decide policy. They follow decisions.

### Who Observes?

**TraceFacade**, **EventReactor**, and **Prometheus** observe.

- TraceFacade: Records execution traces (immutable)
- EventReactor: Listens to events, triggers reactions
- Prometheus: Metrics, dashboards, alerts

**Rule:** Observers are passive. They record, never modify.

### Who Audits?

**RAC (Runtime Audit Contract)** and **Reconciler** audit.

- RAC: Declares expectations before execution
- Reconciler: Compares expectations vs. acknowledgments after
- Result: COMPLETE, INCOMPLETE, or STALE

**Rule:** Auditors verify. They don't forgive missing work.

---

## The Run Lifecycle

```
                    DECIDES                 EXECUTES
                       │                       │
                       ▼                       ▼
┌─────────┐     ┌───────────┐     ┌───────────────┐     ┌───────────┐
│ CREATED │────▶│ AUTHORIZED│────▶│   EXECUTING   │────▶│ COMPLETED │
└─────────┘     └───────────┘     └───────────────┘     └───────────┘
     │               │                    │                   │
     │               │                    │                   │
     ▼               ▼                    ▼                   ▼
  OBSERVES        OBSERVES            OBSERVES            AUDITS
  (trace)         (trace)             (trace)             (reconcile)
```

1. **CREATED** → Run exists, not yet approved
2. **AUTHORIZED** → PolicyChecker approved, ready to execute
3. **EXECUTING** → Worker is running LLM calls
4. **COMPLETED/FAILED** → Execution finished, audit happens

---

## The Audit Contract

Before execution, we declare what MUST happen:

```python
# Expectations (declared at run start)
expectations = [
    ("incidents", "create_incident"),    # If run fails
    ("policies", "evaluate_policy"),     # Always
    ("logs", "start_trace"),             # Always
    ("orchestrator", "finalize_run"),    # MUST happen
]
```

After execution, we check acknowledgments:

```python
# Reconciliation
missing = expectations - acknowledgments

if "finalize_run" not in acks:
    status = "STALE"  # Worker crashed or lost
elif missing:
    status = "INCOMPLETE"  # Something didn't happen
else:
    status = "COMPLETE"  # All good
```

**Key Insight:** If `finalize_run` is never acked, the run is STALE. This is the liveness guarantee.

---

## Governance Profiles

Three pre-defined configurations to avoid flag confusion:

| Profile | Use Case | Enforcement |
|---------|----------|-------------|
| **STRICT** | Production | Everything enforced |
| **STANDARD** | Staging/Dev | Core features, warnings |
| **OBSERVE_ONLY** | Safe rollout | Audit only, no blocking |

Set via: `GOVERNANCE_PROFILE=STRICT`

---

## Quick Reference

### "I want to add a new policy check"

→ Add to **PolicyChecker** (Decides)
→ Never add enforcement logic to RunRunner

### "I want to record a new metric"

→ Add to **TraceFacade** or **Prometheus** (Observes)
→ Observers don't modify execution

### "I want to ensure X always happens"

→ Add an **expectation** in RAC (Audits)
→ Add the corresponding **ack** emission in the executor

### "I want to react to an event"

→ Add a handler to **EventReactor** (Observes → Decides)
→ EventReactor can trigger new decisions, not execute directly

---

## Common Mistakes

| Mistake | Why It's Wrong | Fix |
|---------|----------------|-----|
| PolicyChecker executing LLM calls | Deciders don't execute | Move to RunRunner |
| RunRunner deciding policy | Executors don't decide | Call PolicyChecker |
| TraceFacade modifying run state | Observers don't modify | Use engine instead |
| Skipping finalize_run ack | Breaks liveness guarantee | Always ack finalize |
| Mixing feature flags randomly | Undefined behavior | Use Governance Profile |

---

## Required Reading

1. `docs/architecture/CROSS_DOMAIN_ORCHESTRATION_AUDIT.md` — Full system design
2. `backend/app/services/governance/profile.py` — Governance profiles
3. `backend/app/worker/orchestration/` — ROK implementation
4. `backend/app/services/audit/` — RAC implementation

---

## One Sentence Summary

> **PolicyChecker decides, RunRunner executes, TraceFacade observes, RAC audits — and finalize_run must always be acked.**
