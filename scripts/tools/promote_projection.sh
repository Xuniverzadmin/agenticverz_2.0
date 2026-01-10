#!/usr/bin/env bash
# ==============================================================================
# Projection Promotion Pipeline
#
# Layer: L7 — Ops & Deployment
# Product: system-wide
# Temporal:
#   Trigger: manual (explicit promotion)
#   Execution: sync
# Role: Promote projection from preflight to production
# Reference: PIN-388 (Projection Promotion Pipeline)
#
# GOVERNANCE RULES:
# - Promotion is explicit, never automatic
# - Only _meta fields change, no recompilation
# - SDSR verification required before promotion
# - Artifact movement, not recomputation
#
# USAGE:
#   ./scripts/tools/promote_projection.sh --from preflight --to production
#   ./scripts/tools/promote_projection.sh --check  # Verify promotion eligibility
#   ./scripts/tools/promote_projection.sh --rollback  # Rollback to previous
# ==============================================================================

set -euo pipefail

# Paths
CANONICAL_DIR="design/l2_1/ui_contract"
PREFLIGHT_FILE="${CANONICAL_DIR}/ui_projection_lock.json"
PRODUCTION_FILE="${CANONICAL_DIR}/ui_projection_lock_production.json"
BACKUP_DIR="${CANONICAL_DIR}/backups"
PUBLIC_DIR="website/app-shell/public/projection"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==============================================================================
# Helper Functions
# ==============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_jq() {
    if ! command -v jq &> /dev/null; then
        log_error "jq is required but not installed"
        exit 1
    fi
}

# ==============================================================================
# Validation Functions
# ==============================================================================

check_promotion_eligibility() {
    log_info "Checking promotion eligibility..."

    # Check file exists
    if [[ ! -f "$PREFLIGHT_FILE" ]]; then
        log_error "Preflight projection not found: $PREFLIGHT_FILE"
        return 1
    fi

    # Check SDSR verification
    local sdsr_verified
    sdsr_verified=$(jq -r '._meta.sdsr_verified // false' "$PREFLIGHT_FILE")
    if [[ "$sdsr_verified" != "true" ]]; then
        log_error "SDSR verification required before promotion"
        log_error "Run SDSR scenarios and regenerate projection"
        return 1
    fi

    # Check for DRAFT or UNBOUND panels
    local draft_count
    local unbound_count
    draft_count=$(jq -r '._statistics.draft_panels // 0' "$PREFLIGHT_FILE")
    unbound_count=$(jq -r '._statistics.unbound_panels // 0' "$PREFLIGHT_FILE")

    if [[ "$draft_count" -gt 0 ]]; then
        log_warn "Found $draft_count DRAFT panels - consider SDSR verification"
    fi

    if [[ "$unbound_count" -gt 0 ]]; then
        log_error "Found $unbound_count UNBOUND panels - cannot promote"
        return 1
    fi

    # Check routes are relative
    local routes_relative
    routes_relative=$(jq -r '._meta.routes_relative // false' "$PREFLIGHT_FILE")
    if [[ "$routes_relative" != "true" ]]; then
        log_error "Routes must be relative (routes_relative=true)"
        log_error "Regenerate projection with updated compiler"
        return 1
    fi

    # Check current environment
    local current_env
    current_env=$(jq -r '._meta.environment // "unknown"' "$PREFLIGHT_FILE")
    if [[ "$current_env" != "preflight" ]]; then
        log_warn "Current environment is '$current_env', expected 'preflight'"
    fi

    log_success "Promotion eligibility: PASSED"
    return 0
}

show_promotion_diff() {
    log_info "Promotion will change these _meta fields:"
    echo ""
    echo "  environment:     preflight → production"
    echo "  approval_status: EXPERIMENTAL → APPROVED"
    echo ""
    log_info "All other fields remain unchanged (no recompilation)"
}

# ==============================================================================
# Promotion Functions
# ==============================================================================

create_backup() {
    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    mkdir -p "$BACKUP_DIR"

    if [[ -f "$PRODUCTION_FILE" ]]; then
        cp "$PRODUCTION_FILE" "${BACKUP_DIR}/ui_projection_lock_production_${timestamp}.json"
        log_success "Backed up existing production projection"
    fi

    cp "$PREFLIGHT_FILE" "${BACKUP_DIR}/ui_projection_lock_preflight_${timestamp}.json"
    log_success "Backed up preflight projection"
}

promote() {
    log_info "Starting promotion: preflight → production"

    # Create backup
    create_backup

    # Transform meta fields only
    jq '
        ._meta.environment = "production" |
        ._meta.approval_status = "APPROVED" |
        ._meta.promoted_at = (now | strftime("%Y-%m-%dT%H:%M:%SZ"))
    ' "$PREFLIGHT_FILE" > "$PRODUCTION_FILE"

    log_success "Created production projection: $PRODUCTION_FILE"

    # Copy to public directory for production deployment
    mkdir -p "$PUBLIC_DIR"
    cp "$PRODUCTION_FILE" "${PUBLIC_DIR}/ui_projection_lock.json"
    log_success "Copied to public directory: ${PUBLIC_DIR}/ui_projection_lock.json"

    # Verify
    local prod_env
    local prod_status
    prod_env=$(jq -r '._meta.environment' "$PRODUCTION_FILE")
    prod_status=$(jq -r '._meta.approval_status' "$PRODUCTION_FILE")

    if [[ "$prod_env" == "production" && "$prod_status" == "APPROVED" ]]; then
        log_success "Promotion complete!"
        echo ""
        echo "Production projection:"
        jq '._meta | {environment, approval_status, promoted_at}' "$PRODUCTION_FILE"
    else
        log_error "Promotion verification failed"
        return 1
    fi
}

rollback() {
    log_info "Rolling back to previous production projection..."

    local latest_backup
    latest_backup=$(ls -t "${BACKUP_DIR}"/ui_projection_lock_production_*.json 2>/dev/null | head -1)

    if [[ -z "$latest_backup" ]]; then
        log_error "No backup found to rollback to"
        return 1
    fi

    cp "$latest_backup" "$PRODUCTION_FILE"
    cp "$PRODUCTION_FILE" "${PUBLIC_DIR}/ui_projection_lock.json"

    log_success "Rolled back to: $latest_backup"
}

# ==============================================================================
# CLI
# ==============================================================================

show_help() {
    cat << EOF
Projection Promotion Pipeline

Usage:
    $0 --check              Check promotion eligibility
    $0 --from preflight --to production    Promote projection
    $0 --rollback           Rollback to previous production
    $0 --status             Show current projection status
    $0 --help               Show this help

Options:
    --check        Verify SDSR verification, no UNBOUND panels, routes_relative
    --from ENV     Source environment (preflight)
    --to ENV       Target environment (production)
    --rollback     Restore previous production projection
    --status       Show current projection metadata
    --force        Skip eligibility check (dangerous)

Examples:
    # Check if promotion is safe
    $0 --check

    # Promote after check passes
    $0 --from preflight --to production

    # Emergency rollback
    $0 --rollback
EOF
}

show_status() {
    log_info "Current projection status:"
    echo ""

    if [[ -f "$PREFLIGHT_FILE" ]]; then
        echo "Preflight ($PREFLIGHT_FILE):"
        jq '._meta | {environment, approval_status, sdsr_verified, routes_relative}' "$PREFLIGHT_FILE"
        echo ""
    fi

    if [[ -f "$PRODUCTION_FILE" ]]; then
        echo "Production ($PRODUCTION_FILE):"
        jq '._meta | {environment, approval_status, promoted_at}' "$PRODUCTION_FILE"
    else
        echo "Production: Not yet promoted"
    fi
}

main() {
    check_jq

    local action=""
    local from_env=""
    local to_env=""
    local force=false

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --check)
                action="check"
                shift
                ;;
            --from)
                from_env="$2"
                shift 2
                ;;
            --to)
                to_env="$2"
                shift 2
                ;;
            --rollback)
                action="rollback"
                shift
                ;;
            --status)
                action="status"
                shift
                ;;
            --force)
                force=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    case "$action" in
        check)
            check_promotion_eligibility
            show_promotion_diff
            ;;
        rollback)
            rollback
            ;;
        status)
            show_status
            ;;
        *)
            if [[ -n "$from_env" && -n "$to_env" ]]; then
                if [[ "$from_env" != "preflight" || "$to_env" != "production" ]]; then
                    log_error "Only 'preflight → production' promotion is supported"
                    exit 1
                fi

                if [[ "$force" != true ]]; then
                    check_promotion_eligibility || exit 1
                fi

                show_promotion_diff
                echo ""
                read -p "Proceed with promotion? [y/N] " -n 1 -r
                echo ""
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    promote
                else
                    log_info "Promotion cancelled"
                fi
            else
                show_help
                exit 1
            fi
            ;;
    esac
}

main "$@"
