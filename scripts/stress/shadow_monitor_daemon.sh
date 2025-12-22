#!/bin/bash
# Shadow Run Monitor Daemon
# Runs in background, checks every 5 minutes, alerts on issues
#
# Usage: ./shadow_monitor_daemon.sh start|stop|status
# Logs to: /var/lib/aos/shadow_monitor.log

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITOR_PID_FILE="/var/run/shadow_monitor.pid"
MONITOR_LOG="/var/lib/aos/shadow_monitor.log"
CHECK_INTERVAL=300  # 5 minutes
ALERT_FILE="/var/lib/aos/shadow_alerts.json"

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo "[$(date -Iseconds)] $1" | tee -a "$MONITOR_LOG"
}

log_alert() {
    local level="$1"
    local message="$2"
    local timestamp=$(date -Iseconds)

    # Log to file
    echo "[$timestamp] ALERT[$level]: $message" | tee -a "$MONITOR_LOG"

    # Append to alerts JSON
    echo "{\"timestamp\": \"$timestamp\", \"level\": \"$level\", \"message\": \"$message\"}" >> "$ALERT_FILE"

    # Send to webhook if configured
    if [ -n "${SHADOW_HOOK:-}" ]; then
        curl -sS -X POST -H "Content-Type: application/json" \
            -d "{\"alert\": \"$level\", \"message\": \"$message\", \"timestamp\": \"$timestamp\"}" \
            "$SHADOW_HOOK" >/dev/null 2>&1 || true
    fi
}

check_shadow_health() {
    local LOGFILE=$(ls -t /var/lib/aos/shadow_24h_*.log 2>/dev/null | head -1)
    local issues=0

    # 1. Check if shadow process is running
    local PID=$(pgrep -f "run_shadow_simulation.sh.*--hours 24" | head -1)
    if [ -z "$PID" ]; then
        log_alert "CRITICAL" "Shadow process NOT RUNNING"
        return 1
    fi

    # 2. Check for recent log activity (last 10 minutes)
    if [ -n "$LOGFILE" ]; then
        local last_mod=$(stat -c %Y "$LOGFILE" 2>/dev/null || echo 0)
        local now=$(date +%s)
        local age=$((now - last_mod))

        if [ "$age" -gt 600 ]; then
            log_alert "WARNING" "Log file stale - no updates in ${age}s"
            ((issues++))
        fi
    else
        log_alert "WARNING" "No shadow log file found"
        ((issues++))
    fi

    # 3. Check for mismatches
    if [ -n "$LOGFILE" ]; then
        local mismatch_errors=$(grep -E "[1-9][0-9]* mismatches|mismatches detected" "$LOGFILE" 2>/dev/null | grep -v ", 0 mismatches" | wc -l)
        if [ "$mismatch_errors" -gt 0 ]; then
            log_alert "CRITICAL" "MISMATCHES DETECTED: $mismatch_errors errors in log"
            return 1
        fi
    fi

    # 4. Check disk space
    local disk_pct=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
    if [ "$disk_pct" -gt 90 ]; then
        log_alert "WARNING" "Disk usage high: ${disk_pct}%"
        ((issues++))
    fi

    # 5. Check golden directory size
    local GOLDEN_DIR="${GOLDEN_DIR:-/var/lib/aos/golden}"
    if [ -d "$GOLDEN_DIR" ]; then
        local golden_size=$(du -sm "$GOLDEN_DIR" 2>/dev/null | cut -f1)
        if [ "$golden_size" -gt 1000 ]; then
            log_alert "WARNING" "Golden directory large: ${golden_size}MB"
            ((issues++))
        fi
    fi

    # 6. Get current stats
    local cycles=$(grep -c "Running cycle" "$LOGFILE" 2>/dev/null || echo 0)
    local success=$(grep -c ", 0 mismatches" "$LOGFILE" 2>/dev/null || echo 0)

    if [ "$issues" -eq 0 ]; then
        log "HEALTHY: PID=$PID, Cycles=$cycles, Success=$success, Disk=${disk_pct}%"
    else
        log "DEGRADED: PID=$PID, Cycles=$cycles, Issues=$issues"
    fi

    return $issues
}

run_daemon() {
    log "Starting shadow monitor daemon (interval: ${CHECK_INTERVAL}s)"

    while true; do
        check_shadow_health
        sleep "$CHECK_INTERVAL"
    done
}

start_daemon() {
    if [ -f "$MONITOR_PID_FILE" ]; then
        local old_pid=$(cat "$MONITOR_PID_FILE")
        if kill -0 "$old_pid" 2>/dev/null; then
            echo -e "${YELLOW}Monitor already running (PID: $old_pid)${NC}"
            return 1
        fi
    fi

    mkdir -p /var/lib/aos
    nohup "$0" daemon >> "$MONITOR_LOG" 2>&1 &
    local new_pid=$!
    echo "$new_pid" > "$MONITOR_PID_FILE"
    echo -e "${GREEN}Monitor started (PID: $new_pid)${NC}"
    echo "Log: $MONITOR_LOG"
    echo "Alerts: $ALERT_FILE"
}

stop_daemon() {
    if [ -f "$MONITOR_PID_FILE" ]; then
        local pid=$(cat "$MONITOR_PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            rm -f "$MONITOR_PID_FILE"
            echo -e "${GREEN}Monitor stopped (PID: $pid)${NC}"
        else
            rm -f "$MONITOR_PID_FILE"
            echo -e "${YELLOW}Monitor was not running${NC}"
        fi
    else
        echo -e "${YELLOW}No PID file found${NC}"
    fi
}

show_status() {
    echo "═══════════════════════════════════════════════════════════════"
    echo "           SHADOW MONITOR STATUS"
    echo "═══════════════════════════════════════════════════════════════"

    if [ -f "$MONITOR_PID_FILE" ]; then
        local pid=$(cat "$MONITOR_PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "Monitor: ${GREEN}RUNNING${NC} (PID: $pid)"
        else
            echo -e "Monitor: ${RED}DEAD${NC} (stale PID file)"
        fi
    else
        echo -e "Monitor: ${YELLOW}NOT RUNNING${NC}"
    fi

    echo ""
    echo "Log file: $MONITOR_LOG"
    if [ -f "$MONITOR_LOG" ]; then
        echo "Log size: $(du -h "$MONITOR_LOG" | cut -f1)"
        echo ""
        echo "Last 10 log entries:"
        tail -10 "$MONITOR_LOG" | sed 's/^/  /'
    fi

    echo ""
    if [ -f "$ALERT_FILE" ]; then
        local alert_count=$(wc -l < "$ALERT_FILE")
        echo "Alerts: $alert_count total"
        echo "Recent alerts:"
        tail -5 "$ALERT_FILE" | sed 's/^/  /'
    else
        echo "Alerts: None"
    fi

    echo "═══════════════════════════════════════════════════════════════"
}

case "${1:-status}" in
    start)
        start_daemon
        ;;
    stop)
        stop_daemon
        ;;
    status)
        show_status
        ;;
    daemon)
        run_daemon
        ;;
    check)
        check_shadow_health
        ;;
    *)
        echo "Usage: $0 {start|stop|status|check}"
        exit 1
        ;;
esac
