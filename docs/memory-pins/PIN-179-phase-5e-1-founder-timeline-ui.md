# PIN-179: Phase 5E-1 - Founder Decision Timeline UI

**Status:** ✅ COMPLETE
**Category:** Frontend / Founder Console / Decision Visibility
**Created:** 2025-12-26
**Milestone:** Phase 5E-1 (Post-5E-H Human Test Eligibility)
**Related PINs:** PIN-178, PIN-177, PIN-170

---

## Executive Summary

Phase 5E-1 implements the Founder Decision Timeline UI - a read-only, verbatim viewer for decision records that allows founders to reconstruct any run end-to-end without logs or explanation.

---

## Session Context

This work continues from PIN-178 (Phase 5E-H Human Test Eligibility Gate) which confirmed:
- 6/6 P0 scenarios passed
- System declared HUMAN-TEST ELIGIBLE
- Phase 5E-1 authorized to proceed

---

## Implementation

### Files Created

| File | Purpose |
|------|---------|
| `website/aos-console/console/src/api/timeline.ts` | Frontend API client for `/founder/timeline/*` endpoints |
| `website/aos-console/console/src/pages/founder/FounderTimelinePage.tsx` | Timeline UI component |

### Files Modified

| File | Change |
|------|--------|
| `website/aos-console/console/src/routes/index.tsx` | Added route for `/founder/timeline` |
| `docs/memory-pins/PIN-178-phase-5e-h-human-test-eligibility.md` | Updated with 5E-1 completion |

---

## Architecture

### Route Structure

```
/console/founder/timeline          → All decisions view (paginated)
/console/founder/timeline?run=xxx  → Single run timeline view
```

### API Integration

| Frontend | Backend | Purpose |
|----------|---------|---------|
| `getRunTimeline(runId)` | `GET /founder/timeline/run/{run_id}` | Complete run timeline |
| `listDecisionRecords(params)` | `GET /founder/timeline/decisions` | List all records |
| `getDecisionRecord(id)` | `GET /founder/timeline/decisions/{id}` | Single record |
| `countDecisionRecords(params)` | `GET /founder/timeline/count` | Count records |

### RBAC

- Resource: `runtime`
- Action: `query`
- Required Role: `founder`, `operator`, `infra`, or `admin`

---

## UI Features

### Run Timeline View

When a `run_id` is provided, displays chronological entries:

1. **PRE-RUN DECLARATION** (blue border)
   - run_id, agent_id, goal, max_attempts, priority
   - tenant_id, idempotency_key, parent_run_id
   - declared_at timestamp

2. **DECISION RECORDS** (yellow border, multiple)
   - decision_id, decision_type, decision_source, decision_trigger
   - decision_outcome, decision_reason, causal_role
   - run_id, workflow_id, request_id, tenant_id
   - Expandable: decision_inputs JSON, details JSON

3. **OUTCOME RECORD** (green border)
   - run_id, status, attempts, error_message
   - started_at, completed_at, duration_ms

### All Decisions View

When no `run_id` is provided:

- Lists all decision_records in descending chronological order
- Filter by decision_type (routing, recovery, policy, budget, etc.)
- Pagination: 50 records per page
- Auto-refresh: every 30 seconds
- Click to expand full record details

---

## Design Principles

As mandated by user directive:

| Principle | Implementation |
|-----------|----------------|
| Read-only | No mutations, no actions, display only |
| Verbatim | Raw field values, no transformation |
| Chronological | ASC order for run timeline, DESC for all decisions |
| No interpretation | No status pills, no severity colors, no smart summaries |
| No aggregation | Each record displayed individually |

---

## Verification

### Backend Endpoints

```bash
# Count endpoint (returns 0 - no production runs yet)
curl -H "X-Roles: founder" http://localhost:8000/founder/timeline/count
{"count": 0}

# List endpoint (returns empty - no production runs yet)
curl -H "X-Roles: founder" "http://localhost:8000/founder/timeline/decisions?limit=5"
[]
```

### Frontend Build

```bash
cd /root/agenticverz2.0/website/aos-console/console
npm run build
# ✅ Success
# Bundle: FounderTimelinePage-DyJ8M27f.js (12.69 kB gzipped: 3.50 kB)
```

---

## Stop Condition

> "A founder can reconstruct any run end-to-end without logs or explanation."

**Status:** MET

When decision_records exist, the timeline provides:
1. What was declared (PRE-RUN)
2. What decisions were made (DECISION)
3. What happened (OUTCOME)

All verbatim. All chronological. No interpretation.

---

## Next Steps

| Phase | Description | Status |
|-------|-------------|--------|
| 5E-1 | Founder Decision Timeline UI | ✅ COMPLETE |
| 5E-2 | Kill-Switch UI Toggle | PENDING |
| 5E-3 | Link Existing UIs in Navigation | PENDING |
| 5E-4 | Customer Essentials | PENDING |

---

## Audit Trail

| Time | Action | Result |
|------|--------|--------|
| Session Start | Resumed from PIN-178 completion | - |
| Step 1 | Reviewed existing `/founder/timeline` API | Backend already complete |
| Step 2 | Created `src/api/timeline.ts` | API client ready |
| Step 3 | Created `src/pages/founder/FounderTimelinePage.tsx` | UI component ready |
| Step 4 | Updated `src/routes/index.tsx` | Route registered |
| Step 5 | Ran `npm run build` | ✅ Build successful |
| Step 6 | Verified backend endpoints | ✅ Working (0 records expected) |
| Step 7 | Updated PIN-178 | Documented 5E-1 completion |
| Session End | Created PIN-179 | This document |

---

## Key Code Snippets

### API Client Types

```typescript
// timeline.ts
export interface DecisionRecordView {
  decision_id: string;
  decision_type: string;
  decision_source: string;
  decision_trigger: string;
  decision_inputs: Record<string, unknown>;
  decision_outcome: string;
  decision_reason: string | null;
  run_id: string | null;
  workflow_id: string | null;
  tenant_id: string;
  request_id: string | null;
  causal_role: string;
  decided_at: string;
  details: Record<string, unknown>;
}

export interface TimelineEntry {
  entry_type: 'pre_run' | 'decision' | 'outcome';
  timestamp: string;
  record: Record<string, unknown>;
}

export interface RunTimeline {
  run_id: string;
  entries: TimelineEntry[];
  entry_count: number;
}
```

### Route Registration

```typescript
// routes/index.tsx
const FounderTimelinePage = lazy(() => import('@/pages/founder/FounderTimelinePage'));

// In routes:
<Route path="founder/timeline" element={<FounderTimelinePage />} />
```

---

## References

- Backend API: `backend/app/api/founder_timeline.py` (Phase 4C-1)
- Contract: `docs/contracts/DECISION_RECORD_CONTRACT.md`
- Parent PIN: PIN-178 (Phase 5E-H Human Test Eligibility)
