# PIN-092: SSE Lifecycle Hardening & Console Fixes

**Status:** COMPLETE
**Created:** 2025-12-16
**Category:** Console / SSE / Streaming
**Trigger:** Post-worker-run error analysis

---

## Summary

Hardened SSE (Server-Sent Events) lifecycle handling in the Worker Execution Console. Separated real bugs from expected browser behavior. Fixed iframe sandbox permissions and API endpoint errors.

---

## Issues Addressed

### 1. SSE Reconnect Replay (Real UI Bug)

**Problem:** After run completion, React component remounts triggered duplicate SSE connections, replaying the entire event stream.

**Root Cause:** `useEffect` for SSE reconnected when component remounted or state changed, with no guard for completed runs.

**Fix:** Added `streamEndedForRunRef` latch in `useWorkerStream.ts`:
- Set latch on `run_completed` or `run_failed` events
- Check latch before creating EventSource
- Clear latch on `reset()` to allow new runs

```typescript
// Final-state latch: prevents reconnection after run completes/fails
const streamEndedForRunRef = useRef<string | null>(null);

// Guard in useEffect
if (streamEndedForRunRef.current === runId) {
  log('CONNECT', `⏹️ Run ${runId} already ended, skipping SSE reconnection`);
  return;
}
```

### 2. SSE Error Noise (Expected Behavior)

**Problem:** Console showed `❌ SSE ERROR` after every completed run.

**Root Cause:** EventSource has no concept of "graceful close". When backend closes stream after `run_completed`, browser fires `onerror`. This is standard SSE behavior.

**Fix:** Suppress error logging when run already completed:

```typescript
eventSource.onerror = (error) => {
  if (streamEndedForRunRef.current === runId) {
    log('CONNECT', `ℹ️ SSE closed after run ended (expected behavior)`);
    setIsConnected(false);
    return; // Don't report error for expected close
  }
  // ... actual error handling
};
```

### 3. Iframe Sandbox Error (Real UI Bug)

**Problem:** HTML artifact preview showed "Blocked script execution... 'allow-scripts' permission is not set".

**Fix:** Added `allow-scripts` to iframe sandbox in `ArtifactPreview.tsx:121`:

```tsx
// Before
sandbox="allow-same-origin"

// After
sandbox="allow-same-origin allow-scripts"
```

### 4. `/api/v1/failures/stats` 500 Error (Real Backend Bug)

**Problem:** Endpoint returned 500 Internal Server Error.

**Root Cause:** SQLAlchemy `col("count")` doesn't work - "count" was a label alias, not a column.

**Fix:** Used `func.count()` expression directly for ordering in `failures.py`:

```python
count_col = func.count(FailureMatch.id)
top_codes_result = session.exec(
    select(FailureMatch.error_code, count_col)
    .group_by(FailureMatch.error_code)
    .order_by(count_col.desc())
    .limit(10)
).all()
```

---

## Classification Table

| Issue | Type | Action Taken |
|-------|------|--------------|
| SSE error after completion | Expected behavior | Suppress logging |
| SSE reconnect replay | UI lifecycle bug | Added final-state latch |
| iframe sandbox error | Real UI bug | Added `allow-scripts` |
| failures/stats 500 | Backend bug | Fixed SQLAlchemy query |
| health 503 during restart | Transient | No action needed |

---

## Key Insight

> SSE `onerror` fires when stream closes. This is NOT a bug. Every production SSE system exhibits this behavior. The correct response is to check if the run already completed before treating it as an error.

---

## Files Changed

| File | Change |
|------|--------|
| `website/aos-console/console/src/hooks/useWorkerStream.ts` | Added `streamEndedForRunRef` latch, smart error handling |
| `website/aos-console/console/src/pages/workers/components/ArtifactPreview.tsx` | Added `allow-scripts` to iframe sandbox |
| `backend/app/api/failures.py` | Fixed SQLAlchemy aggregate ordering |

---

## Verification

```bash
# Endpoint returns valid JSON
curl -s -H "X-API-Key: $AOS_API_KEY" "https://agenticverz.com/api/v1/failures/stats"
# Returns: {"total_failures":0,"matched_failures":0,...}

# Console logs after run completion
# Shows: "ℹ️ SSE closed after run ended (expected behavior)"
# Instead of: "❌ SSE ERROR"
```

---

## Doctrine

**SSE Contract:** `onerror` after stream completion is expected. Never treat post-completion errors as failures. Never add retries for completed runs.

---

*Deployed: 2025-12-16*
