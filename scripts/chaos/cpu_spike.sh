#!/usr/bin/env bash
# scripts/chaos/cpu_spike.sh
#
# CPU spike chaos experiment - simulates high CPU load.
# Tests system behavior under CPU pressure.
#
# Usage:
#   ./cpu_spike.sh                      # 30 second spike, 80% load
#   ./cpu_spike.sh --duration 60        # 60 second spike
#   ./cpu_spike.sh --load 95            # 95% CPU load
#   ./cpu_spike.sh --cores 4            # Use only 4 cores
#   ./cpu_spike.sh --stop               # Stop all stress processes
#
# Environment Variables:
#   CHAOS_ALLOWED  - Must be "true" to run (safety check)

set -e

# Configuration
CHAOS_ALLOWED="${CHAOS_ALLOWED:-false}"

# Defaults
SPIKE_DURATION=30
CPU_LOAD=80
NUM_CORES=$(nproc)

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

run_cpu_spike() {
    local tool
    tool=$(check_stress_tool)

    log_info "Running CPU spike..."
    log_info "Tool: $tool"
    log_info "Duration: ${SPIKE_DURATION}s"
    log_info "Target Load: ${CPU_LOAD}%"
    log_info "Cores: $NUM_CORES"
    echo ""

    if [[ "$tool" == "stress-ng" ]]; then
        # stress-ng has more precise CPU load control
        stress-ng --cpu "$NUM_CORES" --cpu-load "$CPU_LOAD" --timeout "${SPIKE_DURATION}s" &
    else
        # stress doesn't support precise load, use all CPUs
        stress --cpu "$NUM_CORES" --timeout "${SPIKE_DURATION}s" &
    fi

    local pid=$!
    log_info "Stress process started (PID: $pid)"

    # Monitor in background
    (
        sleep "$SPIKE_DURATION"
        log_info "CPU spike duration complete"
    ) &

    wait $pid
    log_info "CPU spike finished"
}

stop_stress() {
    log_info "Stopping all stress processes..."

    # Kill stress-ng processes
    pkill -9 stress-ng 2>/dev/null || true
    pkill -9 stress 2>/dev/null || true

    log_info "Stress processes stopped"
}

show_cpu_stats() {
    log_info "Current CPU stats:"
    if command -v mpstat &> /dev/null; then
        mpstat 1 1
    else
        top -bn1 | head -5
    fi
}

show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "CPU spike chaos experiment"
    echo ""
    echo "Options:"
    echo "  --duration SEC   Spike duration in seconds (default: 30)"
    echo "  --load PERCENT   Target CPU load percentage (default: 80)"
    echo "  --cores NUM      Number of cores to stress (default: all)"
    echo "  --stop           Stop all stress processes"
    echo "  --stats          Show current CPU stats"
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
                SPIKE_DURATION="$2"
                shift 2
                ;;
            --load)
                CPU_LOAD="$2"
                shift 2
                ;;
            --cores)
                NUM_CORES="$2"
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

    log_info "=== CPU Spike Chaos Experiment ==="

    # Handle stop
    if [[ "$do_stop" == true ]]; then
        stop_stress
        exit 0
    fi

    # Handle stats
    if [[ "$show_stats" == true ]]; then
        show_cpu_stats
        exit 0
    fi

    # Safety check
    check_safety

    # Run experiment
    run_cpu_spike

    log_info "=== Chaos experiment complete ==="
}

main "$@"
