# PIN-050: M10 Recovery Suggestion Engine - Complete

**Status:** COMPLETE
**Date:** 2025-12-08
**Milestone:** M10
**Depends on:** M8, M9

---

## Summary

M10 Recovery Suggestion Engine is now fully implemented. The system provides:
- Automatic recovery suggestion generation based on historical patterns
- Confidence scoring using weighted time-decay algorithm
- Human-in-the-loop approval workflow via CLI
- Full API integration with M9 failure matching system

---

## Components Implemented

### 1. Database Schema (`alembic/versions/017_create_recovery_candidates.py`)

**Tables:**
- `recovery_candidates` - Main table storing suggestions with confidence scores
- `recovery_candidates_audit` - Immutable audit trail for approval decisions

**Views:**
- `recovery_candidates_with_context` - Joins candidates with failure context

**Key Features:**
- Idempotent upserts via unique `failure_match_id`
- Occurrence counting for pattern learning
- CHECK constraints for confidence bounds (0.0-1.0)
- Partial index for pending candidates

### 2. Matcher Service (`app/services/recovery_matcher.py`)

**Confidence Scoring Algorithm:**
```python
# Time decay: weight(t) = exp(-lambda * age_days)
HALF_LIFE_DAYS = 30
LAMBDA = ln(2) / 30  # ~0.0231

# Confidence blending
confidence = ALPHA * score_weighted + (1 - ALPHA) * score_basic
# Where ALPHA = 0.7
```

**Confidence Levels:**
- `EXACT_MATCH_CONFIDENCE = 0.95` - Catalog match
- `NO_HISTORY_CONFIDENCE = 0.20` - Default when no history
- `MIN_CONFIDENCE_THRESHOLD = 0.10` - Minimum to persist

**Key Methods:**
- `suggest(request)` - Generate suggestion with confidence
- `get_candidates(status, limit, offset)` - List by status
- `approve_candidate(id, by, decision, note)` - Approve/reject

### 3. FastAPI Endpoints (`app/api/recovery.py`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/recovery/suggest` | POST | Generate recovery suggestion |
| `/api/v1/recovery/candidates` | GET | List candidates by status |
| `/api/v1/recovery/approve` | POST | Approve/reject candidate |
| `/api/v1/recovery/candidates/{id}` | DELETE | Revoke suggestion |
| `/api/v1/recovery/stats` | GET | Approval statistics |

### 4. CLI Commands (`cli/aos.py`)

```bash
# List pending candidates
aos recovery candidates --status pending

# Approve a candidate
aos recovery approve --id 5 --by operator_name --note "looks good"

# Reject a candidate
aos recovery approve --id 4 --by operator_name --note "not applicable" --reject

# View stats
aos recovery stats
```

### 5. Prometheus Metrics (`app/metrics.py`)

```python
recovery_suggestions_total      # Counter by source, decision
recovery_suggestions_latency    # Histogram of processing time
recovery_approvals_total        # Counter by decision
recovery_candidates_pending     # Gauge of pending count
```

---

## Acceptance Criteria Status

| # | Criteria | Status |
|---|----------|--------|
| AC1 | API suggests corrections for at least 5 catalog entries | PASS (7 suggestions generated) |
| AC2 | CLI can list + approve candidates | PASS |
| AC3 | Table populates with candidates | PASS |
| AC4 | Confidence scores vary across scenarios | PASS (6 distinct values: 0.20, 0.25, 0.33, 0.56, 0.95, 1.00) |

---

## Test Results

```
tests/test_recovery.py
├── TestConfidenceScoring (5 tests) .............. PASSED
├── TestErrorNormalization (3 tests) ............. PASSED
├── TestSuggestionGeneration (2 tests) ........... PASSED
├── TestAcceptanceCriteria (2 tests) ............. PASSED
└── TestCLI (2 tests) ............................ PASSED
```

---

## Integration Points

### Input: M9 Failure Matches
```python
POST /api/v1/recovery/suggest
{
    "failure_match_id": "uuid",
    "failure_payload": {
        "error_type": "TIMEOUT",
        "raw": "Connection timed out..."
    },
    "source": "worker"
}
```

### Output: Recovery Candidates
```json
{
    "suggested_recovery": "Implement retry with exponential backoff",
    "confidence": 0.85,
    "explain": {
        "method": "weighted_time_decay",
        "matches": 12,
        "occurrences": 15,
        "score_weighted": 0.89,
        "half_life_days": 30
    }
}
```

---

## Files Changed

```
backend/
├── alembic/versions/
│   └── 017_create_recovery_candidates.py  (NEW)
├── app/
│   ├── api/
│   │   └── recovery.py                    (NEW)
│   ├── services/
│   │   ├── __init__.py                    (NEW)
│   │   └── recovery_matcher.py            (NEW)
│   ├── main.py                            (MODIFIED - router added)
│   └── metrics.py                         (MODIFIED - M10 metrics)
├── cli/
│   └── aos.py                             (MODIFIED - recovery commands)
└── tests/
    └── test_recovery.py                   (NEW)
```

---

## Configuration

No new environment variables required. Uses existing:
- `DATABASE_URL` - PostgreSQL connection

---

## Next Steps

- M11: Skill Expansion
- M12: Beta Rollout
- M13: Console UI (optional - currently CLI-only as per spec)

---

## References

- PIN-033: M8-M14 Machine-Native Realignment
- M10 Blueprint: Recovery Suggestion Engine
- M9 PIN-049: Failure Persistence Complete
