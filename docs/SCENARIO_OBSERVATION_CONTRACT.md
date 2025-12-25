# Scenario Observation Contract

**Effective:** 2025-12-25
**Scope:** All scenario analysis until SYSTEM_TRUTH_LEDGER has >= 10 entries

---

## Claude Output Format (MANDATORY)

Claude must **only** output in this structure. No exceptions.

```
SCENARIO-ID:
MILESTONE:
PRIMARY TRUTH SURFACE:
  - Intent | Decision | Constraint | Outcome

SECONDARY SURFACES:
  - (if any)

SYSTEM BEHAVIOR OBSERVED:
  (facts only, no judgment)

HUMAN EXPECTATION:
  (what a reasonable user assumed)

TRUTH GAP TYPE:
  - Missing
  - Opaque
  - Misleading
  - Contradictory

WHICH CONSOLE IS AFFECTED:
  - Customer
  - Founder
  - Both

BROKEN PROMISE (if any):
  (what the system implicitly promised but didn't uphold)

IS THIS A NEW TRUTH?
  - Yes / No

IF YES, WHICH CONTRACT MUST EVOLVE:
  - Pre-Run Contract
  - Decision Record
  - Constraint Declaration
  - Outcome Reconciliation
```

---

## Claude is FORBIDDEN from:

- Proposing fixes
- Suggesting UI
- Improving wording
- Hypothesizing intent
- Pattern speculation
- Solution ideation
- UX recommendations

---

## Claude is REQUIRED to:

- Extract system truth only
- Say "Missing" if information is missing
- Mark Customer vs Founder if gap affects them differently
- Output structured format only

---

## Enforcement

If Claude output does not match the format above, reject it and re-prompt:

> "Extract system truth only. No advice. No solutions. No speculation. If information is missing, say 'Missing'."

---

## Phase Rules

| Phase | Allowed |
|-------|---------|
| Ledger < 10 entries | Observation only |
| Ledger >= 10 entries | Pattern grouping allowed |
| Ledger >= 15 entries | Contract evolution allowed |

Until ledger has volume, Claude is a **court stenographer**, not a designer.
