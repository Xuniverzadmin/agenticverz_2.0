# M4 Incident Playbook

**Version:** 1.0
**Created:** 2025-12-02
**Last Updated:** 2025-12-02

---

## Quick Reference

| Incident Type | Severity | First Action |
|---------------|----------|--------------|
| Mismatch detected | P0 | Emergency stop → Capture → Analyze |
| Shadow process died | P1 | Check logs → Restart if clean |
| Disk full | P1 | Archive golden → Clear tmp |
| Stale logs (>30min) | P2 | Check process → Restart |
| Webhook failures | P3 | Check network → Queue locally |

---

## 1. MISMATCH DETECTED

### Severity: P0 - Critical

**Symptoms:**
- Shadow monitor reports `CRITICAL: X mismatch errors found`
- Cron check exits with code 1
- Log contains `[1-9][0-9]* mismatches`

### Immediate Actions (copy/paste)

```bash
# 1. STOP - Enable emergency workflow stop
./scripts/ops/disable-workflows.sh enable
export WORKFLOW_EMERGENCY_STOP=true

# 2. VERIFY - Confirm stop is active
./scripts/ops/disable-workflows.sh status

# 3. CAPTURE - Preserve all evidence
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
INCIDENT_DIR="/root/reports/m4-incident-$TIMESTAMP"
mkdir -p "$INCIDENT_DIR"

# Capture logs
cp /var/lib/aos/shadow_24h_*.log "$INCIDENT_DIR/"
cp /var/lib/aos/shadow_monitor.log "$INCIDENT_DIR/"
cp /var/lib/aos/shadow_cron_alerts.log "$INCIDENT_DIR/" 2>/dev/null

# Capture golden files
SHADOW_GOLDEN=$(ls -td /tmp/shadow_simulation_*/golden 2>/dev/null | head -1)
if [ -n "$SHADOW_GOLDEN" ]; then
    tar czf "$INCIDENT_DIR/golden_files.tgz" "$SHADOW_GOLDEN"
fi

# Capture system state
ps aux > "$INCIDENT_DIR/ps_aux.txt"
df -h > "$INCIDENT_DIR/disk_usage.txt"
free -h > "$INCIDENT_DIR/memory.txt"

echo "Incident artifacts saved to: $INCIDENT_DIR"
```

### Analysis Steps

```bash
# 4. ANALYZE - Find the mismatching files
LOGFILE=$(ls -t /var/lib/aos/shadow_24h_*.log | head -1)

# Find mismatch entries
grep -E "mismatch|MISMATCH|differ" "$LOGFILE" | head -20

# Get the specific run IDs that failed
grep -B5 "mismatches detected" "$LOGFILE" | grep "run_id"

# 5. DIFF - Run golden diff debug on failing files
# Replace with actual file paths from grep output
python3 scripts/stress/golden_diff_debug.py \
    --golden-a /path/to/primary.golden.json \
    --golden-b /path/to/shadow.golden.json \
    --verbose > "$INCIDENT_DIR/diff_analysis.txt"

# 6. SUMMARIZE - Generate summary report
python3 scripts/stress/golden_diff_debug.py \
    --summary-dir "$SHADOW_GOLDEN" \
    --output "$INCIDENT_DIR/golden_summary.json"
```

### Root Cause Categories

| Category | Indicator | Fix |
|----------|-----------|-----|
| VOLATILE_LEAK | `duration_ms`, `timestamp` in diff | Exclude field from hash |
| SEED_MISMATCH | Different seeds for same run_id | Check seed propagation |
| UNSEEDED_RNG | Random values differ | Add seed to RNG calls |
| EXTERNAL_CALL | API response differs | Mock external calls |
| DETERMINISM_VIOLATION | Step hashes differ | Debug specific step |

### Recovery

```bash
# 7. FIX - After identifying root cause and applying fix

# Re-run failing workflow 10x locally to verify fix
for i in {1..10}; do
    PYTHONPATH=backend python3 -c "
from app.workflow.engine import WorkflowEngine
# ... test specific workflow
"
done

# 8. RESUME - Only after fix verified
./scripts/ops/disable-workflows.sh disable
unset WORKFLOW_EMERGENCY_STOP

# 9. RESTART shadow run (optional - if time permits)
./scripts/stress/run_shadow_simulation.sh --hours 4 --workers 3 --verbose
```

---

## 2. SHADOW PROCESS DIED

### Severity: P1 - High

**Symptoms:**
- `pgrep -f run_shadow_simulation` returns nothing
- Monitor daemon reports `CRITICAL: Shadow process not running`

### Immediate Actions

```bash
# 1. CHECK - What happened?
LOGFILE=$(ls -t /var/lib/aos/shadow_24h_*.log | head -1)
tail -100 "$LOGFILE"

# Check for errors
grep -i "error\|fatal\|killed\|oom" "$LOGFILE" | tail -20

# Check system logs
journalctl -u shadow-monitor --since "1 hour ago" 2>/dev/null || \
    grep shadow /var/log/syslog | tail -20

# 2. ASSESS - How much progress was made?
./scripts/stress/shadow_debug.sh cycles

# 3. DECIDE - Restart or investigate?
# If clean exit (completed early): document and proceed
# If crash/OOM: investigate before restart
```

### Restart Procedure

```bash
# Only restart if logs show clean state (no corruption)

# Check last successful cycle
grep "0 mismatches" "$LOGFILE" | tail -5

# If clean, restart for remaining time
ELAPSED_HOURS=$(grep -c "Running cycle" "$LOGFILE" | awk '{print int($1/120)}')
REMAINING=$((24 - ELAPSED_HOURS))

if [ "$REMAINING" -gt 0 ]; then
    nohup ./scripts/stress/run_shadow_simulation.sh \
        --hours "$REMAINING" \
        --workers 3 \
        --verbose \
        >> /var/lib/aos/shadow_24h_continued.log 2>&1 &
    echo "Restarted shadow run for $REMAINING hours (PID: $!)"
fi
```

---

## 3. DISK FULL

### Severity: P1 - High

**Symptoms:**
- `df -h` shows >95% usage
- Monitor daemon reports disk warning/critical
- Write operations failing

### Immediate Actions

```bash
# 1. ASSESS - What's using space?
df -h /tmp /var/lib/aos /root
du -sh /tmp/shadow_simulation_* 2>/dev/null
du -sh /var/lib/aos/golden 2>/dev/null

# 2. ARCHIVE - Move old golden files
mkdir -p /root/archive/golden
SHADOW_GOLDEN=$(ls -td /tmp/shadow_simulation_*/golden 2>/dev/null | head -1)

# Archive golden files older than 1 day
find "$SHADOW_GOLDEN" -type f -name "*.json" -mtime +1 -print0 | \
    xargs -0 -I{} mv {} /root/archive/golden/

# Or compress in place
tar czf /root/archive/golden_$(date +%Y%m%d).tgz "$SHADOW_GOLDEN"

# 3. CLEANUP - Remove temporary files
rm -rf /tmp/shadow_simulation_*/summaries/*.json 2>/dev/null

# 4. VERIFY
df -h /tmp /var/lib/aos
```

### Prevention

```bash
# Add to crontab for automatic cleanup
echo "0 */4 * * * find /tmp/shadow_simulation_*/golden -type f -mtime +1 -delete" | crontab -
```

---

## 4. STALE LOGS

### Severity: P2 - Medium

**Symptoms:**
- Log file not updated in >10 minutes
- Monitor reports `WARNING: Log stale for Xs`

### Immediate Actions

```bash
# 1. CHECK - Is process running but stuck?
PID=$(pgrep -f "run_shadow_simulation.sh.*--hours 24" | head -1)

if [ -n "$PID" ]; then
    # Process exists - check what it's doing
    ps -p "$PID" -o pid,state,etime,cmd

    # Check for zombie children
    ps --ppid "$PID" -o pid,state,cmd

    # Check file descriptors
    ls -la /proc/$PID/fd/ 2>/dev/null | head -10

    # Check for blocking I/O
    cat /proc/$PID/stack 2>/dev/null
else
    echo "Process not running - see 'SHADOW PROCESS DIED' section"
fi

# 2. If stuck on external call, may need to kill and restart
# kill -TERM $PID  # graceful
# kill -9 $PID     # force (last resort)
```

---

## 5. WEBHOOK FAILURES

### Severity: P3 - Low

**Symptoms:**
- Alerts not reaching webhook.site
- `curl` to webhook URL fails

### Immediate Actions

```bash
# 1. TEST - Is webhook reachable?
curl -v -X POST https://webhook.site/YOUR_TOKEN \
    -H "Content-Type: application/json" \
    -d '{"test": "connectivity"}'

# 2. If network issue, alerts still logged locally
tail -20 /var/lib/aos/shadow_monitor.log
tail -20 /var/lib/aos/shadow_cron_alerts.log

# 3. Check syslog for cron alerts
grep shadow-monitor /var/log/syslog | tail -20
```

---

## Post-Incident Checklist

After any P0/P1 incident:

- [ ] Root cause identified and documented
- [ ] Fix applied and verified
- [ ] Incident artifacts archived (`/root/reports/m4-incident-*`)
- [ ] PIN-015 updated with incident summary
- [ ] Shadow run resumed or completed
- [ ] Monitoring verified working

---

## Contacts & Escalation

| Role | Contact | When |
|------|---------|------|
| Primary Operator | (self) | All incidents |
| Backup | - | If primary unavailable |

---

## Related Documents

- [PIN-015](../memory-pins/PIN-015-m4-validation-maturity-gates.md) - Validation Gates
- [PIN-016](../memory-pins/PIN-016-m4-ops-tooling-runbook.md) - Ops Tooling
- [PIN-017](../memory-pins/PIN-017-m4-monitoring-infrastructure.md) - Monitoring
- [M4 Runbook](m4-workflow-engine.md) - Operations Guide
