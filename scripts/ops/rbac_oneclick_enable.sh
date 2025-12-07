#!/usr/bin/env bash
# =============================================================================
# RBAC One-Click Enablement Script
# =============================================================================
# Purpose: Complete automated RBAC enablement with manual confirmation gates
# Usage: ./rbac_oneclick_enable.sh [--dry-run] [--non-interactive] [--observe-time SECONDS]
#
# Options:
#   --dry-run          Run checks without making changes
#   --non-interactive  Skip all confirmation prompts (for CI/CD)
#   --observe-time N   Observation period in seconds (default 900 = 15 min, CI default 60)
#
# This script orchestrates the full RBAC enablement sequence:
#   1. Pre-flight checks
#   2. Database backup
#   3. Enable RBAC_ENFORCE=true
#   4. Smoke tests
#   5. Monitoring checklist
#   6. Observation period
#   7. Final verification
#
# The script pauses at critical junctures for manual confirmation unless
# --non-interactive is specified.
# =============================================================================

set -uo pipefail

# Configuration
BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
MACHINE_TOKEN="${MACHINE_SECRET_TOKEN:-}"
BACKUP_DIR="${BACKUP_DIR:-/root/agenticverz2.0/backups}"
ENV_FILE="${ENV_FILE:-/root/agenticverz2.0/.env}"
COMPOSE_FILE="${COMPOSE_FILE:-/root/agenticverz2.0/docker-compose.yml}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="/var/log/aos"
LOG_FILE="${LOG_DIR}/rbac_enable_$(date +%Y%m%d_%H%M%S).log"
DRY_RUN=false
NON_INTERACTIVE=false
OBSERVE_TIME=""

# Parse args
for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            ;;
        --non-interactive)
            NON_INTERACTIVE=true
            ;;
        --observe-time=*)
            OBSERVE_TIME="${arg#*=}"
            ;;
    esac
done

# Set observe time defaults based on mode
if [[ -z "$OBSERVE_TIME" ]]; then
    if $NON_INTERACTIVE; then
        OBSERVE_TIME=60  # 60 seconds for CI
    else
        OBSERVE_TIME=900  # 15 minutes for interactive
    fi
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Logging
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "$msg"
    echo "$msg" >> "$LOG_FILE" 2>/dev/null || true
}

log_pass() { log "${GREEN}[PASS]${NC} $1"; }
log_fail() { log "${RED}[FAIL]${NC} $1"; }
log_warn() { log "${YELLOW}[WARN]${NC} $1"; }
log_info() { log "${BLUE}[INFO]${NC} $1"; }
log_step() {
    echo ""
    echo -e "${CYAN}${BOLD}========================================${NC}"
    log "${CYAN}${BOLD}STEP: $1${NC}"
    echo -e "${CYAN}${BOLD}========================================${NC}"
    echo ""
}

# Helper: Run psql command
run_psql() {
    PGPASSWORD=novapass psql -h localhost -p 6432 -U nova -d nova_aos "$@" 2>/dev/null
}

# Helper: Confirm before proceeding (skips in non-interactive mode)
confirm() {
    local prompt="${1:-Continue?}"
    if $NON_INTERACTIVE; then
        echo ""
        echo -e "${BLUE}[AUTO]${NC} $prompt (--non-interactive: skipping)"
        return 0
    fi
    echo ""
    echo -e "${YELLOW}${BOLD}>>> $prompt${NC}"
    echo -e "${YELLOW}Press ENTER to continue, or Ctrl+C to abort...${NC}"
    read -r
}

# Helper: Countdown with cancellation option
countdown() {
    local seconds=$1
    local message="${2:-Waiting}"

    echo ""
    for ((i=seconds; i>0; i--)); do
        printf "\r${BLUE}%s... %d seconds remaining (Ctrl+C to abort)${NC}  " "$message" "$i"
        sleep 1
    done
    printf "\r%-60s\n" ""
}

# =============================================================================
# Step 1: Pre-flight Checks
# =============================================================================
step_preflight() {
    log_step "1/7: Pre-flight Checks"

    local errors=0

    # Check API health
    if curl -sf "${BASE_URL}/health" > /dev/null 2>&1; then
        log_pass "API health check - ${BASE_URL}/health"
    else
        log_fail "API not responding at $BASE_URL"
        ((errors++))
    fi

    # Check RBAC info endpoint (use machine token if available)
    local rbac_info
    if [[ -n "$MACHINE_TOKEN" ]]; then
        rbac_info=$(curl -sf -H "X-Machine-Token: ${MACHINE_TOKEN}" "${BASE_URL}/api/v1/rbac/info" 2>/dev/null || echo '{}')
    else
        rbac_info=$(curl -sf "${BASE_URL}/api/v1/rbac/info" 2>/dev/null || echo '{}')
    fi
    if [[ "$rbac_info" != "{}" ]]; then
        local enforce hash
        enforce=$(echo "$rbac_info" | jq -r '.enforce_mode')
        hash=$(echo "$rbac_info" | jq -r '.hash // "none"')
        log_pass "RBAC endpoint available (enforce=$enforce, hash=$hash)"

        if [[ "$enforce" == "true" ]]; then
            log_warn "RBAC is already enforced! Re-running enablement may be redundant."
        fi
    else
        log_fail "RBAC info endpoint not responding"
        ((errors++))
    fi

    # Check machine token
    if [[ -n "$MACHINE_TOKEN" ]]; then
        log_pass "MACHINE_SECRET_TOKEN is set (${#MACHINE_TOKEN} chars)"
    else
        log_fail "MACHINE_SECRET_TOKEN not set - machine auth will fail!"
        ((errors++))
    fi

    # Check database
    if run_psql -c "SELECT 1" > /dev/null 2>&1; then
        log_pass "Database connectivity (PgBouncer:6432)"
    else
        log_fail "Cannot connect to database"
        ((errors++))
    fi

    # Check RBAC audit table
    if run_psql -c "SELECT 1 FROM system.rbac_audit LIMIT 1" > /dev/null 2>&1; then
        log_pass "RBAC audit table exists (system.rbac_audit)"
    else
        log_fail "RBAC audit table not found"
        ((errors++))
    fi

    # Check memory audit table
    if run_psql -c "SELECT 1 FROM system.memory_audit LIMIT 1" > /dev/null 2>&1; then
        log_pass "Memory audit table exists (system.memory_audit)"
    else
        log_fail "Memory audit table not found"
        ((errors++))
    fi

    # Check memory pins table
    if run_psql -c "SELECT 1 FROM system.memory_pins LIMIT 1" > /dev/null 2>&1; then
        log_pass "Memory pins table exists (system.memory_pins)"
    else
        log_fail "Memory pins table not found"
        ((errors++))
    fi

    # Check TTL cron
    if crontab -l 2>/dev/null | grep -q "memory_ttl_cleanup"; then
        log_pass "TTL cleanup cron is installed"
    else
        log_warn "TTL cleanup cron not detected"
    fi

    # Check Prometheus metrics
    if curl -sf "${BASE_URL}/metrics" 2>/dev/null | grep -q "rbac_engine_decisions_total"; then
        log_pass "RBAC metrics are exposed"
    else
        log_warn "RBAC metrics not found in /metrics"
    fi

    # Summary
    echo ""
    if [[ $errors -eq 0 ]]; then
        log_pass "All pre-flight checks passed"
        return 0
    else
        log_fail "$errors pre-flight check(s) failed"
        return 1
    fi
}

# =============================================================================
# Step 2: Database Backup
# =============================================================================
step_backup() {
    log_step "2/7: Database Backup"

    if $DRY_RUN; then
        log_info "[DRY-RUN] Would create backup in $BACKUP_DIR"
        return 0
    fi

    mkdir -p "$BACKUP_DIR"
    local timestamp
    timestamp=$(date -u +"%Y%m%dT%H%M%SZ")
    local backup_file="${BACKUP_DIR}/m7_pre_rbac_enable_${timestamp}.dump"

    log_info "Creating backup: $backup_file"

    if command -v pg_dump &> /dev/null; then
        PGPASSWORD=novapass pg_dump -h localhost -p 6432 -U nova -Fc nova_aos -f "$backup_file"
    elif docker ps 2>/dev/null | grep -q nova_db; then
        docker exec nova_db pg_dump -U nova -Fc nova_aos > "$backup_file"
    else
        log_fail "Cannot create backup: pg_dump not available"
        return 1
    fi

    if [[ -f "$backup_file" ]]; then
        local size
        size=$(du -h "$backup_file" | cut -f1)
        log_pass "Backup created: $backup_file ($size)"
        echo "$backup_file"
    else
        log_fail "Backup file not created"
        return 1
    fi
}

# =============================================================================
# Step 3: Enable RBAC Enforcement
# =============================================================================
step_enable() {
    log_step "3/7: Enable RBAC Enforcement"

    if $DRY_RUN; then
        log_info "[DRY-RUN] Would set RBAC_ENFORCE=true in $ENV_FILE"
        log_info "[DRY-RUN] Would restart backend service"
        return 0
    fi

    # Backup env file
    if [[ -f "$ENV_FILE" ]]; then
        cp "$ENV_FILE" "${ENV_FILE}.bak.$(date +%Y%m%d%H%M%S)"
        log_info "Environment file backed up"
    else
        log_fail "Environment file not found: $ENV_FILE"
        return 1
    fi

    # Update RBAC_ENFORCE
    if grep -q "^RBAC_ENFORCE=" "$ENV_FILE"; then
        sed -i 's/^RBAC_ENFORCE=.*/RBAC_ENFORCE=true/' "$ENV_FILE"
    else
        echo "RBAC_ENFORCE=true" >> "$ENV_FILE"
    fi
    log_pass "Set RBAC_ENFORCE=true in $ENV_FILE"

    # Restart backend
    log_info "Restarting backend service..."

    if [[ -f "$COMPOSE_FILE" ]]; then
        cd "$(dirname "$COMPOSE_FILE")"
        docker compose up -d backend
        log_pass "Backend restart initiated via docker compose"
    elif systemctl is-active --quiet agenticverz-backend 2>/dev/null; then
        sudo systemctl restart agenticverz-backend
        log_pass "Backend restart initiated via systemd"
    else
        log_warn "Could not restart backend automatically"
        log_info "Please restart manually!"
    fi

    # Wait for health
    log_info "Waiting for backend to become healthy..."
    local healthy=false
    for i in {1..24}; do
        if curl -sf "${BASE_URL}/health" > /dev/null 2>&1; then
            healthy=true
            break
        fi
        printf "\r  Attempt %d/24..." "$i"
        sleep 5
    done
    echo ""

    if $healthy; then
        log_pass "Backend is healthy"
    else
        log_fail "Backend did not become healthy within 2 minutes"
        return 1
    fi

    # Verify RBAC is enforced (use machine token if available)
    local enforce
    if [[ -n "$MACHINE_TOKEN" ]]; then
        enforce=$(curl -sf -H "X-Machine-Token: ${MACHINE_TOKEN}" "${BASE_URL}/api/v1/rbac/info" 2>/dev/null | jq -r '.enforce_mode')
    else
        enforce=$(curl -sf "${BASE_URL}/api/v1/rbac/info" 2>/dev/null | jq -r '.enforce_mode')
    fi
    if [[ "$enforce" == "true" ]]; then
        log_pass "RBAC enforcement confirmed: ENABLED"
    else
        log_warn "RBAC enforcement status: $enforce (expected: true)"
    fi
}

# =============================================================================
# Step 4: Smoke Tests
# =============================================================================
step_smoke() {
    log_step "4/7: Smoke Tests"

    local pass=0
    local fail=0
    local tenant="smoke-oneclick-$(date +%s)"

    # Test 1: Machine token allows write
    if [[ -n "$MACHINE_TOKEN" ]]; then
        local status
        status=$(curl -s -o /dev/null -w "%{http_code}" \
            -X POST "${BASE_URL}/api/v1/memory/pins" \
            -H "X-Machine-Token: ${MACHINE_TOKEN}" \
            -H "Content-Type: application/json" \
            -d "{\"tenant_id\":\"$tenant\",\"key\":\"smoke:machine\",\"value\":{\"test\":true}}")

        if [[ "$status" == "200" ]] || [[ "$status" == "201" ]]; then
            log_pass "Machine token write: HTTP $status"
            ((pass++))
        else
            log_fail "Machine token write: HTTP $status (expected 200/201)"
            ((fail++))
        fi
    else
        log_warn "Skipping machine token test (token not set)"
    fi

    # Test 2: Unauthorized access blocked (when RBAC enforced)
    local status
    status=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "${BASE_URL}/api/v1/memory/pins" \
        -H "Content-Type: application/json" \
        -d "{\"tenant_id\":\"$tenant\",\"key\":\"smoke:unauth\",\"value\":{}}")

    local rbac_enforce
    if [[ -n "$MACHINE_TOKEN" ]]; then
        rbac_enforce=$(curl -sf -H "X-Machine-Token: ${MACHINE_TOKEN}" "${BASE_URL}/api/v1/rbac/info" 2>/dev/null | jq -r '.enforce_mode')
    else
        rbac_enforce=$(curl -sf "${BASE_URL}/api/v1/rbac/info" 2>/dev/null | jq -r '.enforce_mode')
    fi

    if [[ "$rbac_enforce" == "true" ]]; then
        if [[ "$status" == "403" ]]; then
            log_pass "Unauthorized blocked: HTTP 403"
            ((pass++))
        else
            log_fail "Unauthorized NOT blocked: HTTP $status (expected 403)"
            ((fail++))
        fi
    else
        log_info "Unauthorized response: HTTP $status (RBAC not enforced)"
        ((pass++))
    fi

    # Test 3: GET memory pin
    if [[ -n "$MACHINE_TOKEN" ]]; then
        status=$(curl -s -o /dev/null -w "%{http_code}" \
            "${BASE_URL}/api/v1/memory/pins/smoke:machine?tenant_id=$tenant" \
            -H "X-Machine-Token: ${MACHINE_TOKEN}")

        if [[ "$status" == "200" ]]; then
            log_pass "Memory pin read: HTTP $status"
            ((pass++))
        else
            log_warn "Memory pin read: HTTP $status"
        fi
    fi

    # Test 4: CostSim V2 status
    status=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/costsim/v2/status")
    if [[ "$status" == "200" ]]; then
        log_pass "CostSim V2 status: HTTP $status"
        ((pass++))
    else
        log_fail "CostSim V2 status: HTTP $status (expected 200)"
        ((fail++))
    fi

    # Test 5: Metrics endpoint
    if curl -sf "${BASE_URL}/metrics" 2>/dev/null | grep -q "rbac_engine"; then
        log_pass "Prometheus metrics: RBAC metrics present"
        ((pass++))
    else
        log_warn "Prometheus metrics: RBAC metrics not found"
    fi

    # Test 6: Check RBAC audit entries exist
    local audit_count
    audit_count=$(run_psql -t -c "SELECT count(*) FROM system.rbac_audit WHERE ts > now() - interval '5 minutes'" 2>/dev/null | tr -d ' ')
    if [[ -n "$audit_count" ]] && [[ "$audit_count" -gt 0 ]]; then
        log_pass "RBAC audit: $audit_count entries in last 5 min"
        ((pass++))
    else
        log_info "RBAC audit: No recent entries (may be expected)"
    fi

    # Summary
    echo ""
    log_info "Smoke test results: $pass passed, $fail failed"

    if [[ $fail -gt 0 ]]; then
        return 1
    fi
    return 0
}

# =============================================================================
# Step 5: Monitoring Checklist
# =============================================================================
step_monitoring_checklist() {
    log_step "5/7: Monitoring Checklist"

    echo "Please verify the following in Grafana/Prometheus:"
    echo ""
    echo "  [ ] rbac_engine_decisions_total counter is incrementing"
    echo "  [ ] rbac_engine_decisions_total{decision=\"deny\"} is near zero (or expected)"
    echo "  [ ] memory_pins_operations_total counter is incrementing"
    echo "  [ ] No elevated error rates in logs"
    echo "  [ ] No unusual latency spikes in p99 histograms"
    echo ""

    log_info "Current key metrics:"

    # Fetch and display key metrics
    local metrics
    metrics=$(curl -sf "${BASE_URL}/metrics" 2>/dev/null || echo "")

    if [[ -n "$metrics" ]]; then
        echo "  RBAC decisions:"
        echo "$metrics" | grep "rbac_engine_decisions_total" | head -5 | sed 's/^/    /'
        echo ""
        echo "  Memory operations:"
        echo "$metrics" | grep "memory_pins_operations_total" | head -5 | sed 's/^/    /'
        echo ""
    fi

    # Show recent RBAC denials
    log_info "Recent RBAC denials (last hour):"
    run_psql -c "SELECT ts, subject, resource, action, reason FROM system.rbac_audit WHERE allowed = false AND ts > now() - interval '1 hour' ORDER BY ts DESC LIMIT 5" 2>/dev/null || true

    echo ""
}

# =============================================================================
# Step 6: Observation Period
# =============================================================================
step_observe() {
    local observe_min=$((OBSERVE_TIME / 60))
    log_step "6/7: Observation Period (${observe_min} minutes / ${OBSERVE_TIME}s)"

    log_info "Starting ${observe_min}-minute observation period..."
    log_info "During this time, monitor:"
    echo "  - Grafana dashboards for anomalies"
    echo "  - Application logs for errors"
    echo "  - Alert channels for any triggered alerts"
    echo ""
    if ! $NON_INTERACTIVE; then
        log_info "You can abort with Ctrl+C to rollback immediately."
    fi
    echo ""

    if $DRY_RUN; then
        log_info "[DRY-RUN] Would wait $OBSERVE_TIME seconds"
        return 0
    fi

    # Calculate intervals based on total observation time
    local interval=60  # Default 60 second intervals
    if [[ $OBSERVE_TIME -lt 120 ]]; then
        interval=$((OBSERVE_TIME / 2))
        [[ $interval -lt 10 ]] && interval=10
    fi
    local iterations=$((OBSERVE_TIME / interval))
    [[ $iterations -lt 1 ]] && iterations=1

    # Progress updates at each interval
    local elapsed=0
    for ((i=1; i<=iterations; i++)); do
        countdown $interval "Observation period ($elapsed/$OBSERVE_TIME seconds)"
        elapsed=$((i * interval))

        # Quick health check
        if curl -sf "${BASE_URL}/health" > /dev/null 2>&1; then
            log_pass "Health check OK at ${elapsed}s"
        else
            log_fail "Health check FAILED at ${elapsed}s"
            return 1
        fi

        # Check for new denials
        local denials
        denials=$(run_psql -t -c "SELECT count(*) FROM system.rbac_audit WHERE allowed = false AND ts > now() - interval '1 minute'" 2>/dev/null | tr -d ' ')
        if [[ -n "$denials" ]] && [[ "$denials" -gt 0 ]]; then
            log_warn "RBAC denials in last minute: $denials"
        fi
    done

    log_pass "Observation period completed successfully"
}

# =============================================================================
# Step 7: Final Verification
# =============================================================================
step_final_verify() {
    log_step "7/7: Final Verification"

    local pass=0
    local fail=0

    # RBAC status (use machine token if available)
    local enforce
    if [[ -n "$MACHINE_TOKEN" ]]; then
        enforce=$(curl -sf -H "X-Machine-Token: ${MACHINE_TOKEN}" "${BASE_URL}/api/v1/rbac/info" 2>/dev/null | jq -r '.enforce_mode')
    else
        enforce=$(curl -sf "${BASE_URL}/api/v1/rbac/info" 2>/dev/null | jq -r '.enforce_mode')
    fi
    if [[ "$enforce" == "true" ]]; then
        log_pass "RBAC enforcement: ENABLED"
        ((pass++))
    else
        log_warn "RBAC enforcement: $enforce"
    fi

    # API health
    if curl -sf "${BASE_URL}/health" > /dev/null 2>&1; then
        log_pass "API health: OK"
        ((pass++))
    else
        log_fail "API health: FAIL"
        ((fail++))
    fi

    # Database
    if run_psql -c "SELECT 1" > /dev/null 2>&1; then
        log_pass "Database: OK"
        ((pass++))
    else
        log_fail "Database: FAIL"
        ((fail++))
    fi

    # RBAC audit entries
    local audit_count
    audit_count=$(run_psql -t -c "SELECT count(*) FROM system.rbac_audit" 2>/dev/null | tr -d ' ')
    log_info "Total RBAC audit entries: $audit_count"

    # Memory audit entries
    local memory_count
    memory_count=$(run_psql -t -c "SELECT count(*) FROM system.memory_audit" 2>/dev/null | tr -d ' ')
    log_info "Total memory audit entries: $memory_count"

    echo ""
    echo -e "${GREEN}${BOLD}==============================================================================${NC}"
    echo -e "${GREEN}${BOLD}RBAC ENABLEMENT COMPLETE${NC}"
    echo -e "${GREEN}${BOLD}==============================================================================${NC}"
    echo ""
    echo "  Status: RBAC_ENFORCE=true"
    echo "  Log: $LOG_FILE"
    echo ""
    echo "  Next steps:"
    echo "    1. Monitor for 24-48 hours"
    echo "    2. Review RBAC denials daily"
    echo "    3. Run chaos experiments after stabilization"
    echo ""
    echo "  To rollback: ${SCRIPT_DIR}/rbac_enable.sh disable"
    echo ""

    if [[ $fail -gt 0 ]]; then
        return 1
    fi
    return 0
}

# =============================================================================
# Rollback Handler
# =============================================================================
rollback() {
    log_fail "Enablement interrupted - initiating rollback..."

    if [[ -f "$ENV_FILE" ]]; then
        if grep -q "^RBAC_ENFORCE=" "$ENV_FILE"; then
            sed -i 's/^RBAC_ENFORCE=.*/RBAC_ENFORCE=false/' "$ENV_FILE"
        else
            echo "RBAC_ENFORCE=false" >> "$ENV_FILE"
        fi
        log_info "Set RBAC_ENFORCE=false"
    fi

    if [[ -f "$COMPOSE_FILE" ]]; then
        cd "$(dirname "$COMPOSE_FILE")"
        docker compose up -d backend 2>/dev/null || true
    fi

    log_warn "Rollback complete. RBAC enforcement disabled."
    exit 1
}

# =============================================================================
# Main
# =============================================================================
main() {
    # Setup log directory
    mkdir -p "$LOG_DIR" 2>/dev/null || true

    # Trap for rollback on interrupt
    trap rollback SIGINT SIGTERM

    echo ""
    echo -e "${CYAN}${BOLD}==============================================================================${NC}"
    echo -e "${CYAN}${BOLD}       RBAC One-Click Enablement Script${NC}"
    echo -e "${CYAN}${BOLD}==============================================================================${NC}"
    echo ""

    if $DRY_RUN; then
        echo -e "${YELLOW}  *** DRY RUN MODE - No changes will be made ***${NC}"
        echo ""
    fi

    if $NON_INTERACTIVE; then
        echo -e "${BLUE}  *** NON-INTERACTIVE MODE - All prompts will be auto-confirmed ***${NC}"
        echo ""
    fi

    log_info "Log file: $LOG_FILE"
    log_info "Base URL: $BASE_URL"
    log_info "Machine token: ${MACHINE_TOKEN:+SET (${#MACHINE_TOKEN} chars)}"
    log_info "Observation time: ${OBSERVE_TIME}s"
    log_info "Non-interactive: $NON_INTERACTIVE"
    echo ""

    confirm "Ready to begin RBAC enablement sequence?"

    # Step 1: Pre-flight
    if ! step_preflight; then
        log_fail "Pre-flight checks failed. Aborting."
        exit 1
    fi
    confirm "Pre-flight checks passed. Proceed to backup?"

    # Step 2: Backup
    if ! step_backup; then
        log_fail "Backup failed. Aborting."
        exit 1
    fi
    confirm "Backup complete. Proceed to enable RBAC?"

    # Step 3: Enable
    if ! step_enable; then
        log_fail "Enable failed. Rolling back..."
        rollback
    fi
    confirm "RBAC enabled. Proceed to smoke tests?"

    # Step 4: Smoke
    if ! step_smoke; then
        log_warn "Some smoke tests failed. Review above output."
        confirm "Continue despite smoke test warnings? (Or Ctrl+C to rollback)"
    fi
    confirm "Smoke tests complete. Review monitoring checklist?"

    # Step 5: Monitoring checklist
    step_monitoring_checklist
    confirm "Monitoring checklist reviewed. Begin 15-minute observation?"

    # Step 6: Observation
    step_observe

    # Step 7: Final verification
    step_final_verify

    # Success
    trap - SIGINT SIGTERM
    exit 0
}

main "$@"
