#!/usr/bin/env bash
# scripts/chaos/memory_pressure.sh
#
# Memory pressure chaos experiment - simulates high memory usage.
# Tests system behavior under memory pressure and OOM handling.
#
# Usage:
#   ./memory_pressure.sh                    # 30 second, 1GB allocation
#   ./memory_pressure.sh --duration 60      # 60 second pressure
#   ./memory_pressure.sh --size 2G          # Allocate 2GB
#   ./memory_pressure.sh --percent 70       # Use 70% of available RAM
#   ./memory_pressure.sh --stop             # Stop all memory stress
#
# Environment Variables:
#   CHAOS_ALLOWED  - Must be "true" to run (safety check)

set -e

# Configuration
CHAOS_ALLOWED="${CHAOS_ALLOWED:-false}"

# Defaults
PRESSURE_DURATION=30
MEMORY_SIZE="1G"
MEMORY_PERCENT=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# =============================================================================
# Functions
# =============================================================================

log_info() {
    echo -e "${GREEN}[CHAOS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[CHAOS]${NC} $1"
}

log_error() {
    echo -e "${RED}[CHAOS]${NC} $1"
}

check_safety() {
    if [[ "$CHAOS_ALLOWED" != "true" ]]; then
        log_error "CHAOS_ALLOWED is not set to 'true'. Refusing to run."
        log_error "Set CHAOS_ALLOWED=true to enable chaos experiments."
        exit 1
    fi
}

check_stress_tool() {
    if command -v stress-ng &> /dev/null; then
        echo "stress-ng"
    elif command -v stress &> /dev/null; then
        echo "stress"
    else
        log_error "Neither stress-ng nor stress found."
        log_error "Install with: apt-get install stress-ng"
        exit 1
    fi
}

get_available_memory() {
    # Get available memory in bytes
    local available
    available=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
    echo $((available * 1024))
}

calculate_memory_from_percent() {
    local percent=$1
    local available
    available=$(get_available_memory)
    local target=$((available * percent / 100))

    # Convert to human-readable
    if [[ $target -gt $((1024 * 1024 * 1024)) ]]; then
        echo "$((target / 1024 / 1024 / 1024))G"
    else
        echo "$((target / 1024 / 1024))M"
    fi
}

show_memory_stats() {
    log_info "Current memory stats:"
    free -h
    echo ""
    log_info "Available memory: $(awk '/MemAvailable/ {printf "%.2f GB", $2/1024/1024}' /proc/meminfo)"
}

run_memory_pressure() {
    local tool
    tool=$(check_stress_tool)

    # Calculate size from percent if specified
    local size="$MEMORY_SIZE"
    if [[ -n "$MEMORY_PERCENT" ]]; then
        size=$(calculate_memory_from_percent "$MEMORY_PERCENT")
        log_info "Calculated size from ${MEMORY_PERCENT}%: $size"
    fi

    log_info "Running memory pressure..."
    log_info "Tool: $tool"
    log_info "Duration: ${PRESSURE_DURATION}s"
    log_info "Memory Size: $size"
    echo ""

    show_memory_stats

    if [[ "$tool" == "stress-ng" ]]; then
        stress-ng --vm 1 --vm-bytes "$size" --vm-keep --timeout "${PRESSURE_DURATION}s" &
    else
        stress --vm 1 --vm-bytes "$size" --timeout "${PRESSURE_DURATION}s" &
    fi

    local pid=$!
    log_info "Memory stress started (PID: $pid)"

    # Monitor memory usage
    (
        while kill -0 $pid 2>/dev/null; do
            local used
            used=$(awk '/MemAvailable/ {printf "%.1f", (1 - $2/'"$(awk '/MemTotal/ {print $2}' /proc/meminfo)"') * 100}' /proc/meminfo)
            echo -ne "\r[CHAOS] Memory usage: ${used}%    "
            sleep 2
        done
        echo ""
    ) &

    wait $pid
    log_info "Memory pressure finished"
    echo ""
    show_memory_stats
}

stop_stress() {
    log_info "Stopping all memory stress processes..."

    pkill -9 stress-ng 2>/dev/null || true
    pkill -9 stress 2>/dev/null || true

    log_info "Memory stress processes stopped"
    echo ""
    show_memory_stats
}

show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Memory pressure chaos experiment"
    echo ""
    echo "Options:"
    echo "  --duration SEC   Pressure duration in seconds (default: 30)"
    echo "  --size SIZE      Memory to allocate, e.g., 1G, 500M (default: 1G)"
    echo "  --percent PCT    Use percentage of available RAM (overrides --size)"
    echo "  --stop           Stop all memory stress processes"
    echo "  --stats          Show current memory stats"
    echo "  --help           Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  CHAOS_ALLOWED    - Must be 'true' to run"
}

# =============================================================================
# Main
# =============================================================================

main() {
    local do_stop=false
    local show_stats=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --duration)
                PRESSURE_DURATION="$2"
                shift 2
                ;;
            --size)
                MEMORY_SIZE="$2"
                shift 2
                ;;
            --percent)
                MEMORY_PERCENT="$2"
                shift 2
                ;;
            --stop)
                do_stop=true
                shift
                ;;
            --stats)
                show_stats=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    log_info "=== Memory Pressure Chaos Experiment ==="

    # Handle stop
    if [[ "$do_stop" == true ]]; then
        stop_stress
        exit 0
    fi

    # Handle stats
    if [[ "$show_stats" == true ]]; then
        show_memory_stats
        exit 0
    fi

    # Safety check
    check_safety

    # Run experiment
    run_memory_pressure

    log_info "=== Chaos experiment complete ==="
}

main "$@"
