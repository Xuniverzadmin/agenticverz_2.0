# PIN-222: C2 Implementation Specification

**Status:** SPECIFICATION (Ready for Implementation)
**Created:** 2025-12-28
**Phase:** C2 (Prediction)
**Prerequisites:** PIN-220 APPROVED, PIN-221 ACTIVE
**Playbook Reference:** `docs/playbooks/SESSION_PLAYBOOK.yaml` v1.2

---

## Purpose

This PIN provides the **implementation specification** for C2 Prediction Plane.

Contains:
1. Minimal data schema
2. Executable test cases (P1-P6 compliant)
3. CI guardrails

**Rule:** *Boringly small. Anything "flexible" here becomes authority later.*

---

## Part 1: Minimal C2 Data Schema

### Table: `prediction_events`

**Purpose:** Persist advisory-only predictions with guaranteed delete safety, replay blindness, and expiry.

```sql
CREATE TABLE prediction_events (
    prediction_id      UUID PRIMARY KEY,
    subject_type       TEXT NOT NULL,   -- tenant | incident | workflow
    subject_id         TEXT NOT NULL,   -- string reference, NO FK
    prediction_type    TEXT NOT NULL,   -- incident_risk | cost_spike | policy_drift
    confidence_score   REAL NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    advisory           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at         TIMESTAMPTZ NOT NULL,
    metadata           JSONB
);

-- Hard constraint: advisory MUST be TRUE
ALTER TABLE prediction_events
ADD CONSTRAINT chk_prediction_advisory
CHECK (advisory = TRUE);

-- Index for expiry cleanup
CREATE INDEX idx_prediction_events_expires_at ON prediction_events(expires_at);

-- Index for subject lookup
CREATE INDEX idx_prediction_events_subject ON prediction_events(subject_type, subject_id);
```

### Explicitly Forbidden

| Forbidden | Reason |
|-----------|--------|
| Foreign keys to truth tables | Creates coupling |
| Nullable `expires_at` | Predictions must expire |
| Status fields (active, resolved) | Implies lifecycle authority |
| Any enforcement-implying column | Violates I-C2-2 |

---

## Expiry & Retention Rules

```yaml
expiry_policy:
  default_ttl: 30 minutes
  max_ttl: 24 hours
  renewal_allowed: false
  manual_delete_allowed: true
```

### Invariants

- Predictions **must expire**
- Expiry must not trigger side effects
- Deletion must be safe and silent

> If predictions accumulate indefinitely → **C2 FAIL**

---

## Replay Rule (Critical)

> Replay **must not read** `prediction_events`
> Replay **must not emit** `prediction_events`

This is the single most important C2 safety rule.

---

## Part 2: Executable C2 Test Cases

Each test follows P1-P6 principles.

---

### C2-T1: Incident Risk Prediction (S1)

**Test Intent:** Verify false positives, false negatives, and outage safety.

**Execution (P1/P2):**
- Run on **Neon**
- Claude executes real LLM + DB
- Prediction job runs once

**Action:**
1. Generate telemetry for tenant X
2. Insert prediction:
   - `prediction_type = incident_risk`
   - `confidence_score = 0.82`
   - `advisory = TRUE`
   - `expires_at = now() + interval '30 minutes'`
3. Do **nothing else**

**Assertions:**
- [ ] No incident created
- [ ] No control-path change
- [ ] Prediction visible only via O4 API
- [ ] Deleting prediction changes nothing
- [ ] Replay hash identical before/after

**Failure Injection:**
- Stop prediction job
- Verify incidents still trigger normally (FM-C2-3)

---

### C2-T2: Cost Spike Prediction (S2)

**Test Intent:** Verify Redis loss and semantic restraint.

**Execution (P1/P2):**
- Real Neon DB
- Redis enabled, then disabled

**Action:**
1. Generate cost telemetry
2. Store rolling aggregates in Redis
3. Create `cost_spike` prediction

**Assertions:**
- [ ] Prediction disappears if Redis wiped
- [ ] System behavior unchanged
- [ ] No throttling triggered
- [ ] No retry logic changes

**Critical Semantic Check:**
- [ ] UI wording contains "Advisory"
- [ ] No "will exceed", "will breach", "confirmed"

---

### C2-T3: Policy Drift Prediction (S3)

**Test Intent:** Verify delete safety and semantic leak prevention.

**Action:**
1. Create workflows similar to historical violations
2. Generate `policy_drift` prediction

**Assertions:**
- [ ] No policy enforcement
- [ ] No incident creation
- [ ] Prediction expiry removes it silently
- [ ] Replay output identical before/after deletion

**Semantic Check:**
- [ ] Prediction not visible in O1/O2/O3
- [ ] O4 labeling explicit and unavoidable

---

### P6 Fallback Rule

Repeat **one** test locally only if:
- Neon cost spike
- Infrastructure constraint

Local results are **supplementary only**.

---

## Part 3: C2 CI Guardrails

These prevent regression mechanically.

---

### Guardrail 1: Import Isolation (Hard Block)

**Rule:** Prediction code must never be imported into control, execution, or replay paths.

**CI Check:**
```bash
# Fail if prediction imports found in forbidden paths
grep -rE "from app\.predictions|import.*predictions" \
    backend/app/worker/runtime \
    backend/app/replay \
    backend/app/control && exit 1
echo "GR-1 PASS: No prediction imports in control/execution/replay"
```

**Enforcement:** BLOCKER

---

### Guardrail 2: Advisory Enforcement

**Rule:** All predictions must have `advisory = TRUE`.

**CI Check:**
```bash
# Verify constraint exists in migration
grep -q "chk_prediction_advisory" backend/alembic/versions/*.py || exit 1

# Verify no code sets advisory=FALSE
grep -rE "advisory\s*=\s*False" backend/app/predictions && exit 1
echo "GR-2 PASS: Advisory constraint enforced"
```

**Enforcement:** BLOCKER

---

### Guardrail 3: Replay Blindness

**Rule:** Replay must not reference predictions.

**CI Check:**
```bash
# Fail if replay references prediction_events
grep -rE "prediction_events|from app\.predictions" \
    backend/app/replay && exit 1
echo "GR-3 PASS: Replay does not reference predictions"
```

**Enforcement:** BLOCKER

---

### Guardrail 4: Semantic Lint (Human-Aware)

**Rule:** Prediction UI must not use authoritative language.

**CI Check (best-effort):**
```bash
# Scan for authoritative language in prediction-related UI
grep -riE "confirmed|will fail|guaranteed|detected root cause|certain" \
    frontend/src/**/prediction* \
    frontend/src/**/advisory* && {
    echo "GR-4 WARNING: Authoritative language detected - human review required"
    exit 0  # Warning, not blocker
}
echo "GR-4 PASS: No authoritative language detected"
```

**Enforcement:** WARNING (human must approve)

---

### Guardrail 5: Redis Authority Protection

**Rule:** Redis loss must not change behavior.

**CI Simulation:**
```bash
# Run tests with Redis disabled
REDIS_URL="" pytest tests/c2/ -v
echo "GR-5 PASS: Tests pass without Redis"
```

**Enforcement:** BLOCKER

---

## Future Creep Prevention

These WILL creep in if not guarded:

| Creep Pattern | Prevention |
|---------------|------------|
| Prediction renewal loops | `renewal_allowed: false` |
| Confidence inflation | UI labels confidence as "informational only" |
| Redis backpressure hacks | GR-5 Redis simulation |
| UI proximity creep | GR-4 semantic lint + O4-only rule |
| "Temporary" fields | Schema explicitly forbidden list |

---

## Implementation Order (Recommended)

1. **Schema + CI** — Foundation, no logic yet
2. **One test (T1)** — Prove safety end-to-end
3. **O4 UI contract** — Define labels, placement, wording
4. **Remaining tests (T2, T3)** — Complete coverage

---

## Acceptance Criteria

C2 implementation is **valid** only if:

- [ ] Schema deployed on Neon
- [ ] All 5 CI guardrails passing
- [ ] T1 executed on Neon with all assertions passing
- [ ] Replay hash unchanged after prediction CRUD
- [ ] Human confirms O4 advisory labeling

---

## Truth Anchor

> Predictions that influence execution are not predictions — they are hidden control paths.
>
> C2 must be advisory, or it corrupts the truth-grade guarantees of C1.

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-28 | PIN-222 created with schema, 3 test cases, 5 CI guardrails |
