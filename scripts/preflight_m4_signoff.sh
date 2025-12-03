#!/usr/bin/env bash
# preflight_m4_signoff.sh - Gate runtime changes until M4 validation complete
#
# Usage:
#   ./scripts/preflight_m4_signoff.sh          # Check if M4 signoff is present
#   M4_SIGNOFF=1 ./scripts/preflight_m4_signoff.sh  # Bypass for experiments
#
# Exit codes:
#   0 - Signoff present, safe to proceed
#   1 - Signoff missing, block merge
#   2 - Shadow run still in progress

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[PREFLIGHT]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[PREFLIGHT]${NC} $1"; }
log_error() { echo -e "${RED}[PREFLIGHT]${NC} $1"; }

# Check 1: M4_SIGNOFF environment variable
check_signoff_env() {
    if [[ -n "${M4_SIGNOFF:-}" ]]; then
        log_info "M4_SIGNOFF environment variable is set"
        return 0
    fi
    return 1
}

# Check 2: M4_SIGNOFF file in project root
check_signoff_file() {
    if [[ -f "$PROJECT_ROOT/.m4_signoff" ]]; then
        log_info "M4 signoff file found: $PROJECT_ROOT/.m4_signoff"
        cat "$PROJECT_ROOT/.m4_signoff"
        return 0
    fi
    return 1
}

# Check 3: Shadow run still in progress
check_shadow_run_complete() {
    local shadow_pid
    shadow_pid=$(pgrep -f "run_shadow_simulation.sh" 2>/dev/null || echo "")

    if [[ -n "$shadow_pid" ]]; then
        log_warn "Shadow run still in progress (PID: $shadow_pid)"

        # Get shadow run stats if available
        local shadow_dir
        shadow_dir=$(ls -td /tmp/shadow_simulation_* 2>/dev/null | head -1)
        if [[ -d "$shadow_dir/reports" ]]; then
            local cycles
            cycles=$(ls "$shadow_dir/reports"/cycle_*.json 2>/dev/null | wc -l)
            log_warn "Shadow run has completed $cycles cycles"
        fi

        return 1
    fi

    log_info "No active shadow run detected"
    return 0
}

# Check 4: Verify shadow run completed successfully (if results exist)
check_shadow_run_results() {
    local shadow_dir
    shadow_dir=$(ls -td /tmp/shadow_simulation_* 2>/dev/null | head -1)

    if [[ -z "$shadow_dir" ]]; then
        log_warn "No shadow run results found"
        return 0  # Not a blocker if no shadow run was done
    fi

    # Check for mismatches in the last 100 cycles
    local mismatch_count=0
    if [[ -d "$shadow_dir/reports" ]]; then
        mismatch_count=$(tail -100 "$shadow_dir/reports"/cycle_*.json 2>/dev/null | \
            grep -o '"mismatches":[0-9]*' | \
            grep -v '"mismatches":0' | wc -l || echo "0")
    fi

    if [[ "$mismatch_count" -gt 0 ]]; then
        log_error "Shadow run has $mismatch_count cycles with mismatches in last 100"
        return 1
    fi

    log_info "Shadow run results show 0 mismatches in recent cycles"
    return 0
}

# Check 5: CI status (placeholder - would integrate with GitHub API)
check_ci_status() {
    # TODO: Integrate with GitHub Actions API to verify CI green
    log_info "CI status check (manual verification required)"
    return 0
}

# Main
main() {
    log_info "═══════════════════════════════════════════════════════════════"
    log_info "         M4 Signoff Preflight Check"
    log_info "═══════════════════════════════════════════════════════════════"

    local all_passed=true

    # Check signoff
    if check_signoff_env || check_signoff_file; then
        log_info "✅ M4 signoff present"
    else
        log_error "❌ M4 signoff not found"
        log_error "   Set M4_SIGNOFF=1 or create .m4_signoff file after validation"
        all_passed=false
    fi

    # Check shadow run not active
    if ! check_shadow_run_complete; then
        log_error "❌ Shadow run still in progress - wait for completion"
        all_passed=false
    fi

    # Check shadow run results
    if ! check_shadow_run_results; then
        log_error "❌ Shadow run has mismatches - investigate before proceeding"
        all_passed=false
    fi

    # CI check
    check_ci_status

    echo ""
    if [[ "$all_passed" == "true" ]]; then
        log_info "═══════════════════════════════════════════════════════════════"
        log_info "         ✅ PREFLIGHT PASSED - Safe to proceed"
        log_info "═══════════════════════════════════════════════════════════════"
        exit 0
    else
        log_error "═══════════════════════════════════════════════════════════════"
        log_error "         ❌ PREFLIGHT FAILED - Do not merge runtime changes"
        log_error "═══════════════════════════════════════════════════════════════"
        exit 1
    fi
}

main "$@"
