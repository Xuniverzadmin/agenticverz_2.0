# PIN-475: Kill worker pool — manual restart model for Neon cost control

**Status:** ✅ COMPLETE
**Created:** 2026-01-27
**Category:** Infrastructure / Optimization

---

## Summary

Killed always-on worker pool (3 processes, 666MB) that polled Neon every 2s with zero work for 14 days. Switched to manual restart model to eliminate idle Neon billing.

---

## Details

## Problem

app.worker.pool (PID 232248) + 2 multiprocessing spawn children ran 24/7 since Jan 13.
- Combined RSS: ~666 MB (parent 102 MB + 2 children ~282 MB each)
- Polled Neon Postgres every 2 seconds via SELECT on runs table
- Zero work done since Jan 13 (last healthy run: 2026-01-13 03:31:02)
- 3 stuck runs in RUNNING status since Jan 12 (started_at=NULL, attempts=0)
- Estimated wasted Neon queries: ~604,800 over 14 days (43,200/day)

## What the worker pool does

- Entry: python -m app.worker.pool
- Polls runs table for status IN (queued, retry) every 2 seconds
- Dispatches to ThreadPoolExecutor (4 threads)
- Executes runs via RunRunner → skills → traces
- Persistent connections to Neon (IPv6, sslmode=require)
- Config: WORKER_POLL_INTERVAL=2.0, WORKER_CONCURRENCY=4, WORKER_BATCH_SIZE=8

## Key code locations

- Pool: backend/app/worker/pool.py
- Runner: backend/app/worker/runner.py
- ROK: backend/app/worker/orchestration/run_orchestration_kernel.py
- Phases: backend/app/worker/orchestration/phases.py
- Skills executor: backend/app/skills/executor.py

## Decision: Manual restart model

Options considered:
1. Exponential backoff + idle shutdown (96% query reduction)
2. Kill now, manual restart when needed ← CHOSEN
3. On-demand via systemd socket activation (full re-architecture)

User chose option 2: zero cost at idle, manual start when runs are queued.

## To restart the worker pool

```bash
cd /root/agenticverz2.0/backend
python3 -m app.worker.pool
```

Or in background:
```bash
cd /root/agenticverz2.0/backend && nohup python3 -m app.worker.pool > /tmp/worker_pool.log 2>&1 &
```

## 3 Stuck runs (needs investigation)

All from 2026-01-12 18:00-18:01, started_at=NULL, attempts=0:
- test-evidence-ll...
- test-ev-4c953628...
- test-ev-0f5fa9b3...

These need manual reset to queued or failed status before worker pool is useful again.

## Memory impact

| Metric | Before | After |
|--------|--------|-------|
| Worker pool RSS | 666 MB | 0 MB |
| Combined with PIN-474 (validator) | 1,265 MB freed | - |
| System used | 4.1 Gi | 3.1 Gi |
| System available | 7.5 Gi | 8.6 Gi |

## Future consideration

If runs become frequent again, implement exponential backoff + idle shutdown:
- Backoff: 2s → 5s → 15s → 30s → 60s when no work found
- Auto-exit after 30 min idle (systemd can restart on-demand)
- Cuts idle queries from 43,200/day to ~1,500/day

---

## Related PINs

- [PIN-474](PIN-474-.md)
