#!/bin/bash
# Shadow Run Cron Check - for crontab
# Runs silently unless issues found, then logs to syslog

LOGFILE=$(ls -t /var/lib/aos/shadow_24h_*.log 2>/dev/null | head -1)
ALERT_LOG="/var/lib/aos/shadow_cron_alerts.log"

# Check if shadow is running
PID=$(pgrep -f "run_shadow_simulation.sh.*--hours 24" | head -1)
if [ -z "$PID" ]; then
    echo "[$(date -Iseconds)] CRITICAL: Shadow process not running" >> "$ALERT_LOG"
    logger -t shadow-monitor "CRITICAL: Shadow process not running"
    exit 1
fi

# Check for mismatches
if [ -n "$LOGFILE" ]; then
    ERRORS=$(grep -E "[1-9][0-9]* mismatches" "$LOGFILE" 2>/dev/null | grep -v ", 0 mismatches" | wc -l)
    if [ "$ERRORS" -gt 0 ]; then
        echo "[$(date -Iseconds)] CRITICAL: $ERRORS mismatch errors found" >> "$ALERT_LOG"
        logger -t shadow-monitor "CRITICAL: $ERRORS mismatch errors found"
        exit 1
    fi
fi

# Check log freshness (alert if no update in 10 min)
if [ -n "$LOGFILE" ]; then
    LAST_MOD=$(stat -c %Y "$LOGFILE" 2>/dev/null || echo 0)
    NOW=$(date +%s)
    AGE=$((NOW - LAST_MOD))
    if [ "$AGE" -gt 600 ]; then
        echo "[$(date -Iseconds)] WARNING: Log stale for ${AGE}s" >> "$ALERT_LOG"
        logger -t shadow-monitor "WARNING: Log stale for ${AGE}s"
    fi
fi

# Periodic status log (every run)
CYCLES=$(grep -c "Running cycle" "$LOGFILE" 2>/dev/null || echo 0)
SUCCESS=$(grep -c ", 0 mismatches" "$LOGFILE" 2>/dev/null || echo 0)
echo "[$(date -Iseconds)] OK: PID=$PID Cycles=$CYCLES Success=$SUCCESS" >> "$ALERT_LOG"

exit 0
