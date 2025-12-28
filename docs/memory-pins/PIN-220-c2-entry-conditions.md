# PIN-220: C2 Prediction Plane — Entry Conditions

**Status:** APPROVED (Entry conditions approved 2025-12-28)
**Created:** 2025-12-28
**Phase:** C2 (Prediction)
**Prerequisite:** C1 CERTIFIED (PIN-212)
**Playbook Reference:** `docs/playbooks/SESSION_PLAYBOOK.yaml` v1.2

---

## Purpose

This PIN defines the **entry conditions** for Phase C2 (Prediction Plane).

This is a **permit to begin design**, not a design document.

C2 cannot begin until:
1. All entry conditions are satisfied
2. Human explicitly says: **"C2 entry conditions approved"**

---

## What C2 IS

C2 is the **Prediction Plane** — the layer that provides advisory predictions about agent behavior, cost, and outcomes.

Key characteristics:
- **Advisory only** — predictions inform, never enforce
- **Labeled** — all predictions carry explicit `is_advisory: true` labels
- **Persisted** — predictions are stored in Neon (not Redis)
- **Observable** — predictions are visible through O1-O4 surfaces

---

## What C2 Is NOT

C2 is **not**:
- Enforcement (that's truth, not prediction)
- Control path (predictions cannot gate execution)
- Authoritative (predictions are always advisory)
- Redis-dependent (Redis accelerates, never stores truth)

---

## Entry Conditions (ALL REQUIRED)

### EC-1: C1 Must Be Certified

| Condition | Status |
|-----------|--------|
| C1 telemetry plane certified | YES (PIN-212) |
| C1 CI enforcement active | YES |
| No open C1 regressions | VERIFY |

### EC-2: Playbook v1.2 Must Be Active

| Condition | Status |
|-----------|--------|
| SESSION_PLAYBOOK.yaml v1.2 deployed | YES |
| Testing principles (P1-P6) documented | YES |
| Infrastructure authority map documented | YES |
| Phase transition rules documented | YES |

### EC-3: Human Approval Required

| Condition | Status |
|-----------|--------|
| Human explicitly approves C2 entry | PENDING |
| Explicit phrase: "C2 entry conditions approved" | PENDING |

---

## C2 Allowed Actions

Once entry conditions are approved, C2 may:

| Action | Constraint |
|--------|------------|
| Create prediction tables in Neon | Must include `is_advisory: true` field |
| Create prediction endpoints | Must return `advisory: true` in response |
| Use Redis for acceleration | Redis loss must not change behavior |
| Surface predictions in UI | Must use advisory language (e.g., "System suggests...") |

---

## C2 Instant Failures

The following actions **immediately fail C2** and require restart:

| Action | Reason |
|--------|--------|
| Prediction influences execution | Violates advisory-only constraint |
| Redis becomes truth store | Violates infrastructure authority |
| Prediction lacks `is_advisory` label | Violates labeling requirement |
| UI implies prediction is authoritative | Violates semantic honesty |
| Testing bypasses Neon | Violates P1-P6 principles |

---

## C2 Verification Requirements

Before C2 can be marked CERTIFIED:

| Verification | Method |
|--------------|--------|
| Real scenario tests on Neon | P1, P2 |
| Full data propagation | P3 |
| O-level visibility (O1-O4) | P4 |
| Human semantic verification | P5 |

---

## Phase Transition: C2 → C3

C3 (Optimization) entry conditions will be defined in a future PIN.

C3 cannot begin until C2 is CERTIFIED.

---

## Playbook Reference

All constraints in this PIN derive from:

```yaml
# docs/playbooks/SESSION_PLAYBOOK.yaml v1.2

phase_transitions:
  C1_to_C2:
    status: LOCKED
    required_artifacts:
      - PIN-220 (C2 Entry Conditions)
    required_verification:
      - Real scenario tests on Neon
      - Propagation verification (modules + O-levels)
      - Human semantic verification
    explicit_unlock_phrase: "C2 entry conditions approved"
```

---

## Unlock Protocol

To unlock C2:

1. Verify all EC-1 conditions (C1 certified, no regressions)
2. Verify all EC-2 conditions (playbook v1.2 active)
3. Human says: **"C2 entry conditions approved"**
4. Update this PIN status to `APPROVED`
5. Update `system_state.current_stage` to `C2_PREDICTION`
6. Update `system_state.stages.C2_PREDICTION` to `ACTIVE`

---

## Truth Anchor

> Predictions that influence execution are not predictions — they are hidden control paths.
>
> C2 must be advisory, or it corrupts the truth-grade guarantees of C1.

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-28 | **APPROVED** — Human said "C2 entry conditions approved". C2 now ACTIVE. |
| 2025-12-28 | PIN-220 created with entry conditions |
