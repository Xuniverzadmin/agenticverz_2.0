#!/bin/bash
# CI Consistency Checker v1.2 - Production-grade CI validation
#
# Usage:
#   ./scripts/ops/ci_consistency_check.sh           # Full check
#   ./scripts/ops/ci_consistency_check.sh --quick   # Fast pre-commit check
#   ./scripts/ops/ci_consistency_check.sh --fix     # Attempt auto-fixes
#
# This script checks for common CI failure patterns:
# 1. Service configuration consistency (Redis, PostgreSQL, etc.)
# 2. Environment variable requirements
# 3. File existence requirements
# 4. Concurrency safety patterns
# 5. Process observability requirements
# 6. Background worker configuration (NEW in v1.2)
# 7. Schema audit infrastructure (NEW in v1.2)
# 8. Migration rollback testing (NEW in v1.2)
# 9. Metrics endpoint validation (NEW in v1.2)
#
# Run before every CI push to catch issues early.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
ERRORS=0
WARNINGS=0
FIXES=0

# Flags
QUICK_MODE=false
FIX_MODE=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --quick) QUICK_MODE=true ;;
        --fix) FIX_MODE=true ;;
        --help|-h)
            echo "Usage: $0 [--quick] [--fix]"
            echo "  --quick  Fast pre-commit check (skip slow tests)"
            echo "  --fix    Attempt to auto-fix issues"
            exit 0
            ;;
    esac
done

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    ERRORS=$((ERRORS + 1))
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

log_ok() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_fix() {
    echo -e "${GREEN}[FIX]${NC} $1"
    FIXES=$((FIXES + 1))
}

header() {
    echo ""
    echo -e "${BLUE}=== $1 ===${NC}"
}

#############################################
# LAYER 1: CI WORKFLOW CONFIGURATION
#############################################

check_ci_workflow() {
    header "CI Workflow Configuration"

    local CI_FILE="$REPO_ROOT/.github/workflows/ci.yml"

    if [[ ! -f "$CI_FILE" ]]; then
        log_error "CI workflow file not found: $CI_FILE"
        return
    fi

    # Check 1: All Redis-dependent jobs must have explicit REDIS_URL
    if grep -q "redis:" "$CI_FILE"; then
        log_ok "Redis service container defined"

        # Check for explicit REDIS_URL in jobs that need it
        # Use sed to extract job block and check for REDIS_URL
        local REDIS_JOBS=("integration" "e2e-tests" "m10-tests")
        for job in "${REDIS_JOBS[@]}"; do
            # Extract the job section and check for REDIS_URL
            # Look for 150 lines after job: to catch all env vars
            if grep -A 150 "^  ${job}:" "$CI_FILE" 2>/dev/null | grep -m1 "REDIS_URL:" >/dev/null 2>&1; then
                log_ok "Job '$job' has explicit REDIS_URL"
            else
                log_error "Job '$job' missing explicit REDIS_URL - may use wrong Redis"
            fi
        done
    else
        log_warn "No Redis service container in CI - external Redis will be used"
    fi

    # Check 2: Worker processes must have PYTHONUNBUFFERED
    if grep -q "python.*worker" "$CI_FILE"; then
        if grep -q "PYTHONUNBUFFERED" "$CI_FILE"; then
            log_ok "PYTHONUNBUFFERED found for worker processes"
        else
            log_error "Worker processes should have PYTHONUNBUFFERED=1"
        fi
    fi

    # Check 3: No '|| true' on critical jobs (allows silent failures)
    if grep -qE "pytest.*\|\| *true" "$CI_FILE" 2>/dev/null; then
        log_error "Found '|| true' on pytest commands - failures will be silently ignored"
    else
        log_ok "No silent failure masking found"
    fi

    # Check 4: All jobs should have timeout-minutes
    local JOBS_WITHOUT_TIMEOUT=$(grep -c "^  [a-z-]*:" "$CI_FILE" || true)
    local TIMEOUT_COUNT=$(grep -c "timeout-minutes:" "$CI_FILE" || true)
    if [[ $TIMEOUT_COUNT -lt $JOBS_WITHOUT_TIMEOUT ]]; then
        log_warn "Some jobs may be missing timeout-minutes"
    else
        log_ok "All jobs have timeouts"
    fi

    # Check 5: No DATABASE_URL in job outputs (GitHub blocks secrets)
    if grep -q "outputs:" "$CI_FILE" && grep -A 10 "outputs:" "$CI_FILE" | grep -q "database_url:"; then
        log_error "DATABASE_URL in job outputs - GitHub blocks secrets in outputs!"
        log_info "  Fix: Each job should construct DATABASE_URL via neonctl + GITHUB_ENV"
    else
        log_ok "No secret-containing job outputs detected"
    fi

    # Check 6: Neon ephemeral branch jobs must construct their own DATABASE_URL
    local NEON_JOBS=("integration" "costsim" "costsim-integration" "costsim-wiremock" "e2e-tests" "m10-tests")
    for job in "${NEON_JOBS[@]}"; do
        if grep -A 100 "^  ${job}:" "$CI_FILE" 2>/dev/null | grep -q "neonctl connection-string"; then
            log_ok "Job '$job' constructs DATABASE_URL via neonctl"
        elif grep -A 100 "^  ${job}:" "$CI_FILE" 2>/dev/null | grep -q "needs.setup-neon-branch.outputs.database_url"; then
            log_error "Job '$job' uses database_url from outputs - will fail due to secret blocking"
        fi
    done
}

#############################################
# LAYER 2: INFRASTRUCTURE DEPENDENCIES
#############################################

check_infrastructure_deps() {
    header "Infrastructure Dependencies"

    # Check 1: WireMock mappings exist
    local WIREMOCK_DIR="$REPO_ROOT/tools/wiremock/mappings"
    if [[ -d "$WIREMOCK_DIR" ]]; then
        local MAPPING_COUNT=$(find "$WIREMOCK_DIR" -name "*.json" | wc -l)
        if [[ $MAPPING_COUNT -gt 0 ]]; then
            log_ok "WireMock mappings: $MAPPING_COUNT files"
        else
            log_error "WireMock directory exists but no mappings found"
        fi
    else
        log_warn "WireMock mappings directory not found"
    fi

    # Check 2: Docker Compose services match CI services
    local COMPOSE_FILE="$REPO_ROOT/docker-compose.yml"
    if [[ -f "$COMPOSE_FILE" ]]; then
        log_ok "docker-compose.yml exists"

        # Check Redis configuration consistency
        if grep -q "redis:" "$COMPOSE_FILE"; then
            log_ok "Redis service in docker-compose.yml"
        fi

        if grep -q "postgres:" "$COMPOSE_FILE"; then
            log_ok "PostgreSQL service in docker-compose.yml"
        fi
    else
        log_warn "docker-compose.yml not found"
    fi

    # Check 3: Required environment variables documented
    local ENV_EXAMPLE="$REPO_ROOT/.env.example"
    if [[ -f "$ENV_EXAMPLE" ]]; then
        local REQUIRED_VARS=("DATABASE_URL" "REDIS_URL" "AOS_API_KEY")
        for var in "${REQUIRED_VARS[@]}"; do
            if grep -q "^$var=" "$ENV_EXAMPLE" || grep -q "^#.*$var" "$ENV_EXAMPLE"; then
                log_ok "Env var documented: $var"
            else
                log_error "Missing from .env.example: $var"
            fi
        done
    else
        log_warn ".env.example not found"
    fi
}

#############################################
# LAYER 3: CODE PATTERNS
#############################################

check_code_patterns() {
    header "Code Patterns"

    # Check 1: Atomic operations for concurrency
    local CONCURRENT_FILE="$REPO_ROOT/backend/app/utils/concurrent_runs.py"
    if [[ -f "$CONCURRENT_FILE" ]]; then
        if grep -q "ACQUIRE_SCRIPT" "$CONCURRENT_FILE" || grep -q "Lua" "$CONCURRENT_FILE"; then
            log_ok "Concurrency limiter uses atomic operations"
        else
            log_error "Concurrency limiter may have TOCTOU vulnerability"
        fi
    fi

    # Check 2: No synchronous DB calls in async context
    if ! $QUICK_MODE; then
        local SYNC_DB_PATTERN="session.execute.*SELECT"
        local ASYNC_FILES=$(find "$REPO_ROOT/backend/app" -name "*.py" -exec grep -l "async def" {} \; 2>/dev/null || true)
        local SYNC_IN_ASYNC=0
        for f in $ASYNC_FILES; do
            if grep -q "with Session" "$f" 2>/dev/null; then
                # Check if it's inside an async function
                if grep -B 5 "with Session" "$f" | grep -q "async def"; then
                    log_warn "Potential sync DB in async context: $f"
                    SYNC_IN_ASYNC=$((SYNC_IN_ASYNC + 1))
                fi
            fi
        done
        if [[ $SYNC_IN_ASYNC -eq 0 ]]; then
            log_ok "No obvious sync DB calls in async context"
        fi
    fi

    # Check 3: Health endpoints exist
    local MAIN_FILE="$REPO_ROOT/backend/app/main.py"
    if [[ -f "$MAIN_FILE" ]]; then
        if grep -q "/health" "$MAIN_FILE" || grep -q "@app.get.*health" "$MAIN_FILE"; then
            log_ok "Health endpoint defined"
        else
            log_warn "No health endpoint found in main.py"
        fi
    fi

    # Check 4: Background processes should be observable
    if grep -rq "nohup.*python" "$REPO_ROOT/.github" 2>/dev/null; then
        if grep -rq "PYTHONUNBUFFERED\|python -u" "$REPO_ROOT/.github" 2>/dev/null; then
            log_ok "Background Python processes use unbuffered output"
        else
            log_error "Background Python processes may have buffered output"
        fi
    fi
}

#############################################
# LAYER 4: ALEMBIC MIGRATIONS
#############################################

check_alembic_migrations() {
    header "Alembic Migrations"

    local ALEMBIC_DIR="$REPO_ROOT/backend/alembic/versions"

    if [[ ! -d "$ALEMBIC_DIR" ]]; then
        log_warn "Alembic versions directory not found"
        return
    fi

    # Check 1: Revision IDs must be <= 32 characters (alembic_version column limit)
    local LONG_REVISIONS=0
    for f in "$ALEMBIC_DIR"/*.py; do
        [[ -f "$f" ]] || continue
        [[ "$f" == *"__pycache__"* ]] && continue

        local REV=$(grep "^revision = " "$f" 2>/dev/null | head -1 | sed "s/revision = ['\"]//g" | sed "s/['\"]//g")
        if [[ -n "$REV" ]]; then
            local LEN=${#REV}
            if [[ $LEN -gt 32 ]]; then
                log_error "Revision ID too long ($LEN > 32): $REV"
                log_info "  File: $(basename "$f")"
                LONG_REVISIONS=$((LONG_REVISIONS + 1))
            elif [[ $LEN -gt 28 ]]; then
                log_warn "Revision ID near limit ($LEN/32): $REV"
            fi
        fi
    done

    if [[ $LONG_REVISIONS -eq 0 ]]; then
        log_ok "All revision IDs fit within varchar(32)"
    fi

    # Check 2: Verify single migration head (no multiple heads)
    if command -v alembic &>/dev/null; then
        cd "$REPO_ROOT/backend" 2>/dev/null || true
        local HEADS=$(PYTHONPATH=. alembic heads 2>/dev/null | grep -c "head" || echo "0")
        if [[ "$HEADS" == "1" ]]; then
            log_ok "Single migration head (no branching)"
        elif [[ "$HEADS" -gt 1 ]]; then
            log_error "Multiple migration heads detected - run 'alembic merge heads'"
        fi
        cd "$REPO_ROOT" 2>/dev/null || true
    else
        log_info "Alembic not in PATH - skipping head check"
    fi

    # Check 3: Migrations should use idempotent patterns (IF NOT EXISTS, DO blocks)
    local NON_IDEMPOTENT=0
    for f in "$ALEMBIC_DIR"/*.py; do
        [[ -f "$f" ]] || continue
        [[ "$f" == *"__pycache__"* ]] && continue

        # Check for CREATE TABLE without IF NOT EXISTS
        if grep -q "CREATE TABLE [^I]" "$f" 2>/dev/null && ! grep -q "IF NOT EXISTS\|DO \$\$" "$f" 2>/dev/null; then
            # Only warn for newer migrations (028+)
            local BASENAME=$(basename "$f")
            if [[ "$BASENAME" > "028" ]]; then
                log_warn "Non-idempotent migration: $(basename "$f")"
                NON_IDEMPOTENT=$((NON_IDEMPOTENT + 1))
            fi
        fi
    done

    if [[ $NON_IDEMPOTENT -eq 0 ]]; then
        log_ok "Recent migrations use idempotent patterns"
    fi
}

#############################################
# LAYER 5: TEST INFRASTRUCTURE
#############################################

check_test_infrastructure() {
    header "Test Infrastructure"

    # Check 1: Test fixtures handle cleanup
    local CONFTEST="$REPO_ROOT/backend/tests/conftest.py"
    if [[ -f "$CONFTEST" ]]; then
        if grep -q "yield" "$CONFTEST"; then
            log_ok "Test fixtures use yield for cleanup"
        else
            log_warn "Test fixtures may not properly clean up resources"
        fi
    fi

    # Check 2: Integration tests have skip conditions
    local INTEGRATION_TEST="$REPO_ROOT/backend/tests/test_integration.py"
    if [[ -f "$INTEGRATION_TEST" ]]; then
        if grep -q "skipif\|requires_" "$INTEGRATION_TEST"; then
            log_ok "Integration tests have conditional skips"
        else
            log_warn "Integration tests should have skip conditions for missing services"
        fi
    fi

    # Check 3: No hardcoded test timeouts that are too short
    if ! $QUICK_MODE; then
        local SHORT_TIMEOUTS=$(grep -rn "timeout.*=[0-9]" "$REPO_ROOT/backend/tests" 2>/dev/null | grep -v "30\|60\|120" | head -5)
        if [[ -n "$SHORT_TIMEOUTS" ]]; then
            log_warn "Some tests have potentially short timeouts:"
            echo "$SHORT_TIMEOUTS" | head -3
        else
            log_ok "Test timeouts look reasonable"
        fi
    fi
}

#############################################
# LAYER 5: SERVICE CONNECTIVITY MATRIX
#############################################

check_service_matrix() {
    header "Service Connectivity Matrix"

    cat <<EOF

Service Matrix (CI vs Local vs Production):
┌────────────────┬────────────────────────────────┬─────────────────────┬─────────────────────┐
│ Service        │ CI (GitHub Actions)            │ Local (docker)      │ Production          │
├────────────────┼────────────────────────────────┼─────────────────────┼─────────────────────┤
│ PostgreSQL     │ Neon ephemeral branch          │ localhost:5433      │ Neon (cloud)        │
│                │ (fallback: Docker localhost)   │                     │                     │
│ Redis          │ localhost:6379 (container)     │ localhost:6379      │ Upstash (cloud)     │
│ Backend        │ localhost:8000                 │ localhost:8000      │ api.agenticverz.com │
│ WireMock       │ localhost:8080                 │ localhost:8080      │ N/A                 │
└────────────────┴────────────────────────────────┴─────────────────────┴─────────────────────┘

CI Database Strategy (Ephemeral Neon Branches):
┌─────────────────────┬────────────────────────────────────────────────────┐
│ Phase               │ Description                                        │
├─────────────────────┼────────────────────────────────────────────────────┤
│ setup-neon-branch   │ Creates branch: ci-{run_id}-{attempt}              │
│                     │ Parent: Agenticverz-AOS (production snapshot)      │
├─────────────────────┼────────────────────────────────────────────────────┤
│ Each DB job         │ Uses neonctl to construct DATABASE_URL             │
│                     │ (Cannot pass URL as output - GitHub blocks secrets)│
├─────────────────────┼────────────────────────────────────────────────────┤
│ cleanup-neon-branch │ Deletes ephemeral branch after all jobs complete   │
└─────────────────────┴────────────────────────────────────────────────────┘

EOF

    log_info "Ensure CI jobs use correct service URLs for their environment"
    log_ok "Service matrix documented"
}

#############################################
# LAYER 6: PRE-FLIGHT CHECKS (QUICK MODE)
#############################################

preflight_checks() {
    header "Pre-Flight Checks"

    # Check 1: Git status clean (for reliable CI)
    if git status --porcelain | grep -q .; then
        log_warn "Uncommitted changes detected - CI will use committed state"
    else
        log_ok "Git working directory clean"
    fi

    # Check 2: Branch is up to date
    local CURRENT_BRANCH=$(git branch --show-current)
    if [[ -n "$CURRENT_BRANCH" ]]; then
        log_info "Current branch: $CURRENT_BRANCH"
    fi

    # Check 3: Last CI run status
    if command -v gh &>/dev/null; then
        local LAST_RUN=$(gh run list --limit 1 --json conclusion,status,name 2>/dev/null | head -1 || echo "")
        if [[ -n "$LAST_RUN" ]]; then
            log_info "Last CI run: $LAST_RUN"
        fi
    else
        log_info "Install 'gh' CLI for CI status checks"
    fi
}

#############################################
# LAYER 7: PRODUCTION-GRADE CI ELEMENTS (v1.2)
#############################################

check_production_ci_elements() {
    header "Production-Grade CI Elements (v1.2)"

    local CI_FILE="$REPO_ROOT/.github/workflows/ci.yml"

    # Check 1: Schema audit script exists
    local SCHEMA_AUDIT="$REPO_ROOT/scripts/ops/schema_audit.py"
    if [[ -f "$SCHEMA_AUDIT" ]]; then
        log_ok "Schema audit script exists: scripts/ops/schema_audit.py"
    else
        log_error "Missing schema audit script - required for drift detection"
        log_info "  Create: scripts/ops/schema_audit.py"
    fi

    # Check 2: Metrics validation script exists
    local METRICS_SCRIPT="$REPO_ROOT/scripts/ops/metrics_validation.py"
    if [[ -f "$METRICS_SCRIPT" ]]; then
        log_ok "Metrics validation script exists: scripts/ops/metrics_validation.py"
    else
        log_error "Missing metrics validation script - required for observability"
        log_info "  Create: scripts/ops/metrics_validation.py"
    fi

    # Check 3: CI has migration rollback test (up/down/up pattern)
    if [[ -f "$CI_FILE" ]]; then
        if grep -q "alembic downgrade" "$CI_FILE" 2>/dev/null; then
            log_ok "CI includes migration rollback test (up/down/up)"
        else
            log_error "CI missing migration rollback test"
            log_info "  Add: alembic upgrade head && alembic downgrade base && alembic upgrade head"
        fi
    fi

    # Check 4: CI has schema audit step
    if [[ -f "$CI_FILE" ]]; then
        if grep -q "schema_audit.py\|schema-audit\|Schema audit" "$CI_FILE" 2>/dev/null; then
            log_ok "CI includes schema audit step"
        else
            log_warn "CI missing schema audit step"
            log_info "  Add: python scripts/ops/schema_audit.py"
        fi
    fi

    # Check 5: CI has worker health check step (for e2e tests)
    if [[ -f "$CI_FILE" ]]; then
        if grep -q "Worker health check\|pgrep.*worker\|worker.*running" "$CI_FILE" 2>/dev/null; then
            log_ok "CI includes worker health check"
        else
            log_warn "CI missing explicit worker health check"
            log_info "  Add: pgrep -f 'app.worker.pool' check step"
        fi
    fi

    # Check 6: CI has metrics endpoint validation (for e2e tests)
    if [[ -f "$CI_FILE" ]]; then
        if grep -q "metrics_validation.py\|Metrics endpoint validation\|nova_runs_total" "$CI_FILE" 2>/dev/null; then
            log_ok "CI includes metrics endpoint validation"
        else
            log_warn "CI missing metrics endpoint validation"
            log_info "  Add: python scripts/ops/metrics_validation.py"
        fi
    fi

    # Check 7: E2E test worker startup uses PYTHONUNBUFFERED
    if [[ -f "$CI_FILE" ]]; then
        if grep -A 20 "e2e-tests:" "$CI_FILE" 2>/dev/null | grep -q "PYTHONUNBUFFERED"; then
            log_ok "E2E worker uses PYTHONUNBUFFERED for observable output"
        else
            log_warn "E2E worker may have buffered output"
            log_info "  Add: PYTHONUNBUFFERED=1 to worker startup"
        fi
    fi

    # Check 8: E2E shows adequate worker logs on failure
    if [[ -f "$CI_FILE" ]]; then
        if grep -q "tail.*50\|tail.*100\|tail -n 50\|tail -n 100" "$CI_FILE" 2>/dev/null; then
            log_ok "CI shows adequate log output (50+ lines)"
        else
            log_warn "CI may show truncated logs - increase tail count"
        fi
    fi
}

#############################################
# SUMMARY
#############################################

print_summary() {
    header "Summary"

    echo ""
    if [[ $ERRORS -eq 0 ]]; then
        echo -e "${GREEN}All consistency checks passed!${NC}"
    else
        echo -e "${RED}Found $ERRORS error(s) that need attention.${NC}"
    fi

    if [[ $WARNINGS -gt 0 ]]; then
        echo -e "${YELLOW}Found $WARNINGS warning(s) to review.${NC}"
    fi

    if [[ $FIXES -gt 0 ]]; then
        echo -e "${GREEN}Applied $FIXES automatic fix(es).${NC}"
    fi

    echo ""
    echo "Documentation:"
    echo "  - RCA Report: docs/RCA-CI-FIXES-2025-12-07.md"
    echo "  - Memory PIN: docs/memory-pins/PIN-045-ci-infrastructure-fixes.md"
    echo "  - Memory PIN: docs/memory-pins/PIN-079-ci-ephemeral-neon-fixes.md"
    echo ""

    if [[ $ERRORS -gt 0 ]]; then
        echo -e "${RED}CI push NOT recommended until errors are resolved.${NC}"
        exit 1
    else
        echo -e "${GREEN}Safe to push to CI.${NC}"
        exit 0
    fi
}

#############################################
# MAIN
#############################################

main() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     CI Consistency Checker v1.2            ║${NC}"
    echo -e "${BLUE}║     Fool-Proof Prevention Mechanism        ║${NC}"
    echo -e "${BLUE}║     + Production-Grade CI (2025-12-15)     ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
    echo ""

    if $QUICK_MODE; then
        log_info "Running in quick mode (skipping slow checks)"
    fi

    cd "$REPO_ROOT"

    preflight_checks
    check_ci_workflow
    check_infrastructure_deps
    check_code_patterns
    check_alembic_migrations

    if ! $QUICK_MODE; then
        check_test_infrastructure
        check_service_matrix
        check_production_ci_elements
    fi

    print_summary
}

main "$@"
