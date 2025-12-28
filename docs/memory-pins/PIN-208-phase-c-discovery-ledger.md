# PIN-208: Phase C Discovery Ledger

**Status:** COMPLETE
**Date:** 2025-12-27
**Category:** Phase C / Observability
**Phase:** C

---

## Purpose

Implement a passive, append-only observation system that records interesting signals without enforcing visibility or requiring approval.

**Truth Anchor:**
> Discovery Ledger records curiosity, not decisions.
> Decisions come later, deliberately.

---

## Problem Statement

Phase B established truth-grade data (EXISTS state). But:
- DPCC verifies *what should be visible is visible*
- CSEG verifies *forbidden consoles don't see data*

Neither answers: **"What should be visible in the first place?"**

Premature answer: Build approval workflows and promotion systems.
**Correct answer:** Build a passive observation log. Decide later.

---

## Solution: Discovery Ledger

A passive, append-only system that:

| Does | Does NOT |
|------|----------|
| Auto-detect candidate signals | Enforce visibility |
| Store why they might matter | Require approval |
| Aggregate over time | Trigger UI changes |
| Allow founder/dev to inspect | Affect customer behavior |
| Record curiosity | Block progress |

---

## Implementation

### 1. Database Table

**Migration:** `059_pc_discovery_ledger.py`

```sql
CREATE TABLE discovery_ledger (
    id              UUID PRIMARY KEY,
    artifact        TEXT NOT NULL,      -- e.g. prediction_events
    field           TEXT,               -- e.g. confidence (nullable)
    signal_type     TEXT NOT NULL,      -- e.g. high_operator_access
    evidence        JSONB NOT NULL,     -- counts, queries, etc.
    confidence      NUMERIC(3,2),       -- optional 0.00-1.00
    detected_by     TEXT NOT NULL,      -- subsystem name
    phase           TEXT NOT NULL,      -- B / C / D
    environment     TEXT NOT NULL,      -- local / staging / prod
    first_seen_at   TIMESTAMPTZ,
    last_seen_at    TIMESTAMPTZ,
    seen_count      INTEGER DEFAULT 1,
    status          TEXT DEFAULT 'observed'  -- observed/ignored/promoted
);
```

### 2. Signal Recording

**Module:** `app/discovery/ledger.py`

```python
from app.discovery import emit_signal

emit_signal(
    artifact="prediction_events",
    signal_type="high_operator_access",
    evidence={"count_7d": 21, "distinct_sessions": 5},
    detected_by="api_access_monitor",
    confidence=0.8
)
```

Signals are **aggregated**: same (artifact, field, signal_type) updates `seen_count`.

### 3. API Endpoint

**Route:** `GET /api/v1/discovery`

Founder Console only. Read-only. Sorted by frequency.

```json
{
  "items": [
    {
      "artifact": "prediction_events",
      "field": null,
      "signal_type": "high_operator_access",
      "seen_count": 21,
      "last_seen_at": "2025-12-27T10:22:00Z"
    }
  ],
  "total": 1,
  "note": "Discovery Ledger records curiosity, not decisions."
}
```

---

## Signal Classes

| Class | Description | Source |
|-------|-------------|--------|
| `high_operator_access` | Humans keep looking at this | API access logs |
| `dominant_field` | This field keeps showing up | pattern_feedback, predictions |
| `frequent_join_target` | This relationship is important | SQL logs, debug queries |
| `threshold_crossing` | Signal is strong enough | Predictions, cost analysis |

---

## Relationship to DPCC / CSEG

```
Data exists (Phase B)
    ↓
Discovery Ledger records signals (automated, Phase C)
    ↓
Human notices pattern (optional)
    ↓
Human creates visibility contract (manual)
    ↓
DPCC / CSEG enforce propagation (automated)
```

**Key:** DPCC/CSEG only apply AFTER manual visibility contract creation.
Discovery alone does NOT trigger enforcement.

---

## Files Created/Modified

| File | Purpose |
|------|---------|
| `backend/alembic/versions/059_pc_discovery_ledger.py` | Migration |
| `backend/app/discovery/__init__.py` | Module init |
| `backend/app/discovery/ledger.py` | Signal recording helpers |
| `backend/app/api/discovery.py` | API endpoint |
| `backend/app/main.py` | Router registration |
| `docs/contracts/visibility_lifecycle.yaml` | Simplified to DL model |

---

## Phase C Acceptance Criteria

- [x] Discovery Ledger table exists
- [x] Signal emission works (aggregates correctly)
- [x] API endpoint returns signals
- [x] No enforcement on discovery alone
- [x] DPCC/CSEG unchanged (require manual visibility contract)
- [x] SESSION_PLAYBOOK.yaml updated with discovery_ledger.yaml
- [x] discovery_ledger.yaml contract created
- [x] DPC/PLC checks integrated in visibility_validator.py
- [x] Split-brain DB fix (all scripts use explicit DATABASE_URL)
- [x] All 6 artifacts have discovery signals in Neon

**Explicitly NOT required:**
- Approval workflows
- Automatic promotion
- Customer-facing changes

---

## Updates (2025-12-27)

### Split-Brain DB Fix

Fixed critical issue where DPC/PLC checks were importing from `app.db` instead of using the validator's own `get_database_url()`. This caused potential split-brain where validator checked local DB but backend used Neon.

**Fix:** Both DPC and PLC now use psycopg2 with the validator's `get_database_url()`:

```python
# Uses same DB as visibility_validator (no split-brain)
import psycopg2
database_url = get_database_url()
conn = psycopg2.connect(database_url)
```

### Discovery Signals Emitted

All 6 visibility contract artifacts now have discovery signals in Neon:

| Artifact | Signal Type | Status | Confidence |
|----------|-------------|--------|------------|
| pattern_feedback | high_operator_access | observed | 0.85 |
| policy_proposals | high_operator_access | observed | 0.85 |
| policy_versions | frequent_join_target | observed | 0.80 |
| prediction_events | high_operator_access | observed | 0.90 |
| worker_runs | high_operator_access | observed | 0.95 |
| traces | high_operator_access | observed | 0.95 |

### Validator Checks

- **DPC (Discovery Presence Check):** PASS for all 6 artifacts
- **PLC (Promotion Legitimacy Check):** WARNING (status=observed, not promoted)

This is correct Phase C behavior - signals are discovered but not yet promoted.

### Contracts Wired

| Contract | Purpose |
|----------|---------|
| `docs/contracts/discovery_ledger.yaml` | Signal recording rules, promotion rules |
| `docs/playbooks/SESSION_PLAYBOOK.yaml` | Mandatory load at session start |
| `docs/contracts/visibility_lifecycle.yaml` | DPC/PLC promotion rules added |

---

## Phase C Core Principle: Listen, Don't Act

**Truth Anchor:**
> Phase C is for listening, not acting.
> Acting too early destroys signal.

### Why Listening Matters

1. **Signal Quality:** Incomplete data leads to wrong conclusions
2. **Pattern Emergence:** True patterns reveal themselves over time
3. **Premature Enforcement:** Blocks legitimate behavior before understanding it
4. **Information Destruction:** Acting on noise removes the signal

### Phase C Behavior

| System | Behavior | Rationale |
|--------|----------|-----------|
| Discovery Ledger | Records passively | Curiosity, not decisions |
| DPC Check | Warns, doesn't block | Observe what's missing |
| PLC Check | Warns, doesn't block | Know promotion gaps |
| DPCC | Blocks code changes | Code is harder to undo |
| CSEG | Blocks scope expansion | Scope creep is invisible |

### The Phase C → D Transition

Phase D upgrades warnings to blockers **only after**:
- Sufficient signal has accumulated
- Patterns have been observed
- Human review has occurred
- Visibility contracts are complete

**Rule:** Don't skip listening. The value is in the observation.

---

## Verification

```bash
# Emit signals (from backend/)
DATABASE_URL="..." python3 -c "
from app.discovery.ledger import emit_signal
emit_signal(artifact='prediction_events', signal_type='high_operator_access', ...)
"

# Query signals via API
curl http://localhost:8000/api/v1/discovery

# Run validator with discovery checks
DATABASE_URL="..." python3 scripts/ops/visibility_validator.py --check-all --phase C
```

---

## Related Documents

| Document | Location |
|----------|----------|
| Visibility Contract | `docs/contracts/visibility_contract.yaml` |
| Visibility Lifecycle | `docs/contracts/visibility_lifecycle.yaml` |
| Console Truth Model | `docs/contracts/CONSOLE_TRUTH_MODEL.md` |
| Session Playbook | `docs/playbooks/SESSION_PLAYBOOK.yaml` |
| Database Contract | `docs/contracts/database_contract.yaml` |
| PIN-207 | Phase A & B Re-Run with VCL Gates |
| PIN-209 | Claude Assumption Elimination (guardrails) |

---

*Created: 2025-12-27*
*Phase: C*
*Reference: Phase C Discovery Ledger Design*
