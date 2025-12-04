#!/bin/bash
# Shadow Run Debug Console
# Interactive debugging for the 24-hour shadow run
#
# Usage: ./shadow_debug.sh [command]
# Commands: tail, cycles, mismatches, golden, process, full, replay

set -uo pipefail

LOGFILE=$(ls -t /var/lib/aos/shadow_24h_*.log 2>/dev/null | head -1)
SHADOW_DIR=$(ls -td /tmp/shadow_simulation_* 2>/dev/null | head -1)
GOLDEN_DIR="${GOLDEN_DIR:-/var/lib/aos/golden}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

cmd_tail() {
    local lines="${1:-50}"
    echo -e "${CYAN}=== Last $lines log lines ===${NC}"
    tail -n "$lines" "$LOGFILE" 2>/dev/null || echo "No log file found"
}

cmd_cycles() {
    echo -e "${CYAN}=== Cycle Statistics ===${NC}"
    if [ -n "$LOGFILE" ]; then
        local total=$(grep -c "Running cycle" "$LOGFILE" 2>/dev/null || echo 0)
        local success=$(grep -c ", 0 mismatches" "$LOGFILE" 2>/dev/null || echo 0)
        local errors=$(grep -E "[1-9][0-9]* mismatches" "$LOGFILE" 2>/dev/null | grep -v ", 0 mismatches" | wc -l)
        
        echo "Total cycles started: $total"
        echo -e "Successful cycles:    ${GREEN}$success${NC}"
        echo -e "Cycles with errors:   ${RED}$errors${NC}"
        echo ""
        echo "Progress reports:"
        grep "Progress:" "$LOGFILE" | tail -5 | sed 's/^/  /'
    else
        echo "No log file found"
    fi
}

cmd_mismatches() {
    echo -e "${CYAN}=== Mismatch Analysis ===${NC}"
    if [ -n "$LOGFILE" ]; then
        local errors=$(grep -E "[1-9][0-9]* mismatches|MISMATCH|mismatch detected" "$LOGFILE" 2>/dev/null | grep -v ", 0 mismatches")
        if [ -n "$errors" ]; then
            echo -e "${RED}MISMATCHES FOUND:${NC}"
            echo "$errors" | tail -20 | sed 's/^/  /'
        else
            echo -e "${GREEN}No mismatches detected${NC}"
        fi
    fi
    
    # Check cycle reports for details
    if [ -d "$SHADOW_DIR/reports" ]; then
        echo ""
        echo "Checking cycle reports for mismatch details..."
        local mismatch_files=$(grep -l '"mismatches": [1-9]' "$SHADOW_DIR/reports/cycle_*.json" 2>/dev/null)
        if [ -n "$mismatch_files" ]; then
            echo -e "${RED}Cycles with mismatches:${NC}"
            for f in $mismatch_files; do
                echo "  $f:"
                jq '.mismatch_details' "$f" 2>/dev/null | head -20 | sed 's/^/    /'
            done
        else
            echo -e "${GREEN}All cycle reports show 0 mismatches${NC}"
        fi
    fi
}

cmd_golden() {
    echo -e "${CYAN}=== Golden File Analysis ===${NC}"
    
    # Check shadow golden dir
    if [ -d "$SHADOW_DIR/golden" ]; then
        local count=$(find "$SHADOW_DIR/golden" -name "*.json" 2>/dev/null | wc -l)
        local size=$(du -sh "$SHADOW_DIR/golden" 2>/dev/null | cut -f1)
        echo "Shadow golden dir: $SHADOW_DIR/golden"
        echo "  Files: $count"
        echo "  Size:  $size"
        echo "  Recent files:"
        ls -lt "$SHADOW_DIR/golden"/*.json 2>/dev/null | head -5 | awk '{print "    " $NF}'
    fi
    
    # Check persistent golden dir
    if [ -d "$GOLDEN_DIR" ]; then
        local count=$(find "$GOLDEN_DIR" -name "*.json" 2>/dev/null | wc -l)
        local size=$(du -sh "$GOLDEN_DIR" 2>/dev/null | cut -f1)
        echo ""
        echo "Persistent golden dir: $GOLDEN_DIR"
        echo "  Files: $count"
        echo "  Size:  $size"
    fi
    
    # Sample a golden file
    echo ""
    echo "Sample golden file structure:"
    local sample=$(find "$SHADOW_DIR/golden" -name "*.json" 2>/dev/null | head -1)
    if [ -n "$sample" ]; then
        jq 'keys' "$sample" 2>/dev/null | sed 's/^/  /'
    fi
}

cmd_process() {
    echo -e "${CYAN}=== Process Information ===${NC}"
    
    local PID=$(pgrep -f "run_shadow_simulation.sh.*--hours 24" | head -1)
    if [ -n "$PID" ]; then
        echo -e "Shadow process: ${GREEN}RUNNING${NC}"
        echo ""
        ps -p "$PID" -o pid,ppid,stat,etime,%cpu,%mem,args --no-headers | sed 's/^/  /'
        echo ""
        echo "Child processes:"
        pgrep -P "$PID" 2>/dev/null | while read cpid; do
            ps -p "$cpid" -o pid,stat,args --no-headers 2>/dev/null | sed 's/^/  /'
        done
        
        echo ""
        echo "Open files:"
        lsof -p "$PID" 2>/dev/null | grep -E "\.log|\.json|shadow" | head -10 | sed 's/^/  /'
    else
        echo -e "Shadow process: ${RED}NOT RUNNING${NC}"
    fi
}

cmd_replay() {
    echo -e "${CYAN}=== Replay Test ===${NC}"
    echo "Running quick replay verification on recent golden files..."
    
    if [ -d "$SHADOW_DIR" ] && [ -f "$SHADOW_DIR/shadow_runner.py" ]; then
        echo ""
        PRIMARY_WORKERS=1 WORKFLOWS_PER_CYCLE=3 GOLDEN_DIR="$SHADOW_DIR/golden" \
            timeout 30 python3 "$SHADOW_DIR/shadow_runner.py" 2>&1 | jq . 2>/dev/null || cat
    else
        echo "Shadow runner not found in $SHADOW_DIR"
    fi
}

cmd_full() {
    echo -e "${CYAN}══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}           SHADOW RUN DEBUG REPORT${NC}"
    echo -e "${CYAN}══════════════════════════════════════════════════════════════════${NC}"
    echo "Generated: $(date -Iseconds)"
    echo ""
    
    cmd_process
    echo ""
    cmd_cycles
    echo ""
    cmd_mismatches
    echo ""
    cmd_golden
    echo ""
    
    echo -e "${CYAN}=== Resource Usage ===${NC}"
    echo "Disk:"
    df -h / | tail -1 | awk '{print "  Used: " $3 " / " $2 " (" $5 ")"}'
    echo "Memory:"
    free -h | grep Mem | awk '{print "  Used: " $3 " / " $2}'
    echo ""
    
    echo -e "${CYAN}=== Log File Info ===${NC}"
    if [ -n "$LOGFILE" ]; then
        echo "Path: $LOGFILE"
        echo "Size: $(du -h "$LOGFILE" | cut -f1)"
        echo "Lines: $(wc -l < "$LOGFILE")"
        local first=$(head -1 "$LOGFILE" | grep -oE '[0-9]{2}:[0-9]{2}:[0-9]{2}' | head -1)
        local last=$(tail -1 "$LOGFILE" | grep -oE '[0-9]{2}:[0-9]{2}:[0-9]{2}' | head -1)
        echo "Time range: $first - $last"
    fi
    
    echo ""
    echo -e "${CYAN}══════════════════════════════════════════════════════════════════${NC}"
}

show_help() {
    echo "Shadow Run Debug Console"
    echo ""
    echo "Usage: $0 [command] [args]"
    echo ""
    echo "Commands:"
    echo "  tail [n]     Show last n log lines (default: 50)"
    echo "  cycles       Show cycle statistics"
    echo "  mismatches   Analyze any mismatches"
    echo "  golden       Analyze golden files"
    echo "  process      Show process information"
    echo "  replay       Run quick replay test"
    echo "  full         Full debug report"
    echo "  help         Show this help"
    echo ""
    echo "Environment:"
    echo "  LOGFILE:    $LOGFILE"
    echo "  SHADOW_DIR: $SHADOW_DIR"
    echo "  GOLDEN_DIR: $GOLDEN_DIR"
}

case "${1:-help}" in
    tail)
        cmd_tail "${2:-50}"
        ;;
    cycles)
        cmd_cycles
        ;;
    mismatches)
        cmd_mismatches
        ;;
    golden)
        cmd_golden
        ;;
    process)
        cmd_process
        ;;
    replay)
        cmd_replay
        ;;
    full)
        cmd_full
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
