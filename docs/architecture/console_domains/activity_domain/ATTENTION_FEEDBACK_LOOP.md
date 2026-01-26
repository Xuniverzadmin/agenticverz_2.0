# Attention Feedback Loop Architecture

**Status:** IMPLEMENTED
**Version:** 1.0
**Effective:** 2026-01-19
**Reference:** ACTIVITY_DOMAIN_CONTRACT.md Section 21-22

---

## Overview

The Attention Feedback Loop provides operator acknowledge/suppress controls for Activity signals using the existing `audit_ledger` infrastructure. No new tables are created.

**Design Principles:**
1. Signals remain projections — feedback is overlay metadata
2. Uses existing audit_ledger — append-only, immutable
3. Time-bound suppression only — no permanent silencing
4. Acknowledgment = responsibility, not hiding — dampens rank, doesn't remove
5. Tenant-scoped suppression — applies to tenant, actor is informational
6. Canonical fingerprint derivation — always from backend projection, never client input

---

## Critical Invariants

| Invariant | Description | Status |
|-----------|-------------|--------|
| **SIGNAL-ID-001** | Signal identity derived from backend projection, never client input | LOCKED |
| **ATTN-DAMP-001** | Acknowledgement dampening is idempotent (apply once, 0.6x) | FROZEN |
| **AUDIT-SIGNAL-CTX-001** | signal_context fields are fixed and versioned | ENFORCED |
| **SIGNAL-SCOPE-001** | Suppression applies tenant-wide, actor for accountability | ENFORCED |
| **SIGNAL-SUPPRESS-001** | Suppression is temporary (15-1440 minutes) | ENFORCED |
| **SIGNAL-ACK-001** | Acknowledgement records responsibility, doesn't hide | ENFORCED |
| **SIGNAL-FEEDBACK-001** | Feedback doesn't alter run state or policy evaluation | ENFORCED |

---

## Architecture

### Layer Structure

```
┌─────────────────────────────────────────────────────────────┐
│ L2 — Product APIs                                           │
│   activity.py                                               │
│   POST /signals/{fingerprint}/ack                           │
│   POST /signals/{fingerprint}/suppress                      │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ L4 — Domain Engines                                         │
│   signal_feedback_service.py  (feedback operations)         │
│   signal_identity.py          (fingerprint computation)     │
│   attention_ranking_service.py (dampening + filtering)      │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ L6 — Platform Substrate                                     │
│   audit_ledger table (SIGNAL entity type)                   │
│   v_runs_o2 view (signal projection source)                 │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. Client calls POST /signals/{fingerprint}/ack or /suppress
                           │
2. API validates signal exists via v_runs_o2
                           │
3. Server computes canonical fingerprint (SIGNAL-ID-001)
                           │
4. Feedback written to audit_ledger (SIGNAL entity)
                           │
5. GET /signals or /attention-queue queries join audit_ledger
                           │
6. Suppressed signals filtered from attention queue
   Acknowledged signals receive 0.6x dampening
```

---

## Signal Fingerprint

**Format:** `sig-{sha256[:16]}`

**Derivation (SIGNAL-ID-001):**
```python
raw = f"{run_id}:{signal_type}:{risk_type}:{evaluation_outcome}"
fingerprint = f"sig-{hashlib.sha256(raw.encode()).hexdigest()[:16]}"
```

**Module:** `backend/app/services/activity/signal_identity.py`

**Critical Rule:** Fingerprint is ALWAYS derived from backend projection row, NEVER from client-supplied payload.

---

## Audit Ledger Schema

### Entity Type
```python
class AuditEntityType(str, Enum):
    SIGNAL = "SIGNAL"  # NEW
```

### Event Types
```python
class AuditEventType(str, Enum):
    SIGNAL_ACKNOWLEDGED = "SignalAcknowledged"  # NEW
    SIGNAL_SUPPRESSED = "SignalSuppressed"      # NEW
```

### Signal Context (v1.0)
```python
class SignalContext(TypedDict):
    run_id: str
    signal_type: str           # COST_RISK, TIME_RISK, etc.
    risk_type: str             # COST, TIME, TOKENS, RATE
    evaluation_outcome: str    # BREACH, NEAR_THRESHOLD, OK
    policy_id: Optional[str]   # Governing policy if any
    schema_version: str        # "1.0"
```

---

## Attention Queue Dampening

**Constant:** `ACK_DAMPENER = 0.6` (FROZEN)

**Logic (ATTN-DAMP-001):**
```python
# Idempotent — apply ONCE, not compound
if feedback.event_type == 'SignalAcknowledged':
    effective_score = base_score * 0.6
else:
    effective_score = base_score
```

**Sorting:** Queue is re-sorted by `effective_attention_score` after dampening.

---

## Suppression Behavior

**Duration Constraints (SIGNAL-SUPPRESS-001):**
- Minimum: 15 minutes
- Maximum: 1440 minutes (24 hours)
- No permanent suppression allowed

**Filtering Logic:**
```sql
WHERE (sf.suppress_until IS NULL OR sf.suppress_until < NOW())
```

**After Expiry:** Signal automatically reappears if still active (no manual action needed).

---

## API Endpoints

### POST `/api/v1/activity/signals/{signal_fingerprint}/ack`

**Request:**
```json
{
  "run_id": "run-abc",
  "signal_type": "COST_RISK",
  "risk_type": "COST",
  "comment": "Acknowledged"
}
```

**Response (200):**
```json
{
  "signal_fingerprint": "sig-a1b2c3d4e5f6g7h8",
  "acknowledged": true,
  "acknowledged_by": "user-123",
  "acknowledged_at": "2026-01-19T17:00:00Z"
}
```

**Errors:**
- `409 Conflict`: Signal not currently visible

### POST `/api/v1/activity/signals/{signal_fingerprint}/suppress`

**Request:**
```json
{
  "run_id": "run-abc",
  "signal_type": "COST_RISK",
  "risk_type": "COST",
  "duration_minutes": 60,
  "reason": "Known issue"
}
```

**Response (200):**
```json
{
  "signal_fingerprint": "sig-a1b2c3d4e5f6g7h8",
  "suppressed_until": "2026-01-19T18:00:00Z"
}
```

**Errors:**
- `400 Bad Request`: Invalid duration (must be 15-1440)
- `409 Conflict`: Signal not currently visible

---

## Response Model Extension

### SignalFeedbackModel
```python
class SignalFeedbackModel(BaseModel):
    acknowledged: bool = False
    acknowledged_by: str | None = None
    acknowledged_at: datetime | None = None
    suppressed_until: datetime | None = None
```

### SignalProjection (Extended)
```python
class SignalProjection(BaseModel):
    signal_id: str
    signal_fingerprint: str  # NEW — for feedback operations
    run_id: str
    signal_type: str
    severity: str
    summary: str
    policy_context: PolicyContext
    created_at: datetime
    feedback: SignalFeedbackModel | None = None  # NEW
```

---

## Files Modified/Created

| File | Change |
|------|--------|
| `backend/app/models/audit_ledger.py` | Added SIGNAL entity, event types |
| `backend/app/services/logs/audit_ledger_service.py` | Added convenience methods |
| `backend/app/services/activity/signal_identity.py` | **NEW** — fingerprint computation |
| `backend/app/services/activity/signal_feedback_service.py` | **NEW** — feedback operations |
| `backend/app/services/activity/attention_ranking_service.py` | Added dampening + suppression |
| `backend/app/api/activity.py` | Added endpoints + response models |
| `docs/architecture/activity/ACTIVITY_DOMAIN_CONTRACT.md` | Added Section 21-22 |

---

## SDSR Scenarios

| Scenario | Description |
|----------|-------------|
| `SDSR-ACT-V2-SIGNAL-ACK-001` | Signal acknowledgment validation |
| `SDSR-ACT-V2-SIGNAL-SUPPRESS-001` | Signal suppression validation |

---

## Non-Goals

- No permanent suppression
- No mutable signal state
- No hidden operator overrides
- No new tables

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `ACTIVITY_DOMAIN_CONTRACT.md` Section 21-22 | Contract rules |
| `ACTIVITY_CAPABILITY_REGISTRY.yaml` | Capability registration |
| Implementation Plan | Original design spec |

---

## Implementation Verification

**Status:** ALL PHASES COMPLETE (2026-01-19)

| Phase | Component | Status |
|-------|-----------|--------|
| Phase 1 | Audit Infrastructure (L6) | ✅ Verified |
| Phase 2 | Audit Service Extension (L4) | ✅ Verified |
| Phase 3 | Signal Identity Module | ✅ Verified |
| Phase 3b | Signal Feedback Service | ✅ Verified |
| Phase 4 | API Endpoints (L2) | ✅ Verified |
| Phase 5 | Response Model Extension | ✅ Verified |
| Phase 6 | Attention Queue Integration | ✅ Verified |
| Phase 7 | Signals Endpoint Update | ✅ Verified |
| Phase 8 | Contract Rules | ✅ Verified |
| Phase 9 | SDSR Scenarios | ✅ Created |

**Verification Notes:**
- All invariants enforced in code
- ACK_DAMPENER = 0.6 frozen in `attention_ranking_service.py`
- Suppression duration enforced: 15-1440 minutes
- SDSR scenarios ready for E2E validation

**Test Results (2026-01-19):**
- Unit tests: 15/15 passed (`backend/tests/unit/test_signal_feedback.py`)
- BLCA validation: 0 violations (CLEAN)
- SDSR scenarios: 2 valid YAML files with 13 invariants total

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-01-19 | 1.1 | Added implementation verification status |
| 2026-01-19 | 1.0 | Initial implementation |
