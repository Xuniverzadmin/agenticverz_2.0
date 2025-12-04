# PIN-017: M4 Monitoring Infrastructure

**Serial:** PIN-017
**Title:** M4 Shadow Run Monitoring Infrastructure
**Category:** Operations / Monitoring
**Status:** COMPLETE
**Created:** 2025-12-02
**Updated:** 2025-12-02

---

## Executive Summary

This PIN documents the monitoring infrastructure created to ensure reliable oversight of the 24-hour M4 shadow simulation. The infrastructure provides multi-layered monitoring with daemon-based continuous checks, cron-based system integration, and interactive debugging capabilities.

---

## Monitoring Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SHADOW RUN MONITORING                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Daemon     │    │    Cron      │    │   Debug      │      │
│  │  (5 min)     │    │  (15 min)    │    │  Console     │      │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘      │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ shadow_      │    │ shadow_      │    │ shadow_      │      │
│  │ monitor.log  │    │ cron_alerts  │    │ (stdout)     │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                                   │
│         ▼                   ▼                                   │
│  ┌──────────────┐    ┌──────────────┐                          │
│  │  Webhook     │    │   Syslog     │                          │
│  │  (optional)  │    │   logger     │                          │
│  └──────────────┘    └──────────────┘                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Shadow Monitor Daemon

**Path:** `scripts/stress/shadow_monitor_daemon.sh`
**Interval:** 5 minutes
**Log:** `/var/lib/aos/shadow_monitor.log`

**Health Checks Performed:**
| Check | Threshold | Alert Level |
|-------|-----------|-------------|
| Process alive | PID exists | CRITICAL |
| Log freshness | < 10 min | WARNING |
| Mismatch count | = 0 | CRITICAL |
| Disk usage | < 90% | WARNING |
| Disk usage | < 95% | CRITICAL |

**Commands:**
```bash
# Start daemon
./scripts/stress/shadow_monitor_daemon.sh start

# Check status
./scripts/stress/shadow_monitor_daemon.sh status

# Single health check
./scripts/stress/shadow_monitor_daemon.sh check

# Stop daemon
./scripts/stress/shadow_monitor_daemon.sh stop
```

**Output Format:**
```
[2025-12-02T14:05:31+01:00] HEALTHY: PID=752320, Cycles=106, Success=116, Disk=14%
[2025-12-02T14:10:31+01:00] HEALTHY: PID=752320, Cycles=117, Success=127, Disk=14%
```

---

### 2. Shadow Cron Check

**Path:** `scripts/stress/shadow_cron_check.sh`
**Interval:** 15 minutes (via crontab)
**Log:** `/var/lib/aos/shadow_cron_alerts.log`

**Crontab Entry:**
```bash
*/15 * * * * /root/agenticverz2.0/scripts/stress/shadow_cron_check.sh
```

**Behavior:**
- Silent on success (logs OK status only)
- Logs to syslog on WARNING/CRITICAL
- Returns exit code 1 on critical issues

**Checks:**
1. Shadow process running
2. Mismatch detection (excludes "0 mismatches" false positives)
3. Log freshness (alert if stale > 10 min)

**Integration:**
- Syslog: `logger -t shadow-monitor "MESSAGE"`
- System monitoring tools can watch for `shadow-monitor` tag

---

### 3. Shadow Debug Console

**Path:** `scripts/stress/shadow_debug.sh`
**Type:** Interactive / On-demand

**Commands:**
| Command | Description |
|---------|-------------|
| `full` | Complete status report (all sections) |
| `tail` | Last 20 log lines |
| `cycles` | Cycle statistics and progress |
| `mismatches` | Mismatch analysis and details |
| `golden` | Golden file counts, sizes, samples |
| `process` | Process info, children, open files |
| `replay <id>` | Replay specific workflow by run_id |

**Usage:**
```bash
# Full report
./scripts/stress/shadow_debug.sh full

# Specific analysis
./scripts/stress/shadow_debug.sh mismatches
./scripts/stress/shadow_debug.sh golden
```

**Full Report Sections:**
1. Process Information (PID, elapsed, children, open files)
2. Cycle Statistics (total, successful, errors, progress)
3. Mismatch Analysis (error detection, cycle reports)
4. Golden File Analysis (counts, sizes, recent files, structure)
5. Resource Usage (disk, memory)
6. Log File Info (path, size, lines, time range)

---

## Log Files

| Log File | Purpose | Rotation |
|----------|---------|----------|
| `/var/lib/aos/shadow_24h_*.log` | Main shadow run output | Per-run |
| `/var/lib/aos/shadow_monitor.log` | Daemon health checks | Manual |
| `/var/lib/aos/shadow_cron_alerts.log` | Cron check alerts | Manual |
| `/var/log/syslog` | System-level alerts | System |

---

## Alert Levels

| Level | Meaning | Action |
|-------|---------|--------|
| HEALTHY | All checks pass | None |
| WARNING | Non-critical issue | Monitor closely |
| CRITICAL | Failure detected | Immediate investigation |

**Critical Conditions:**
- Shadow process not running
- Mismatches detected (non-zero count)
- Disk usage > 95%
- Log stale > 30 minutes

**Warning Conditions:**
- Log stale 10-30 minutes
- Disk usage 90-95%

---

## Current Shadow Run Status

**Run Details:**
- Started: 2025-12-02 13:12:19 CET
- Expected End: 2025-12-03 ~13:12 CET
- PID: 752320
- Log: `/var/lib/aos/shadow_24h_20251202_131219.log`

**Status at T+1h:**
| Metric | Value |
|--------|-------|
| Cycles | 119 |
| Workflows | ~1,071 |
| Replays | ~1,071 |
| Mismatches | 0 |
| Golden Files | ~1,100 |
| Disk Usage | 14% |

**Active Monitoring:**
- Monitor Daemon: PID 790726
- Cron Job: Active (*/15 * * * *)

---

## Troubleshooting

### Daemon Not Starting
```bash
# Check for existing process
pgrep -f shadow_monitor_daemon

# Check log permissions
ls -la /var/lib/aos/shadow_monitor.log

# Start with debug
bash -x ./scripts/stress/shadow_monitor_daemon.sh start
```

### Cron Not Running
```bash
# Verify cron entry
crontab -l | grep shadow

# Check cron log
grep shadow /var/log/syslog

# Manual test
/root/agenticverz2.0/scripts/stress/shadow_cron_check.sh
```

### Debug Console Errors
```bash
# Ensure shadow run is active
pgrep -f run_shadow_simulation

# Check log file exists
ls -la /var/lib/aos/shadow_24h_*.log
```

---

## Integration with Existing Tools

| Existing Tool | Integration Point |
|---------------|-------------------|
| `shadow_sanity_check.sh` | 4-hour manual checks |
| `check_shadow_status.sh` | Quick status queries |
| `golden_diff_debug.py` | Mismatch root cause analysis |
| `disable-workflows.sh` | Emergency stop capability |

**Recommended Schedule:**
- Daemon: Continuous (5 min intervals)
- Cron: Continuous (15 min intervals)
- Sanity Check: Manual at T+4h, T+8h, T+12h, T+16h, T+20h
- Debug Console: On-demand for investigation

---

## Files Created

| File | Size | Purpose |
|------|------|---------|
| `scripts/stress/shadow_monitor_daemon.sh` | 4.8K | Background monitoring |
| `scripts/stress/shadow_debug.sh` | 5.2K | Interactive debugging |
| `scripts/stress/shadow_cron_check.sh` | 1.3K | Cron-based checks |

---

## Related Documents

- [PIN-015](PIN-015-m4-validation-maturity-gates.md) - M4 Validation Gates
- [PIN-016](PIN-016-m4-ops-tooling-runbook.md) - M4 Ops Tooling (updated)
- [M4 Runbook](../runbooks/m4-workflow-engine.md) - Operations Guide

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-02 | Initial creation documenting monitoring infrastructure |
