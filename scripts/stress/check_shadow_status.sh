#!/bin/bash
# Check 24-hour Shadow Run Status

LOGFILE=$(ls -t /var/lib/aos/shadow_24h_*.log 2>/dev/null | head -1)

if [ -z "$LOGFILE" ]; then
    echo "No shadow run log found"
    exit 1
fi

echo "═══════════════════════════════════════════════════════════════"
echo "               24-HOUR SHADOW RUN STATUS"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Log file: $LOGFILE"
echo ""

# Check if process is running
PID=$(pgrep -f "run_shadow_simulation.sh.*--hours 24" | head -1)
if [ -n "$PID" ]; then
    echo "Process: RUNNING (PID: $PID)"
    ELAPSED=$(ps -p $PID -o etime= 2>/dev/null | tr -d ' ')
    echo "Elapsed: $ELAPSED"
else
    echo "Process: NOT RUNNING"
fi
echo ""

# Count cycles
CYCLES=$(grep -c "Running cycle" "$LOGFILE" 2>/dev/null || echo "0")
MATCHES=$(grep -c ", 0 mismatches" "$LOGFILE" 2>/dev/null || echo "0")
ERRORS=$(grep -c "mismatches detected" "$LOGFILE" 2>/dev/null || echo "0")

echo "Cycles started:    $CYCLES"
echo "Successful cycles: $MATCHES"
echo "Cycles with errors: $ERRORS"
echo ""

# Last few log lines
echo "Last 10 log entries:"
tail -10 "$LOGFILE"
echo ""
echo "═══════════════════════════════════════════════════════════════"

# Exit with error if errors detected
if [ "$ERRORS" -gt 0 ] 2>/dev/null; then
    exit 1
fi
exit 0
