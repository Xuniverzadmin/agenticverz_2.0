# PIN-131: M25 Real Evidence Trail Capture Protocol

**Status:** ACTIVE
**Created:** 2025-12-23
**Category:** Governance / Evidence
**Milestone:** M25 Learning Proof - Validation Phase

---

## Purpose

Before M26 coding begins, we must capture **one real closed-loop proof**.

Not simulated. Not demo data. Real evidence from the system.

This becomes:
- Internal proof that graduation works
- Demo backbone for external presentations
- Regression test narrative

---

## The Canonical Story

We need to capture ONE complete narrative:

```
1. Real incident occurs
   ↓
2. Pattern is created/matched
   ↓
3. Recovery is suggested and applied
   ↓
4. Policy is generated and enters shadow
   ↓
5. Policy is promoted to active
   ↓
6. Second similar incident is PREVENTED
   ↓
7. Graduation engine reflects improvement
```

---

## Evidence Artifacts to Capture

### Stage 1: Incident Creation

| Artifact | Value | Notes |
|----------|-------|-------|
| incident_id | `inc_real_XXXXX` | Must NOT have `sim_` prefix |
| tenant_id | Real tenant | Not `tenant_demo` |
| created_at | Timestamp | |
| severity | Actual severity | |
| title | Real incident title | |

**Capture command:**
```sql
SELECT id, tenant_id, title, severity, created_at
FROM incidents
WHERE id = '<incident_id>'
```

### Stage 2: Pattern Matching

| Artifact | Value | Notes |
|----------|-------|-------|
| pattern_id | `pat_XXXXX` | |
| confidence_band | strong_match/weak_match/novel | |
| matched_at | Timestamp | |

**Capture command:**
```sql
SELECT * FROM loop_events
WHERE incident_id = '<incident_id>'
AND stage = 'pattern_matched'
```

### Stage 3: Recovery Application

| Artifact | Value | Notes |
|----------|-------|-------|
| recovery_id | `rec_XXXXX` | |
| status | applied | Must be applied, not rejected |
| applied_at | Timestamp | |

**Capture command:**
```sql
SELECT * FROM recovery_candidates
WHERE source_incident_id = '<incident_id>'
AND status = 'applied'
```

### Stage 4: Policy Generation

| Artifact | Value | Notes |
|----------|-------|-------|
| policy_id | `pol_XXXXX` | |
| source_type | recovery | Born from failure |
| mode | shadow → active | Track promotion |
| created_at | Timestamp | |

**Capture command:**
```sql
SELECT id, source_type, mode, created_at
FROM policy_rules
WHERE source_incident_id = '<incident_id>'
```

### Stage 5: Prevention Event

| Artifact | Value | Notes |
|----------|-------|-------|
| prevention_id | `prev_XXXXX` | NOT `prev_sim_` |
| original_incident_id | From Stage 1 | |
| blocked_incident_id | New incident | |
| is_simulated | false | CRITICAL |
| created_at | Timestamp | |

**Capture command:**
```sql
SELECT * FROM prevention_records
WHERE original_incident_id = '<incident_id>'
AND is_simulated = false
```

### Stage 6: Graduation Delta

**Before evidence:**
```sql
SELECT level, gates_json, computed_at
FROM graduation_history
ORDER BY computed_at DESC
LIMIT 1
```

**After evidence:**
```sql
-- Trigger re-evaluation
POST /integration/graduation/re-evaluate

-- Capture new state
SELECT level, gates_json, computed_at
FROM graduation_history
ORDER BY computed_at DESC
LIMIT 1
```

---

## Verification Checklist

Before declaring evidence trail complete:

- [ ] All incident IDs are real (no `sim_` prefix)
- [ ] All records have `is_simulated = false`
- [ ] Timeline spans at least 24 hours (realistic)
- [ ] Prevention event links to original incident
- [ ] Graduation history shows level change
- [ ] Gate 1 (prevention) shows as PASSED

---

## Evidence Trail JSON Format

Capture all artifacts in this format:

```json
{
  "evidence_trail_id": "trail_XXXXX",
  "captured_at": "2025-12-XX",
  "is_simulated": false,

  "stage_1_incident": {
    "incident_id": "inc_XXXXX",
    "tenant_id": "tenant_XXXXX",
    "title": "...",
    "severity": 3,
    "created_at": "..."
  },

  "stage_2_pattern": {
    "pattern_id": "pat_XXXXX",
    "confidence_band": "strong_match",
    "matched_at": "..."
  },

  "stage_3_recovery": {
    "recovery_id": "rec_XXXXX",
    "status": "applied",
    "applied_at": "..."
  },

  "stage_4_policy": {
    "policy_id": "pol_XXXXX",
    "mode": "active",
    "promoted_at": "..."
  },

  "stage_5_prevention": {
    "prevention_id": "prev_XXXXX",
    "blocked_incident_id": "inc_XXXXX",
    "is_simulated": false,
    "created_at": "..."
  },

  "stage_6_graduation": {
    "before": {
      "level": "alpha",
      "gate1_passed": false
    },
    "after": {
      "level": "beta",
      "gate1_passed": true
    },
    "delta": {
      "level_change": "alpha → beta",
      "gates_passed_change": "0 → 1"
    }
  }
}
```

---

## Capture Script

Run this to capture evidence trail:

```bash
# Set environment
export DATABASE_URL="postgresql://..."
export EVIDENCE_INCIDENT_ID="inc_XXXXX"

# Run capture
python scripts/ops/m25_capture_evidence_trail.py \
  --incident-id $EVIDENCE_INCIDENT_ID \
  --output evidence_trail.json
```

---

## What This Proves

When we have this evidence trail, we can say:

1. **"The system learned from failure"** - Policy was born from incident
2. **"The learning prevented recurrence"** - Prevention event exists
3. **"Graduation reflects reality"** - Level changed based on evidence
4. **"The loop is closed"** - Full cycle is documented

This is not marketing. This is proof.

---

## Timeline

| Step | Due | Status |
|------|-----|--------|
| Create capture script | 2025-12-24 | [ ] |
| Identify real incident for trail | 2025-12-24 | [ ] |
| Wait for prevention event | Depends on traffic | [ ] |
| Capture full trail | After prevention | [ ] |
| Validate graduation delta | After capture | [ ] |

---

## Failure Modes

If we cannot capture real evidence:

1. **No incidents occurring** - Need to onboard real workload
2. **Policies not generating** - Check loop dispatcher
3. **Prevention not triggering** - Check pattern matching threshold
4. **Graduation not updating** - Check evaluator job

Each failure mode has diagnostic steps - this is data, not failure.

---

## Related PINs

- PIN-130: M25 Code Freeze Declaration
- PIN-129: M25 Pillar Integration Blueprint
