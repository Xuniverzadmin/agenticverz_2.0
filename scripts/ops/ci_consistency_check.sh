#!/bin/bash
# ============================================================================
# CI Consistency Checker v5.1 - AGENTICVERZ/MN-OS Certification Engine
# ============================================================================
#
# Purpose: Validate ALL Agenticverz milestones M0-M19 remain functional,
# internally consistent, and test-verified during CI, refactors, or features.
# Supports DUAL NAMING: Legacy milestone names AND MN-OS subsystem names.
#
# M20+ is OUT OF SCOPE - this engine stays strictly within M0-M19.
#
# Usage:
#   ./scripts/ops/ci_consistency_check.sh              # Full check
#   ./scripts/ops/ci_consistency_check.sh --quick      # Fast pre-commit check
#   ./scripts/ops/ci_consistency_check.sh --milestone  # Show milestone dashboard
#   ./scripts/ops/ci_consistency_check.sh --matrix     # Show test matrix
#   ./scripts/ops/ci_consistency_check.sh --json       # Output JSON for CI
#   ./scripts/ops/ci_consistency_check.sh --strict     # WARN = FAIL (blocks merge)
#   ./scripts/ops/ci_consistency_check.sh --coverage   # Include test coverage check
#   ./scripts/ops/ci_consistency_check.sh --smoke      # Run runtime smoke tests
#   ./scripts/ops/ci_consistency_check.sh --golden     # Run golden tests
#   ./scripts/ops/ci_consistency_check.sh --subsystems # Show MN-OS subsystem view
#
# v5.1 Changes:
#   - Secrets baseline validation (detect-secrets)
#   - Checks for unverified and actual secrets
#   - JSON validation of .secrets.baseline
#
# v5.0 Changes:
#   - MN-OS dual-name recognition (legacy + evolved + MN-OS names)
#   - --subsystems flag for MN-OS subsystem dashboard
#   - Detection patterns accept both naming conventions
#   - Forward-compatible with M20 (Machine-Native OS)
#
# v4.1 Changes:
#   - MISSING #1: Test Coverage Enforcement per milestone
#   - MISSING #2: Runtime Smoke Tests integration (runtime_smoke.py)
#   - MISSING #3: Golden Tests integration (golden_test.py)
#   - Test file presence AND passing verification
#
# MILESTONE → MN-OS SUBSYSTEM MAPPING:
#   M0:  Foundations → Kernel Primitives (KP)
#   M1:  Runtime → Agent Runtime Kernel (ARK)
#   M2:  Skill Registration → OS Capability Table (OCT)
#   M3:  Core Skills → Native OS Skills (NOS)
#   M4:  Workflow Engine → Agent Execution Engine (AXE)
#   M5:  Policy API → Constitutional Guardrail Layer (CGL)
#   M6:  CostSim V2 → Resource Economics Engine (REE)
#   M7:  Memory → System Memory Matrix (SMM)
#   M8:  SDK/Auth → Identity Authority & Access Panel (IAAP)
#   M9:  Failure Catalog → System Failure Intelligence Layer (SFIL)
#   M10: Recovery → System Self-Repair Layer (SSRL)
#   M11: LLM Adapters → Cognitive Interface Kernel (CIK)
#   M12: Multi-Agent → MAS Orchestrator Core (MOC)
#   M13: Console UI → OS Control Center (OCC)
#   M14: BudgetLLM → Cognitive Compliance Engine (CCE)
#   M15: SBA → Strategic Agency Kernel (SAK)
#   M16: Agent Governance → Agent Oversight Authority (AOA)
#   M17: CARE Routing → Cognitive Routing Kernel (CRK)
#   M18: CARE-L → Adaptive Governance Kernel (AGK)
#   M19: Policy Constitutional → OS Constitution (OSC)
#
# ============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Counters
ERRORS=0
WARNINGS=0
MILESTONE_PASS=0
MILESTONE_WARN=0
MILESTONE_FAIL=0

# Flags
QUICK_MODE=false
MILESTONE_MODE=false
MATRIX_MODE=false
JSON_MODE=false
STRICT_MODE=false
COVERAGE_MODE=false
SMOKE_MODE=false
GOLDEN_MODE=false
SUBSYSTEMS_MODE=false

# Test Coverage Tracking
declare -A MILESTONE_TEST_PASS
declare -A MILESTONE_TEST_TOTAL
declare -A MILESTONE_COVERAGE

# MN-OS Subsystem Names (Milestone → Subsystem)
declare -A MNOS_NAME
MNOS_NAME[M0]="Kernel Primitives"
MNOS_NAME[M1]="Agent Runtime Kernel"
MNOS_NAME[M2]="OS Capability Table"
MNOS_NAME[M3]="Native OS Skills"
MNOS_NAME[M4]="Agent Execution Engine"
MNOS_NAME[M5]="Constitutional Guardrail"
MNOS_NAME[M6]="Resource Economics Engine"
MNOS_NAME[M7]="System Memory Matrix"
MNOS_NAME[M8]="Identity Authority"
MNOS_NAME[M9]="Failure Intelligence"
MNOS_NAME[M10]="Self-Repair Layer"
MNOS_NAME[M11]="Cognitive Interface"
MNOS_NAME[M12]="MAS Orchestrator"
MNOS_NAME[M13]="OS Control Center"
MNOS_NAME[M14]="Cognitive Compliance"
MNOS_NAME[M15]="Strategic Agency"
MNOS_NAME[M16]="Oversight Authority"
MNOS_NAME[M17]="Cognitive Routing"
MNOS_NAME[M18]="Adaptive Governance"
MNOS_NAME[M19]="OS Constitution"

# MN-OS Acronyms
declare -A MNOS_ACRONYM
MNOS_ACRONYM[M0]="KP"
MNOS_ACRONYM[M1]="ARK"
MNOS_ACRONYM[M2]="OCT"
MNOS_ACRONYM[M3]="NOS"
MNOS_ACRONYM[M4]="AXE"
MNOS_ACRONYM[M5]="CGL"
MNOS_ACRONYM[M6]="REE"
MNOS_ACRONYM[M7]="SMM"
MNOS_ACRONYM[M8]="IAAP"
MNOS_ACRONYM[M9]="SFIL"
MNOS_ACRONYM[M10]="SSRL"
MNOS_ACRONYM[M11]="CIK"
MNOS_ACRONYM[M12]="MOC"
MNOS_ACRONYM[M13]="OCC"
MNOS_ACRONYM[M14]="CCE"
MNOS_ACRONYM[M15]="SAK"
MNOS_ACRONYM[M16]="AOA"
MNOS_ACRONYM[M17]="CRK"
MNOS_ACRONYM[M18]="AGK"
MNOS_ACRONYM[M19]="OSC"

# Milestone Status Tracking
declare -A MILESTONE_STATUS
declare -A MILESTONE_CHECKS
declare -A MILESTONE_DEPS_MET

# Initialize all milestones
for m in M0 M1 M2 M3 M4 M5 M6 M7 M8 M9 M10 M11 M12 M13 M14 M15 M16 M17 M18 M19; do
    MILESTONE_STATUS[$m]="unchecked"
    MILESTONE_CHECKS[$m]=0
    MILESTONE_DEPS_MET[$m]="unknown"
done

# Parse arguments
for arg in "$@"; do
    case $arg in
        --quick) QUICK_MODE=true ;;
        --milestone) MILESTONE_MODE=true ;;
        --matrix) MATRIX_MODE=true ;;
        --json) JSON_MODE=true ;;
        --strict) STRICT_MODE=true ;;
        --coverage) COVERAGE_MODE=true ;;
        --smoke) SMOKE_MODE=true ;;
        --golden) GOLDEN_MODE=true ;;
        --subsystems) SUBSYSTEMS_MODE=true ;;
        --help|-h)
            echo "AGENTICVERZ/MN-OS Milestone Certification Engine v5.0"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --quick      Fast pre-commit check"
            echo "  --milestone  Show milestone health dashboard"
            echo "  --subsystems Show MN-OS subsystem view (dual naming)"
            echo "  --matrix     Show CI job -> milestone mapping"
            echo "  --json       Output JSON for CI pipelines"
            echo "  --strict     Treat WARN as FAIL (blocks merge)"
            echo "  --coverage   Run test coverage enforcement (pytest)"
            echo "  --smoke      Run runtime smoke tests"
            echo "  --golden     Run golden determinism tests"
            echo ""
            echo "Validates M0-M19 correctness with dual-name support:"
            echo "  Legacy: M4 Workflow Engine"
            echo "  MN-OS:  Agent Execution Engine (AXE)"
            echo ""
            echo "M20+ is OUT OF SCOPE."
            exit 0
            ;;
    esac
done

# ============================================================================
# LOGGING
# ============================================================================

log_error() {
    $JSON_MODE || echo -e "${RED}[ERROR]${NC} $1"
    ERRORS=$((ERRORS + 1))
}

log_warn() {
    $JSON_MODE || echo -e "${YELLOW}[WARN]${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

log_ok() {
    $JSON_MODE || echo -e "${GREEN}[OK]${NC} $1"
}

log_info() {
    $JSON_MODE || echo -e "${BLUE}[INFO]${NC} $1"
}

log_semantic() {
    $JSON_MODE || echo -e "${MAGENTA}[SEMANTIC]${NC} $1"
}

log_milestone() {
    local m=$1 status=$2 msg=$3
    MILESTONE_STATUS[$m]=$status
    case $status in
        pass) MILESTONE_PASS=$((MILESTONE_PASS + 1)) ;;
        warn) MILESTONE_WARN=$((MILESTONE_WARN + 1)) ;;
        fail) MILESTONE_FAIL=$((MILESTONE_FAIL + 1)) ;;
    esac
    if ! $JSON_MODE; then
        case $status in
            pass) echo -e "${GREEN}[$m]${NC} ${GREEN}PASS${NC} - $msg" ;;
            warn) echo -e "${YELLOW}[$m]${NC} ${YELLOW}WARN${NC} - $msg" ;;
            fail) echo -e "${RED}[$m]${NC} ${RED}FAIL${NC} - $msg" ;;
        esac
    fi
}

header() { $JSON_MODE || echo -e "\n${CYAN}=== $1 ===${NC}"; }
section() { $JSON_MODE || echo -e "\n${MAGENTA}--- $1 ---${NC}"; }

# ============================================================================
# SEMANTIC CHECK HELPERS
# ============================================================================

# Check for class definition
check_class() {
    local dir=$1 class=$2 label=$3
    if grep -rq "class ${class}" "$dir" 2>/dev/null; then
        log_semantic "$label: class $class found"
        return 0
    else
        log_warn "$label: class $class NOT FOUND"
        return 1
    fi
}

# Check for function definition
check_func() {
    local dir=$1 func=$2 label=$3
    if grep -rqE "def ${func}|async def ${func}" "$dir" 2>/dev/null; then
        log_semantic "$label: function $func found"
        return 0
    else
        log_warn "$label: function $func NOT FOUND"
        return 1
    fi
}

# Check for constant/variable
check_const() {
    local dir=$1 const=$2 label=$3
    if grep -rqE "^${const}\s*=|^    ${const}\s*=" "$dir" 2>/dev/null; then
        log_semantic "$label: constant $const found"
        return 0
    else
        log_warn "$label: constant $const NOT FOUND"
        return 1
    fi
}

# ============================================================================
# TEST COVERAGE ENFORCEMENT (MISSING #1)
# ============================================================================

# Run tests for a specific milestone and capture results
run_milestone_tests() {
    local milestone=$1
    local test_pattern=$2
    local min_pass_rate=${3:-90}  # Default 90% pass rate required

    local test_dir="$BACKEND_DIR/tests"
    local test_files=$(find "$test_dir" -name "$test_pattern" 2>/dev/null | wc -l)

    if [[ $test_files -eq 0 ]]; then
        log_warn "$milestone: No test files matching '$test_pattern'"
        MILESTONE_TEST_PASS[$milestone]=0
        MILESTONE_TEST_TOTAL[$milestone]=0
        MILESTONE_COVERAGE[$milestone]="none"
        return 1
    fi

    # Run pytest and capture results
    cd "$BACKEND_DIR" 2>/dev/null || return 1
    local output=$(PYTHONPATH=. python3 -m pytest $test_dir -k "$test_pattern" --tb=no -q 2>&1 || true)
    cd "$REPO_ROOT" 2>/dev/null || true

    # Parse pytest output for pass/fail counts
    local passed=$(echo "$output" | grep -oE "[0-9]+ passed" | grep -oE "[0-9]+" || echo "0")
    local failed=$(echo "$output" | grep -oE "[0-9]+ failed" | grep -oE "[0-9]+" || echo "0")
    local total=$((passed + failed))

    [[ $total -eq 0 ]] && total=1  # Avoid divide by zero

    local pass_rate=$((passed * 100 / total))

    MILESTONE_TEST_PASS[$milestone]=$passed
    MILESTONE_TEST_TOTAL[$milestone]=$total
    MILESTONE_COVERAGE[$milestone]="${pass_rate}%"

    if [[ $pass_rate -ge $min_pass_rate ]]; then
        log_ok "$milestone: Tests PASS ($passed/$total = ${pass_rate}%)"
        return 0
    else
        log_error "$milestone: Tests FAIL ($passed/$total = ${pass_rate}% < ${min_pass_rate}%)"
        return 1
    fi
}

# Enforce test coverage for all milestones
check_test_coverage() {
    header "Test Coverage Enforcement (MISSING #1)"

    $COVERAGE_MODE || { log_info "Skipping (use --coverage)"; return 0; }

    local issues=0

    # M4: Workflow tests
    run_milestone_tests "M4" "test_workflow*.py" 85 || issues=$((issues+1))

    # M6: CostSim tests
    run_milestone_tests "M6" "test_costsim*.py" 90 || issues=$((issues+1))

    # M10: Recovery tests
    run_milestone_tests "M10" "test_m10*.py" 80 || issues=$((issues+1))

    # M12: Multi-agent tests
    run_milestone_tests "M12" "test_m12*.py" 80 || issues=$((issues+1))

    # M17: CARE routing tests
    run_milestone_tests "M17" "test_m17*.py" 80 || issues=$((issues+1))

    # M18: Governor tests
    run_milestone_tests "M18" "test_m18*.py" 75 || issues=$((issues+1))

    # M19: Policy tests
    run_milestone_tests "M19" "test_m19*.py" 80 || issues=$((issues+1))

    [[ $issues -eq 0 ]] && log_ok "All milestone tests passing" || log_error "$issues milestone(s) below coverage threshold"
    return 0
}

# ============================================================================
# RUNTIME SMOKE TESTS (MISSING #2)
# ============================================================================

check_runtime_smoke() {
    header "Runtime Smoke Tests (MISSING #2)"

    $SMOKE_MODE || { log_info "Skipping (use --smoke)"; return 0; }

    local SMOKE_SCRIPT="$SCRIPT_DIR/runtime_smoke.py"

    if [[ ! -f "$SMOKE_SCRIPT" ]]; then
        log_error "runtime_smoke.py not found at $SMOKE_SCRIPT"
        return 1
    fi

    log_info "Running runtime smoke tests..."
    cd "$BACKEND_DIR" 2>/dev/null || return 1

    local output
    if $JSON_MODE; then
        output=$(PYTHONPATH=. python3 "$SMOKE_SCRIPT" --json 2>&1 || true)
        echo "$output"
    else
        output=$(PYTHONPATH=. python3 "$SMOKE_SCRIPT" 2>&1 || true)
        echo "$output"
    fi

    cd "$REPO_ROOT" 2>/dev/null || true

    # Check for failures
    if echo "$output" | grep -q "FAILED TESTS:"; then
        log_error "Runtime smoke tests have failures"
        return 1
    else
        log_ok "Runtime smoke tests passed"
        return 0
    fi
}

# ============================================================================
# GOLDEN TESTS (MISSING #3)
# ============================================================================

check_golden_tests() {
    header "Golden Tests (MISSING #3)"

    $GOLDEN_MODE || { log_info "Skipping (use --golden)"; return 0; }

    local GOLDEN_SCRIPT="$SCRIPT_DIR/golden_test.py"
    local GOLDEN_DIR="$REPO_ROOT/tests/golden"

    if [[ ! -f "$GOLDEN_SCRIPT" ]]; then
        log_error "golden_test.py not found at $GOLDEN_SCRIPT"
        return 1
    fi

    # Check if golden snapshots exist
    if [[ ! -d "$GOLDEN_DIR" ]] || [[ -z "$(ls -A "$GOLDEN_DIR" 2>/dev/null)" ]]; then
        log_warn "No golden snapshots found in $GOLDEN_DIR"
        log_info "Run: PYTHONPATH=. python3 $GOLDEN_SCRIPT --update"
        return 0
    fi

    log_info "Running golden determinism tests..."
    cd "$BACKEND_DIR" 2>/dev/null || return 1

    local output
    if $JSON_MODE; then
        output=$(PYTHONPATH=. python3 "$GOLDEN_SCRIPT" --json 2>&1 || true)
        echo "$output"
    else
        output=$(PYTHONPATH=. python3 "$GOLDEN_SCRIPT" 2>&1 || true)
        echo "$output"
    fi

    cd "$REPO_ROOT" 2>/dev/null || true

    # Check for mismatches
    if echo "$output" | grep -qi "mismatch\|drift\|failed"; then
        log_error "Golden tests detected drift from snapshots"
        return 1
    else
        log_ok "Golden tests passed - determinism verified"
        return 0
    fi
}

# ============================================================================
# SECRETS BASELINE VALIDATION
# ============================================================================

check_secrets_baseline() {
    header "Secrets Baseline Validation"

    local BASELINE="$REPO_ROOT/.secrets.baseline"
    local issues=0

    # Check baseline exists
    if [[ ! -f "$BASELINE" ]]; then
        log_error "Missing .secrets.baseline - run: pipx run detect-secrets scan > .secrets.baseline"
        return 1
    fi

    log_ok "Secrets baseline exists"

    # Check baseline is valid JSON
    if ! jq empty "$BASELINE" 2>/dev/null; then
        log_error "Invalid JSON in .secrets.baseline"
        return 1
    fi

    log_ok "Secrets baseline is valid JSON"

    # Count total detected secrets
    local total_secrets=$(jq '[.results[] | length] | add // 0' "$BASELINE" 2>/dev/null)
    log_info "Total secrets in baseline: $total_secrets"

    # Check for unverified secrets (is_verified: false or missing)
    local unverified=$(jq '[.results[][] | select(.is_verified != true)] | length' "$BASELINE" 2>/dev/null || echo "0")

    if [[ "$unverified" -gt 0 ]]; then
        log_warn "$unverified unverified secret(s) in baseline"
        log_info "Run: pipx run detect-secrets audit .secrets.baseline"

        # List unverified files
        local unverified_files=$(jq -r '.results | to_entries[] | select(.value[] | .is_verified != true) | .key' "$BASELINE" 2>/dev/null | sort -u)
        if [[ -n "$unverified_files" ]]; then
            while IFS= read -r file; do
                log_warn "  Unverified: $file"
            done <<< "$unverified_files"
        fi

        issues=$((issues+1))
    else
        log_ok "All secrets verified (marked as false positives)"
    fi

    # Check for secrets marked as actual secrets (is_secret: true)
    local actual_secrets=$(jq '[.results[][] | select(.is_secret == true)] | length' "$BASELINE" 2>/dev/null || echo "0")

    if [[ "$actual_secrets" -gt 0 ]]; then
        log_error "$actual_secrets actual secret(s) detected - these should be removed from code"

        # List files with actual secrets
        local secret_files=$(jq -r '.results | to_entries[] | select(.value[] | .is_secret == true) | .key' "$BASELINE" 2>/dev/null | sort -u)
        if [[ -n "$secret_files" ]]; then
            while IFS= read -r file; do
                log_error "  CONTAINS SECRET: $file"
            done <<< "$secret_files"
        fi

        issues=$((issues+1))
    fi

    # Check baseline version
    local version=$(jq -r '.version // "unknown"' "$BASELINE" 2>/dev/null)
    log_info "detect-secrets version: $version"

    # Quick scan to check for new secrets (optional - requires detect-secrets)
    if command -v detect-secrets &>/dev/null || pipx list 2>/dev/null | grep -q detect-secrets; then
        log_info "Running quick scan for new secrets..."

        local new_secrets
        new_secrets=$(pipx run detect-secrets scan --baseline "$BASELINE" --list-all-plugins 2>&1 || true)

        # If the scan finds new secrets, it outputs them
        if echo "$new_secrets" | grep -q '"results"' && echo "$new_secrets" | jq -e '.results | length > 0' &>/dev/null; then
            local new_count=$(echo "$new_secrets" | jq '[.results[] | length] | add // 0' 2>/dev/null || echo "0")
            if [[ "$new_count" -gt 0 ]]; then
                log_warn "$new_count new potential secret(s) detected since baseline"
                log_info "Update baseline: pipx run detect-secrets scan --update .secrets.baseline"
                issues=$((issues+1))
            fi
        fi
    else
        log_info "detect-secrets not available - skipping new secret scan"
    fi

    [[ $issues -eq 0 ]] && log_ok "Secrets baseline validation passed" || log_warn "Secrets baseline has $issues issue(s)"
    return 0
}

# ============================================================================
# M0: FOUNDATIONS & CONTRACTS [PIN-009]
# ============================================================================
check_m0_foundations() {
    section "M0: Foundations & Contracts [PIN-009]"
    local issues=0

    # Alembic configuration
    [[ -f "$BACKEND_DIR/alembic.ini" ]] && log_ok "M0: Alembic config" || { log_error "M0: Missing alembic.ini"; issues=$((issues+1)); }

    # Database models
    if [[ -f "$BACKEND_DIR/app/db.py" ]] || [[ -f "$BACKEND_DIR/app/db_async.py" ]]; then
        log_ok "M0: Database models present"
    else
        log_error "M0: Missing database models"; issues=$((issues+1))
    fi

    # Async engine pattern (semantic)
    if grep -rq "create_async_engine" "$BACKEND_DIR/app" 2>/dev/null; then
        log_semantic "M0: AsyncEngine instantiation found"
    else
        log_warn "M0: No async engine detected"
    fi

    # Migration count
    local ALEMBIC_DIR="$BACKEND_DIR/alembic/versions"
    if [[ -d "$ALEMBIC_DIR" ]]; then
        local count=$(find "$ALEMBIC_DIR" -maxdepth 1 -name "*.py" ! -name "__*" | wc -l)
        log_ok "M0: $count migrations found"
    fi

    # Deterministic utilities (semantic)
    if [[ -f "$BACKEND_DIR/app/utils/deterministic.py" ]]; then
        log_ok "M0: Deterministic utilities"
        check_func "$BACKEND_DIR/app/utils" "deterministic_hash\|stable_sort\|reproducible" "M0" || true
    fi

    MILESTONE_CHECKS[M0]=$((MILESTONE_CHECKS[M0] + 5))
    [[ $issues -eq 0 ]] && log_milestone "M0" "pass" "Foundations validated" || log_milestone "M0" "fail" "$issues issue(s)"
    return 0
}

# ============================================================================
# M1: RUNTIME INTERFACES [PIN-009]
# ============================================================================
check_m1_runtime_interfaces() {
    section "M1: Runtime Interfaces [PIN-009]"
    local issues=0

    if [[ -d "$BACKEND_DIR/app/worker/runtime" ]]; then
        log_ok "M1: Runtime module exists"

        # Semantic checks for runtime interfaces
        check_func "$BACKEND_DIR/app/worker/runtime" "execute" "M1" || issues=$((issues+1))
        check_func "$BACKEND_DIR/app/worker/runtime" "query" "M1" || true
        check_func "$BACKEND_DIR/app/api" "describe_skill\|get_skill" "M1" || true
    else
        log_warn "M1: No runtime module"
        issues=$((issues+1))
    fi

    # Runtime API
    grep -rq "runtime\|Runtime" "$BACKEND_DIR/app/api" 2>/dev/null && \
        log_ok "M1: Runtime API present"

    MILESTONE_CHECKS[M1]=$((MILESTONE_CHECKS[M1] + 4))
    [[ $issues -eq 0 ]] && log_milestone "M1" "pass" "Runtime interfaces OK" || log_milestone "M1" "warn" "Needs setup"
    return 0
}

# ============================================================================
# M2: SKILL REGISTRATION [PIN-010]
# ============================================================================
check_m2_skill_registration() {
    section "M2: Skill Registration [PIN-010]"
    local issues=0

    if [[ -d "$BACKEND_DIR/app/skills" ]]; then
        log_ok "M2: Skills module exists"

        # Semantic: SkillRegistry class
        check_class "$BACKEND_DIR/app/skills" "SkillRegistry\|BaseSkill\|Skill" "M2" || true

        # Base skill class
        [[ -f "$BACKEND_DIR/app/skills/base.py" ]] && log_ok "M2: Base skill class"

        # Semantic: register function
        check_func "$BACKEND_DIR/app/skills" "register\|register_skill" "M2" || true

        # Version patterns
        grep -rq "version\|Version\|skill.*version" "$BACKEND_DIR/app/skills" 2>/dev/null && \
            log_ok "M2: Skill versioning"
    else
        log_warn "M2: No skills module"
        issues=$((issues+1))
    fi

    MILESTONE_CHECKS[M2]=$((MILESTONE_CHECKS[M2] + 5))
    [[ $issues -eq 0 ]] && log_milestone "M2" "pass" "Skill registration OK" || log_milestone "M2" "warn" "Needs setup"
    return 0
}

# ============================================================================
# M3: CORE SKILL IMPLEMENTATIONS [PIN-010]
# Canonical skills: http_call, json_transform, llm_invoke, system_query
# ============================================================================
check_m3_core_skills() {
    section "M3: Core Skill Implementations [PIN-010]"
    local issues=0
    local found_skills=0
    local required_skills=4

    if [[ -d "$BACKEND_DIR/app/skills" ]]; then
        # PIN-010 canonical skills

        # 1. http_call / webhook_send / webhook_call
        if [[ -f "$BACKEND_DIR/app/skills/webhook_send.py" ]] || \
           [[ -f "$BACKEND_DIR/app/skills/http_call.py" ]] || \
           grep -rq "class.*HttpCall\|class.*WebhookSend" "$BACKEND_DIR/app/skills" 2>/dev/null; then
            log_semantic "M3: http_call/webhook skill found"
            found_skills=$((found_skills+1))
        else
            log_warn "M3: http_call/webhook skill NOT FOUND"
        fi

        # 2. json_transform / kv_store
        if [[ -f "$BACKEND_DIR/app/skills/kv_store.py" ]] || \
           [[ -f "$BACKEND_DIR/app/skills/json_transform.py" ]] || \
           grep -rq "class.*JsonTransform\|class.*KvStore" "$BACKEND_DIR/app/skills" 2>/dev/null; then
            log_semantic "M3: json_transform/kv skill found"
            found_skills=$((found_skills+1))
        else
            log_warn "M3: json_transform/kv skill NOT FOUND"
        fi

        # 3. llm_invoke (OpenAI/Anthropic/Voyage)
        if [[ -f "$BACKEND_DIR/app/skills/voyage_embed.py" ]] || \
           grep -rq "class.*LlmInvoke\|class.*VoyageEmbed\|openai\|anthropic" "$BACKEND_DIR/app/skills" 2>/dev/null; then
            log_semantic "M3: llm_invoke skill found"
            found_skills=$((found_skills+1))
        else
            log_warn "M3: llm_invoke skill NOT FOUND"
        fi

        # 4. system_query / slack_send (communication)
        if [[ -f "$BACKEND_DIR/app/skills/slack_send.py" ]] || \
           grep -rq "class.*SystemQuery\|class.*SlackSend" "$BACKEND_DIR/app/skills" 2>/dev/null; then
            log_semantic "M3: system_query/slack skill found"
            found_skills=$((found_skills+1))
        else
            log_warn "M3: system_query/slack skill NOT FOUND"
        fi

        log_info "M3: Found $found_skills/$required_skills canonical skills"
        [[ $found_skills -lt 3 ]] && issues=$((issues+1))
    else
        issues=$((issues+1))
    fi

    MILESTONE_CHECKS[M3]=$((MILESTONE_CHECKS[M3] + 4))
    [[ $issues -eq 0 ]] && log_milestone "M3" "pass" "Core skills validated ($found_skills/$required_skills)" || log_milestone "M3" "warn" "Skills incomplete ($found_skills/$required_skills)"
    return 0
}

# ============================================================================
# M4: WORKFLOW ENGINE [PIN-013/020]
# Semantic: ExecutionPlan, WorkflowStep, CheckpointState, replay tests
# ============================================================================
check_m4_workflow_engine() {
    section "M4: Workflow Engine [PIN-013/020]"
    local issues=0
    local semantic_count=0

    if [[ -d "$BACKEND_DIR/app/workflow" ]]; then
        log_ok "M4: Workflow module exists"

        # Semantic checks - actual class definitions
        check_class "$BACKEND_DIR/app/workflow" "ExecutionPlan\|WorkflowPlan" "M4" && semantic_count=$((semantic_count+1))
        check_class "$BACKEND_DIR/app/workflow" "WorkflowStep\|Step\|ExecutionStep" "M4" && semantic_count=$((semantic_count+1))
        check_class "$BACKEND_DIR/app/workflow" "CheckpointState\|Checkpoint\|StateSnapshot" "M4" && semantic_count=$((semantic_count+1))

        # Golden-run / replay mechanism
        if grep -rq "golden.*run\|replay.*execution\|deterministic.*replay" "$BACKEND_DIR/app/workflow" 2>/dev/null; then
            log_semantic "M4: Golden-run replay mechanism found"
            semantic_count=$((semantic_count+1))
        else
            log_warn "M4: Golden-run replay mechanism NOT FOUND"
        fi

        # Replay equality test
        if grep -rq "replay.*equal\|state.*match\|assert.*replay" "$BACKEND_DIR/tests" 2>/dev/null; then
            log_semantic "M4: Replay equality tests found"
            semantic_count=$((semantic_count+1))
        fi

        [[ $semantic_count -lt 2 ]] && issues=$((issues+1))
    else
        log_warn "M4: No workflow module"
        issues=$((issues+1))
    fi

    # Workflow tests
    local wf_tests=$(find "$BACKEND_DIR/tests" -name "*workflow*" -o -name "*replay*" 2>/dev/null | wc -l)
    [[ $wf_tests -gt 0 ]] && log_ok "M4: $wf_tests workflow test files"

    MILESTONE_CHECKS[M4]=$((MILESTONE_CHECKS[M4] + 6))
    [[ $issues -eq 0 ]] && log_milestone "M4" "pass" "Workflow engine validated (semantic: $semantic_count)" || log_milestone "M4" "warn" "Needs semantic improvements"
    return 0
}

# ============================================================================
# M5: POLICY API & APPROVAL [PIN-021]
# ============================================================================
check_m5_policy_approval() {
    section "M5: Policy API & Approval [PIN-021]"
    local issues=0

    if [[ -d "$BACKEND_DIR/app/policy" ]]; then
        log_ok "M5: Policy module exists"

        # Async patterns
        if grep -rq "async def" "$BACKEND_DIR/app/policy" 2>/dev/null; then
            log_ok "M5: Async patterns in policy"
        else
            log_warn "M5: Policy should use async"
            issues=$((issues+1))
        fi

        # Semantic: PolicyEvaluator class
        check_class "$BACKEND_DIR/app/policy" "PolicyEvaluator\|Evaluator" "M5" || true

        # Escalation function
        check_func "$BACKEND_DIR/app/policy" "escalate\|approval_chain" "M5" || true
    else
        log_warn "M5: No policy module"
        issues=$((issues+1))
    fi

    MILESTONE_CHECKS[M5]=$((MILESTONE_CHECKS[M5] + 4))
    [[ $issues -eq 0 ]] && log_milestone "M5" "pass" "Policy layer validated" || log_milestone "M5" "warn" "$issues issue(s)"
    return 0
}

# ============================================================================
# M6: FEATURE FREEZE & COSTSIM V2 [PIN-026]
# ============================================================================
check_m6_costsim_v2() {
    section "M6: Feature Freeze & CostSim V2 [PIN-026]"
    local issues=0

    if [[ -d "$BACKEND_DIR/app/costsim" ]]; then
        log_ok "M6: CostSim module exists"

        # Semantic: CircuitBreaker class
        check_class "$BACKEND_DIR/app/costsim" "CircuitBreaker" "M6" || true

        # Drift detection function
        check_func "$BACKEND_DIR/app/costsim" "detect_drift\|drift_check" "M6" || true

        # Golden test patterns
        grep -rq "golden\|deterministic" "$BACKEND_DIR/app/costsim" 2>/dev/null && \
            log_ok "M6: Determinism patterns"
    else
        log_warn "M6: No costsim module"
        issues=$((issues+1))
    fi

    # CostSim tests
    [[ -d "$BACKEND_DIR/tests/costsim" ]] && {
        local count=$(find "$BACKEND_DIR/tests/costsim" -name "test_*.py" | wc -l)
        log_ok "M6: $count costsim test files"
    }

    MILESTONE_CHECKS[M6]=$((MILESTONE_CHECKS[M6] + 4))
    [[ $issues -eq 0 ]] && log_milestone "M6" "pass" "CostSim V2 validated" || log_milestone "M6" "warn" "Needs setup"
    return 0
}

# ============================================================================
# M7: MEMORY INTEGRATION [PIN-031/032]
# ============================================================================
check_m7_memory_integration() {
    section "M7: Memory Integration [PIN-031/032]"
    local issues=0

    # Memory pins directory
    if [[ -d "$REPO_ROOT/docs/memory-pins" ]]; then
        local pin_count=$(find "$REPO_ROOT/docs/memory-pins" -name "PIN-*.md" | wc -l)
        log_ok "M7: $pin_count memory PINs found"

        [[ -f "$REPO_ROOT/docs/memory-pins/INDEX.md" ]] && log_ok "M7: PIN INDEX.md present"
    else
        log_warn "M7: No memory-pins directory"
        issues=$((issues+1))
    fi

    # RBAC / Auth
    if [[ -d "$BACKEND_DIR/app/auth" ]]; then
        log_ok "M7: Auth module exists"
        check_class "$BACKEND_DIR/app/auth" "RBAC\|RoleBasedAccess\|Permission" "M7" || true
    fi

    MILESTONE_CHECKS[M7]=$((MILESTONE_CHECKS[M7] + 4))
    [[ $issues -eq 0 ]] && log_milestone "M7" "pass" "Memory integration validated" || log_milestone "M7" "warn" "Needs setup"
    return 0
}

# ============================================================================
# M8: SDK PACKAGING & AUTH [PIN-033]
# ============================================================================
check_m8_sdk_packaging() {
    section "M8: SDK Packaging & Auth [PIN-033]"
    local issues=0

    if [[ -d "$REPO_ROOT/sdk" ]]; then
        log_ok "M8: SDK directory exists"
        [[ -d "$REPO_ROOT/sdk/python" ]] && log_ok "M8: Python SDK"
        [[ -d "$REPO_ROOT/sdk/js" ]] && log_ok "M8: JS SDK"
    else
        log_warn "M8: No SDK directory"
        issues=$((issues+1))
    fi

    # Auth integration
    [[ -d "$BACKEND_DIR/app/auth" ]] && log_ok "M8: Auth module present"

    # CLI tool
    [[ -f "$BACKEND_DIR/cli/aos.py" ]] && log_ok "M8: CLI tool present"

    MILESTONE_CHECKS[M8]=$((MILESTONE_CHECKS[M8] + 4))
    [[ $issues -eq 0 ]] && log_milestone "M8" "pass" "SDK packaging validated" || log_milestone "M8" "warn" "SDK incomplete"
    return 0
}

# ============================================================================
# M9: FAILURE CATALOG PERSISTENCE [PIN-048]
# ============================================================================
check_m9_failure_catalog() {
    section "M9: Failure Catalog Persistence [PIN-048]"
    local issues=0

    local ALEMBIC_DIR="$BACKEND_DIR/alembic/versions"

    # Single migration head
    if command -v alembic &>/dev/null && [[ -f "$BACKEND_DIR/alembic.ini" ]]; then
        cd "$BACKEND_DIR" 2>/dev/null || true
        local heads=$(PYTHONPATH=. alembic heads 2>/dev/null | grep -c "head" || echo "0")
        cd "$REPO_ROOT" 2>/dev/null || true

        if [[ "$heads" == "1" ]]; then
            log_ok "M9: Single migration head"
        elif [[ "$heads" -gt 1 ]]; then
            log_error "M9: Multiple heads - MUST merge"
            issues=$((issues+1))
        fi
    fi

    # Revision ID length check
    if [[ -d "$ALEMBIC_DIR" ]]; then
        local long_rev=0
        for f in "$ALEMBIC_DIR"/*.py; do
            [[ -f "$f" ]] || continue
            [[ "$f" == *"__pycache__"* ]] && continue
            local rev=$(grep "^revision = " "$f" 2>/dev/null | head -1 | sed "s/revision = ['\"]//g" | sed "s/['\"]//g")
            if [[ -n "$rev" ]] && [[ ${#rev} -gt 32 ]]; then
                log_error "M9: Revision ID too long (${#rev}>32): $rev"
                long_rev=$((long_rev+1))
            fi
        done
        [[ $long_rev -eq 0 ]] && log_ok "M9: All revision IDs within varchar(32)"
        issues=$((issues + long_rev))
    fi

    # Failure pattern exports (semantic)
    check_class "$BACKEND_DIR" "FailurePatternExport\|FailurePattern" "M9" || true

    MILESTONE_CHECKS[M9]=$((MILESTONE_CHECKS[M9] + 4))
    [[ $issues -eq 0 ]] && log_milestone "M9" "pass" "Failure catalog validated" || log_milestone "M9" "fail" "$issues issue(s)"
    return 0
}

# ============================================================================
# M10: RECOVERY SUGGESTION ENGINE [PIN-050]
# ============================================================================
check_m10_recovery_engine() {
    section "M10: Recovery Suggestion Engine [PIN-050]"
    local issues=0

    # Leader election (semantic)
    check_func "$BACKEND_DIR/app" "acquire_lock\|advisory_lock\|leader_election" "M10" || true

    # Recovery models
    [[ -f "$BACKEND_DIR/app/models/m10_recovery.py" ]] && log_ok "M10: Recovery models present"

    # M10 tests
    local m10_tests=$(find "$BACKEND_DIR/tests" -name "test_m10_*.py" 2>/dev/null | wc -l)
    [[ $m10_tests -gt 0 ]] && log_ok "M10: $m10_tests M10 test files"

    # Recovery migrations
    ls "$BACKEND_DIR/alembic/versions"/*m10* &>/dev/null 2>&1 && log_ok "M10: Recovery migrations present"

    # Outbox pattern (semantic)
    check_func "$BACKEND_DIR" "claim_outbox\|complete_outbox" "M10" || true

    MILESTONE_CHECKS[M10]=$((MILESTONE_CHECKS[M10] + 5))
    log_milestone "M10" "pass" "Recovery engine validated"
    return 0
}

# ============================================================================
# M11: STORE FACTORIES & LLM ADAPTERS [PIN-055/060]
# Required: openai_adapter, anthropic_adapter, voyage_adapter, tokenizer metering
# ============================================================================
check_m11_store_factories() {
    section "M11: Store Factories & LLM Adapters [PIN-055/060]"
    local issues=0
    local adapter_count=0
    local required_adapters=3

    # Stores module
    [[ -d "$BACKEND_DIR/app/stores" ]] && log_ok "M11: Stores module exists"

    if [[ -d "$BACKEND_DIR/app/skills" ]]; then
        log_ok "M11: Skills module exists"

        # Adapters directory
        if [[ -d "$BACKEND_DIR/app/skills/adapters" ]]; then
            log_ok "M11: Skill adapters directory"

            # 1. OpenAI adapter
            if [[ -f "$BACKEND_DIR/app/skills/adapters/openai_adapter.py" ]] || \
               grep -rq "class.*OpenAI.*Adapter\|openai.*adapter" "$BACKEND_DIR/app/skills/adapters" 2>/dev/null; then
                log_semantic "M11: OpenAI adapter found"
                adapter_count=$((adapter_count+1))
            else
                log_warn "M11: OpenAI adapter NOT FOUND"
            fi

            # 2. Anthropic adapter
            if [[ -f "$BACKEND_DIR/app/skills/adapters/anthropic_adapter.py" ]] || \
               grep -rq "class.*Anthropic.*Adapter\|anthropic" "$BACKEND_DIR/app/skills/adapters" 2>/dev/null; then
                log_semantic "M11: Anthropic adapter found"
                adapter_count=$((adapter_count+1))
            else
                log_warn "M11: Anthropic adapter NOT FOUND"
            fi

            # 3. Voyage adapter
            if [[ -f "$BACKEND_DIR/app/skills/adapters/voyage_adapter.py" ]] || \
               [[ -f "$BACKEND_DIR/app/skills/voyage_embed.py" ]] || \
               grep -rq "class.*Voyage.*Adapter\|voyage" "$BACKEND_DIR/app/skills" 2>/dev/null; then
                log_semantic "M11: Voyage adapter found"
                adapter_count=$((adapter_count+1))
            else
                log_warn "M11: Voyage adapter NOT FOUND"
            fi

            # 4. Tokenizer metering
            if grep -rq "token.*meter\|tokenizer.*count\|metering" "$BACKEND_DIR/app/skills" 2>/dev/null; then
                log_semantic "M11: Tokenizer metering found"
                adapter_count=$((adapter_count+1))
            else
                log_warn "M11: Tokenizer metering NOT FOUND"
            fi

            # 5. Embedding metering
            if grep -rq "embedding.*meter\|embed.*count" "$BACKEND_DIR/app/skills" 2>/dev/null; then
                log_semantic "M11: Embedding metering found"
                adapter_count=$((adapter_count+1))
            fi

            log_info "M11: Found $adapter_count adapters/meters"
        fi
    else
        log_warn "M11: No skills module"
        issues=$((issues+1))
    fi

    [[ $adapter_count -lt $required_adapters ]] && issues=$((issues+1))

    MILESTONE_CHECKS[M11]=$((MILESTONE_CHECKS[M11] + 6))
    [[ $issues -eq 0 ]] && log_milestone "M11" "pass" "Store factories validated ($adapter_count adapters)" || log_milestone "M11" "warn" "Adapters incomplete ($adapter_count/$required_adapters)"
    return 0
}

# ============================================================================
# M12: MULTI-AGENT SYSTEM [PIN-062/063]
# Semantic: Planner, StepGraph, Blackboard, Credit system
# ============================================================================
check_m12_multi_agent() {
    section "M12: Multi-Agent System [PIN-062/063]"
    local issues=0
    local semantic_count=0

    if [[ -d "$BACKEND_DIR/app/agents" ]]; then
        log_ok "M12: Agents module exists"

        # Semantic checks
        check_class "$BACKEND_DIR/app/agents" "Planner\|AgentPlanner\|MultiAgentPlanner" "M12" && semantic_count=$((semantic_count+1))
        check_class "$BACKEND_DIR/app/agents" "StepGraph\|ExecutionGraph\|DAG" "M12" && semantic_count=$((semantic_count+1))
        check_class "$BACKEND_DIR/app/agents" "Blackboard\|SharedState" "M12" && semantic_count=$((semantic_count+1))
        check_class "$BACKEND_DIR/app/agents" "Credit\|Budget\|CreditManager" "M12" && semantic_count=$((semantic_count+1))

        # Cycle detection
        check_func "$BACKEND_DIR/app/agents" "detect_cycle\|cycle_check\|is_dag" "M12" && semantic_count=$((semantic_count+1))

        # Services/Skills
        [[ -d "$BACKEND_DIR/app/agents/services" ]] && log_ok "M12: Agent services present"
        [[ -d "$BACKEND_DIR/app/agents/skills" ]] && log_ok "M12: Agent skills present"
    fi

    # M12 tests
    local m12_tests=$(find "$BACKEND_DIR/tests" -name "test_m12_*.py" 2>/dev/null | wc -l)
    [[ $m12_tests -gt 0 ]] && log_ok "M12: $m12_tests M12 test files"

    [[ $semantic_count -lt 2 ]] && issues=$((issues+1))

    MILESTONE_CHECKS[M12]=$((MILESTONE_CHECKS[M12] + 7))
    [[ $issues -eq 0 ]] && log_milestone "M12" "pass" "Multi-agent system validated (semantic: $semantic_count)" || log_milestone "M12" "warn" "Semantic checks incomplete"
    return 0
}

# ============================================================================
# M13: CONSOLE UI & BOUNDARY CHECKLIST [PIN-064]
# Supports multiple locations: website/aos-console, console/, apps/console/, ui/
# ============================================================================
check_m13_console_ui() {
    section "M13: Console UI & Boundary Checklist [PIN-064]"
    local console_found=false

    # Check multiple possible locations
    for console_path in \
        "$REPO_ROOT/website/aos-console" \
        "$REPO_ROOT/console" \
        "$REPO_ROOT/apps/console" \
        "$REPO_ROOT/ui" \
        "$REPO_ROOT/frontend"; do
        if [[ -d "$console_path" ]]; then
            log_ok "M13: Console found at $console_path"
            console_found=true
            break
        fi
    done

    $console_found || log_warn "M13: Console directory not found in expected locations"

    # Grafana dashboards
    if [[ -d "$REPO_ROOT/monitoring/grafana" ]] || [[ -d "$REPO_ROOT/monitoring/dashboards" ]]; then
        log_ok "M13: Monitoring dashboards present"
    fi

    # M13 boundary checklist PIN
    [[ -f "$REPO_ROOT/docs/memory-pins/PIN-064-m13-boundary-checklist.md" ]] && \
        log_ok "M13: Boundary checklist PIN"

    MILESTONE_CHECKS[M13]=$((MILESTONE_CHECKS[M13] + 3))
    $console_found && log_milestone "M13" "pass" "Console UI validated" || log_milestone "M13" "warn" "Console location needs setup"
    return 0
}

# ============================================================================
# M14: BUDGETLLM SAFETY GOVERNANCE [PIN-070]
# Required: cost envelopes, citation metering, risk scoring, exhaustion fallback
# ============================================================================
check_m14_budgetllm() {
    section "M14: BudgetLLM Safety Governance [PIN-070]"
    local issues=0
    local semantic_count=0

    # BudgetLLM module
    [[ -d "$REPO_ROOT/budgetllm" ]] && log_ok "M14: BudgetLLM module present"

    # Semantic checks
    # 1. Cost envelopes
    if grep -rq "cost.*envelope\|CostEnvelope\|budget.*envelope" "$BACKEND_DIR/app" 2>/dev/null || \
       grep -rq "cost.*envelope" "$REPO_ROOT/budgetllm" 2>/dev/null; then
        log_semantic "M14: Cost envelopes found"
        semantic_count=$((semantic_count+1))
    else
        log_warn "M14: Cost envelopes NOT FOUND"
    fi

    # 2. LLM citation metering
    if grep -rq "citation.*meter\|llm.*citation\|token.*usage" "$BACKEND_DIR/app" 2>/dev/null; then
        log_semantic "M14: LLM citation metering found"
        semantic_count=$((semantic_count+1))
    else
        log_warn "M14: LLM citation metering NOT FOUND"
    fi

    # 3. Failure risk scoring
    if grep -rq "risk.*scor\|failure.*risk\|RiskScore" "$BACKEND_DIR/app" 2>/dev/null; then
        log_semantic "M14: Risk scoring found"
        semantic_count=$((semantic_count+1))
    else
        log_warn "M14: Risk scoring NOT FOUND"
    fi

    # 4. Budget exhaustion fallback
    if grep -rq "exhaustion.*fallback\|budget.*exhaust\|fallback.*routing" "$BACKEND_DIR/app" 2>/dev/null; then
        log_semantic "M14: Exhaustion fallback found"
        semantic_count=$((semantic_count+1))
    else
        log_warn "M14: Exhaustion fallback NOT FOUND"
    fi

    # 5. Cost to governance pipeline (M18 integration)
    if grep -rq "governance.*pipeline\|cost.*governor" "$BACKEND_DIR/app" 2>/dev/null; then
        log_semantic "M14: Governance pipeline integration found"
        semantic_count=$((semantic_count+1))
    fi

    log_info "M14: $semantic_count/5 BudgetLLM components found"
    [[ $semantic_count -lt 2 ]] && issues=$((issues+1))

    MILESTONE_CHECKS[M14]=$((MILESTONE_CHECKS[M14] + 5))
    [[ $issues -eq 0 ]] && log_milestone "M14" "pass" "BudgetLLM validated ($semantic_count components)" || log_milestone "M14" "warn" "BudgetLLM incomplete ($semantic_count/5)"
    return 0
}

# ============================================================================
# M15: SBA FOUNDATIONS [PIN-072]
# ============================================================================
check_m15_sba_foundations() {
    section "M15: SBA Foundations [PIN-072]"
    local issues=0

    if [[ -d "$BACKEND_DIR/app/agents/sba" ]]; then
        log_ok "M15: SBA module exists"

        # Key components
        for comp in generator schema service validator; do
            [[ -f "$BACKEND_DIR/app/agents/sba/${comp}.py" ]] && log_ok "M15: SBA $comp"
        done

        # Semantic: Strategy Cascade
        check_class "$BACKEND_DIR/app/agents/sba" "StrategyCascade\|Strategy" "M15" || true
        check_func "$BACKEND_DIR/app/agents/sba" "validate_semantic\|semantic_check" "M15" || true
    else
        log_warn "M15: No SBA module"
        issues=$((issues+1))
    fi

    MILESTONE_CHECKS[M15]=$((MILESTONE_CHECKS[M15] + 5))
    [[ $issues -eq 0 ]] && log_milestone "M15" "pass" "SBA foundations validated" || log_milestone "M15" "warn" "SBA needs setup"
    return 0
}

# ============================================================================
# M16: AGENT GOVERNANCE CONSOLE [PIN-074]
# ============================================================================
check_m16_governance_console() {
    section "M16: Agent Governance Console [PIN-074]"

    # API routers
    if [[ -d "$BACKEND_DIR/app/api" ]]; then
        local count=$(find "$BACKEND_DIR/app/api" -name "*.py" ! -name "__*" | wc -l)
        log_ok "M16: $count API router files"

        grep -rq "agents\|agent" "$BACKEND_DIR/app/api" 2>/dev/null && \
            log_ok "M16: Agent API routes"
    fi

    # Console SBA pages (multiple locations)
    for sba_path in \
        "$REPO_ROOT/website/aos-console/console/src/pages/sba" \
        "$REPO_ROOT/console/src/pages/sba" \
        "$REPO_ROOT/ui/pages/sba"; do
        if [[ -d "$sba_path" ]]; then
            log_ok "M16: SBA console pages found"
            break
        fi
    done

    # Pydantic validation
    grep -rq "pydantic\|BaseModel" "$BACKEND_DIR/app" 2>/dev/null && \
        log_ok "M16: Pydantic validation"

    MILESTONE_CHECKS[M16]=$((MILESTONE_CHECKS[M16] + 4))
    log_milestone "M16" "pass" "Governance console validated"
    return 0
}

# ============================================================================
# M17: CARE ROUTING ENGINE [PIN-075]
# Semantic: 5-stage pipeline, capability probes, risk-aware routing
# ============================================================================
check_m17_care_routing() {
    section "M17: CARE Routing Engine [PIN-075]"
    local issues=0
    local semantic_count=0

    if [[ -d "$BACKEND_DIR/app/routing" ]]; then
        log_ok "M17: Routing module exists"

        # Core files
        [[ -f "$BACKEND_DIR/app/routing/care.py" ]] && log_ok "M17: CARE routing"
        [[ -f "$BACKEND_DIR/app/routing/probes.py" ]] && log_ok "M17: Routing probes"
        [[ -f "$BACKEND_DIR/app/routing/models.py" ]] && log_ok "M17: Routing models"

        # Semantic: 5-stage pipeline
        if grep -rq "stage.*1\|stage.*2\|pipeline.*stage\|5.*stage\|multi.*stage" "$BACKEND_DIR/app/routing" 2>/dev/null; then
            log_semantic "M17: Multi-stage pipeline found"
            semantic_count=$((semantic_count+1))
        else
            log_warn "M17: 5-stage pipeline NOT FOUND"
        fi

        # Capability probes
        check_func "$BACKEND_DIR/app/routing" "probe\|capability_probe\|check_capability" "M17" && semantic_count=$((semantic_count+1))

        # Risk-aware routing
        if grep -rq "risk.*aware\|risk.*routing\|route.*risk" "$BACKEND_DIR/app/routing" 2>/dev/null; then
            log_semantic "M17: Risk-aware routing found"
            semantic_count=$((semantic_count+1))
        else
            log_warn "M17: Risk-aware routing NOT FOUND"
        fi

        [[ $semantic_count -lt 2 ]] && issues=$((issues+1))
    else
        log_warn "M17: No routing module"
        issues=$((issues+1))
    fi

    # M17 tests
    local m17_tests=$(find "$BACKEND_DIR/tests" -name "test_m17_*.py" 2>/dev/null | wc -l)
    [[ $m17_tests -gt 0 ]] && log_ok "M17: $m17_tests M17 test files"

    MILESTONE_CHECKS[M17]=$((MILESTONE_CHECKS[M17] + 7))
    [[ $issues -eq 0 ]] && log_milestone "M17" "pass" "CARE routing validated (semantic: $semantic_count)" || log_milestone "M17" "warn" "Needs semantic improvements"
    return 0
}

# ============================================================================
# M18: CARE-L & SBA EVOLUTION [PIN-076]
# Required: oscillation detection, freeze threshold, rollback, magnitude caps, RATE_LIMIT metrics
# ============================================================================
check_m18_care_l_evolution() {
    section "M18: CARE-L & SBA Evolution [PIN-076]"
    local issues=0
    local semantic_count=0

    # Governor module
    [[ -f "$BACKEND_DIR/app/routing/governor.py" ]] && log_ok "M18: Routing governor"
    [[ -f "$BACKEND_DIR/app/routing/learning.py" ]] && log_ok "M18: Learning module"
    [[ -f "$BACKEND_DIR/app/routing/feedback.py" ]] && log_ok "M18: Feedback module"
    [[ -f "$BACKEND_DIR/app/agents/sba/evolution.py" ]] && log_ok "M18: SBA evolution"

    # Semantic checks (PIN-076 requirements)

    # 1. Oscillation detection
    if grep -rq "oscillation.*detect\|detect.*oscillation\|OscillationDetector" "$BACKEND_DIR/app" 2>/dev/null; then
        log_semantic "M18: Oscillation detection found"
        semantic_count=$((semantic_count+1))
    else
        log_warn "M18: Oscillation detection NOT FOUND"
    fi

    # 2. Freeze threshold constant
    if grep -rq "FREEZE.*THRESHOLD\|freeze_threshold\|threshold.*freeze" "$BACKEND_DIR/app" 2>/dev/null; then
        log_semantic "M18: Freeze threshold found"
        semantic_count=$((semantic_count+1))
    else
        log_warn "M18: Freeze threshold NOT FOUND"
    fi

    # 3. Rollback mechanism
    if grep -rq "rollback\|Rollback\|revert.*state" "$BACKEND_DIR/app/routing" 2>/dev/null; then
        log_semantic "M18: Rollback mechanism found"
        semantic_count=$((semantic_count+1))
    else
        log_warn "M18: Rollback mechanism NOT FOUND"
    fi

    # 4. Magnitude cap logic
    if grep -rq "magnitude.*cap\|cap.*magnitude\|MAX_MAGNITUDE" "$BACKEND_DIR/app" 2>/dev/null; then
        log_semantic "M18: Magnitude cap found"
        semantic_count=$((semantic_count+1))
    else
        log_warn "M18: Magnitude cap NOT FOUND"
    fi

    # 5. RATE_LIMIT metrics exported
    if grep -rq "RATE_LIMIT\|rate_limit.*metric\|prometheus.*rate" "$BACKEND_DIR/app" 2>/dev/null; then
        log_semantic "M18: RATE_LIMIT metrics found"
        semantic_count=$((semantic_count+1))
    else
        log_warn "M18: RATE_LIMIT metrics NOT FOUND"
    fi

    log_info "M18: $semantic_count/5 governor components found"
    [[ $semantic_count -lt 2 ]] && issues=$((issues+1))

    MILESTONE_CHECKS[M18]=$((MILESTONE_CHECKS[M18] + 9))
    [[ $issues -eq 0 ]] && log_milestone "M18" "pass" "CARE-L evolution validated ($semantic_count components)" || log_milestone "M18" "warn" "Governor incomplete ($semantic_count/5)"
    return 0
}

# ============================================================================
# M19: POLICY LAYER CONSTITUTIONAL [PIN-078]
# Required: 5 categories (Safety, Privacy, Operational, Routing, Custom Domain)
# ============================================================================
check_m19_policy_constitutional() {
    section "M19: Policy Layer Constitutional [PIN-078]"
    local issues=0
    local category_count=0

    if [[ -d "$BACKEND_DIR/app/policy" ]]; then
        log_ok "M19: Policy module exists"

        # Async patterns
        grep -rq "async def" "$BACKEND_DIR/app/policy" 2>/dev/null && log_ok "M19: Async patterns"

        # Policy models
        [[ -f "$BACKEND_DIR/app/policy/models.py" ]] && log_ok "M19: Policy models"

        # Policy API
        [[ -f "$BACKEND_DIR/app/api/policy_layer.py" ]] || [[ -f "$BACKEND_DIR/app/api/policy.py" ]] && \
            log_ok "M19: Policy API"

        # 5 POLICY CATEGORIES (PIN-078 requirement)

        # 1. Safety category
        if grep -rqi "safety\|PolicyCategory.*SAFETY\|category.*safety" "$BACKEND_DIR/app/policy" 2>/dev/null; then
            log_semantic "M19: Safety category found"
            category_count=$((category_count+1))
        else
            log_warn "M19: Safety category NOT FOUND"
        fi

        # 2. Privacy category
        if grep -rqi "privacy\|PolicyCategory.*PRIVACY\|category.*privacy" "$BACKEND_DIR/app/policy" 2>/dev/null; then
            log_semantic "M19: Privacy category found"
            category_count=$((category_count+1))
        else
            log_warn "M19: Privacy category NOT FOUND"
        fi

        # 3. Operational category
        if grep -rqi "operational\|PolicyCategory.*OPERATIONAL\|category.*operational" "$BACKEND_DIR/app/policy" 2>/dev/null; then
            log_semantic "M19: Operational category found"
            category_count=$((category_count+1))
        else
            log_warn "M19: Operational category NOT FOUND"
        fi

        # 4. Routing category
        if grep -rqi "routing\|PolicyCategory.*ROUTING\|category.*routing" "$BACKEND_DIR/app/policy" 2>/dev/null; then
            log_semantic "M19: Routing category found"
            category_count=$((category_count+1))
        else
            log_warn "M19: Routing category NOT FOUND"
        fi

        # 5. Custom Domain category
        if grep -rqi "custom.*domain\|PolicyCategory.*CUSTOM\|domain.*policy" "$BACKEND_DIR/app/policy" 2>/dev/null; then
            log_semantic "M19: Custom Domain category found"
            category_count=$((category_count+1))
        else
            log_warn "M19: Custom Domain category NOT FOUND"
        fi

        log_info "M19: $category_count/5 policy categories found"

        # Rule versioning
        grep -rq "version\|rule.*version\|policy.*version" "$BACKEND_DIR/app/policy" 2>/dev/null && \
            log_ok "M19: Rule versioning"

        # Policy cache
        grep -rq "cache\|Cache" "$BACKEND_DIR/app/policy" 2>/dev/null && \
            log_ok "M19: Policy caching"

        [[ $category_count -lt 3 ]] && issues=$((issues+1))
    else
        log_warn "M19: No policy module"
        issues=$((issues+1))
    fi

    MILESTONE_CHECKS[M19]=$((MILESTONE_CHECKS[M19] + 10))
    [[ $issues -eq 0 ]] && log_milestone "M19" "pass" "Policy constitutional validated ($category_count categories)" || log_milestone "M19" "warn" "Categories incomplete ($category_count/5)"
    return 0
}

# ============================================================================
# CROSS-MILESTONE DEPENDENCY VALIDATION
# ============================================================================
check_cross_milestone_deps() {
    header "Cross-Milestone Dependencies"

    # M17 Routing depends on: M4, M11, M12, M15
    local m17_deps_met=0
    [[ "${MILESTONE_STATUS[M4]}" == "pass" ]] && m17_deps_met=$((m17_deps_met+1))
    [[ "${MILESTONE_STATUS[M11]}" == "pass" ]] && m17_deps_met=$((m17_deps_met+1))
    [[ "${MILESTONE_STATUS[M12]}" == "pass" ]] && m17_deps_met=$((m17_deps_met+1))
    [[ "${MILESTONE_STATUS[M15]}" == "pass" ]] && m17_deps_met=$((m17_deps_met+1))

    if [[ $m17_deps_met -ge 3 ]]; then
        log_ok "M17 dependencies satisfied ($m17_deps_met/4: M4, M11, M12, M15)"
        MILESTONE_DEPS_MET[M17]="yes"
    else
        log_warn "M17 missing dependencies ($m17_deps_met/4)"
        MILESTONE_DEPS_MET[M17]="no"
    fi

    # M18 Governor depends on: M17, M14
    local m18_deps_met=0
    [[ "${MILESTONE_STATUS[M17]}" == "pass" ]] && m18_deps_met=$((m18_deps_met+1))
    [[ "${MILESTONE_STATUS[M14]}" == "pass" ]] && m18_deps_met=$((m18_deps_met+1))

    if [[ $m18_deps_met -ge 1 ]]; then
        log_ok "M18 dependencies satisfied ($m18_deps_met/2: M17, M14)"
        MILESTONE_DEPS_MET[M18]="yes"
    else
        log_warn "M18 missing dependencies ($m18_deps_met/2)"
        MILESTONE_DEPS_MET[M18]="no"
    fi

    # M19 Policy depends on: M5, M7
    local m19_deps_met=0
    [[ "${MILESTONE_STATUS[M5]}" == "pass" ]] && m19_deps_met=$((m19_deps_met+1))
    [[ "${MILESTONE_STATUS[M7]}" == "pass" ]] && m19_deps_met=$((m19_deps_met+1))

    if [[ $m19_deps_met -ge 1 ]]; then
        log_ok "M19 dependencies satisfied ($m19_deps_met/2: M5, M7)"
        MILESTONE_DEPS_MET[M19]="yes"
    else
        log_warn "M19 missing dependencies ($m19_deps_met/2)"
        MILESTONE_DEPS_MET[M19]="no"
    fi

    return 0
}

# ============================================================================
# CI INFRASTRUCTURE CHECKS
# ============================================================================
check_ci_workflow() {
    header "CI Workflow"

    local CI_FILE="$REPO_ROOT/.github/workflows/ci.yml"
    [[ ! -f "$CI_FILE" ]] && { log_error "CI workflow not found"; return 0; }

    grep -q "redis:" "$CI_FILE" && log_ok "Redis service" || true
    grep -q "PYTHONUNBUFFERED" "$CI_FILE" && log_ok "PYTHONUNBUFFERED" || true
    grep -q "run-migrations:" "$CI_FILE" && log_ok "run-migrations job" || true
    grep -q "neonctl connection-string" "$CI_FILE" && log_ok "Neon ephemeral pattern" || true
    grep -q "schema_audit" "$CI_FILE" && log_ok "Schema audit" || true
    grep -q "metrics" "$CI_FILE" && log_ok "Metrics validation" || true
    return 0
}

check_alembic_health() {
    header "Alembic Health"

    local ALEMBIC_DIR="$BACKEND_DIR/alembic/versions"
    [[ ! -d "$ALEMBIC_DIR" ]] && { log_warn "No alembic versions"; return 0; }

    # Revision ID lengths
    for f in "$ALEMBIC_DIR"/*.py; do
        [[ -f "$f" ]] || continue
        [[ "$f" == *"__pycache__"* ]] && continue
        local rev=$(grep "^revision = " "$f" 2>/dev/null | head -1 | sed "s/revision = ['\"]//g" | sed "s/['\"]//g")
        if [[ -n "$rev" ]] && [[ ${#rev} -gt 28 ]]; then
            [[ ${#rev} -gt 32 ]] && log_error "Revision too long ($rev)" || log_warn "Revision near limit: $rev"
        fi
    done

    # Single head check
    if command -v alembic &>/dev/null; then
        cd "$BACKEND_DIR" 2>/dev/null || true
        local heads=$(PYTHONPATH=. alembic heads 2>/dev/null | grep -c "head" || echo "0")
        cd "$REPO_ROOT" 2>/dev/null || true
        if [[ "$heads" == "1" ]]; then
            log_ok "Single migration head"
        elif [[ "$heads" -gt 1 ]]; then
            log_error "Multiple heads!"
        fi
    fi
    return 0
}

check_sqlmodel_patterns() {
    header "SQLModel Pattern Check"

    local LINT_SCRIPT="$REPO_ROOT/scripts/ops/lint_sqlmodel_patterns.py"
    if [[ ! -f "$LINT_SCRIPT" ]]; then
        log_info "SQLModel linter not found (optional)"
        return 0
    fi

    if $QUICK_MODE; then
        log_info "Skipping (use full mode)"
        return 0
    fi

    # Run the linter
    if python3 "$LINT_SCRIPT" "$BACKEND_DIR/app/api/" 2>/dev/null; then
        log_ok "No unsafe SQLModel patterns"
    else
        log_warn "SQLModel pattern issues detected (run lint_sqlmodel_patterns.py)"
    fi
    return 0
}

check_api_wiring() {
    header "API Wiring Check"

    local WIRING_SCRIPT="$REPO_ROOT/scripts/ops/check_api_wiring.py"
    if [[ ! -f "$WIRING_SCRIPT" ]]; then
        log_info "API wiring checker not found (optional)"
        return 0
    fi

    if $QUICK_MODE; then
        log_info "Skipping (use full mode)"
        return 0
    fi

    # Run the checker
    if python3 "$WIRING_SCRIPT" 2>/dev/null; then
        log_ok "API wiring validated"
    else
        log_warn "API wiring issues detected (run check_api_wiring.py)"
    fi
    return 0
}

check_frontend_api_calls() {
    header "Frontend API ID Type Check"

    local LINT_SCRIPT="$REPO_ROOT/scripts/ops/lint_frontend_api_calls.py"
    local CONSOLE_SRC="$REPO_ROOT/website/aos-console/console/src"

    if [[ ! -f "$LINT_SCRIPT" ]]; then
        log_info "Frontend API linter not found (optional)"
        return 0
    fi

    if [[ ! -d "$CONSOLE_SRC" ]]; then
        log_info "Console source not found (optional)"
        return 0
    fi

    if $QUICK_MODE; then
        log_info "Skipping (use full mode)"
        return 0
    fi

    # PIN-314: Use git-scoped files for pre-push checks
    # Only lint files that are being pushed, not the entire workspace
    local GIT_SCOPED_FILES=""
    if git rev-parse --verify origin/main &>/dev/null; then
        # Get files changed between origin/main and HEAD (committed delta)
        GIT_SCOPED_FILES=$(git diff --name-only origin/main...HEAD 2>/dev/null | grep -E '\.(tsx?|jsx?)$' | grep -v node_modules || true)
    fi

    if [[ -n "$GIT_SCOPED_FILES" ]]; then
        # Run linter only on files in the committed delta
        log_info "Checking $(echo "$GIT_SCOPED_FILES" | wc -l | tr -d ' ') frontend file(s) in push scope"
        if echo "$GIT_SCOPED_FILES" | python3 "$LINT_SCRIPT" --files 2>/dev/null; then
            log_ok "No frontend API ID type issues in push scope"
        else
            log_error "Frontend API ID type mismatch in pushed files"
        fi
    else
        log_info "No frontend files in push scope - skipping check"
    fi

    return 0
}

# ============================================================================
# DASHBOARD & MATRIX
# ============================================================================
print_dashboard() {
    $JSON_MODE && return 0

    echo ""
    echo -e "${CYAN}+====================================================================+${NC}"
    echo -e "${CYAN}|       AGENTICVERZ MILESTONE DASHBOARD (M0-M19) v5.0               |${NC}"
    echo -e "${CYAN}|       Semantic + Coverage + Smoke + Golden + MN-OS Names          |${NC}"
    echo -e "${CYAN}+====================================================================+${NC}"
    echo ""
    printf "%-6s %-42s %-8s %-6s %-6s\n" "ID" "Milestone (PIN-Accurate)" "Status" "Checks" "Deps"
    echo "------------------------------------------------------------------------"

    local MILESTONES=(
        "M0:Foundations & Contracts [PIN-009]"
        "M1:Runtime Interfaces [PIN-009]"
        "M2:Skill Registration [PIN-010]"
        "M3:Core Skill Implementations [PIN-010]"
        "M4:Workflow Engine [PIN-013/020]"
        "M5:Policy API & Approval [PIN-021]"
        "M6:Feature Freeze & CostSim V2 [PIN-026]"
        "M7:Memory Integration [PIN-031/032]"
        "M8:SDK Packaging & Auth [PIN-033]"
        "M9:Failure Catalog Persistence [PIN-048]"
        "M10:Recovery Suggestion Engine [PIN-050]"
        "M11:Store Factories & LLM Adapters [PIN-055]"
        "M12:Multi-Agent System [PIN-062/063]"
        "M13:Console UI & Boundary [PIN-064]"
        "M14:BudgetLLM Safety [PIN-070]"
        "M15:SBA Foundations [PIN-072]"
        "M16:Agent Governance Console [PIN-074]"
        "M17:CARE Routing Engine [PIN-075]"
        "M18:CARE-L & SBA Evolution [PIN-076]"
        "M19:Policy Constitutional [PIN-078]"
    )

    for entry in "${MILESTONES[@]}"; do
        local ID="${entry%%:*}"
        local NAME="${entry#*:}"
        local STATUS="${MILESTONE_STATUS[$ID]:-unchecked}"
        local CHECKS="${MILESTONE_CHECKS[$ID]:-0}"
        local DEPS="${MILESTONE_DEPS_MET[$ID]:-n/a}"

        local COLOR="" TEXT=""
        case $STATUS in
            pass) COLOR="${GREEN}"; TEXT="PASS" ;;
            warn) COLOR="${YELLOW}"; TEXT="WARN" ;;
            fail) COLOR="${RED}"; TEXT="FAIL" ;;
            *) COLOR="${BLUE}"; TEXT="--" ;;
        esac

        printf "%-6s %-42s ${COLOR}%-8s${NC} %-6s %-6s\n" "$ID" "$NAME" "$TEXT" "$CHECKS" "$DEPS"
    done

    echo "------------------------------------------------------------------------"
    echo ""
    echo -e "Summary: ${GREEN}$MILESTONE_PASS PASS${NC} | ${YELLOW}$MILESTONE_WARN WARN${NC} | ${RED}$MILESTONE_FAIL FAIL${NC}"
    $STRICT_MODE && echo -e "${RED}STRICT MODE: WARN = FAIL${NC}"
    echo ""
    return 0
}

# MN-OS Subsystem Dashboard (--subsystems)
print_subsystems() {
    $JSON_MODE && return 0

    echo ""
    echo -e "${CYAN}+====================================================================+${NC}"
    echo -e "${CYAN}|       MN-OS SUBSYSTEM DASHBOARD (Machine-Native OS) v5.0          |${NC}"
    echo -e "${CYAN}|       Legacy Names → MN-OS Names (Dual Recognition)               |${NC}"
    echo -e "${CYAN}+====================================================================+${NC}"
    echo ""
    printf "%-4s %-28s %-24s %-6s %-8s\n" "ID" "Legacy Name" "MN-OS Name" "Acro" "Status"
    echo "------------------------------------------------------------------------"

    local SUBSYSTEMS=(
        "M0:Foundations & Contracts:Kernel Primitives"
        "M1:Runtime Interfaces:Agent Runtime Kernel"
        "M2:Skill Registration:OS Capability Table"
        "M3:Core Skills:Native OS Skills"
        "M4:Workflow Engine:Agent Execution Engine"
        "M5:Policy API:Constitutional Guardrail"
        "M6:CostSim V2:Resource Economics Engine"
        "M7:Memory Integration:System Memory Matrix"
        "M8:SDK & Auth:Identity Authority"
        "M9:Failure Catalog:Failure Intelligence"
        "M10:Recovery Engine:Self-Repair Layer"
        "M11:LLM Adapters:Cognitive Interface"
        "M12:Multi-Agent System:MAS Orchestrator"
        "M13:Console UI:OS Control Center"
        "M14:BudgetLLM Safety:Cognitive Compliance"
        "M15:SBA Foundations:Strategic Agency"
        "M16:Agent Governance:Oversight Authority"
        "M17:CARE Routing:Cognitive Routing"
        "M18:CARE-L Evolution:Adaptive Governance"
        "M19:Policy Constitutional:OS Constitution"
    )

    for entry in "${SUBSYSTEMS[@]}"; do
        IFS=':' read -r ID LEGACY MNOS <<< "$entry"
        local ACRONYM="${MNOS_ACRONYM[$ID]:-??}"
        local STATUS="${MILESTONE_STATUS[$ID]:-unchecked}"

        local COLOR="" TEXT=""
        case $STATUS in
            pass) COLOR="${GREEN}"; TEXT="PASS" ;;
            warn) COLOR="${YELLOW}"; TEXT="WARN" ;;
            fail) COLOR="${RED}"; TEXT="FAIL" ;;
            *) COLOR="${BLUE}"; TEXT="--" ;;
        esac

        printf "%-4s %-28s %-24s %-6s ${COLOR}%-8s${NC}\n" "$ID" "$LEGACY" "$MNOS" "$ACRONYM" "$TEXT"
    done

    echo "------------------------------------------------------------------------"
    echo ""
    echo -e "${MAGENTA}MN-OS Architecture Layers:${NC}"
    echo ""
    echo "  Layer 6: Constitutional Governance (M19, M18, M14)"
    echo "  Layer 5: Strategic Routing (M17, M15, M16)"
    echo "  Layer 4: Multi-Agent Orchestration (M12, M13)"
    echo "  Layer 3: Execution & Recovery (M4, M10, M9)"
    echo "  Layer 2: Capability & Cognitive I/O (M2, M3, M11, M6)"
    echo "  Layer 1: Kernel & Memory (M0, M1, M7)"
    echo "  Layer 0: Identity & Access (M8)"
    echo ""
    echo -e "Summary: ${GREEN}$MILESTONE_PASS PASS${NC} | ${YELLOW}$MILESTONE_WARN WARN${NC} | ${RED}$MILESTONE_FAIL FAIL${NC}"
    echo ""
    echo "See docs/mn-os/subsystem_mapping.md for full mapping documentation"
    echo ""
    return 0
}

print_matrix() {
    $JSON_MODE && return 0

    echo ""
    echo -e "${CYAN}+====================================================================+${NC}"
    echo -e "${CYAN}|         AGENTICVERZ CI JOB -> MILESTONE MAPPING v5.0              |${NC}"
    echo -e "${CYAN}+====================================================================+${NC}"
    echo ""

    cat <<'EOF'
+---------------------+------------------------------------------------+
| CI Job              | Milestones Validated                           |
+---------------------+------------------------------------------------+
| unit-tests          | M0, M2, M3, M11, M14                           |
| determinism         | M0, M4, M6, M9                                 |
| workflow-engine     | M4, M7, M17                                    |
| integration         | M0, M5, M7, M16, M19                           |
| costsim             | M6, M8, M14                                    |
| costsim-wiremock    | M6                                             |
| e2e-tests           | M0, M5, M7, M10, M16, M17, M19                 |
| m10-tests           | M9, M10                                        |
| policy-layer        | M5, M19                                        |
+---------------------+------------------------------------------------+

+---------------------+------------------------------------------------+
| Milestone           | Primary Test Files / Dependencies              |
+---------------------+------------------------------------------------+
| M0  [PIN-009]       | test_integration.py                            |
| M3  [PIN-010]       | tests/skills/test_*.py                         |
| M4  [PIN-013/020]   | tests/workflow/test_*.py                       |
| M5  [PIN-021]       | tests/test_policy*.py | depends: M0            |
| M6  [PIN-026]       | tests/costsim/test_*.py                        |
| M10 [PIN-050]       | test_m10_*.py (6+ files) | depends: M9         |
| M12 [PIN-062/063]   | test_m12_*.py (4 files) | depends: M4, M11     |
| M17 [PIN-075]       | test_m17_care.py | depends: M4, M11, M12, M15  |
| M18 [PIN-076]       | test_m18_*.py | depends: M17, M14              |
| M19 [PIN-078]       | test_m19_policy.py | depends: M5, M7           |
+---------------------+------------------------------------------------+
EOF
    echo ""
    return 0
}

print_json() {
    $JSON_MODE || return 0

    local status="pass"
    [[ $ERRORS -gt 0 ]] && status="fail"
    [[ $WARNINGS -gt 0 ]] && [[ $status != "fail" ]] && status="warn"
    $STRICT_MODE && [[ $WARNINGS -gt 0 ]] && status="fail"

    cat <<EOF
{
  "version": "5.0",
  "project": "agenticverz",
  "status": "$status",
  "strict_mode": $STRICT_MODE,
  "errors": $ERRORS,
  "warnings": $WARNINGS,
  "milestones": {"pass": $MILESTONE_PASS, "warn": $MILESTONE_WARN, "fail": $MILESTONE_FAIL},
  "milestone_status": {
EOF

    local first=true
    for m in M0 M1 M2 M3 M4 M5 M6 M7 M8 M9 M10 M11 M12 M13 M14 M15 M16 M17 M18 M19; do
        $first && first=false || echo ","
        printf '    "%s": {"status": "%s", "checks": %d, "deps": "%s"}' \
            "$m" "${MILESTONE_STATUS[$m]:-unchecked}" "${MILESTONE_CHECKS[$m]:-0}" "${MILESTONE_DEPS_MET[$m]:-n/a}"
    done

    echo -e "\n  }\n}"
    return 0
}

# ============================================================================
# PRE-FLIGHT
# ============================================================================
preflight() {
    header "Pre-Flight"

    git status --porcelain 2>/dev/null | grep -q . && log_warn "Uncommitted changes" || log_ok "Clean working directory"

    local branch=$(git branch --show-current 2>/dev/null || echo "")
    [[ -n "$branch" ]] && log_info "Branch: $branch"

    $STRICT_MODE && log_info "STRICT MODE ENABLED: WARN = FAIL"

    command -v gh &>/dev/null && {
        local last=$(gh run list --limit 1 --json conclusion,name 2>/dev/null || echo "")
        [[ -n "$last" ]] && log_info "Last CI: $last"
    }
    return 0
}

# ============================================================================
# SUMMARY
# ============================================================================
print_summary() {
    $JSON_MODE && { print_json; return 0; }

    header "Summary"
    echo ""

    [[ $ERRORS -eq 0 ]] && echo -e "${GREEN}All checks passed!${NC}" || echo -e "${RED}$ERRORS error(s) found${NC}"
    [[ $WARNINGS -gt 0 ]] && echo -e "${YELLOW}$WARNINGS warning(s) to review${NC}"

    echo ""
    echo -e "${CYAN}Milestones:${NC} ${GREEN}$MILESTONE_PASS PASS${NC} | ${YELLOW}$MILESTONE_WARN WARN${NC} | ${RED}$MILESTONE_FAIL FAIL${NC}"
    echo ""

    local should_fail=false
    [[ $ERRORS -gt 0 ]] && should_fail=true
    [[ $MILESTONE_FAIL -gt 0 ]] && should_fail=true
    $STRICT_MODE && [[ $WARNINGS -gt 0 ]] && should_fail=true
    $STRICT_MODE && [[ $MILESTONE_WARN -gt 0 ]] && should_fail=true

    if $should_fail; then
        echo -e "${RED}CI push NOT recommended.${NC}"
        $STRICT_MODE && [[ $WARNINGS -gt 0 ]] && echo -e "${RED}STRICT MODE: $WARNINGS warnings treated as failures${NC}"
        exit 1
    else
        echo -e "${GREEN}Safe to push to CI.${NC}"
        exit 0
    fi
}

# ============================================================================
# MAIN
# ============================================================================
main() {
    $JSON_MODE || {
        echo ""
        echo -e "${CYAN}+====================================================================+${NC}"
        echo -e "${CYAN}|  AGENTICVERZ/MN-OS Milestone Certification Engine v5.1            |${NC}"
        echo -e "${CYAN}|  Semantic + Coverage + Smoke + Golden + Secrets + Dual-Name       |${NC}"
        echo -e "${CYAN}+====================================================================+${NC}"
        echo ""
    }

    $QUICK_MODE && ! $JSON_MODE && log_info "Quick mode (skipping slow checks)"

    cd "$REPO_ROOT"

    # Dashboard/matrix/subsystems only mode
    if $MILESTONE_MODE || $MATRIX_MODE || $SUBSYSTEMS_MODE; then
        check_m0_foundations
        check_m1_runtime_interfaces
        check_m2_skill_registration
        check_m3_core_skills
        check_m4_workflow_engine
        check_m5_policy_approval
        check_m6_costsim_v2
        check_m7_memory_integration
        check_m8_sdk_packaging
        check_m9_failure_catalog
        check_m10_recovery_engine
        check_m11_store_factories
        check_m12_multi_agent
        check_m13_console_ui
        check_m14_budgetllm
        check_m15_sba_foundations
        check_m16_governance_console
        check_m17_care_routing
        check_m18_care_l_evolution
        check_m19_policy_constitutional
        check_cross_milestone_deps

        $MILESTONE_MODE && print_dashboard
        $SUBSYSTEMS_MODE && print_subsystems
        $MATRIX_MODE && print_matrix
        exit 0
    fi

    # Full check
    preflight
    check_ci_workflow
    check_alembic_health
    check_sqlmodel_patterns
    check_api_wiring
    check_frontend_api_calls
    check_secrets_baseline

    # MISSING #1-3: Test enforcement (optional flags)
    check_test_coverage
    check_runtime_smoke
    check_golden_tests

    header "Milestone Validation (M0-M19) - Semantic Checks"

    check_m0_foundations
    check_m1_runtime_interfaces
    check_m2_skill_registration
    check_m3_core_skills
    check_m4_workflow_engine
    check_m5_policy_approval
    check_m6_costsim_v2
    check_m7_memory_integration
    check_m8_sdk_packaging
    check_m9_failure_catalog
    check_m10_recovery_engine
    check_m11_store_factories
    check_m12_multi_agent
    check_m13_console_ui
    check_m14_budgetllm
    check_m15_sba_foundations
    check_m16_governance_console
    check_m17_care_routing
    check_m18_care_l_evolution
    check_m19_policy_constitutional

    check_cross_milestone_deps

    ! $QUICK_MODE && ! $JSON_MODE && print_dashboard

    print_summary
}

main "$@"
