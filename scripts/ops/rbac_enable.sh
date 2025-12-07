#!/usr/bin/env bash
# =============================================================================
# RBAC Enablement Script - Sections A through G
# =============================================================================
# Purpose: Safe, controlled, reversible RBAC enforcement rollout
# Usage: ./rbac_enable.sh [COMMAND]
#
# Commands:
#   preflight     - Run pre-flight checks (Section A4, B, C, D)
#   backup        - Create database backup (Section F2)
#   enable        - Enable RBAC_ENFORCE=true (Section A2)
#   disable       - Emergency rollback to RBAC_ENFORCE=false (Section F1)
#   smoke         - Run smoke tests (Section A1, A3)
#   verify        - Run verification one-liners (Section H)
#   full          - Run full enablement sequence (backup + enable + smoke)
#   status        - Check current RBAC status
#
# Environment:
#   BASE_URL              - API base URL (default: http://127.0.0.1:8000)
#   MACHINE_SECRET_TOKEN  - Machine authentication token
#   DATABASE_URL          - PostgreSQL connection string
#   BACKUP_DIR            - Backup directory (default: /root/agenticverz2.0/backups)
#   COMPOSE_FILE          - Docker compose file path
#   ENV_FILE              - Environment file path (default: /root/agenticverz2.0/.env)
# =============================================================================

set -euo pipefail

# Configuration
BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
MACHINE_TOKEN="${MACHINE_SECRET_TOKEN:-}"
DATABASE_URL="${DATABASE_URL:-postgresql://nova:novapass@localhost:6432/nova_aos}"
BACKUP_DIR="${BACKUP_DIR:-/root/agenticverz2.0/backups}"
COMPOSE_FILE="${COMPOSE_FILE:-/root/agenticverz2.0/docker-compose.yml}"
ENV_FILE="${ENV_FILE:-/root/agenticverz2.0/.env}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

log_pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
log_fail() { echo -e "${RED}[FAIL]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_section() {
    echo ""
    echo -e "${BOLD}=== $1 ===${NC}"
}

# =============================================================================
# Section F2: Database Backup
# =============================================================================
cmd_backup() {
    log_section "F2: Database Backup"

    mkdir -p "$BACKUP_DIR"
    TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
    BACKUP_FILE="${BACKUP_DIR}/m7_pre_enable_${TIMESTAMP}.dump"

    log_info "Creating backup: $BACKUP_FILE"

    if command -v pg_dump &> /dev/null; then
        pg_dump -Fc "$DATABASE_URL" -f "$BACKUP_FILE"
    elif docker ps | grep -q nova_db; then
        docker exec nova_db pg_dump -U nova -Fc nova_aos > "$BACKUP_FILE"
    else
        log_fail "Cannot create backup: pg_dump not found and nova_db container not running"
        return 1
    fi

    if [[ -f "$BACKUP_FILE" ]]; then
        SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        log_pass "Backup created: $BACKUP_FILE ($SIZE)"
        echo "$BACKUP_FILE"
    else
        log_fail "Backup file not created"
        return 1
    fi
}

# =============================================================================
# Section A4: Pre-flight Checks
# =============================================================================
cmd_preflight() {
    log_section "A4: Pre-flight Checks"

    local ERRORS=0

    # Check API health
    if curl -sf "${BASE_URL}/health" > /dev/null 2>&1; then
        log_pass "API health check"
    else
        log_fail "API not responding at $BASE_URL"
        ((ERRORS++))
    fi

    # Check RBAC info endpoint
    RBAC_INFO=$(curl -sf "${BASE_URL}/api/v1/rbac/info" 2>/dev/null || echo '{}')
    if [[ "$RBAC_INFO" != "{}" ]]; then
        ENFORCE=$(echo "$RBAC_INFO" | jq -r '.enforce_mode // "unknown"')
        HASH=$(echo "$RBAC_INFO" | jq -r '.hash // "none"')
        log_pass "RBAC endpoint available (enforce=$ENFORCE, hash=$HASH)"
    else
        log_fail "RBAC info endpoint not responding"
        ((ERRORS++))
    fi

    # Check machine token is set
    if [[ -n "$MACHINE_TOKEN" ]]; then
        log_pass "MACHINE_SECRET_TOKEN is set"
    else
        log_warn "MACHINE_SECRET_TOKEN not set (required for machine auth)"
    fi

    # Check database connectivity
    if PGPASSWORD="${DATABASE_URL##*:@}" psql "$DATABASE_URL" -c "SELECT 1" > /dev/null 2>&1; then
        log_pass "Database connectivity"
    elif docker exec nova_db psql -U nova -d nova_aos -c "SELECT 1" > /dev/null 2>&1; then
        log_pass "Database connectivity (via docker)"
    else
        log_fail "Cannot connect to database"
        ((ERRORS++))
    fi

    # Check RBAC audit table exists
    if psql "$DATABASE_URL" -c "SELECT 1 FROM system.rbac_audit LIMIT 1" > /dev/null 2>&1; then
        log_pass "RBAC audit table exists (system.rbac_audit)"
    else
        log_fail "RBAC audit table not found"
        ((ERRORS++))
    fi

    # Check memory audit table exists
    if psql "$DATABASE_URL" -c "SELECT 1 FROM system.memory_audit LIMIT 1" > /dev/null 2>&1; then
        log_pass "Memory audit table exists (system.memory_audit)"
    else
        log_fail "Memory audit table not found"
        ((ERRORS++))
    fi

    # Check backup directory
    if [[ -d "$BACKUP_DIR" ]] || mkdir -p "$BACKUP_DIR" 2>/dev/null; then
        log_pass "Backup directory accessible: $BACKUP_DIR"
    else
        log_warn "Cannot create backup directory: $BACKUP_DIR"
    fi

    # Check Docker/systemd
    if docker ps | grep -q nova_agent_manager; then
        log_pass "Backend container running"
    elif systemctl is-active --quiet agenticverz-backend 2>/dev/null; then
        log_pass "Backend systemd service running"
    else
        log_warn "Could not detect backend service"
    fi

    log_section "Pre-flight Summary"
    if [[ $ERRORS -eq 0 ]]; then
        log_pass "All pre-flight checks passed"
        return 0
    else
        log_fail "$ERRORS pre-flight check(s) failed"
        return 1
    fi
}

# =============================================================================
# Section A2: Enable RBAC Enforcement
# =============================================================================
cmd_enable() {
    log_section "A2: Enable RBAC Enforcement"

    # Check if env file exists
    if [[ ! -f "$ENV_FILE" ]]; then
        log_fail "Environment file not found: $ENV_FILE"
        return 1
    fi

    # Backup current env
    cp "$ENV_FILE" "${ENV_FILE}.bak.$(date +%Y%m%d%H%M%S)"
    log_info "Environment file backed up"

    # Update RBAC_ENFORCE
    if grep -q "^RBAC_ENFORCE=" "$ENV_FILE"; then
        sed -i 's/^RBAC_ENFORCE=.*/RBAC_ENFORCE=true/' "$ENV_FILE"
    else
        echo "RBAC_ENFORCE=true" >> "$ENV_FILE"
    fi
    log_info "Set RBAC_ENFORCE=true in $ENV_FILE"

    # Restart backend
    log_info "Restarting backend service..."

    if [[ -f "$COMPOSE_FILE" ]]; then
        cd "$(dirname "$COMPOSE_FILE")"
        docker compose up -d backend
        log_pass "Backend restarted via docker compose"
    elif systemctl is-active --quiet agenticverz-backend 2>/dev/null; then
        sudo systemctl restart agenticverz-backend
        log_pass "Backend restarted via systemd"
    else
        log_warn "Could not restart backend automatically"
        log_info "Please restart manually: docker compose up -d backend"
    fi

    # Wait for health
    log_info "Waiting for backend to become healthy..."
    sleep 5

    for i in {1..12}; do
        if curl -sf "${BASE_URL}/health" > /dev/null 2>&1; then
            log_pass "Backend is healthy"
            break
        fi
        sleep 5
    done

    # Verify RBAC is enforced
    ENFORCE=$(curl -sf "${BASE_URL}/api/v1/rbac/info" 2>/dev/null | jq -r '.enforce_mode // "unknown"')
    if [[ "$ENFORCE" == "true" ]]; then
        log_pass "RBAC enforcement confirmed: ENABLED"
    else
        log_warn "RBAC enforcement status: $ENFORCE"
    fi
}

# =============================================================================
# Section F1: Emergency Rollback
# =============================================================================
cmd_disable() {
    log_section "F1: Emergency Rollback - Disable RBAC"

    echo -e "${RED}WARNING: This will disable RBAC enforcement${NC}"
    echo ""

    # Update env file
    if [[ -f "$ENV_FILE" ]]; then
        if grep -q "^RBAC_ENFORCE=" "$ENV_FILE"; then
            sed -i 's/^RBAC_ENFORCE=.*/RBAC_ENFORCE=false/' "$ENV_FILE"
        else
            echo "RBAC_ENFORCE=false" >> "$ENV_FILE"
        fi
        log_info "Set RBAC_ENFORCE=false in $ENV_FILE"
    fi

    # Restart backend
    log_info "Restarting backend service..."

    if [[ -f "$COMPOSE_FILE" ]]; then
        cd "$(dirname "$COMPOSE_FILE")"
        docker compose up -d backend
    elif systemctl is-active --quiet agenticverz-backend 2>/dev/null; then
        sudo systemctl restart agenticverz-backend
    else
        log_warn "Could not restart backend automatically"
    fi

    sleep 5

    # Verify
    ENFORCE=$(curl -sf "${BASE_URL}/api/v1/rbac/info" 2>/dev/null | jq -r '.enforce_mode // "unknown"')
    if [[ "$ENFORCE" == "false" ]]; then
        log_pass "RBAC enforcement DISABLED"
    else
        log_warn "RBAC status: $ENFORCE"
    fi
}

# =============================================================================
# Section A1 + A3: Smoke Tests
# =============================================================================
cmd_smoke() {
    log_section "Smoke Tests (A1 + A3)"

    # Run the dedicated smoke test script
    if [[ -f "${SCRIPT_DIR}/rbac_enable_smoke.sh" ]]; then
        "${SCRIPT_DIR}/rbac_enable_smoke.sh" "$BASE_URL"
    else
        log_warn "Smoke test script not found at ${SCRIPT_DIR}/rbac_enable_smoke.sh"
        log_info "Running inline smoke tests..."

        # A1: Test machine token
        if [[ -n "$MACHINE_TOKEN" ]]; then
            STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
                -X POST "${BASE_URL}/api/v1/memory/pins" \
                -H "X-Machine-Token: ${MACHINE_TOKEN}" \
                -H "Content-Type: application/json" \
                -d '{"tenant_id":"smoke-test","key":"smoke:token","value":{"t":1}}')
            if [[ "$STATUS" == "200" ]] || [[ "$STATUS" == "201" ]]; then
                log_pass "A1: Machine token access: HTTP $STATUS"
            else
                log_fail "A1: Machine token access: HTTP $STATUS"
            fi
        fi

        # A3: Test unauthorized
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
            -X POST "${BASE_URL}/api/v1/memory/pins" \
            -H "Content-Type: application/json" \
            -d '{"tenant_id":"smoke-test","key":"smoke:unauth","value":{}}')
        if [[ "$STATUS" == "403" ]]; then
            log_pass "A3: Unauthorized blocked: HTTP 403"
        elif [[ "$STATUS" == "200" ]] || [[ "$STATUS" == "201" ]]; then
            log_warn "A3: Unauthorized allowed: HTTP $STATUS (RBAC not enforced?)"
        else
            log_info "A3: Unauthorized response: HTTP $STATUS"
        fi
    fi
}

# =============================================================================
# Section H: Verification One-Liners
# =============================================================================
cmd_verify() {
    log_section "H: Verification One-Liners"

    # RBAC audit count
    log_info "RBAC audit entries:"
    psql "$DATABASE_URL" -c "SELECT count(*) as rbac_audit_count FROM system.rbac_audit" 2>/dev/null || \
        log_warn "Could not query RBAC audit"

    # Memory audit sample
    log_info "Memory audit (recent 10):"
    psql "$DATABASE_URL" -c \
        "SELECT ts, operation, tenant_id, key FROM system.memory_audit ORDER BY ts DESC LIMIT 10" 2>/dev/null || \
        log_warn "Could not query memory audit"

    # Expired pins check
    log_info "Expired pins pending cleanup:"
    psql "$DATABASE_URL" -c \
        "SELECT count(*) as expired_pins FROM system.memory_pins
         WHERE expires_at IS NOT NULL AND expires_at < now()" 2>/dev/null || \
        log_warn "Could not query expired pins"

    # Prometheus metrics
    log_info "Key Prometheus metrics:"
    curl -s "${BASE_URL}/metrics" 2>/dev/null | \
        grep -E 'rbac_engine_decisions_total|memory_pins_operations_total' | head -10 || \
        log_warn "Could not fetch metrics"
}

# =============================================================================
# Status Check
# =============================================================================
cmd_status() {
    log_section "Current RBAC Status"

    # RBAC info
    RBAC_INFO=$(curl -sf "${BASE_URL}/api/v1/rbac/info" 2>/dev/null || echo '{}')

    if [[ "$RBAC_INFO" != "{}" ]]; then
        echo "$RBAC_INFO" | jq .
    else
        log_warn "Could not fetch RBAC info"
    fi

    # Recent denials
    log_info "Recent RBAC denials (last 10):"
    psql "$DATABASE_URL" -c \
        "SELECT ts, subject, resource, action, reason
         FROM system.rbac_audit
         WHERE allowed = false
         ORDER BY ts DESC LIMIT 10" 2>/dev/null || \
        log_warn "Could not query RBAC denials"
}

# =============================================================================
# Full Enablement Sequence
# =============================================================================
cmd_full() {
    log_section "Full RBAC Enablement Sequence"

    echo "This will:"
    echo "  1. Run pre-flight checks"
    echo "  2. Create database backup"
    echo "  3. Enable RBAC_ENFORCE=true"
    echo "  4. Run smoke tests"
    echo ""
    echo -e "${YELLOW}Press Enter to continue or Ctrl+C to abort...${NC}"
    read -r

    # Step 1: Pre-flight
    if ! cmd_preflight; then
        log_fail "Pre-flight checks failed. Aborting."
        return 1
    fi

    # Step 2: Backup
    if ! cmd_backup; then
        log_fail "Backup failed. Aborting."
        return 1
    fi

    # Step 3: Enable
    cmd_enable

    # Step 4: Smoke
    sleep 5
    cmd_smoke

    log_section "Enablement Complete"
    log_info "Monitor for 15-30 minutes before rolling out further"
    log_info "To rollback: $0 disable"
}

# =============================================================================
# Help
# =============================================================================
cmd_help() {
    echo "RBAC Enablement Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  preflight  - Run pre-flight checks"
    echo "  backup     - Create database backup"
    echo "  enable     - Enable RBAC_ENFORCE=true"
    echo "  disable    - Emergency rollback"
    echo "  smoke      - Run smoke tests"
    echo "  verify     - Run verification queries"
    echo "  status     - Check current RBAC status"
    echo "  full       - Full enablement sequence"
    echo "  help       - Show this help"
    echo ""
    echo "Environment:"
    echo "  BASE_URL              - API base URL (default: http://127.0.0.1:8000)"
    echo "  MACHINE_SECRET_TOKEN  - Machine authentication token"
    echo "  DATABASE_URL          - PostgreSQL connection string"
    echo "  BACKUP_DIR            - Backup directory"
    echo "  ENV_FILE              - Environment file path"
}

# =============================================================================
# Main
# =============================================================================
main() {
    COMMAND="${1:-help}"

    case "$COMMAND" in
        preflight) cmd_preflight ;;
        backup)    cmd_backup ;;
        enable)    cmd_enable ;;
        disable)   cmd_disable ;;
        smoke)     cmd_smoke ;;
        verify)    cmd_verify ;;
        status)    cmd_status ;;
        full)      cmd_full ;;
        help|--help|-h) cmd_help ;;
        *)
            log_fail "Unknown command: $COMMAND"
            cmd_help
            exit 1
            ;;
    esac
}

main "$@"
