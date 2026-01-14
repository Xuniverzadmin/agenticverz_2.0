# Claude Architecture Execution Checklist

**Version:** v1.0
**Authority:** ARCHITECTURE_CONSTRAINTS_V1.yaml
**Use:** Before ANY code change

---

## Quick Decision Tree

```
Is this a UI plan change?
├── YES → STOP. Ask human.
└── NO → Continue

Is this adding new semantics?
├── YES → STOP. Ask human.
└── NO → Continue

Is this bypassing automation?
├── YES → STOP. Fix automation instead.
└── NO → Continue

Is this fixing backend to match SDSR expectation?
├── YES → PROCEED (autonomous zone)
└── NO → Check if in autonomous zone
```

---

## Autonomous Fix Zones (NO ASK REQUIRED)

| Zone | Trigger | Example Fixes |
|------|---------|---------------|
| **AUTO-A** | SDSR failure, schema violation | Fix endpoint shape, query logic, capability status |
| **AUTO-B** | Script error, CI failure | Fix pipeline, PDG allowlist, naming mismatch |
| **AUTO-C** | Terminology drift identified | Global rename (LLM_RUNS → EXECUTIONS) |
| **AUTO-D** | Panel render failure | Fix empty state, state label, rendering bug |

**Key:** These fixes restore correctness without changing meaning.

---

## Hard Stop Zones (MUST ASK)

| Zone | Examples | Why |
|------|----------|-----|
| **STOP-A** | Add panel, remove domain, mark DEFERRED | UI plan is human intent |
| **STOP-B** | New attention reason, new lifecycle state | Semantics change meaning |
| **STOP-C** | Skip PDG, copy projection manually | Authority inversion |
| **STOP-D** | Add interpretation panel, cross-domain summary | Interpretation is human |

**Key:** These changes alter what the system means to humans.

---

## Before Writing Code

```
ARCHITECTURE PRE-CHECK

1. What layer am I modifying? [1-7]
   → Lower layers cannot reshape higher layers

2. Does this change ui_plan.yaml?
   → If YES: STOP AND ASK

3. Does this add new semantics?
   → If YES: STOP AND ASK

4. Does this bypass automation?
   → If YES: FIX AUTOMATION INSTEAD

5. Is this in an autonomous fix zone?
   → If YES: Proceed with fix
   → If NO: STOP AND ASK
```

---

## When Blocked

Use this exact format:

```
BLOCKED AT: <layer name>
REASON: <exact rule ID or invariant violated>
REQUIRES: <human decision | automation fix>
NO WORKAROUND APPLIED
```

**Never:**
- Apply silent fixes
- Create workarounds
- Bypass and continue

---

## Authority Stack (Memorize This)

```
1. ui_plan.yaml          ← CANNOT TOUCH (human intent)
2. Intent YAML           ← Can create/modify (with panel)
3. Capability Registry   ← Can update status (with SDSR)
4. SDSR Scenarios        ← Can fix expectations (not weaken)
5. Backend Endpoints     ← FREE TO FIX (implementation)
6. Compiler              ← FREE TO FIX (pipeline)
7. Frontend              ← FREE TO FIX (rendering)
```

**Rule:** Always work at the lowest necessary layer.

---

## Panel State Quick Reference

| State | Render? | Controls? | Can Fix? |
|-------|---------|-----------|----------|
| EMPTY | YES (placeholder) | NO | Add intent YAML |
| UNBOUND | YES (coming soon) | NO | Add capability |
| DRAFT | YES (disabled) | DISABLED | Run SDSR |
| BOUND | YES (full) | YES | N/A (done) |
| DEFERRED | CONFIGURABLE | NO | Human only |

---

## Common Violations to Avoid

| Violation | Correct Action |
|-----------|----------------|
| "Let me just copy the projection file" | Run pipeline properly |
| "I'll add this panel to make it work" | Ask human first |
| "I'll weaken this SDSR check" | Fix backend instead |
| "The UI should show this differently" | UI is intent, not opinion |
| "Backend isn't ready so I'll hide the panel" | Panel stays, shows empty state |

---

## Self-Check Before Response

```
□ Did I identify the layer I'm working in?
□ Am I in an autonomous fix zone?
□ Did I avoid touching ui_plan.yaml?
□ Did I avoid adding new semantics?
□ Did I avoid bypassing automation?
□ If blocked, did I report it properly?
```

**If any box is unchecked or uncertain → STOP AND ASK**

---

## References

| Document | Purpose |
|----------|---------|
| `ARCHITECTURE_CONSTRAINTS_V1.yaml` | Full machine-checkable rules |
| `UI_AS_CONSTRAINT_V1.md` | Doctrine |
| `PDG_STATE_INVARIANTS_V1.yaml` | State transitions |
| `CUSTOMER_CONSOLE_V1_CONSTITUTION.md` | Constitutional authority |
