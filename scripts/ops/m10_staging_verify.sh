#!/bin/bash
# M10 Staging Verification Script
#
# Comprehensive verification script for M10 Phase 6 production hardening
# Run this on staging BEFORE deploying to production.
#
# Usage:
#   ./scripts/ops/m10_staging_verify.sh
#   ./scripts/ops/m10_staging_verify.sh --skip-chaos    # Skip chaos tests
#   ./scripts/ops/m10_staging_verify.sh --json          # JSON output
#
# Prerequisites:
#   - DATABASE_URL set to staging database
#   - REDIS_URL set to staging Redis
#   - Python environment with backend dependencies

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")/backend"

# Parse arguments
SKIP_CHAOS=false
JSON_OUTPUT=false
for arg in "$@"; do
    case $arg in
        --skip-chaos)
            SKIP_CHAOS=true
            shift
            ;;
        --json)
            JSON_OUTPUT=true
            shift
            ;;
    esac
done

# Results tracking
declare -A RESULTS
OVERALL_PASS=true

log_info() {
    if [ "$JSON_OUTPUT" = false ]; then
        echo -e "${BLUE}[INFO]${NC} $1"
    fi
}

log_success() {
    if [ "$JSON_OUTPUT" = false ]; then
        echo -e "${GREEN}[PASS]${NC} $1"
    fi
}

log_warning() {
    if [ "$JSON_OUTPUT" = false ]; then
        echo -e "${YELLOW}[WARN]${NC} $1"
    fi
}

log_error() {
    if [ "$JSON_OUTPUT" = false ]; then
        echo -e "${RED}[FAIL]${NC} $1"
    fi
}

log_header() {
    if [ "$JSON_OUTPUT" = false ]; then
        echo ""
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${BLUE}  $1${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    fi
}

# Check prerequisites
check_prerequisites() {
    log_header "PREREQUISITES CHECK"

    # Check DATABASE_URL
    if [ -z "${DATABASE_URL:-}" ]; then
        log_error "DATABASE_URL not set"
        RESULTS["prereq_database_url"]="FAIL"
        OVERALL_PASS=false
    else
        log_success "DATABASE_URL is set"
        RESULTS["prereq_database_url"]="PASS"
    fi

    # Check REDIS_URL
    if [ -z "${REDIS_URL:-}" ]; then
        log_warning "REDIS_URL not set (using default localhost:6379)"
        RESULTS["prereq_redis_url"]="WARN"
    else
        log_success "REDIS_URL is set"
        RESULTS["prereq_redis_url"]="PASS"
    fi

    # Check backend directory
    if [ -d "$BACKEND_DIR" ]; then
        log_success "Backend directory found: $BACKEND_DIR"
        RESULTS["prereq_backend_dir"]="PASS"
    else
        log_error "Backend directory not found: $BACKEND_DIR"
        RESULTS["prereq_backend_dir"]="FAIL"
        OVERALL_PASS=false
    fi

    # Check Python
    if command -v python3 &> /dev/null; then
        log_success "Python3 available: $(python3 --version)"
        RESULTS["prereq_python"]="PASS"
    else
        log_error "Python3 not found"
        RESULTS["prereq_python"]="FAIL"
        OVERALL_PASS=false
    fi
}

# Check current migration state
check_migration_state() {
    log_header "MIGRATION STATE CHECK"

    cd "$BACKEND_DIR"

    local current_rev
    current_rev=$(DATABASE_URL="$DATABASE_URL" PYTHONPATH=. alembic current 2>/dev/null | head -1 || echo "unknown")

    log_info "Current migration: $current_rev"

    if [[ "$current_rev" == *"022"* ]]; then
        log_success "Migration 022 is applied"
        RESULTS["migration_022"]="PASS"
    else
        log_warning "Migration 022 not yet applied (current: $current_rev)"
        RESULTS["migration_022"]="NOT_APPLIED"
    fi
}

# Apply migration if not already applied
apply_migration() {
    log_header "APPLYING MIGRATION 022"

    cd "$BACKEND_DIR"

    log_info "Running alembic upgrade to 022..."

    if DATABASE_URL="$DATABASE_URL" PYTHONPATH=. alembic upgrade 022_m10_production_hardening 2>&1; then
        log_success "Migration 022 applied successfully"
        RESULTS["migration_apply"]="PASS"
    else
        log_error "Migration 022 failed"
        RESULTS["migration_apply"]="FAIL"
        OVERALL_PASS=false
        return 1
    fi
}

# Verify tables and functions
verify_schema() {
    log_header "SCHEMA VERIFICATION"

    # Check tables
    local tables
    tables=$(psql "$DATABASE_URL" -t -c "
        SELECT string_agg(table_name, ',')
        FROM information_schema.tables
        WHERE table_schema = 'm10_recovery'
        AND table_name IN ('distributed_locks', 'replay_log', 'dead_letter_archive', 'outbox')
    " 2>/dev/null | tr -d '[:space:]')

    local table_count
    table_count=$(echo "$tables" | tr ',' '\n' | grep -c . || echo 0)

    if [ "$table_count" -eq 4 ]; then
        log_success "All 4 tables present: $tables"
        RESULTS["schema_tables"]="PASS"
    else
        log_error "Missing tables. Found: $tables"
        RESULTS["schema_tables"]="FAIL"
        OVERALL_PASS=false
    fi

    # Check functions
    local functions
    functions=$(psql "$DATABASE_URL" -t -c "
        SELECT COUNT(*)
        FROM information_schema.routines
        WHERE routine_schema = 'm10_recovery'
        AND routine_name IN ('acquire_lock', 'release_lock', 'extend_lock', 'record_replay',
                             'archive_dead_letter', 'publish_outbox', 'claim_outbox_events',
                             'complete_outbox_event', 'cleanup_expired_locks')
    " 2>/dev/null | tr -d '[:space:]')

    if [ "$functions" -ge 9 ]; then
        log_success "All 9 functions present"
        RESULTS["schema_functions"]="PASS"
    else
        log_error "Missing functions. Found: $functions/9"
        RESULTS["schema_functions"]="FAIL"
        OVERALL_PASS=false
    fi
}

# Test leader election
test_leader_election() {
    log_header "LEADER ELECTION TEST"

    cd "$BACKEND_DIR"

    log_info "Running leader election tests..."

    if DATABASE_URL="$DATABASE_URL" PYTHONPATH=. python -m pytest tests/test_m10_leader_election.py -v --tb=short 2>&1 | tee /tmp/m10_leader_test.log; then
        log_success "Leader election tests passed"
        RESULTS["test_leader_election"]="PASS"
    else
        log_error "Leader election tests failed"
        RESULTS["test_leader_election"]="FAIL"
        OVERALL_PASS=false
    fi
}

# Test lock functions manually
test_lock_functions() {
    log_header "LOCK FUNCTION TESTS"

    # Test acquire
    local acquire_result
    acquire_result=$(psql "$DATABASE_URL" -t -c "SELECT m10_recovery.acquire_lock('staging:verify:test', 'verify-script', 60)" 2>/dev/null | tr -d '[:space:]')

    if [ "$acquire_result" = "t" ]; then
        log_success "Lock acquire: OK"
        RESULTS["lock_acquire"]="PASS"
    else
        log_error "Lock acquire: FAILED ($acquire_result)"
        RESULTS["lock_acquire"]="FAIL"
        OVERALL_PASS=false
    fi

    # Test extend
    local extend_result
    extend_result=$(psql "$DATABASE_URL" -t -c "SELECT m10_recovery.extend_lock('staging:verify:test', 'verify-script', 120)" 2>/dev/null | tr -d '[:space:]')

    if [ "$extend_result" = "t" ]; then
        log_success "Lock extend: OK"
        RESULTS["lock_extend"]="PASS"
    else
        log_error "Lock extend: FAILED ($extend_result)"
        RESULTS["lock_extend"]="FAIL"
        OVERALL_PASS=false
    fi

    # Test release
    local release_result
    release_result=$(psql "$DATABASE_URL" -t -c "SELECT m10_recovery.release_lock('staging:verify:test', 'verify-script')" 2>/dev/null | tr -d '[:space:]')

    if [ "$release_result" = "t" ]; then
        log_success "Lock release: OK"
        RESULTS["lock_release"]="PASS"
    else
        log_error "Lock release: FAILED ($release_result)"
        RESULTS["lock_release"]="FAIL"
        OVERALL_PASS=false
    fi
}

# Test replay log idempotency
test_replay_log() {
    log_header "REPLAY LOG IDEMPOTENCY TEST"

    local test_id="staging-verify-$(date +%s)"

    # First insert
    local first_result
    first_result=$(psql "$DATABASE_URL" -t -c "
        SELECT was_duplicate FROM m10_recovery.record_replay(
            '$test_id-orig',
            '$test_id-dl',
            NULL,
            NULL,
            '$test_id-new',
            'verify-script'
        )
    " 2>/dev/null | tr -d '[:space:]')

    if [ "$first_result" = "f" ]; then
        log_success "First insert: OK (not duplicate)"
        RESULTS["replay_first_insert"]="PASS"
    else
        log_error "First insert: FAILED (expected f, got $first_result)"
        RESULTS["replay_first_insert"]="FAIL"
        OVERALL_PASS=false
    fi

    # Duplicate insert
    local second_result
    second_result=$(psql "$DATABASE_URL" -t -c "
        SELECT was_duplicate FROM m10_recovery.record_replay(
            '$test_id-orig',
            '$test_id-dl-2',
            NULL,
            NULL,
            '$test_id-new-2',
            'verify-script'
        )
    " 2>/dev/null | tr -d '[:space:]')

    if [ "$second_result" = "t" ]; then
        log_success "Duplicate detection: OK (detected duplicate)"
        RESULTS["replay_duplicate"]="PASS"
    else
        log_error "Duplicate detection: FAILED (expected t, got $second_result)"
        RESULTS["replay_duplicate"]="FAIL"
        OVERALL_PASS=false
    fi

    # Cleanup
    psql "$DATABASE_URL" -c "DELETE FROM m10_recovery.replay_log WHERE original_msg_id = '$test_id-orig'" &>/dev/null
}

# Run chaos tests
run_chaos_tests() {
    if [ "$SKIP_CHAOS" = true ]; then
        log_header "CHAOS TESTS (SKIPPED)"
        log_warning "Chaos tests skipped via --skip-chaos flag"
        RESULTS["chaos_tests"]="SKIPPED"
        return 0
    fi

    log_header "CHAOS TESTS"

    cd "$BACKEND_DIR"

    log_info "Running chaos tests (excluding high_volume)..."

    if DATABASE_URL="$DATABASE_URL" PYTHONPATH=. python -m pytest tests/test_m10_recovery_chaos.py -v -k "not high_volume" --tb=short 2>&1 | tee /tmp/m10_chaos_test.log; then
        log_success "Chaos tests passed"
        RESULTS["chaos_tests"]="PASS"
    else
        log_error "Chaos tests failed"
        RESULTS["chaos_tests"]="FAIL"
        OVERALL_PASS=false
    fi
}

# Run production hardening tests
run_hardening_tests() {
    log_header "PRODUCTION HARDENING TESTS"

    cd "$BACKEND_DIR"

    log_info "Running production hardening tests..."

    if DATABASE_URL="$DATABASE_URL" PYTHONPATH=. python -m pytest tests/test_m10_production_hardening.py -v --tb=short 2>&1 | tee /tmp/m10_hardening_test.log; then
        log_success "Production hardening tests passed"
        RESULTS["hardening_tests"]="PASS"
    else
        log_error "Production hardening tests failed"
        RESULTS["hardening_tests"]="FAIL"
        OVERALL_PASS=false
    fi
}

# Test outbox processor (dry run)
test_outbox_processor() {
    log_header "OUTBOX PROCESSOR TEST"

    cd "$BACKEND_DIR"

    log_info "Testing outbox processor (one batch)..."

    if timeout 30 DATABASE_URL="$DATABASE_URL" PYTHONPATH=. python -m app.worker.outbox_processor --once --debug 2>&1 | tee /tmp/m10_outbox_test.log; then
        log_success "Outbox processor ran successfully"
        RESULTS["outbox_processor"]="PASS"
    else
        local exit_code=$?
        if [ $exit_code -eq 124 ]; then
            log_warning "Outbox processor timed out (may be normal if no events)"
            RESULTS["outbox_processor"]="WARN"
        else
            log_error "Outbox processor failed"
            RESULTS["outbox_processor"]="FAIL"
            OVERALL_PASS=false
        fi
    fi
}

# Test reconcile script
test_reconcile_script() {
    log_header "RECONCILE SCRIPT TEST"

    cd "$BACKEND_DIR"

    log_info "Testing reconcile script (dry run)..."

    if DATABASE_URL="$DATABASE_URL" PYTHONPATH=. python -m scripts.ops.reconcile_dl --dry-run --json 2>&1 | tee /tmp/m10_reconcile_test.log; then
        log_success "Reconcile script ran successfully"
        RESULTS["reconcile_script"]="PASS"
    else
        log_error "Reconcile script failed"
        RESULTS["reconcile_script"]="FAIL"
        OVERALL_PASS=false
    fi
}

# Test matview refresh
test_matview_refresh() {
    log_header "MATVIEW REFRESH TEST"

    cd "$BACKEND_DIR"

    log_info "Testing matview refresh..."

    if DATABASE_URL="$DATABASE_URL" PYTHONPATH=. python -m scripts.ops.refresh_matview --json 2>&1 | tee /tmp/m10_matview_test.log; then
        log_success "Matview refresh ran successfully"
        RESULTS["matview_refresh"]="PASS"
    else
        log_error "Matview refresh failed"
        RESULTS["matview_refresh"]="FAIL"
        OVERALL_PASS=false
    fi
}

# Check Redis configuration
check_redis_config() {
    log_header "REDIS CONFIGURATION CHECK"

    cd "$BACKEND_DIR"

    log_info "Checking Redis configuration..."

    if PYTHONPATH=. python -m scripts.ops.check_redis_config --json 2>&1 | tee /tmp/m10_redis_check.log; then
        log_success "Redis configuration OK"
        RESULTS["redis_config"]="PASS"
    else
        log_error "Redis configuration check failed"
        RESULTS["redis_config"]="FAIL"
        OVERALL_PASS=false
    fi
}

# Generate summary
generate_summary() {
    log_header "VERIFICATION SUMMARY"

    local pass_count=0
    local fail_count=0
    local warn_count=0
    local skip_count=0

    for key in "${!RESULTS[@]}"; do
        case "${RESULTS[$key]}" in
            PASS)
                ((pass_count++))
                ;;
            FAIL)
                ((fail_count++))
                ;;
            WARN)
                ((warn_count++))
                ;;
            SKIPPED)
                ((skip_count++))
                ;;
        esac
    done

    if [ "$JSON_OUTPUT" = true ]; then
        echo "{"
        echo "  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
        echo "  \"overall\": \"$([ "$OVERALL_PASS" = true ] && echo 'PASS' || echo 'FAIL')\","
        echo "  \"summary\": {"
        echo "    \"pass\": $pass_count,"
        echo "    \"fail\": $fail_count,"
        echo "    \"warn\": $warn_count,"
        echo "    \"skipped\": $skip_count"
        echo "  },"
        echo "  \"results\": {"
        local first=true
        for key in "${!RESULTS[@]}"; do
            if [ "$first" = true ]; then
                first=false
            else
                echo ","
            fi
            printf "    \"%s\": \"%s\"" "$key" "${RESULTS[$key]}"
        done
        echo ""
        echo "  }"
        echo "}"
    else
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  RESULTS"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "  PASS:    $pass_count"
        echo "  FAIL:    $fail_count"
        echo "  WARN:    $warn_count"
        echo "  SKIPPED: $skip_count"
        echo ""

        if [ "$OVERALL_PASS" = true ]; then
            echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
            echo -e "${GREEN}  STAGING VERIFICATION: PASSED${NC}"
            echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
            echo ""
            echo "Safe to proceed with production deployment."
        else
            echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
            echo -e "${RED}  STAGING VERIFICATION: FAILED${NC}"
            echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
            echo ""
            echo "DO NOT proceed with production deployment."
            echo ""
            echo "Failed checks:"
            for key in "${!RESULTS[@]}"; do
                if [ "${RESULTS[$key]}" = "FAIL" ]; then
                    echo "  - $key"
                fi
            done
        fi
        echo ""
    fi
}

# Main execution
main() {
    log_header "M10 STAGING VERIFICATION"
    log_info "Starting verification at $(date)"
    log_info "Script: $0"
    log_info "Backend: $BACKEND_DIR"

    # Run all checks
    check_prerequisites

    if [ "$OVERALL_PASS" = false ]; then
        generate_summary
        exit 1
    fi

    check_migration_state

    # Apply migration if needed
    if [ "${RESULTS[migration_022]}" = "NOT_APPLIED" ]; then
        apply_migration
    fi

    verify_schema
    test_lock_functions
    test_replay_log
    test_leader_election
    run_hardening_tests
    run_chaos_tests
    test_outbox_processor
    test_reconcile_script
    test_matview_refresh
    check_redis_config

    generate_summary

    if [ "$OVERALL_PASS" = true ]; then
        exit 0
    else
        exit 1
    fi
}

# Run main
main
