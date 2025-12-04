# AOS Operations Suite Overview

**Version:** 1.0
**Created:** 2025-12-02
**Last Updated:** 2025-12-02

---

## Quick Reference

| Tool | Purpose | Path | Frequency |
|------|---------|------|-----------|
| Shadow Monitor Daemon | Continuous health checks | `scripts/stress/shadow_monitor_daemon.sh` | Every 5 min |
| Shadow Debug Console | Interactive debugging | `scripts/stress/shadow_debug.sh` | On-demand |
| Shadow Cron Check | System-level monitoring | `scripts/stress/shadow_cron_check.sh` | Every 15 min |
| Golden Retention | Storage management | `scripts/ops/golden_retention.sh` | Every 6h |
| Emergency Stop | Workflow kill switch | `scripts/ops/disable-workflows.sh` | Emergency |
| Golden Diff Debug | Mismatch analysis | `scripts/stress/golden_diff_debug.py` | On-demand |
| Shadow Sanity Check | 4-hour health check | `scripts/stress/shadow_sanity_check.sh` | Every 4h |

---

## 1. Monitoring Daemon

**Path:** `scripts/stress/shadow_monitor_daemon.sh`
**Log:** `/var/lib/aos/shadow_monitor.log`

### Purpose
Background daemon providing continuous health monitoring during shadow simulations.

### Commands

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

### Health Checks Performed

| Check | Threshold | Alert Level |
|-------|-----------|-------------|
| Process alive | PID exists | CRITICAL |
| Log freshness | < 10 min | WARNING |
| Mismatch count | = 0 | CRITICAL |
| Disk usage | < 90% | WARNING |
| Disk usage | < 95% | CRITICAL |

### Output Format
```
[2025-12-02T14:05:31+01:00] HEALTHY: PID=752320, Cycles=106, Success=116, Disk=14%
```

---

## 2. Debug Console

**Path:** `scripts/stress/shadow_debug.sh`

### Purpose
Interactive debugging console for investigating shadow run issues.

### Commands

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

### Full Report Sections

1. **Process Information** - PID, elapsed time, child processes, open files
2. **Cycle Statistics** - Total cycles, successful, errors, progress reports
3. **Mismatch Analysis** - Error detection, cycle reports with issues
4. **Golden File Analysis** - Counts, sizes, recent files, structure sample
5. **Resource Usage** - Disk space, memory usage
6. **Log File Info** - Path, size, line count, time range

---

## 3. Cron Check

**Path:** `scripts/stress/shadow_cron_check.sh`
**Log:** `/var/lib/aos/shadow_cron_alerts.log`
**Syslog Tag:** `shadow-monitor`

### Purpose
Silent cron-based monitoring that only logs/alerts on issues.

### Crontab Entry
```bash
*/15 * * * * /root/agenticverz2.0/scripts/stress/shadow_cron_check.sh
```

### Checks Performed
1. Shadow process running
2. Mismatch detection (excludes "0 mismatches" false positives)
3. Log freshness (alert if stale > 10 min)

### Integration
- Logs to syslog via `logger -t shadow-monitor`
- Exit code 1 on critical issues
- Silent on success (logs OK status only)

### Viewing Alerts
```bash
# Check cron alert log
tail -50 /var/lib/aos/shadow_cron_alerts.log

# Check syslog
grep shadow-monitor /var/log/syslog | tail -20
```

---

## 4. Retention Script

**Path:** `scripts/ops/golden_retention.sh`
**Log:** `/var/lib/aos/golden_retention.log`

### Purpose
Manage golden file storage to prevent disk exhaustion during long-running simulations.

### Commands

```bash
# Show current storage status
./scripts/ops/golden_retention.sh status

# Archive files older than N days
./scripts/ops/golden_retention.sh archive --days 1

# Delete old files (with confirmation)
./scripts/ops/golden_retention.sh cleanup --days 7

# Force delete without confirmation
./scripts/ops/golden_retention.sh cleanup --days 7 --force

# Dry run (show what would happen)
./scripts/ops/golden_retention.sh archive --days 1 --dry-run

# Verify archive integrity
./scripts/ops/golden_retention.sh verify

# Restore from archive
./scripts/ops/golden_retention.sh restore /path/to/archive.tgz
```

### Environment Variables
- `ARCHIVE_DIR` - Archive location (default: `/root/archive/golden`)
- `RETENTION_DAYS` - Default retention period (default: 7)

### Monitored Directories
- `/tmp/shadow_simulation_*/golden`
- `/var/lib/aos/golden`

### Storage Projections (24h Shadow Run)

| Time | Est. Cycles | Est. Files | Est. Size |
|------|-------------|------------|-----------|
| T+6h | ~720 | ~6,500 | ~26M |
| T+12h | ~1,440 | ~13,000 | ~52M |
| T+24h | ~2,880 | ~26,000 | ~104M |

---

## 5. Emergency Workflow Stop

**Path:** `scripts/ops/disable-workflows.sh`
**Flag File:** `/var/lib/aos/.workflow_emergency_stop`

### Purpose
Emergency kill switch for workflow execution during incidents.

### Commands

```bash
# Enable emergency stop
./scripts/ops/disable-workflows.sh enable

# Check status
./scripts/ops/disable-workflows.sh status

# Disable (re-enable workflows)
./scripts/ops/disable-workflows.sh disable
```

### Mechanism
1. Creates flag file at `/var/lib/aos/.workflow_emergency_stop`
2. Sets `WORKFLOW_EMERGENCY_STOP` environment variable
3. Logs timestamp and user for audit

### When to Use
- P0: Mismatch detected
- P1: Unrecoverable process failure
- Before: Manual intervention on production data

---

## 6. Golden Lifecycle Tools

### Golden Diff Debug

**Path:** `scripts/stress/golden_diff_debug.py`

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

**Root Cause Categories:**
- `VOLATILE_LEAK` - Timestamp, duration leaked into hash
- `SEED_MISMATCH` - Different seeds for same run_id
- `UNSEEDED_RNG` - Random values without seed
- `EXTERNAL_CALL` - External API response differs
- `DETERMINISM_VIOLATION` - Step hashes differ unexpectedly

### Shadow Sanity Check

**Path:** `scripts/stress/shadow_sanity_check.sh`

```bash
# Run 4-hour sanity check
./scripts/stress/shadow_sanity_check.sh
```

**5 Sections:**
1. Process Status - PID and elapsed time
2. Mismatch Check - Error detection with correct filtering
3. Disk Usage - Storage monitoring
4. Recent Activity - Last 10 log entries
5. Prometheus Metrics - Workflow metrics if available

### Quick Status Check

**Path:** `scripts/stress/check_shadow_status.sh`

```bash
# Quick one-line status
./scripts/stress/check_shadow_status.sh
```

---

## Operational Workflows

### Starting a Shadow Run

```bash
# 1. Pre-flight checks
curl -s http://localhost:8000/health | jq .status
redis-cli ping
docker ps | grep -E "worker|backend"
df -h /tmp /var/lib/aos

# 2. Start shadow simulation
nohup ./scripts/stress/run_shadow_simulation.sh \
    --hours 24 --workers 3 --verbose \
    >> /var/lib/aos/shadow_24h_$(date +%Y%m%d_%H%M%S).log 2>&1 &

# 3. Start monitoring
./scripts/stress/shadow_monitor_daemon.sh start

# 4. Verify cron is active
crontab -l | grep shadow
```

### During Shadow Run

| Frequency | Tool | Command |
|-----------|------|---------|
| Every 1-2h | Quick status | `./scripts/stress/check_shadow_status.sh` |
| Every 4h | Sanity check | `./scripts/stress/shadow_sanity_check.sh` |
| Every 6h | Storage check | `./scripts/ops/golden_retention.sh status` |
| On-demand | Full debug | `./scripts/stress/shadow_debug.sh full` |

### Post-Shadow Run

```bash
# 1. Verify completion
grep "Shadow simulation complete" /var/lib/aos/shadow_24h_*.log

# 2. Stop monitoring
./scripts/stress/shadow_monitor_daemon.sh stop

# 3. Archive golden files
./scripts/ops/golden_retention.sh archive --days 0

# 4. Generate summary
python3 scripts/stress/golden_diff_debug.py \
    --summary-dir /tmp/shadow_simulation_*/golden \
    --output /root/reports/m4-shadow-summary.json
```

### Incident Response

```bash
# 1. Emergency stop
./scripts/ops/disable-workflows.sh enable

# 2. Capture evidence
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p /root/reports/m4-incident-$TIMESTAMP
cp /var/lib/aos/shadow_*.log /root/reports/m4-incident-$TIMESTAMP/

# 3. Analyze
python3 scripts/stress/golden_diff_debug.py \
    --summary-dir /tmp/shadow_simulation_*/golden \
    > /root/reports/m4-incident-$TIMESTAMP/analysis.txt

# 4. Follow playbook
# See: docs/runbooks/m4-incident-playbook.md
```

---

## Log File Locations

| Log | Path | Purpose |
|-----|------|---------|
| Shadow run | `/var/lib/aos/shadow_24h_*.log` | Main simulation output |
| Monitor daemon | `/var/lib/aos/shadow_monitor.log` | Daemon health checks |
| Cron alerts | `/var/lib/aos/shadow_cron_alerts.log` | Cron check results |
| Golden retention | `/var/lib/aos/golden_retention.log` | Archival operations |
| System | `/var/log/syslog` | Shadow-monitor tagged entries |

---

## Troubleshooting

### Daemon Won't Start
```bash
# Check for existing process
pgrep -f shadow_monitor_daemon
# Kill if needed
pkill -f shadow_monitor_daemon
# Retry
./scripts/stress/shadow_monitor_daemon.sh start
```

### Cron Not Running
```bash
# Verify entry exists
crontab -l | grep shadow
# Check cron service
systemctl status cron
# Manual test
/root/agenticverz2.0/scripts/stress/shadow_cron_check.sh
```

### Disk Full
```bash
# Check usage
df -h /tmp /var/lib/aos
# Emergency cleanup
./scripts/ops/golden_retention.sh cleanup --days 1 --force
# Or archive first
./scripts/ops/golden_retention.sh archive --days 0
```

### Shadow Process Stuck
```bash
# Check state
./scripts/stress/shadow_debug.sh process
# Check for blocking I/O
cat /proc/$(pgrep -f run_shadow_simulation)/stack
# If truly stuck, kill gracefully
kill -TERM $(pgrep -f run_shadow_simulation)
```

---

## Related Documentation

| Document | Path | Purpose |
|----------|------|---------|
| PIN-016 | `docs/memory-pins/PIN-016-m4-ops-tooling-runbook.md` | Ops tooling overview |
| PIN-017 | `docs/memory-pins/PIN-017-m4-monitoring-infrastructure.md` | Monitoring details |
| PIN-018 | `docs/memory-pins/PIN-018-m4-incident-ops-readiness.md` | Incident readiness |
| Incident Playbook | `docs/runbooks/m4-incident-playbook.md` | Incident response |
| M4 Runbook | `docs/runbooks/m4-workflow-engine.md` | Full operations guide |
