# PIN-117: Evidence Report Enhancements & ID Type Safety

**Status:** ✅ COMPLETE
**Created:** 2025-12-21
**Author:** Claude Opus 4.5
**Depends On:** PIN-100 (M23 AI Incident Console)
**Milestone:** M23

---

## Executive Summary

Enhanced the Evidence Report PDF generator based on production feedback, and fixed a critical ID type mismatch bug in the replay functionality. Added prevention mechanisms to catch similar ID type issues in CI.

---

## Changes Made

### 1. Evidence Report PDF Improvements

#### 1.1 Added 1-Page Incident Snapshot (Front Matter)

New method `_build_incident_snapshot()` creates an executive summary page at the front of the report:

```
┌─────────────────────────────────────────────┐
│         INCIDENT SNAPSHOT                    │
│                                              │
│  Incident ID: inc_demo_4a5e594b              │
│  Timestamp: 2025-12-21T10:30:00Z             │
│  Customer: Demo Tenant                       │
│  Severity: HIGH                              │
│  Status: RESOLVED                            │
│                                              │
│  Model: gpt-4o-mini                          │
│  Policies Evaluated: 5                       │
│  Policies Passed: 5                          │
│  Deterministic: ✓ Yes                        │
│                                              │
│  ROOT CAUSE                                  │
│  [Brief root cause summary]                  │
│                                              │
│  IMPACT                                      │
│  • [Impact item 1]                           │
│  • [Impact item 2]                           │
└─────────────────────────────────────────────┘
```

**Benefits:**
- Legal/leadership can understand incident in 30 seconds
- First page provides decision context
- Audit-friendly summary

#### 1.2 Added Severity Definition Box

New section explaining severity levels:

| Severity | Definition |
|----------|------------|
| **HIGH** | Immediate action required. User-facing impact or data exposure risk. |
| **MEDIUM** | Action required within 24 hours. Degraded experience or potential risk. |
| **LOW** | Scheduled review. Minor issue, no immediate user impact. |

#### 1.3 Fixed Customer Display

- Changed "Unknown Customer" → "Demo Tenant" for demo/evaluation reports
- Production reports show actual tenant name
- Consistent branding for demo environments

#### 1.4 Softened Legal Attestation

Changed language from legalistic threats to professional guidance:

```
# Before (too aggressive):
"This document constitutes legal evidence..."
"Falsification of this document may result in..."

# After (professional):
"This report provides a factual record of AI system behavior..."
"Information contained herein is intended for incident review..."
```

#### 1.5 Added Severity/Status Fields to IncidentEvidence

```python
@dataclass
class IncidentEvidence:
    # ... existing fields ...
    severity: str = "HIGH"      # HIGH, MEDIUM, LOW
    status: str = "RESOLVED"    # OPEN, INVESTIGATING, RESOLVED
```

---

### 2. Replay ID Type Mismatch Fix

#### Problem

Replay button returned 404 error:
```
POST https://agenticverz.com/guard/replay/inc_demo_4a5e594b 404
```

#### Root Cause

Frontend was sending `incident.id` (prefix `inc_`) but replay endpoint expected `call_id` (prefix `call_`).

#### Solution

1. **Backend:** Added `call_id` field to `IncidentSummary` model
2. **Frontend:** Changed `onReplay(incident.id)` to `onReplay(incident.call_id)`
3. **Guard API:** Updated `list_incidents` to include first related `call_id`

**Files Modified:**
- `backend/app/api/guard.py` - Added `call_id` to `IncidentSummary`
- `website/aos-console/console/src/api/guard.ts` - Added `call_id` to `Incident` interface
- `website/aos-console/console/src/pages/guard/GuardDashboard.tsx` - Fixed replay button

---

### 3. Prevention System Update

Created new linter to prevent similar ID type mismatches:

**File:** `scripts/ops/lint_frontend_api_calls.py`

**Patterns Detected:**
| Pattern | Description | Severity |
|---------|-------------|----------|
| `onReplay(incident.id)` | incident.id in replay context | error |
| `/replay/${incident.id}` | incident.id in replay URL | error |
| `/replay/inc_` | Hardcoded inc_ prefix in replay | error |
| `/incidents/${call_id}` | call_id in incident endpoint | warning |

**ID Type Contracts:**
```
/replay/{id}      → expects call_id (call_xxx)
/incidents/{id}   → expects incident_id (inc_xxx)
/keys/{id}        → expects key_id (varies)
```

**Integration:**
- Added to `scripts/ops/ci_consistency_check.sh`
- Updated `docs/PREVENTION_PLAYBOOK.md`

---

## Files Changed

| File | Change |
|------|--------|
| `backend/app/services/evidence_report.py` | Added incident snapshot, severity box, softened language |
| `backend/app/api/guard.py` | Added `call_id` to `IncidentSummary` model |
| `website/aos-console/console/src/api/guard.ts` | Added `call_id` to Incident interface |
| `website/aos-console/console/src/pages/guard/GuardDashboard.tsx` | Fixed replay button to use `call_id` |
| `scripts/ops/lint_frontend_api_calls.py` | NEW: Frontend API ID type linter |
| `scripts/ops/ci_consistency_check.sh` | Added frontend API ID type check |
| `docs/PREVENTION_PLAYBOOK.md` | Documented ID type mismatch pattern |

---

## Testing

### Evidence Report
```bash
# Generate demo evidence report
curl -X GET "https://agenticverz.com/guard/incidents/inc_demo_4a5e594b/export?format=pdf" \
  -H "X-API-Key: $API_KEY" \
  -o evidence_report.pdf
```

### Replay Button
```bash
# Replay now uses correct call_id
curl -X POST "https://agenticverz.com/guard/replay/call_abc123" \
  -H "X-API-Key: $API_KEY"
```

### Prevention Linter
```bash
python scripts/ops/lint_frontend_api_calls.py website/aos-console/console/src/
# Should report no errors after fix
```

---

## Related PINs

- **PIN-100**: M23 AI Incident Console - Production Ready
- **PIN-097**: Prevention System v1.1 - Code Quality Automation
- **PIN-099**: SQLModel Row Extraction Patterns

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-21 | Created PIN-117 with evidence report enhancements and ID type fix |
