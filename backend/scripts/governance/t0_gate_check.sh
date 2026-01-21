#!/usr/bin/env bash
# Layer: L8 — Ops/Catalyst
# Product: system-wide
# Reference: GAP_IMPLEMENTATION_PLAN_V1.md IMPL-GATE-001
#
# T0 Gate Check Script
# Verifies all T0 (critical) governance gaps are properly implemented
# before allowing T1/T2 work to proceed.
#
# Usage: ./scripts/governance/t0_gate_check.sh [--verbose] [--fix]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
VERBOSE=false
FIX_MODE=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --fix)
            FIX_MODE=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_verbose() {
    if [ "$VERBOSE" = true ]; then
        echo -e "       $1"
    fi
}

# T0 GAP implementations to verify
declare -A T0_MODULES=(
    # GAP-068: Policy Conflict Resolution
    ["GAP-068"]="app/policy/conflict_resolver.py"
    # GAP-031: Binding Moment Enforcement
    ["GAP-031"]="app/policy/binding_moment_enforcer.py"
    # GAP-035: Failure Mode Handling
    ["GAP-035"]="app/policy/failure_mode_handler.py"
    # GAP-069: Runtime Kill Switch
    ["GAP-069"]="app/policy/kill_switch.py"
    # GAP-070: Degraded Mode
    ["GAP-070"]="app/policy/degraded_mode.py"
    # GAP-016: Step Enforcement
    ["GAP-016"]="app/worker/enforcement/step_enforcement.py"
    # GAP-030: Enforcement Guard
    ["GAP-030"]="app/worker/enforcement/enforcement_guard.py"
    # GAP-046: EventReactor Initialization
    ["GAP-046"]="app/events/reactor_initializer.py"
    # GAP-067: SPINE Validation
    ["GAP-067"]="app/startup/boot_guard.py"
    # GAP-065: Retrieval Mediator
    ["GAP-065"]="app/services/mediation/retrieval_mediator.py"
    # GAP-066: Skill Registry Filter
    ["GAP-066"]="app/skills/skill_registry_filter.py"
    # GAP-059: HTTP Connector
    ["GAP-059"]="app/services/connectors/http_connector.py"
    # GAP-060: SQL Gateway
    ["GAP-060"]="app/services/connectors/sql_gateway.py"
    # GAP-063: MCP Connector
    ["GAP-063"]="app/services/connectors/mcp_connector.py"
)

# Required exports from each module
declare -A T0_EXPORTS=(
    ["GAP-068"]="resolve_policy_conflict,PolicyAction"
    ["GAP-031"]="should_evaluate_policy,EvaluationPoint"
    ["GAP-035"]="handle_evaluation_error,FailureMode"
    ["GAP-069"]="activate_kill_switch,is_kill_switch_active"
    ["GAP-070"]="enter_degraded_mode,is_degraded_mode_active"
    ["GAP-016"]="enforce_before_step_completion,EnforcementResult"
    ["GAP-030"]="enforcement_guard,EnforcementSkippedError"
    ["GAP-046"]="initialize_event_reactor,get_reactor_status"
    ["GAP-067"]="validate_spine_components,SpineValidationError"
    ["GAP-065"]="RetrievalMediator,MediatedResult"
    ["GAP-066"]="filter_skills_for_governance,UNGOVERNED_SKILLS"
    ["GAP-059"]="HttpConnectorService,HttpConnectorConfig"
    ["GAP-060"]="SqlGatewayService,QueryTemplate"
    ["GAP-063"]="McpConnectorService,McpToolDefinition"
)

echo "=========================================="
echo "T0 Governance Gate Check"
echo "Reference: GAP_IMPLEMENTATION_PLAN_V1.md"
echo "IMPL-GATE-001: No T1/T2 until T0 passes"
echo "=========================================="
echo ""

cd "$BACKEND_DIR"

# Track results
PASSED=0
FAILED=0
WARNINGS=0

# Check 1: All T0 modules exist
echo "Check 1: Module Existence"
echo "--------------------------"

for gap in "${!T0_MODULES[@]}"; do
    module="${T0_MODULES[$gap]}"
    if [ -f "$module" ]; then
        log_info "$gap: $module EXISTS"
        ((PASSED++))
    else
        log_error "$gap: $module MISSING"
        ((FAILED++))
    fi
done

echo ""

# Check 2: All T0 modules are importable
echo "Check 2: Module Importability"
echo "-----------------------------"

for gap in "${!T0_MODULES[@]}"; do
    module="${T0_MODULES[$gap]}"
    if [ ! -f "$module" ]; then
        continue
    fi

    # Convert file path to module path
    module_path="${module%.py}"
    module_path="${module_path//\//.}"

    # Try to import the module
    if python3 -c "import $module_path" 2>/dev/null; then
        log_info "$gap: IMPORTABLE"
        log_verbose "    Module: $module_path"
        ((PASSED++))
    else
        log_error "$gap: IMPORT FAILED"
        log_verbose "    Module: $module_path"
        ((FAILED++))
    fi
done

echo ""

# Check 3: Required exports present
echo "Check 3: Required Exports"
echo "-------------------------"

for gap in "${!T0_EXPORTS[@]}"; do
    module="${T0_MODULES[$gap]}"
    exports="${T0_EXPORTS[$gap]}"

    if [ ! -f "$module" ]; then
        continue
    fi

    # Convert file path to module path
    module_path="${module%.py}"
    module_path="${module_path//\//.}"

    # Check each export
    IFS=',' read -ra export_list <<< "$exports"
    all_present=true

    for export_name in "${export_list[@]}"; do
        if python3 -c "from $module_path import $export_name" 2>/dev/null; then
            log_verbose "    $export_name: present"
        else
            log_error "$gap: Missing export '$export_name'"
            all_present=false
        fi
    done

    if [ "$all_present" = true ]; then
        log_info "$gap: All exports present"
        ((PASSED++))
    else
        ((FAILED++))
    fi
done

echo ""

# Check 4: Unit tests exist
echo "Check 4: Unit Tests Exist"
echo "-------------------------"

TEST_DIR="tests/governance/t0"
if [ -d "$TEST_DIR" ]; then
    test_count=$(find "$TEST_DIR" -name "test_*.py" | wc -l)
    if [ "$test_count" -ge 10 ]; then
        log_info "Found $test_count test files in $TEST_DIR"
        ((PASSED++))
    else
        log_warn "Only $test_count test files (expected >= 10)"
        ((WARNINGS++))
    fi
else
    log_error "Test directory $TEST_DIR not found"
    ((FAILED++))
fi

echo ""

# Check 5: Wiring integrations
echo "Check 5: Wiring Integrations"
echo "----------------------------"

# Check main.py has EventReactor init
if grep -q "initialize_event_reactor" app/main.py 2>/dev/null; then
    log_info "main.py: EventReactor initialization found"
    ((PASSED++))
else
    log_error "main.py: Missing EventReactor initialization"
    ((FAILED++))
fi

# Check main.py has SPINE validation
if grep -q "validate_spine_components" app/main.py 2>/dev/null; then
    log_info "main.py: SPINE validation found"
    ((PASSED++))
else
    log_error "main.py: Missing SPINE validation"
    ((FAILED++))
fi

# Check prevention_engine.py has conflict resolution
if grep -q "resolve_policy_conflict" app/policy/prevention_engine.py 2>/dev/null; then
    log_info "prevention_engine.py: Conflict resolution wired"
    ((PASSED++))
else
    log_error "prevention_engine.py: Missing conflict resolution"
    ((FAILED++))
fi

# Check runner.py has enforcement guard
if grep -q "enforcement_guard" app/worker/runner.py 2>/dev/null; then
    log_info "runner.py: Enforcement guard wired"
    ((PASSED++))
else
    log_error "runner.py: Missing enforcement guard"
    ((FAILED++))
fi

# Check skills/__init__.py has governance filter
if grep -q "apply_governance_filter" app/skills/__init__.py 2>/dev/null; then
    log_info "skills/__init__.py: Governance filter wired"
    ((PASSED++))
else
    log_error "skills/__init__.py: Missing governance filter"
    ((FAILED++))
fi

echo ""

# Summary
echo "=========================================="
echo "T0 GATE CHECK SUMMARY"
echo "=========================================="
echo ""
echo -e "Passed:   ${GREEN}$PASSED${NC}"
echo -e "Failed:   ${RED}$FAILED${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
echo ""

if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}=========================================="
    echo "T0 GATE: PASSED"
    echo ""
    echo "All T0 governance gaps are implemented."
    echo "T1/T2 work may proceed."
    echo -e "==========================================${NC}"
    exit 0
else
    echo -e "${RED}=========================================="
    echo "T0 GATE: FAILED"
    echo ""
    echo "T0 gaps incomplete. Fix before proceeding."
    echo "Reference: IMPL-GATE-001"
    echo -e "==========================================${NC}"
    exit 1
fi
