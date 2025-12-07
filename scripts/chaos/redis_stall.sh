#!/usr/bin/env bash
# scripts/chaos/redis_stall.sh
#
# Redis stall chaos experiment - simulates Redis becoming unresponsive.
# Tests fail-open behavior and cache fallback mechanisms.
#
# Usage:
#   ./redis_stall.sh                    # 30 second stall
#   ./redis_stall.sh --duration 60      # 60 second stall
#   ./redis_stall.sh --mode pause       # PAUSE (default)
#   ./redis_stall.sh --mode debug-sleep # DEBUG SLEEP
#   ./redis_stall.sh --restore          # Restore Redis immediately
#
# Environment Variables:
#   REDIS_HOST     - Redis host (default: localhost)
#   REDIS_PORT     - Redis port (default: 6379)
#   REDIS_PASSWORD - Redis password (optional)
#   CHAOS_ALLOWED  - Must be "true" to run (safety check)

set -e

# Configuration
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASSWORD="${REDIS_PASSWORD:-}"
CHAOS_ALLOWED="${CHAOS_ALLOWED:-false}"

# Defaults
STALL_DURATION=30
STALL_MODE="pause"

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

redis_cli() {
    local cmd=("redis-cli" "-h" "$REDIS_HOST" "-p" "$REDIS_PORT")
    if [[ -n "$REDIS_PASSWORD" ]]; then
        cmd+=("-a" "$REDIS_PASSWORD")
    fi
    "${cmd[@]}" "$@"
}

check_redis() {
    if ! redis_cli PING > /dev/null 2>&1; then
        log_error "Cannot connect to Redis at $REDIS_HOST:$REDIS_PORT"
        exit 1
    fi
    log_info "Redis connection verified"
}

stall_pause() {
    log_info "Pausing Redis clients for ${STALL_DURATION}s..."
    log_warn "This will block all Redis commands!"

    # CLIENT PAUSE blocks all client connections
    redis_cli CLIENT PAUSE $((STALL_DURATION * 1000))

    log_info "Redis paused. Waiting for duration..."
    sleep "$STALL_DURATION"

    log_info "Redis should now be responsive again"
}

stall_debug_sleep() {
    log_info "Putting Redis into DEBUG SLEEP for ${STALL_DURATION}s..."
    log_warn "Redis will be completely unresponsive!"

    # DEBUG SLEEP makes Redis completely unresponsive
    # Note: This requires DEBUG command to be enabled
    redis_cli DEBUG SLEEP "$STALL_DURATION" &

    log_info "Redis in debug sleep. Waiting for duration..."
    sleep "$STALL_DURATION"

    log_info "Redis should now be responsive again"
}

restore_redis() {
    log_info "Restoring Redis..."

    # Unpause clients
    redis_cli CLIENT UNPAUSE 2>/dev/null || true

    # Verify connection
    if redis_cli PING > /dev/null 2>&1; then
        log_info "Redis restored and responding"
    else
        log_warn "Redis may still be recovering"
    fi
}

show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Redis stall chaos experiment"
    echo ""
    echo "Options:"
    echo "  --duration SEC   Stall duration in seconds (default: 30)"
    echo "  --mode MODE      Stall mode: pause or debug-sleep (default: pause)"
    echo "  --restore        Restore Redis immediately"
    echo "  --help           Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  REDIS_HOST       - Redis host"
    echo "  REDIS_PORT       - Redis port"
    echo "  REDIS_PASSWORD   - Redis password"
    echo "  CHAOS_ALLOWED    - Must be 'true' to run"
}

# =============================================================================
# Main
# =============================================================================

main() {
    local do_restore=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --duration)
                STALL_DURATION="$2"
                shift 2
                ;;
            --mode)
                STALL_MODE="$2"
                shift 2
                ;;
            --restore)
                do_restore=true
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

    log_info "=== Redis Stall Chaos Experiment ==="
    log_info "Host: $REDIS_HOST:$REDIS_PORT"

    # Safety check
    check_safety

    # Check Redis connection
    check_redis

    # Handle restore
    if [[ "$do_restore" == true ]]; then
        restore_redis
        exit 0
    fi

    # Run experiment
    log_info "Mode: $STALL_MODE"
    log_info "Duration: ${STALL_DURATION}s"
    echo ""

    case "$STALL_MODE" in
        pause)
            stall_pause
            ;;
        debug-sleep)
            stall_debug_sleep
            ;;
        *)
            log_error "Unknown mode: $STALL_MODE"
            exit 1
            ;;
    esac

    log_info "=== Chaos experiment complete ==="
}

main "$@"
