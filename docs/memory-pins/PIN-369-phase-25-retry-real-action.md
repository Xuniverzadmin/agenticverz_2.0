# PIN-369: Phase-2.5 RETRY Real Action

**Status:** ✅ IMPLEMENTED
**Created:** 2026-01-09
**Category:** UI Pipeline / Phase-2.5

---

## Summary

First real action: RETRY creates actual DB record. One real action, one real state change, one real feedback loop.

---

## Implementation Details

### Backend

**Endpoint:** `POST /api/v1/workers/business-builder/runs/{run_id}/retry`

**File:** `backend/app/api/workers.py:1102-1165`

**Behavior:**
- Creates new run linked to original via `parent_run_id`
- Only allows retry of `completed` or `failed` runs
- Returns `RunRetryResponse` with `id`, `parent_run_id`, `status`
- DB write only, no agent execution triggered
- Status set to `queued` for new run

### Frontend

**Files Modified:**

1. **`src/api/worker.ts`** - Added `retryRun(runId)` API function
   - Returns `RetryRunResponse` interface

2. **`src/contexts/SimulationContext.tsx`** - Added real action support
   - `REAL_MODE_CONTROLS` array: `['RETRY']`
   - `executeRealAction(controlType, panelId, runId)` function
   - `isRealMode(controlType)` check
   - `isRealModeControl()` export

3. **`src/components/simulation/SimulatedControl.tsx`** - Updated for real execution
   - Added `entityId` prop (optional - fallback to simulation if absent)
   - Updated `handleClick` and `handleConfirm` to route real actions
   - Badge shows "REAL" (green) for graduated controls with entityId
   - Badge shows "SIMULATED" (amber) for simulation mode

### Visual Indicators

| Mode | Badge Color | Badge Text |
|------|-------------|------------|
| REAL | Green | REAL |
| SIMULATED | Amber | SIMULATED |
| BLOCKED | Red | BLOCKED |

### Entity ID Flow

```
PanelView → SimulatedControl(entityId=runId)
                    ↓
            isRealMode(control.type) && entityId?
                    ↓
            YES → executeRealAction(type, panelId, runId)
            NO  → executeSimulatedAction(type, panelId)
```

### Testing Requirements

E2E test requires:
1. Create a run (via worker)
2. Wait for `completed` or `failed` status
3. Click RETRY control with entityId
4. Verify new run appears with `parent_run_id` set

### E2E Test Results (2026-01-09)

**Test Run:**
```bash
# Original run (completed)
ID: 0f2a5a32-689b-4a9a-828c-8d1464ae9fae
Status: completed

# After retry:
curl -X POST /api/v1/workers/business-builder/runs/{id}/retry
Response: {"id":"f7ba9604-1ab9-4261-9903-67cccd9dd252","parent_run_id":"0f2a5a32-689b-4a9a-828c-8d1464ae9fae","status":"queued"}

# Database verification:
ID: f7ba9604-1ab9-4261-9903-67cccd9dd252
  Status: running
  Parent: 0f2a5a32-689b-4a9a-828c-8d1464ae9fae
```

**Result:** ✅ PASS - New run created with correct `parent_run_id` linkage

---

## Related PINs

- [PIN-368](PIN-368-phase-2a2-simulation-mode.md) - Phase-2A.2 Simulation Mode
