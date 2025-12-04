# PIN-016: M4 Operations Tooling & Runbook

**Serial:** PIN-016
**Title:** M4 Operations Tooling & Runbook Implementation
**Category:** Operations / Tooling
**Status:** COMPLETE
**Created:** 2025-12-02
**Updated:** 2025-12-02

---

## Executive Summary

This PIN documents the operational tooling and runbook infrastructure created to support M4 Workflow Engine maturity validation and ongoing operations. These tools enable monitoring, incident response, and self-certification for the 24-hour shadow run.

---

## Tools Implemented

### 1. Golden Diff Debug Script

**Path:** `scripts/stress/golden_diff_debug.py`

**Purpose:** Analyzes golden file mismatches to identify root causes including:
- Seed mismatches
- Leaked volatile fields (timestamps, durations)
- Unseeded RNG usage
- External call variations

**Usage:**
```bash
# Compare two golden files
python3 scripts/stress/golden_diff_debug.py \
    --golden-a /path/to/file_a.json \
    --golden-b /path/to/file_b.json \
    --verbose

# Summarize shadow simulation directory
python3 scripts/stress/golden_diff_debug.py \
    --summary-dir /tmp/shadow_simulation_* \
    --output summary.json
```

**Key Features:**
- Identifies VOLATILE_LEAK vs DETERMINISM_VIOLATION
- Flattens nested JSON for field-level comparison
- Generates summary reports for shadow directories
- Returns non-zero exit code on critical issues

---

### 2. Shadow Sanity Check Script

**Path:** `scripts/stress/shadow_sanity_check.sh`

**Purpose:** 4-hour sanity check during 24-hour shadow run covering:
1. Process status (running, elapsed time)
2. Mismatch detection (actual errors, not success messages)
3. Disk usage (golden dir, /tmp, root filesystem)
4. Recent log activity
5. Prometheus metrics (if available)

**Usage:**
```bash
# Run every 4 hours during shadow run
/root/agenticverz2.0/scripts/stress/shadow_sanity_check.sh
```

**Output Sections:**
- `[1/5] Process Status` - PID and elapsed time
- `[2/5] Mismatch Check` - Error detection with correct filtering
- `[3/5] Disk Usage` - Storage monitoring
- `[4/5] Recent Activity` - Last 10 log entries
- `[5/5] Prometheus Metrics` - Workflow metrics if available

---

### 3. Shadow Status Check Script

**Path:** `scripts/stress/check_shadow_status.sh`

**Purpose:** Quick status check for shadow run monitoring.

**Usage:**
```bash
/root/agenticverz2.0/scripts/stress/check_shadow_status.sh
```

---

### 4. Shadow Monitor Daemon

**Path:** `scripts/stress/shadow_monitor_daemon.sh`

**Purpose:** Background daemon that monitors the 24-hour shadow run with:
- Health checks every 5 minutes
- Webhook alert capability for critical issues
- Disk space monitoring
- Process liveness detection
- Mismatch detection

**Usage:**
```bash
# Start the daemon
./scripts/stress/shadow_monitor_daemon.sh start

# Check status
./scripts/stress/shadow_monitor_daemon.sh status

# Single health check
./scripts/stress/shadow_monitor_daemon.sh check

# Stop the daemon
./scripts/stress/shadow_monitor_daemon.sh stop
```

**Log Location:** `/var/lib/aos/shadow_monitor.log`

**Health States:**
- `HEALTHY` - Process running, no mismatches, disk OK
- `WARNING` - Log stale (>10 min) or disk high (>90%)
- `CRITICAL` - Process dead, mismatches detected, or disk full

---

### 5. Shadow Debug Console

**Path:** `scripts/stress/shadow_debug.sh`

**Purpose:** Interactive debug console for investigating shadow run issues.

**Usage:**
```bash
# Full status report
./scripts/stress/shadow_debug.sh full

# Specific commands
./scripts/stress/shadow_debug.sh tail        # Last 20 log lines
./scripts/stress/shadow_debug.sh cycles      # Cycle statistics
./scripts/stress/shadow_debug.sh mismatches  # Mismatch analysis
./scripts/stress/shadow_debug.sh golden      # Golden file analysis
./scripts/stress/shadow_debug.sh process     # Process information
./scripts/stress/shadow_debug.sh replay <id> # Replay specific run
```

**Output Sections (full command):**
- Process Information (PID, elapsed time, child processes)
- Cycle Statistics (total, successful, errors)
- Mismatch Analysis (detailed error reports)
- Golden File Analysis (counts, sizes, recent files)
- Resource Usage (disk, memory)
- Log File Info (path, size, time range)

---

### 6. Shadow Cron Check

**Path:** `scripts/stress/shadow_cron_check.sh`

**Purpose:** Cron-friendly silent monitoring script that:
- Runs every 15 minutes via cron
- Logs only on issues (silent on success)
- Reports to syslog for system integration

**Cron Entry:**
```bash
*/15 * * * * /root/agenticverz2.0/scripts/stress/shadow_cron_check.sh
```

**Log Location:** `/var/lib/aos/shadow_cron_alerts.log`

---

### 7. Emergency Workflow Disable Script

**Path:** `scripts/ops/disable-workflows.sh`

**Purpose:** Emergency stop/start for workflow execution during incidents.

**Usage:**
```bash
# Enable emergency stop
./scripts/ops/disable-workflows.sh enable

# Check status
./scripts/ops/disable-workflows.sh status

# Disable emergency stop (re-enable workflows)
./scripts/ops/disable-workflows.sh disable
```

**Mechanism:**
- Creates/removes `/var/lib/aos/.workflow_emergency_stop` file
- Sets `WORKFLOW_EMERGENCY_STOP` environment variable
- Logs timestamp and user for audit

---

## Runbook Created

### M4 Workflow Engine Runbook

**Path:** `docs/runbooks/m4-workflow-engine.md`

**Contents:**

| Section | Description |
|---------|-------------|
| Overview | Architecture diagram, key components |
| Health Checks | Service, shadow run, database, Prometheus |
| Common Operations | Shadow simulation, golden analysis, key rotation, archival |
| Incident Response | Mismatch playbook, checkpoint failure, Redis failure |
| Troubleshooting | Slow execution, invalid signatures, resume failures |
| Tabletop Checklist | 10-step exercise with expected results |
| Sign-Off Template | Formal certification section |

**Tabletop Exercise Steps:**

| # | Step | Command |
|---|------|---------|
| 1 | Service health | `curl http://localhost:8000/health` |
| 2 | Quick shadow test | `./scripts/stress/run_shadow_simulation.sh --quick` |
| 3 | Sanity script | `./scripts/stress/shadow_sanity_check.sh` |
| 4 | Emergency stop | `./scripts/ops/disable-workflows.sh enable` |
| 5 | Stop status | `./scripts/ops/disable-workflows.sh status` |
| 6 | Re-enable | `./scripts/ops/disable-workflows.sh disable` |
| 7 | Golden diff | `python3 scripts/stress/golden_diff_debug.py --summary-dir ...` |
| 8 | Prometheus alerts | `curl http://localhost:9090/api/v1/alerts` |
| 9 | Checkpoint DB | `psql -c "SELECT COUNT(*) FROM checkpoints"` |
| 10 | Redis connectivity | `redis-cli ping` |

---

## PIN-015 Completion Template

**Path:** `docs/memory-pins/PIN-015-completion-template.md`

**Purpose:** Template for updating PIN-015 after 24-hour shadow run completion.

**Sections:**
- Final Shadow Run Results (metrics table, summary JSON)
- Runbook Tabletop Results (10-step checklist)
- Sign-Off (certification statement, signature block)
- INDEX.md Update instructions

---

## Bug Fixes Applied

### BUG-001: Bash Arithmetic Exit Code

**File:** `scripts/stress/run_shadow_simulation.sh`
**Lines:** 497-499, 511

**Issue:** `((MISMATCHES += 0))` returns exit code 1 under `set -e`

**Fix:**
```bash
((TOTAL_WORKFLOWS += primary_total)) || true
((TOTAL_REPLAYS += replays)) || true
((MISMATCHES += mismatches)) || true
((CYCLES_COMPLETED++)) || true
```

### BUG-002: Mismatch Count False Positive

**File:** `scripts/stress/shadow_sanity_check.sh`

**Issue:** `grep -ci "mismatch"` counted "0 mismatches" success lines

**Fix:**
```bash
MISMATCH_ERRORS=$(grep -E "[1-9][0-9]* mismatches|mismatches detected" "$LOGFILE" | grep -v ", 0 mismatches" | wc -l)
```

---

## File Inventory

| File | Size | Purpose |
|------|------|---------|
| `scripts/stress/golden_diff_debug.py` | 8.5K | Golden file analysis |
| `scripts/stress/shadow_sanity_check.sh` | 4.4K | 4-hour sanity check |
| `scripts/stress/check_shadow_status.sh` | 1.7K | Quick status check |
| `scripts/stress/shadow_monitor_daemon.sh` | 4.8K | Background monitoring daemon |
| `scripts/stress/shadow_debug.sh` | 5.2K | Interactive debug console |
| `scripts/stress/shadow_cron_check.sh` | 1.3K | Cron-based monitoring |
| `scripts/ops/disable-workflows.sh` | 1.8K | Emergency workflow control |
| `docs/runbooks/m4-workflow-engine.md` | 11.7K | Operations runbook |
| `docs/memory-pins/PIN-015-completion-template.md` | 3.4K | Completion template |

---

## Current 24-Hour Shadow Run

**Started:** 2025-12-02 13:12:19 CET
**Expected End:** 2025-12-03 ~13:12 CET
**PID:** 752320

**Status at PIN Creation:**
- Elapsed: ~42 minutes
- Cycles: 83
- Workflows: 747
- Replays: 747
- Mismatches: 0

**Status Update (T+58 min):**
- Elapsed: ~58 minutes
- Cycles: 115
- Workflows: 1,035
- Replays: 1,035
- Mismatches: 0
- Golden Files: 1,035 (4.2M)

**Active Monitoring:**
- Monitor Daemon: Running (PID: 790726), checks every 5 minutes
- Cron Job: Every 15 minutes via `/etc/crontab`
- Log: `/var/lib/aos/shadow_monitor.log`
- Alerts: `/var/lib/aos/shadow_cron_alerts.log`

**Monitoring Commands:**
```bash
# Daemon status
./scripts/stress/shadow_monitor_daemon.sh status

# Full debug report
./scripts/stress/shadow_debug.sh full

# 4-hour sanity check
./scripts/stress/shadow_sanity_check.sh

# Watch live
tail -f /var/lib/aos/shadow_24h_20251202_131219.log
```

---

## Next Steps

1. **Continue monitoring** - Use sanity check every 4 hours
2. **On shadow completion** - Run `golden_diff_debug.py --summary-dir`
3. **Execute tabletop** - Follow runbook checklist
4. **Update PIN-015** - Use completion template
5. **Sign off** - Self-certify or obtain SRE sign-off
6. **Proceed to M5** - After M4 maturity confirmed

---

## Related Documents

- [PIN-014](PIN-014-m4-technical-review.md) - M4 Technical Review
- [PIN-015](PIN-015-m4-validation-maturity-gates.md) - M4 Validation Gates
- [M4 Runbook](../runbooks/m4-workflow-engine.md) - Operations Runbook

---

## Session Summary: Issues, Decisions & Fixes

### Issues Faced

| # | Issue | Severity | Context |
|---|-------|----------|---------|
| 1 | **Bash arithmetic exit code bug** | HIGH | `((MISMATCHES += 0))` returns exit code 1 under `set -e`, causing shadow script to fail on successful cycles |
| 2 | **Mismatch count false positive** | MEDIUM | `grep -ci "mismatch"` counted "0 mismatches" success lines as errors, showing 88 false positives |
| 3 | **Prometheus permissions denied** | MEDIUM | `workflow-alerts.yml` had 600 permissions, Prometheus couldn't read |
| 4 | **Grafana API format rejection** | LOW | Raw dashboard JSON rejected, required wrapper object |
| 5 | **Webhook URL 404** | LOW | Initial webhook.site token was invalid |
| 6 | **Shadow wrapper unbound variable** | MEDIUM | `$SHADOW` variable referenced but never defined |
| 7 | **Unknown `--shadow` argument** | LOW | Wrapper passed invalid flag to shadow script |

### Decisions Made

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Create comprehensive ops tooling suite | Enable self-service monitoring and incident response for 24h shadow run |
| 2 | Use `\|\| true` pattern for bash arithmetic | Standard bash idiom for `set -e` compatibility with zero results |
| 3 | Create runbook with tabletop checklist | Enable self-certification without dedicated SRE |
| 4 | Store logs in `/var/lib/aos/` | Persistent storage survives /tmp cleanup |
| 5 | 30-second cycle interval | Balance between coverage and resource usage |
| 6 | Create PIN-015 completion template | Streamline sign-off process after shadow run |
| 7 | Separate PIN-016 for ops tooling | Keep validation (PIN-015) and tooling (PIN-016) concerns separate |

### Fixes & Workarounds Applied

| # | Fix | File | Details |
|---|-----|------|---------|
| 1 | Bash arithmetic fix | `run_shadow_simulation.sh:497-499,511` | Added `\|\| true` to all `(( ))` operations |
| 2 | Mismatch grep fix | `shadow_sanity_check.sh:38` | Changed to `grep -E "[1-9][0-9]* mismatches" \| grep -v ", 0 mismatches"` |
| 3 | Prometheus permissions | `workflow-alerts.yml` | `chmod 644` |
| 4 | Grafana API wrapper | API call | Wrapped in `{"dashboard": <json>, "overwrite": true}` |
| 5 | Removed `$SHADOW` variable | `shadow_wrapper_notify.sh` | Deleted unused variable and JSON field |
| 6 | Removed `--shadow` flag | `shadow_wrapper_notify.sh` | Removed invalid argument from invocation |

### Pending Items

| # | Task | Status | Blocker |
|---|------|--------|---------|
| 1 | Monitor 24h shadow run | IN PROGRESS | Time (~23h remaining) |
| 2 | Run runbook tabletop exercise | PENDING | After shadow completes |
| 3 | Update PIN-015 with final results | PENDING | After shadow completes |
| 4 | Sign-off M4 maturity | PENDING | After tabletop |
| 5 | Proceed to M5 | PENDING | After M4 sign-off |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-02 | Added monitoring daemon, debug console, and cron check documentation |
| 2025-12-02 | Updated status with T+58min metrics and active monitoring info |
| 2025-12-02 | Added session summary with issues, decisions, fixes |
| 2025-12-02 | Initial creation with all tooling documented |
