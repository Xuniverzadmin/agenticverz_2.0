# PIN-241: Layer Violation Triage Strategy

**Status:** ACTIVE
**Created:** 2025-12-29
**Category:** Architecture / Layer Governance
**Related:** PIN-240 (Seven-Layer Mental Model)

---

## Context

After implementing the seven-layer model (PIN-240), tagging the repo, and creating `layer_validator.py`, the validator found **17 real violations** (L2 → L5 imports). This PIN captures the strategic response: **classify first, refactor later**.

---

## Three Hard Thresholds Crossed

### 1. Canonical Vertical Map
- Layers L1–L7 are **real**, not conceptual
- Files now self-declare their layer
- Products are **slices**, not owners of logic

> **You no longer need to "remember" the codebase — the codebase now explains itself.**

### 2. Architecture as Testable Fact
- `scripts/ops/layer_validator.py` is an **architectural referee**
- 17 violations found = validator works
- Violations are now **visible**, not silent

### 3. Clear Product Definition
> **Product = L1 + L2 + L3 only**

Everything else is shared substrate. No philosophical debates. No registry drift.

---

## The Critical Mental Shift

### Wrong Instinct
"Let me fix the 17 violations."

### Correct Instinct
**"Let me classify the 17 violations by *risk* and *intent*."**

Rushing to refactor loses value.

---

## Violation Triage Buckets

### Bucket A — Structural Smells (HIGH RISK)

**Criteria:**
- L2 → L5 direct imports
- Console API calling workers directly
- Async execution hidden behind product API

**Nature:** Architectural lies

**Action:** Must be fixed eventually. Design proper L3/L4 boundaries.

---

### Bucket B — Shortcut Violations (MEDIUM RISK)

**Criteria:**
- "Just for now" calls
- Test scaffolding leaks
- Temporary orchestration logic

**Nature:** Time debt, not conceptual debt

**Action:** Document, don't refactor yet.

---

### Bucket C — False Positives / Acceptable Bridges (LOW RISK)

**Criteria:**
- Monitoring hooks
- Logging
- Telemetry
- Read-only inspection paths

**Nature:** Allowed exceptions

**Action:** Whitelist in validator with justification.

---

## Refactor Safety Rule

> **No refactor may change runtime behavior while resolving layer violations.**

The system works. We're fixing **truthfulness**, not functionality.
This prevents "cleanup accidents."

---

## The Missing Layer Insight

The validator found L2 importing L5 directly. This means L4 isn't being used as an explicit boundary.

### Current (Wrong):
```
L2  ───▶  L5   ❌
```

### Target (Correct):
```
L2  ───▶  L3  ───▶  L4  ───▶  L5
```

### The Fix Is NOT "Remove the Import"

The fix is:
1. Introduce / strengthen **L3 adapters**
2. Move orchestration intent out of L2
3. Let L5 execute without knowing *who asked*

This preserves value.

---

## Session Playbook Invariant

Add to session discipline:

> If `layer_validator.py` reports a **new violation**, the session must STOP and ask:
> **"Which layer is missing?"**

Not "how to fix," but **why the shortcut exists**.

Future mistakes become *educational*, not destructive.

---

## Two-Axis Mental Map

### Axis 1 — Vertical (Truth)
```
L1 UI
L2 Product API
L3 Adapters
L4 Domain Engines
L5 Workers
L6 Platform
L7 Ops
```

### Axis 2 — Horizontal (Slices)
```
AI Console      → L1/L2/L3
Ops Console     → L1/L2/L3
Product Builder → L1/L2/L3
```

Everything below L3 is **not owned**, only *used*.

This makes the codebase feel *finite* again.

---

## Anti-Patterns (DO NOT)

| Anti-Pattern | Why It's Wrong |
|--------------|----------------|
| "Clean up" orphaned but valuable code | Loses signal |
| Rush to eliminate all 17 violations | Premature optimization |
| Relax validator to get green builds | Hides problems |
| Let product concerns leak into L4+ | Breaks substrate |

---

## What The 17 Violations Mean

The 17 L2 → L5 violations are **signals**, not failures:

1. They indicate where L3/L4 boundaries are weak
2. They show where shortcuts were taken
3. They reveal the actual dependency graph
4. They provide a refactor roadmap

**The violations are educational, not shameful.**

---

## Next Steps (Ordered)

1. **Classify** each of the 17 violations into Bucket A/B/C
2. **Document** Bucket B shortcuts with "why" notes
3. **Whitelist** Bucket C exceptions in validator
4. **Design** L3 adapters for Bucket A violations
5. **Refactor** Bucket A violations (behavior-preserving)

---

## Validator Whitelist Format

For Bucket C exceptions, add to `layer_validator.py`:

```python
# Allowed exceptions with justification
ALLOWED_VIOLATIONS = {
    ("backend/app/api/metrics.py", "from app.worker.telemetry"):
        "Read-only metrics collection, no execution trigger",
    # Add more with explicit justification
}
```

Every exception must have a **documented reason**.

---

## Summary

| Achievement | Status |
|-------------|--------|
| Canonical vertical map | COMPLETE |
| Architecture as testable fact | COMPLETE |
| Clear product definition | COMPLETE |
| Violation triage framework | DEFINED |
| Refactor roadmap | PENDING (classification first) |

**Bottom Line:** The architecture is *recoverable and scalable*. The 17 violations are a roadmap, not a crisis.
