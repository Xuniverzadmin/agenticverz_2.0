# L7 Internal Flows (L7 → L7)

**Status:** VERIFIED
**Generated:** 2025-12-31
**Method:** Codebase survey of ops automation components

---

## Scope

This document records all runtime artifacts produced and consumed entirely within L7.

**L7 definition:**
- Schedulers (systemd timers)
- Ops workers (maintenance jobs)
- Housekeeping logic (cleanup, retention)
- Deployment automation
- Internal coordination mechanisms

---

## L7 → L7 Flow Inventory

| Category | Count | Examples |
|----------|-------|----------|
| Distributed locks | 5 | outbox_processor, dl_reconcile, matview_*, retention_cleanup, reclaim_gc |
| Marker files | 3 | .uploaded, .processed, latest_report.json |
| Checkpoint files | 3 | CSV stats, replay_log, dead_letter_archive |
| Systemd services | 5 | m10-maintenance, m10-daily-stats, m10-synthetic-traffic, aos-cost-snapshot-hourly, aos-cost-snapshot-daily |
| L7-private DB tables | 5 | distributed_locks, replay_log, dead_letter_archive, outbox, retention_jobs |

**Total L7 → L7 flows: 21**

---

## Detailed Inventory

### 1. Distributed Locks (PostgreSQL-backed)

| Lock Type | Producer | Consumer | Purpose |
|-----------|----------|----------|---------|
| `m10:outbox_processor` | outbox_processor.py | orchestrator.py | Single-leader outbox processing |
| `dl_reconcile` | orchestrator.py | reconcile_dl.py | Dead-letter reconciliation |
| `matview_*` | orchestrator.py | matview refresh tasks | Per-view refresh coordination |
| `retention_cleanup` | orchestrator.py | retention_archive.py | Cleanup job coordination |
| `reclaim_gc` | orchestrator.py | lock cleanup task | Expired lock garbage collection |

**Backing store:** `m10_recovery.distributed_locks` table
**Access pattern:** `acquire_lock()` / `release_lock()` SQL functions
**TTL:** Configurable (default 300s)

### 2. Marker Files (Filesystem-based)

| Marker | Producer | Consumer | Location |
|--------|----------|----------|----------|
| `.uploaded` | retry_local_fallback() | retry_r2_fallbacks.sh | /opt/agenticverz/state/fallback-uploads/ |
| `.processed` | m10_daily_stats_export.py | postflight validation | /var/log/m10/*.csv |
| `latest_report.json` | canary_runner.py | rollback automation | scripts/ops/canary/reports/ |

**Access pattern:** Atomic write via flock + rename
**Lifecycle:** Created on success, consumed by next job cycle

### 3. Checkpoint Files (State Tracking)

| Checkpoint | Producer | Consumer | Persistence |
|------------|----------|----------|-------------|
| CSV stats files | m10_daily_stats_export.py | next day's export, retention | /var/log/m10/m10_stats_YYYY-MM.csv |
| replay_log | outbox_processor.py | retry scripts, retention | m10_recovery.replay_log table |
| dead_letter_archive | DL processor | retention_archive.py | m10_recovery.dead_letter_archive table |

**Purpose:** Inter-job state coordination and crash recovery

### 4. Systemd Service Coordination

| Service | Timer | After Dependencies | Output |
|---------|-------|-------------------|--------|
| m10-maintenance.service | Every 5min | postgresql, redis | JSON to journal |
| m10-daily-stats.service | Daily 00:05 | postgresql | CSV to /var/log/m10/ |
| m10-synthetic-traffic.service | Every 30min | postgresql, redis | Event count to journal |
| aos-cost-snapshot-hourly.service | Every hour | network | Snapshot to database |
| aos-cost-snapshot-daily.service | Daily | network | Baseline + snapshot |

**Coordination:** Execution order enforced via systemd dependencies

### 5. L7-Private Database Tables (m10_recovery schema)

| Table | Purpose | L7 Readers Only |
|-------|---------|-----------------|
| distributed_locks | Leader election state | orchestrator.py, outbox_processor.py |
| replay_log | Idempotency tracking | retry scripts, retention cleanup |
| dead_letter_archive | DL message storage | retention_archive.py, reconcile_dl.py |
| outbox | Transactional side-effects | outbox_processor.py |
| retention_jobs | Archive operation metadata | retention_archive.py |

**Schema isolation:** `m10_recovery.*` is never read by L6 or L5

---

## Isolation Properties

### What L7 Does NOT Share

| Property | Enforcement |
|----------|-------------|
| L6 never reads L7 state | Schema separation (m10_recovery.*) |
| L5 never reads L7 locks | Function-based access only |
| L2 has no L7 exposure | No API endpoints for ops state |
| L8 receives metrics only | Aggregated gauges, not raw state |

### Atomicity Guarantees

| Mechanism | Where Used |
|-----------|------------|
| flock + rename | Marker files, feature flags |
| PostgreSQL transactions | Lock acquisition, outbox processing |
| Redis atomic operations | Stream ACKs, dead-letter routing |
| Systemd dependencies | Service execution order |

---

## Conclusion

L7 internal flows are:
- **Intentionally private** — no runtime layer reads L7 operational state
- **Architecturally isolated** — m10_recovery schema is L7-only
- **Safe from runtime coupling** — no hidden dependencies on L7 artifacts

**No action required.** L7 → L7 integrity is verified.

---

**Generated by:** Claude Opus 4.5
**Verification:** 21 flows identified, all L7-internal
**Cross-reference:** L7_L6_FLOWS.md (for L7 outputs that reach L6)
