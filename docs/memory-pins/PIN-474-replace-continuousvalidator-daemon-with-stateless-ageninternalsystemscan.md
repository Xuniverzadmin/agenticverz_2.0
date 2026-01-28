# PIN-474: Replace continuous_validator daemon with stateless agen_internal_system_scan

**Status:** ✅ COMPLETE
**Created:** 2026-01-27
**Category:** Infrastructure / Optimization

---

## Summary

Killed 600MB always-on daemon (continuous_validator.py), replaced with stateless cron-scheduled scanner (agen_internal_system_scan.py). Frontloaded output into session_start.sh so violations are unmissable.

---

## Details

## Problem

continuous_validator.py ran as a persistent watchdog daemon (PID 3139164) since Jan 17.
- Consumed 599 MB RSS while idle for 5 days (last activity Jan 22)
- Only detected file changes (new/modified), missing all pre-existing violations
- Output buried in dotfiles (.validator.log, .validator_status.json) — easy to miss

## Solution

### 1. New scanner: scripts/preflight/agen_internal_system_scan.py
- Stateless: runs once, scans all files, reports, exits
- No watchdog dependency, no threads, no daemon loop
- Memory: ~10 MB for seconds vs 600 MB 24/7
- Full scan of all 253 matching backend files per run
- Backward-compatible: writes same .validator_status.json and .validator.log
- Modes: banner (default), --quiet (cron), --json (machine)
- Exit code: 0=CLEAN, 1=VIOLATIONS

### 2. Cron schedule
- `*/30 * * * * cd /root/agenticverz2.0 && python3 scripts/preflight/agen_internal_system_scan.py --quiet`
- Runs every 30 min, appends to .validator.log

### 3. session_start.sh integration
- Added as step [8/11] — runs fresh scan with full banner
- Violations count as ERROR → blocks session start
- Impossible to miss for Claude or human

### 4. Daemon killed
- PID 3139164 terminated, .validator.pid removed
- Memory recovered: 599 MB (system went from 4.1Gi to 3.6Gi used)

## True Violation Count

Old daemon reported 4 violations (only new files).
Full scan reveals 264 violations across 5 rules:
- MIG-001: 115 (missing MIGRATION_CONTRACT headers)
- RW-001: 72 (router imports in main.py)
- RW-002: 73 (include_router in main.py)
- RAB-001: 3 (direct headroom access)
- NC-001: 1 (naming suffix)

## Files Changed
- NEW: scripts/preflight/agen_internal_system_scan.py
- MODIFIED: scripts/ops/session_start.sh (added step 8/11, renumbered 8-10 to 9-11)
- KILLED: continuous_validator.py daemon process (script retained for reference)
- ADDED: crontab entry for scheduled scans
