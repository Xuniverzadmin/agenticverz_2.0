# Signal Circuit Discovery (SCD) Checklist Template

**Reference:** PRODUCT_DEVELOPMENT_CONTRACT_V3.md
**Phase:** 1 (CI Signal Rediscovery & Stabilization)
**Purpose:** Forensic topology mapping — observe and document, do NOT fix

---

## Instructions

Copy this template for each layer boundary pair. Fill in mechanically.
Do NOT fix anything during discovery. This is forensic work.

**Closed Signal Circuit:** INTENT → EMISSION → TRANSPORT → ADAPTER → CONSUMPTION → CONSEQUENCE

---

## 1. Boundary Lock

```yaml
boundary_pair: L{X}↔L{Y}
from_layer: L{X} — {Layer Name}
to_layer: L{Y} — {Layer Name}
direction: {unidirectional | bidirectional}
crossing_type: {invocation | data | event | side-effect}
```

---

## 2. Declared Intent

> What is the contract at this boundary? (Not what should be — what IS declared)

| Field | Value |
|-------|-------|
| Contract Document | {path or "NONE"} |
| Contract Version | {version or "UNDOCUMENTED"} |
| Intent Statement | {quoted or "IMPLICIT"} |
| Enforcement Level | {BLOCKING / ADVISORY / NONE} |

---

## 3. Expected Signals

> If the contract is honored, what signals MUST exist?

| Signal ID | Signal Name | Emitter (Layer) | Consumer (Layer) | Transport | Consequence |
|-----------|-------------|-----------------|------------------|-----------|-------------|
| EXP-{boundary}-001 | | L{X} | L{Y} | | |
| EXP-{boundary}-002 | | | | | |

---

## 4. Reality Inspection

> Look at the actual code. What signals ACTUALLY exist?

### 4.1 Emitter Audit (L{X} side)

| Location | What it emits | Explicit? | Consumed by? |
|----------|---------------|-----------|--------------|
| {file:line} | | YES/NO | {file:line or UNKNOWN} |

### 4.2 Consumer Audit (L{Y} side)

| Location | What it consumes | Source? | Fails if missing? |
|----------|------------------|---------|-------------------|
| {file:line} | | {file:line or UNKNOWN} | YES/NO |

### 4.3 Transport Audit

| Transport Type | Mechanism | Observable? | Documented? |
|----------------|-----------|-------------|-------------|
| {sync/async/event/db} | {specific mechanism} | YES/NO | YES/NO |

---

## 5. End-to-End Circuit Walk

> Trace one expected signal from intent to consequence.

```
SIGNAL: {signal name}

INTENT:
  → Declared at: {file:line or UNDECLARED}
  → Statement: {what it promises}

EMISSION:
  → Emitter: {file:line}
  → Mechanism: {how it emits}
  → Explicit: YES / NO

TRANSPORT:
  → Type: {sync call / async event / db write / etc.}
  → Observable: YES / NO
  → Failure Mode: {what happens if transport fails}

ADAPTER:
  → Location: {file:line or NONE}
  → Purpose: {translation / validation / none}

CONSUMPTION:
  → Consumer: {file:line or NONE}
  → Explicit: YES / NO
  → Dependency Declared: YES / NO

CONSEQUENCE:
  → What happens on success: {action}
  → What happens on failure: {action or SILENT}
  → Observable: YES / NO
```

---

## 6. Failure Classification

> For each gap found, classify the failure type.

| Gap ID | Gap Description | Classification | Severity |
|--------|-----------------|----------------|----------|
| GAP-{boundary}-001 | | | |

### Classification Codes

| Code | Meaning |
|------|---------|
| MISSING_EMITTER | Expected signal has no emitter code |
| MISSING_CONSUMER | Signal emitted but no consumer exists |
| IMPLICIT_SIGNAL | Signal exists but is not declared in any contract |
| BROKEN_CIRCUIT | Signal emitted, consumer exists, but transport fails |
| BYPASSED_BOUNDARY | L{X} directly accesses L{Y+2} without adapter |
| HUMAN_ONLY_SIGNAL | Signal requires human observation (no CI) |
| PHANTOM_SIGNAL | Signal documented but never emitted |
| ORPHAN_SIGNAL | Signal emitted but orphaned (no consumer, no effect) |

---

## 7. Risk Statement

> What is the governance risk of this boundary's current state?

```
RISK SUMMARY:
  - Circuit Status: {CLOSED / PARTIAL / BROKEN / MISSING}
  - Gap Count: {N}
  - Critical Gaps: {list}
  - Blocking for Phase 2: YES / NO
  - Human Action Required: YES / NO

RISK NARRATIVE:
  {1-2 sentences describing the risk}
```

---

## 8. Registry Entry

> Proposed entry for CI_SIGNAL_REGISTRY.md

```yaml
boundary: L{X}↔L{Y}
circuit_status: {CLOSED | PARTIAL | BROKEN | MISSING}
signals_expected: {count}
signals_found: {count}
gaps:
  - id: GAP-{boundary}-001
    type: {classification code}
    severity: {P0/P1/P2}
    description: {brief}
enforcement:
  ci_coverage: {YES | PARTIAL | NO}
  blocking_workflow: {workflow name or NONE}
  advisory_workflow: {workflow name or NONE}
phase_1_complete: {YES | NO}
phase_1_blocker: {description or NONE}
```

---

## 9. Hard Rules (Verification)

Check each rule. All must be YES to complete.

| Rule | Check | Status |
|------|-------|--------|
| Did I observe, not fix? | | YES / NO |
| Did I document what IS, not what SHOULD BE? | | YES / NO |
| Did I trace at least one full circuit? | | YES / NO |
| Did I classify all gaps found? | | YES / NO |
| Did I note human-only signals? | | YES / NO |
| Did I check both directions if bidirectional? | | YES / NO |

---

## 10. Completion Test

> Can you answer these questions from this document alone?

| Question | Can Answer? |
|----------|-------------|
| What signals cross this boundary? | YES / NO |
| Where are they emitted? | YES / NO |
| Where are they consumed? | YES / NO |
| What happens if any signal is missing? | YES / NO |
| Which gaps block Phase 2? | YES / NO |

**If any answer is NO → checklist is incomplete.**

---

## Changelog

| Date | Change |
|------|--------|
| {date} | Initial discovery for L{X}↔L{Y} |
