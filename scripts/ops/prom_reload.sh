#!/usr/bin/env bash
# scripts/ops/prom_reload.sh
#
# Prometheus reload script with LKG (Last-Known-Good) backup strategy.
# Validates rules before reload, backs up current config, and supports rollback.
#
# Usage:
#   ./prom_reload.sh                     # Validate and reload
#   ./prom_reload.sh --check-only        # Only validate, don't reload
#   ./prom_reload.sh --rollback          # Rollback to LKG
#   ./prom_reload.sh --force             # Skip validation, force reload
#   PROM_RELOAD_URL=http://host:9090/-/reload ./prom_reload.sh
#
# Environment Variables:
#   PROM_RELOAD_URL   - Prometheus reload endpoint (default: http://localhost:9090/-/reload)
#   PROM_RULES_DIR    - Rules directory (default: /etc/prometheus/rules)
#   PROM_CONFIG       - Main config file (default: /etc/prometheus/prometheus.yml)
#   PROM_LKG_DIR      - LKG backup directory (default: /var/lib/prometheus/lkg)
#   PROM_RELOAD_TOKEN - Auth token for reload endpoint (optional)

set -e

# Configuration
PROM_RELOAD_URL="${PROM_RELOAD_URL:-http://localhost:9090/-/reload}"
PROM_RULES_DIR="${PROM_RULES_DIR:-/etc/prometheus/rules}"
PROM_CONFIG="${PROM_CONFIG:-/etc/prometheus/prometheus.yml}"
PROM_LKG_DIR="${PROM_LKG_DIR:-/var/lib/prometheus/lkg}"
PROM_RELOAD_TOKEN="${PROM_RELOAD_TOKEN:-}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Timestamp
TS=$(date +%Y%m%d_%H%M%S)

# =============================================================================
# Functions
# =============================================================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_promtool() {
    if ! command -v promtool &> /dev/null; then
        log_error "promtool not found. Install prometheus-tools package."
        exit 1
    fi
}

validate_config() {
    log_info "Validating Prometheus configuration..."

    # Validate main config
    if [[ -f "$PROM_CONFIG" ]]; then
        if ! promtool check config "$PROM_CONFIG" 2>&1; then
            log_error "Config validation failed: $PROM_CONFIG"
            return 1
        fi
        log_info "Main config valid: $PROM_CONFIG"
    fi

    # Validate rules
    if [[ -d "$PROM_RULES_DIR" ]]; then
        local rules_found=0
        for rules_file in "$PROM_RULES_DIR"/*.yml "$PROM_RULES_DIR"/*.yaml; do
            if [[ -f "$rules_file" ]]; then
                rules_found=1
                if ! promtool check rules "$rules_file" 2>&1; then
                    log_error "Rules validation failed: $rules_file"
                    return 1
                fi
                log_info "Rules valid: $rules_file"
            fi
        done

        if [[ $rules_found -eq 0 ]]; then
            log_warn "No rules files found in $PROM_RULES_DIR"
        fi
    else
        log_warn "Rules directory not found: $PROM_RULES_DIR"
    fi

    log_info "All validations passed"
    return 0
}

backup_lkg() {
    log_info "Creating LKG backup..."

    # Create LKG directory if needed
    mkdir -p "$PROM_LKG_DIR"

    # Backup main config
    if [[ -f "$PROM_CONFIG" ]]; then
        cp "$PROM_CONFIG" "$PROM_LKG_DIR/prometheus.yml.lkg"
        log_info "Backed up main config"
    fi

    # Backup rules directory
    if [[ -d "$PROM_RULES_DIR" ]]; then
        rm -rf "$PROM_LKG_DIR/rules"
        cp -r "$PROM_RULES_DIR" "$PROM_LKG_DIR/rules"
        log_info "Backed up rules directory"
    fi

    # Record backup timestamp
    echo "$TS" > "$PROM_LKG_DIR/timestamp"

    log_info "LKG backup complete at $PROM_LKG_DIR"
}

rollback_lkg() {
    log_info "Rolling back to LKG..."

    if [[ ! -d "$PROM_LKG_DIR" ]]; then
        log_error "No LKG backup found at $PROM_LKG_DIR"
        exit 1
    fi

    # Check timestamp
    if [[ -f "$PROM_LKG_DIR/timestamp" ]]; then
        local lkg_ts
        lkg_ts=$(cat "$PROM_LKG_DIR/timestamp")
        log_info "Rolling back to LKG from $lkg_ts"
    fi

    # Restore main config
    if [[ -f "$PROM_LKG_DIR/prometheus.yml.lkg" ]]; then
        cp "$PROM_LKG_DIR/prometheus.yml.lkg" "$PROM_CONFIG"
        log_info "Restored main config"
    fi

    # Restore rules
    if [[ -d "$PROM_LKG_DIR/rules" ]]; then
        rm -rf "$PROM_RULES_DIR"
        cp -r "$PROM_LKG_DIR/rules" "$PROM_RULES_DIR"
        log_info "Restored rules directory"
    fi

    # Trigger reload
    reload_prometheus

    log_info "Rollback complete"
}

reload_prometheus() {
    log_info "Triggering Prometheus reload..."

    local curl_opts=("-X" "POST" "-s" "-w" "%{http_code}" "-o" "/dev/null")

    # Add auth token if configured
    if [[ -n "$PROM_RELOAD_TOKEN" ]]; then
        curl_opts+=("-H" "Authorization: Bearer $PROM_RELOAD_TOKEN")
    fi

    local http_code
    http_code=$(curl "${curl_opts[@]}" "$PROM_RELOAD_URL")

    if [[ "$http_code" == "200" ]]; then
        log_info "Prometheus reload successful (HTTP $http_code)"
        return 0
    else
        log_error "Prometheus reload failed (HTTP $http_code)"
        return 1
    fi
}

check_prometheus_health() {
    log_info "Checking Prometheus health..."

    local prom_base="${PROM_RELOAD_URL%/-/reload}"
    local health_url="$prom_base/-/healthy"

    local http_code
    http_code=$(curl -s -w "%{http_code}" -o /dev/null "$health_url" 2>/dev/null || echo "000")

    if [[ "$http_code" == "200" ]]; then
        log_info "Prometheus is healthy"
        return 0
    else
        log_warn "Prometheus health check failed (HTTP $http_code)"
        return 1
    fi
}

verify_reload() {
    log_info "Verifying reload success..."

    # Wait for Prometheus to apply changes
    sleep 2

    # Check health
    if ! check_prometheus_health; then
        log_error "Post-reload health check failed!"
        log_warn "Consider rolling back with: $0 --rollback"
        return 1
    fi

    # Check for rule errors in Prometheus API
    local prom_base="${PROM_RELOAD_URL%/-/reload}"
    local rules_url="$prom_base/api/v1/rules"

    local rules_response
    rules_response=$(curl -s "$rules_url" 2>/dev/null)

    if echo "$rules_response" | grep -q '"status":"success"'; then
        log_info "Rules loaded successfully"
    else
        log_warn "Could not verify rules status"
    fi

    log_info "Reload verification complete"
    return 0
}

show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --check-only    Only validate configuration, don't reload"
    echo "  --rollback      Rollback to last-known-good configuration"
    echo "  --force         Skip validation and force reload"
    echo "  --no-backup     Skip LKG backup before reload"
    echo "  --help          Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  PROM_RELOAD_URL   - Prometheus reload endpoint"
    echo "  PROM_RULES_DIR    - Rules directory"
    echo "  PROM_CONFIG       - Main config file"
    echo "  PROM_LKG_DIR      - LKG backup directory"
    echo "  PROM_RELOAD_TOKEN - Auth token for reload endpoint"
}

# =============================================================================
# Main
# =============================================================================

main() {
    local check_only=false
    local do_rollback=false
    local force=false
    local skip_backup=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --check-only)
                check_only=true
                shift
                ;;
            --rollback)
                do_rollback=true
                shift
                ;;
            --force)
                force=true
                shift
                ;;
            --no-backup)
                skip_backup=true
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

    log_info "=== Prometheus Reload Script ==="
    log_info "Timestamp: $TS"

    # Handle rollback
    if [[ "$do_rollback" == true ]]; then
        rollback_lkg
        exit 0
    fi

    # Check promtool is available
    check_promtool

    # Validate configuration (unless forced)
    if [[ "$force" != true ]]; then
        if ! validate_config; then
            log_error "Validation failed. Use --force to skip validation."
            exit 1
        fi
    else
        log_warn "Skipping validation (--force specified)"
    fi

    # Exit if check-only
    if [[ "$check_only" == true ]]; then
        log_info "Check complete. Use without --check-only to reload."
        exit 0
    fi

    # Create LKG backup (unless skipped)
    if [[ "$skip_backup" != true ]]; then
        backup_lkg
    else
        log_warn "Skipping LKG backup (--no-backup specified)"
    fi

    # Reload Prometheus
    if ! reload_prometheus; then
        log_error "Reload failed!"
        log_warn "Consider rolling back with: $0 --rollback"
        exit 1
    fi

    # Verify reload
    if ! verify_reload; then
        log_error "Verification failed!"
        log_warn "Consider rolling back with: $0 --rollback"
        exit 1
    fi

    log_info "=== Prometheus reload complete ==="
}

main "$@"
