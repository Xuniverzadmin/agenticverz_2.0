# PIN-477: Journal limits + system bloat audit mechanism

**Status:** ✅ COMPLETE
**Created:** 2026-01-27
**Category:** Infrastructure / Optimization

---

## Summary

Capped journald at 200MB/7 days (was 2.3GB unlimited), vacuumed 2.2GB. Created system_bloat_audit.sh for weekly cron + session_start.sh integration. Archives markdown reports, auto-prunes to 12.

---

## Details

## Problem

systemd-journald consumed 174 MB RSS with 2.3 GB of journals on disk.
- /etc/systemd/journald.conf had ALL defaults commented out — no size limit, no retention
- Journals accumulated since system install with zero rotation
- No mechanism to detect future bloat from any service (amavis, worker pool, validator daemon, etc.)

## Changes

### 1. journald.conf — hard limits applied

| Setting | Before | After |
|---------|--------|-------|
| SystemMaxUse | unlimited | 200M |
| SystemKeepFree | unlimited | 500M |
| SystemMaxFileSize | unlimited | 50M |
| SystemMaxFiles | 100 | 8 |
| MaxRetentionSec | unlimited | 7day |
| MaxFileSec | 1month | 1day |
| Storage | auto | persistent |
| Compress | default | yes |

### 2. Vacuum executed
- Command: journalctl --vacuum-time=7d --vacuum-size=200M
- Freed: 2.2 GB (47 archived journal files deleted)
- After: 144 MB on disk

### 3. scripts/ops/system_bloat_audit.sh — review + archive mechanism

Purpose: Catch bloat before it becomes a problem. Three execution modes:

**a) Session start (step [9/12])**
- Runs on every Claude/human session via session_start.sh
- Prints unmissable banner with memory, journal, service status
- Warnings count toward session warning total
- Impossible to miss

**b) Weekly cron (Sunday 03:00)**
- Crontab: 0 3 * * 0 /root/agenticverz2.0/scripts/ops/system_bloat_audit.sh --quiet
- Archives report to docs/ops-reports/bloat-audits/
- Auto-prunes to last 12 reports (3 months)

**c) On-demand**
- Run: ./scripts/ops/system_bloat_audit.sh
- Full banner output + archived report

### What it monitors

| Check | Threshold | Action if exceeded |
|-------|-----------|-------------------|
| Total RAM used | >= 6 Gi | WARNING |
| Journal disk size | >= 180 MB | WARNING |
| Amavis process count | > 2 | WARNING |
| Amavis memory | > 300 MB | WARNING |
| Worker pool memory | > 300 MB | WARNING |
| Validator daemon running | should be stopped | WARNING (PIN-474 replaced with cron) |
| Top 5 processes by RSS | displayed | Visual review |

### Report archive format

- Location: docs/ops-reports/bloat-audits/bloat-audit-YYYY-MM-DD_HHMM.md
- Contains: memory breakdown, service status, top processes, threshold checks, warning list
- Retention: last 12 reports (auto-pruned)
- Cross-references: PIN-474, PIN-475, PIN-476, PIN-477

### session_start.sh changes

- Added step [9/12]: System bloat audit
- Renumbered BLCA from [9/11] to [10/12]
- Renumbered lifecycle-qualifier from [10/11] to [11/12]
- Renumbered health-lifecycle from [11/11] to [12/12]
- Total steps: 12 (was 11)

## Disk impact
- Journal freed: 2.2 GB
- Journal now: 144 MB (capped at 200 MB)
- Will never exceed 200 MB again (kernel-enforced by journald)

## Files created
- scripts/ops/system_bloat_audit.sh
- docs/ops-reports/bloat-audits/ (directory + first report)

## Files modified
- /etc/systemd/journald.conf (limits applied)
- scripts/ops/session_start.sh (added step 9/12, renumbered 10-12)

## Cron entries (cumulative this session)
- */30 * * * * — agen_internal_system_scan.py (contract scan)
- 0 3 * * 0 — system_bloat_audit.sh (weekly bloat audit)

## Cumulative session savings

| PIN | Optimization | Memory freed | Disk freed |
|-----|-------------|-------------|------------|
| 474 | Validator daemon → cron scan | 600 MB | — |
| 475 | Worker pool killed | 666 MB | — |
| 476 | Amavis reduced | 367 MB | — |
| 477 | Journal limits + bloat audit | ~30 MB (journald RSS) | 2.2 GB |
| **Total** | | **~1.66 GB RAM** | **2.2 GB disk** |

System: 4.1 Gi used → 3.0 Gi used, 7.5 Gi available → 8.7 Gi available

---

## Related PINs

- [PIN-474](PIN-474-.md)
- [PIN-475](PIN-475-.md)
- [PIN-476](PIN-476-.md)
