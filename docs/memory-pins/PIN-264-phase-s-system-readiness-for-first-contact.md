# PIN-264: Phase S — System Readiness for First Contact

**Status:** 📋 ACTIVE
**Created:** 2026-01-01
**Category:** Governance / Pre-Launch
**Milestone:** Phase S

---

## Summary

Pre-incident engineering phase. Build diagnostic capability before users arrive. Four tracks: Error Capture, Replay/Reproduction, Synthetic Traffic, Learning Loop.

---

## Details

# Phase-S: System Readiness for First Contact

**Objective:** Create learning signals before users arrive

> **Replace "observe users" with "observe the system observing itself"**

---

## Current State (Re-baselined 2026-01-01)

| Fact | Status |
|------|--------|
| Architecture | ✅ Correct |
| Governance | ✅ Enforced (L5→L4 CI blocking) |
| CI | ✅ Deterministic |
| Production Traffic | ⚠️ **Zero** |

**Implication:** Cannot rely on user behavior to discover failure modes, bottlenecks, or edge cases.

---

## Goal

When the **first bug / complaint / incident** occurs, you already have:
- ✅ Evidence
- ✅ Timeline  
- ✅ Root cause
- ✅ Prevention path

---

## Four Parallel Tracks

### TRACK 1 — Error & Incident Capture (P0)

**Goal:** Every failure leaves a forensic trail

#### 1.1 Unified Error Envelope (Non-negotiable)

Every error must emit:
```
error_id
timestamp
layer (L2/L4/L5)
component
correlation_id
decision_id (if any)
input_hash (not raw input)
error_class
severity
```

No stacktrace dumps as primary signal.

#### 1.2 Correlation IDs Everywhere

One request/workflow traceable across:
- API
- Domain engine
- Worker
- Decision emission

#### 1.3 Error Persistence (Not Just Logs)

- Append-only error store (DB or JSONL)
- Indexed by error_class + component
- Retained across deploys
- Becomes **incident memory**

---

### TRACK 2 — Replay & Reproduction (P0)

**Goal:** Any serious incident can be replayed deterministically

#### 2.1 Decision Snapshotting

For L4 engines:
- Store inputs (hashed or redacted)
- Store outputs (decisions)
- Store version hash of engine

Enables: "Given same inputs, would today's code behave the same?"

#### 2.2 Worker Replay Mode (Offline)

```bash
python replay_decision.py --decision-id <id>
```

- No live infra
- No API
- Pure deterministic replay
- Debug without traffic

---

### TRACK 3 — Synthetic Traffic & Chaos (P1)

**Goal:** Simulate users since they aren't here yet

#### 3.1 Synthetic Scenario Runner

Job that:
- Creates fake workflows
- Pushes through L2 → L4 → L5
- Uses real code paths (not mocks)

Run: on demand, nightly, before releases

#### 3.2 Fault Injection (Minimal)

Deliberately inject:
- Timeouts
- Malformed inputs
- Missing decisions
- Retries

Tests resilience, not correctness.

---

### TRACK 4 — Learning Loop & Prevention (P0)

**Goal:** Every incident → permanent system improvement

#### 4.1 Incident → Lesson → Prevention Pipeline

```
Incident Record
      ↓
Root Cause (human-written)
      ↓
Preventive Control
      ↓
Governance Update (rule / check / playbook)
```

If incident does NOT produce a check, rule, or playbook update → it will happen again.

#### 4.2 Session Playbook Evolution

SESSION_PLAYBOOK must:
- Reference known incident classes
- Include "what to check first"
- Include "what never to do again"

Experience → Institutional memory.

---

## What NOT to Focus On Now

| ❌ Skip | Reason |
|---------|--------|
| Feature polish | Downstream of observability |
| UX iteration | Need users first |
| Scaling infra | Premature |
| Performance tuning | No traffic to optimize |
| Multi-tenant complexity | Single-tenant first |

---

## Phase-S Exit Criteria

Phase ends when:
1. First real user issue occurs
2. You can diagnose it in **<15 minutes**
3. You can **replay** it
4. You can **prevent recurrence**

---

## Next Concrete Step

> **Design the Unified Error Envelope + Correlation ID standard**

Everything else builds on that.

---

## Reference

- PIN-263: Phase R (L5→L4 Structural Repair)
- PIN-240: Seven-Layer Model
- Session: Phase G → Phase S transition

---

## Related PINs

- [PIN-263](PIN-263-.md)
