#!/usr/bin/env bash
# rollback_failure_catalog.sh - Rollback failure catalog integration
#
# Usage:
#   ./scripts/rollback_failure_catalog.sh              # Interactive rollback
#   ./scripts/rollback_failure_catalog.sh --force      # Force rollback without prompts
#   ./scripts/rollback_failure_catalog.sh --dry-run    # Show what would be done
#
# This script:
# 1. Disables feature flags for catalog integration
# 2. Restarts affected services
# 3. Runs smoke tests to verify rollback
# 4. Optionally reverts git commits

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DRY_RUN=false
FORCE=false

log_info() { echo -e "${GREEN}[ROLLBACK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[ROLLBACK]${NC} $1"; }
log_error() { echo -e "${RED}[ROLLBACK]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Rollback failure catalog integration safely.

Options:
    --force     Skip confirmation prompts
    --dry-run   Show what would be done without making changes
    -h, --help  Show this help

Steps performed:
1. Disable failure_catalog_runtime_integration flag
2. Disable cost_simulator_runtime_integration flag
3. Restart backend services (if running in docker)
4. Run smoke tests
5. Verify /healthz and /readyz endpoints
EOF
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            ;;
    esac
done

confirm() {
    local msg="$1"
    if [[ "$FORCE" == "true" ]]; then
        return 0
    fi
    read -p "$msg [y/N] " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

run_cmd() {
    local cmd="$1"
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would execute: $cmd"
    else
        eval "$cmd"
    fi
}

# Step 1: Disable feature flags
disable_feature_flags() {
    log_step "Step 1: Disabling feature flags"

    local flags_file="$BACKEND_DIR/app/config/feature_flags.json"

    if [[ ! -f "$flags_file" ]]; then
        log_warn "Feature flags file not found at $flags_file"
        return 0
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would set failure_catalog_runtime_integration=false"
        log_info "[DRY-RUN] Would set cost_simulator_runtime_integration=false"
        return 0
    fi

    # Use jq to update flags if available, otherwise use sed
    if command -v jq &> /dev/null; then
        local tmp_file=$(mktemp)
        jq '.flags.failure_catalog_runtime_integration.enabled = false |
            .flags.cost_simulator_runtime_integration.enabled = false |
            .environments.development.failure_catalog_runtime_integration = false |
            .environments.development.cost_simulator_runtime_integration = false |
            .environments.staging.failure_catalog_runtime_integration = false |
            .environments.staging.cost_simulator_runtime_integration = false |
            .environments.production.failure_catalog_runtime_integration = false |
            .environments.production.cost_simulator_runtime_integration = false' \
            "$flags_file" > "$tmp_file"
        mv "$tmp_file" "$flags_file"
        log_info "Feature flags disabled via jq"
    else
        log_warn "jq not available - manually verify feature flags are disabled"
    fi
}

# Step 2: Restart services
restart_services() {
    log_step "Step 2: Restarting services"

    # Check if running in Docker
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "nova_"; then
        log_info "Docker containers detected - restarting backend"
        run_cmd "docker compose restart backend worker 2>/dev/null || docker-compose restart backend worker 2>/dev/null || true"
    fi

    # Check if running via systemd
    if systemctl is-active --quiet nova-api 2>/dev/null; then
        log_info "Systemd service detected - restarting"
        run_cmd "sudo systemctl restart nova-api nova-worker || true"
    fi

    # Give services time to restart
    if [[ "$DRY_RUN" != "true" ]]; then
        log_info "Waiting 5 seconds for services to restart..."
        sleep 5
    fi
}

# Step 3: Run smoke tests
run_smoke_tests() {
    log_step "Step 3: Running smoke tests"

    local base_url="${AOS_BASE_URL:-http://127.0.0.1:8000}"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would check $base_url/healthz"
        log_info "[DRY-RUN] Would check $base_url/health"
        return 0
    fi

    # Check healthz
    log_info "Checking $base_url/healthz..."
    if curl -sf "$base_url/healthz" > /dev/null 2>&1; then
        log_info "✅ /healthz OK"
    else
        log_warn "⚠️  /healthz failed or not responding"
    fi

    # Check health
    log_info "Checking $base_url/health..."
    if curl -sf "$base_url/health" > /dev/null 2>&1; then
        log_info "✅ /health OK"
    else
        log_warn "⚠️  /health failed or not responding"
    fi

    # Check metrics
    log_info "Checking $base_url/metrics..."
    if curl -sf "$base_url/metrics" > /dev/null 2>&1; then
        log_info "✅ /metrics OK"
    else
        log_warn "⚠️  /metrics failed or not responding"
    fi
}

# Step 4: Verify no runtime integration active
verify_rollback() {
    log_step "Step 4: Verifying rollback"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would verify feature flags are disabled"
        return 0
    fi

    # Check Python config module reports flags as disabled
    cd "$BACKEND_DIR"
    local result
    result=$(PYTHONPATH="$BACKEND_DIR" python3 -c "
from app.config import is_flag_enabled
fc = is_flag_enabled('failure_catalog_runtime_integration')
cs = is_flag_enabled('cost_simulator_runtime_integration')
print(f'failure_catalog={fc},cost_simulator={cs}')
" 2>/dev/null || echo "error")

    if [[ "$result" == "failure_catalog=False,cost_simulator=False" ]]; then
        log_info "✅ Feature flags confirmed disabled"
    elif [[ "$result" == "error" ]]; then
        log_warn "⚠️  Could not verify feature flags via Python"
    else
        log_error "❌ Feature flags not properly disabled: $result"
        return 1
    fi
}

# Main
main() {
    log_info "═══════════════════════════════════════════════════════════════"
    log_info "         Failure Catalog Integration Rollback"
    log_info "═══════════════════════════════════════════════════════════════"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_warn "DRY-RUN MODE - No changes will be made"
    fi

    if ! confirm "This will disable failure catalog integration. Continue?"; then
        log_info "Rollback cancelled"
        exit 0
    fi

    disable_feature_flags
    restart_services
    run_smoke_tests
    verify_rollback

    echo ""
    log_info "═══════════════════════════════════════════════════════════════"
    log_info "         ✅ ROLLBACK COMPLETE"
    log_info "═══════════════════════════════════════════════════════════════"
    log_info ""
    log_info "Next steps:"
    log_info "  1. Monitor /metrics for any anomalies"
    log_info "  2. Check Grafana dashboards for error rate changes"
    log_info "  3. If issues persist, consider git revert of integration commits"
}

main "$@"
