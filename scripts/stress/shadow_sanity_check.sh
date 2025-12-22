#!/bin/bash
# M4 Shadow Run - 4-Hour Sanity Check
# Run this every 4 hours during the 24-hour shadow run

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

LOGFILE=$(ls -t /var/lib/aos/shadow_24h_*.log 2>/dev/null | head -1)
GOLDEN_DIR="${GOLDEN_DIR:-/var/lib/aos/golden}"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}         M4 SHADOW RUN - 4-HOUR SANITY CHECK${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Timestamp: $(date -Iseconds)"
echo ""

# 1. Check process status
echo -e "${YELLOW}[1/5] Process Status${NC}"
PID=$(pgrep -f "run_shadow_simulation.sh.*--hours 24" | head -1 || true)
if [ -n "$PID" ]; then
    ELAPSED=$(ps -p $PID -o etime= 2>/dev/null | tr -d ' ')
    echo -e "  ${GREEN}RUNNING${NC} (PID: $PID, Elapsed: $ELAPSED)"
else
    echo -e "  ${RED}NOT RUNNING${NC}"
fi
echo ""

# 2. Check for mismatches
echo -e "${YELLOW}[2/5] Mismatch Check${NC}"
if [ -n "$LOGFILE" ]; then
    # Count actual mismatch errors (not "0 mismatches" success lines)
    MISMATCH_ERRORS=$(grep -E "[1-9][0-9]* mismatches|mismatches detected|MISMATCH" "$LOGFILE" 2>/dev/null | grep -v ", 0 mismatches" | wc -l || echo "0")
    ZERO_MISMATCH=$(grep -c ", 0 mismatches" "$LOGFILE" 2>/dev/null || echo "0")

    if [ "$MISMATCH_ERRORS" -gt 0 ] 2>/dev/null; then
        echo -e "  ${RED}MISMATCHES DETECTED: $MISMATCH_ERRORS error lines${NC}"
        echo "  Recent errors:"
        grep -E "[1-9][0-9]* mismatches|mismatches detected|MISMATCH" "$LOGFILE" 2>/dev/null | grep -v ", 0 mismatches" | tail -5 | sed 's/^/    /'
    else
        echo -e "  ${GREEN}NO MISMATCHES${NC} ($ZERO_MISMATCH successful cycles)"
    fi
else
    echo -e "  ${RED}No log file found${NC}"
fi
echo ""

# 3. Disk usage
echo -e "${YELLOW}[3/5] Disk Usage${NC}"
if [ -d "$GOLDEN_DIR" ]; then
    GOLDEN_SIZE=$(du -sh "$GOLDEN_DIR" 2>/dev/null | cut -f1)
    GOLDEN_COUNT=$(find "$GOLDEN_DIR" -name "*.json" 2>/dev/null | wc -l)
    echo "  Golden dir: $GOLDEN_DIR"
    echo "  Size: $GOLDEN_SIZE"
    echo "  Files: $GOLDEN_COUNT"
else
    echo "  Golden dir not found: $GOLDEN_DIR"
fi

# Check /tmp usage
TMP_SHADOW=$(du -sh /tmp/shadow_simulation_* 2>/dev/null | tail -1 || echo "N/A")
echo "  Shadow tmp: $TMP_SHADOW"

# Check overall disk
ROOT_DISK=$(df -h / | tail -1 | awk '{print $4 " free (" $5 " used)"}')
echo "  Root disk: $ROOT_DISK"
echo ""

# 4. Recent log entries
echo -e "${YELLOW}[4/5] Recent Activity (last 10 entries)${NC}"
if [ -n "$LOGFILE" ]; then
    tail -10 "$LOGFILE" 2>/dev/null | sed 's/^/  /'
else
    echo "  No log file available"
fi
echo ""

# 5. Prometheus metrics (if available)
echo -e "${YELLOW}[5/5] Prometheus Metrics${NC}"
PROM_URL="${PROMETHEUS_URL:-http://localhost:9090}"
if curl -sf "$PROM_URL/api/v1/query?query=up" >/dev/null 2>&1; then
    echo "  Prometheus: ${GREEN}REACHABLE${NC}"

    # Check workflow metrics if available
    REPLAY_TOTAL=$(curl -sf "$PROM_URL/api/v1/query?query=workflow_replay_verifications_total" 2>/dev/null | jq -r '.data.result[0].value[1] // "N/A"' 2>/dev/null || echo "N/A")
    REPLAY_FAIL=$(curl -sf "$PROM_URL/api/v1/query?query=workflow_replay_failures_total" 2>/dev/null | jq -r '.data.result[0].value[1] // "N/A"' 2>/dev/null || echo "N/A")

    echo "  Replay verifications: $REPLAY_TOTAL"
    echo "  Replay failures: $REPLAY_FAIL"
else
    echo "  Prometheus: ${YELLOW}NOT REACHABLE${NC} (expected if running locally)"
fi
echo ""

# Summary
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
if [ -n "$PID" ]; then
    echo -e "${GREEN}Shadow run is HEALTHY${NC}"
else
    echo -e "${RED}Shadow run is NOT RUNNING${NC}"
fi
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
