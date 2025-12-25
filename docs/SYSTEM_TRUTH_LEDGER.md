# System Truth Ledger

**Created:** 2025-12-25
**Entries:** 13
**Status:** ACCUMULATING → THRESHOLD REACHED (pattern grouping unlocked)

---

## Rules

1. No fixes until ledger has >= 10 entries
2. No prioritization yet
3. Just accumulation
4. One entry per scenario observation

---

## Entry Format

```
[YYYY-MM-DD] — Scenario {ID}
Surface: Intent | Decision | Constraint | Outcome
Gap: Missing | Opaque | Misleading | Contradictory
Console: Customer | Founder | Both
Description: {one sentence}
Status: Unresolved
```

---

## Ledger Entries

---

[2025-12-25] — Scenario 1 (Incident Creation)
Surface: Intent
Gap: Opaque
Console: Customer
Description: Pre-execution intent is hidden; no preview of what stages will execute before starting
Status: Unresolved

---

[2025-12-25] — Scenario 1 (Incident Creation)
Surface: Constraint
Gap: Contradictory
Console: Customer
Description: Budget parameter implies constraint; actual behavior is advisory only (5,000 requested, 9,671 used)
Status: Unresolved

---

[2025-12-25] — Scenario 2 (Execution Routing)
Surface: Decision
Gap: Missing
Console: Both
Description: CARE routing decisions not surfaced in workflow responses; routing_decisions field always empty
Status: Unresolved

---

[2025-12-25] — Scenario 2 (Execution Routing)
Surface: Decision
Gap: Misleading
Console: Both
Description: routing_stability: 1.0 reported but no routing occurred; field implies activity that didn't happen
Status: Unresolved

---

[2025-12-25] — Scenario 3 (Recovery Suggestion)
Surface: Decision
Gap: Missing
Console: Founder
Description: Recovery decisions exist (50+ candidates) but are disconnected from workflow execution flow
Status: Unresolved

---

[2025-12-25] — Scenario 3 (Recovery Suggestion)
Surface: Outcome
Gap: Opaque
Console: Founder
Description: recovery_log field exists but when it would be populated is undefined; always empty on success
Status: Unresolved

---

[2025-12-25] — Scenario 4 (Policy Consequence)
Surface: Constraint
Gap: Contradictory
Console: Customer
Description: Simulation warns "budget_insufficient" but execution ignores warning and proceeds
Status: Unresolved

---

[2025-12-25] — Scenario 4 (Policy Consequence)
Surface: Intent
Gap: Opaque
Console: Customer
Description: Policy rules not queryable upfront; violations discoverable only after execution
Status: Unresolved

---

[2025-12-25] — Scenario 5 (Cost/Ops Visibility)
Surface: Outcome
Gap: Missing
Console: Founder
Description: Cost tables (/cost/summary, /cost/dashboard) show 0 despite workflows consuming tokens
Status: Unresolved

---

[2025-12-25] — Scenario 5 (Cost/Ops Visibility)
Surface: Outcome
Gap: Opaque
Console: Founder
Description: Prometheus (60+ metrics) and Grafana (6 dashboards) exist but are undocumented
Status: Unresolved

---

[2025-12-25] — Scenario 5 (Cost/Ops Visibility)
Surface: Outcome
Gap: Missing
Console: Founder
Description: Ops console (/ops/*) returns AUTH_DOMAIN_MISMATCH with no documented access path
Status: Unresolved

---

[2025-12-25] — Scenario 6 (Memory Carryover)
Surface: Intent
Gap: Opaque
Console: Both
Description: MEMORY_CONTEXT_INJECTION=true but no visible effect; memory injection not observable
Status: Unresolved

---

[2025-12-25] — Scenario 6 (Memory Carryover)
Surface: Decision
Gap: Missing
Console: Both
Description: No memory-related fields (memory_context, remembered, context_injected) in workflow responses
Status: Unresolved

---

## Phase Transitions

| Threshold | Unlocks |
|-----------|---------|
| 10 entries | Pattern grouping |
| 15 entries | Contract evolution |
| 20 entries | Surface refactoring |
