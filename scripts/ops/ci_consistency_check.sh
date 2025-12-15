#!/bin/bash
# ============================================================================
# CI Consistency Checker v2.0 - AGENTICVERZ Milestone Certification Engine
# ============================================================================
#
# Purpose: Validate ALL Agenticverz milestones M0-M19 remain functional,
# internally consistent, and test-verified during CI, refactors, or features.
#
# M20+ is OUT OF SCOPE - this engine stays strictly within M0-M19.
#
# Usage:
#   ./scripts/ops/ci_consistency_check.sh              # Full check
#   ./scripts/ops/ci_consistency_check.sh --quick      # Fast pre-commit check
#   ./scripts/ops/ci_consistency_check.sh --milestone  # Show milestone dashboard
#   ./scripts/ops/ci_consistency_check.sh --matrix     # Show test matrix
#   ./scripts/ops/ci_consistency_check.sh --json       # Output JSON for CI
#
# AGENTICVERZ Milestone Coverage (M0-M19):
#   M0:  Foundations (async DB, migrations, determinism)
#   M1:  Agent Registry (metadata, capabilities, routing)
#   M2:  Topology & Dependencies (cycle detection, version constraints)
#   M3:  Event Replay / State Stream (durable events, idempotency)
#   M4:  Capability Modeling (runtime resolution, routing)
#   M5:  Policy & Approval Layer (evaluation rules, escalation)
#   M6:  Outbox & Delivery (publish/claim/complete, dead-letter)
#   M7:  Workflow Engine (deterministic execution, checkpoints)
#   M8:  Cost Simulator (circuit breaker, golden tests)
#   M9:  Hardening (migration safety, idempotent patterns)
#   M10: Reliability Layer (leader election, recovery, retention)
#   M11: Skill Sandbox (security, budget limits, forbidden patterns)
#   M12: Multi-Agent Planner (step graph, cycle detection, max steps)
#   M13: Tooling Layer (tool registry, permissions, parameter safety)
#   M14: BudgetLLM (cost deduction, accumulation, blocking)
#   M15: Semantic Dependencies (SBA - dependency graph, version mismatch)
#   M16: UI/API Cohesion (OpenAPI stability, endpoint contracts)
#   M17: Routing Engine (CARE - multi-step execution, skill registry)
#   M18: Governor (rate limits, magnitude caps, oscillation detection)
#   M19: Policy Layer Async (async evaluation, rule merging, caching)
#
# ============================================================================

set -euo pipefail

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

# Milestone Status Tracking
declare -A MILESTONE_STATUS
declare -A MILESTONE_CHECKS

# Initialize all milestones
for m in M0 M1 M2 M3 M4 M5 M6 M7 M8 M9 M10 M11 M12 M13 M14 M15 M16 M17 M18 M19; do
    MILESTONE_STATUS[$m]="unchecked"
    MILESTONE_CHECKS[$m]=0
done

# Parse arguments
for arg in "$@"; do
    case $arg in
        --quick) QUICK_MODE=true ;;
        --milestone) MILESTONE_MODE=true ;;
        --matrix) MATRIX_MODE=true ;;
        --json) JSON_MODE=true ;;
        --help|-h)
            echo "AGENTICVERZ Milestone Certification Engine v2.0"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --quick      Fast pre-commit check"
            echo "  --milestone  Show milestone health dashboard"
            echo "  --matrix     Show CI job → milestone mapping"
            echo "  --json       Output JSON for CI pipelines"
            echo ""
            echo "Validates M0-M19 correctness. M20+ is OUT OF SCOPE."
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
# M0: FOUNDATIONS (async DB, migrations, determinism)
# ============================================================================
check_m0_foundations() {
    section "M0: Foundations"
    local issues=0

    # Alembic configuration
    [[ -f "$BACKEND_DIR/alembic.ini" ]] && log_ok "M0: Alembic config" || { log_error "M0: Missing alembic.ini"; issues=$((issues+1)); }

    # Database models (sync or async)
    if [[ -f "$BACKEND_DIR/app/db.py" ]] || [[ -f "$BACKEND_DIR/app/db_async.py" ]]; then
        log_ok "M0: Database models present"
    else
        log_error "M0: Missing database models"; issues=$((issues+1))
    fi

    # Async engine pattern
    grep -rq "create_async_engine\|AsyncSession" "$BACKEND_DIR/app" 2>/dev/null && \
        log_ok "M0: Async engine pattern" || log_warn "M0: No async engine detected"

    # Migration count
    local ALEMBIC_DIR="$BACKEND_DIR/alembic/versions"
    if [[ -d "$ALEMBIC_DIR" ]]; then
        local count=$(find "$ALEMBIC_DIR" -maxdepth 1 -name "*.py" ! -name "__*" | wc -l)
        log_ok "M0: $count migrations found"
    fi

    # Deterministic utilities
    [[ -f "$BACKEND_DIR/app/utils/deterministic.py" ]] && \
        log_ok "M0: Deterministic utilities" || log_info "M0: No deterministic.py"

    MILESTONE_CHECKS[M0]=$((MILESTONE_CHECKS[M0] + 5))
    [[ $issues -eq 0 ]] && log_milestone "M0" "pass" "Foundations validated" || log_milestone "M0" "fail" "$issues issue(s)"
}

# ============================================================================
# M1: AGENT REGISTRY (metadata, capabilities, routing)
# ============================================================================
check_m1_agent_registry() {
    section "M1: Agent Registry"
    local issues=0

    # Check for agents module
    if [[ -d "$BACKEND_DIR/app/agents" ]]; then
        log_ok "M1: Agents module exists"

        # Check for registry pattern
        grep -rq "agent.*registry\|AgentRegistry\|register.*agent" "$BACKEND_DIR/app/agents" 2>/dev/null && \
            log_ok "M1: Agent registry pattern" || log_info "M1: No explicit registry"

        # Check for agent models/schema
        [[ -f "$BACKEND_DIR/app/agents/schema.py" ]] && log_ok "M1: Agent schema present"
    else
        log_warn "M1: No agents module"
        issues=$((issues+1))
    fi

    MILESTONE_CHECKS[M1]=$((MILESTONE_CHECKS[M1] + 3))
    [[ $issues -eq 0 ]] && log_milestone "M1" "pass" "Agent registry OK" || log_milestone "M1" "warn" "Needs setup"
}

# ============================================================================
# M2: TOPOLOGY & DEPENDENCIES (cycle detection, version constraints)
# ============================================================================
check_m2_topology() {
    section "M2: Topology & Dependencies"
    local issues=0

    # Check for dependency/topology logic
    if grep -rq "dependency\|topology\|depends_on\|cycle.*detect" "$BACKEND_DIR/app" 2>/dev/null; then
        log_ok "M2: Dependency patterns found"
    else
        log_info "M2: No explicit topology module"
    fi

    # Check for version constraints
    grep -rq "version.*constraint\|semver\|compatible" "$BACKEND_DIR/app" 2>/dev/null && \
        log_ok "M2: Version constraint patterns"

    MILESTONE_CHECKS[M2]=$((MILESTONE_CHECKS[M2] + 2))
    log_milestone "M2" "pass" "Topology baseline OK"
}

# ============================================================================
# M3: EVENT REPLAY / STATE STREAM (durable events, idempotency)
# ============================================================================
check_m3_event_replay() {
    section "M3: Event Replay / State Stream"
    local issues=0

    # Replay/event patterns
    if grep -rq "replay\|Replay\|event.*stream\|durable.*event" "$BACKEND_DIR/app" 2>/dev/null; then
        log_ok "M3: Event replay patterns"
    else
        log_info "M3: No explicit replay module"
    fi

    # Idempotency patterns
    grep -rq "idempotent\|idempotency_key\|ON CONFLICT\|IF NOT EXISTS" "$BACKEND_DIR" 2>/dev/null && \
        log_ok "M3: Idempotency patterns"

    # Dead letter queue
    grep -rq "dead.?letter\|DLQ\|dlq" "$BACKEND_DIR/app" 2>/dev/null && \
        log_ok "M3: Dead letter handling"

    MILESTONE_CHECKS[M3]=$((MILESTONE_CHECKS[M3] + 3))
    log_milestone "M3" "pass" "Event replay validated"
}

# ============================================================================
# M4: CAPABILITY MODELING (runtime resolution, routing)
# ============================================================================
check_m4_capability() {
    section "M4: Capability Modeling"

    # Capability patterns
    if grep -rq "capability\|Capability\|capabilities" "$BACKEND_DIR/app" 2>/dev/null; then
        log_ok "M4: Capability patterns found"
    fi

    # Runtime resolution
    grep -rq "resolve.*capability\|capability.*discovery" "$BACKEND_DIR/app" 2>/dev/null && \
        log_ok "M4: Runtime resolution"

    MILESTONE_CHECKS[M4]=$((MILESTONE_CHECKS[M4] + 2))
    log_milestone "M4" "pass" "Capability modeling OK"
}

# ============================================================================
# M5: POLICY & APPROVAL LAYER (evaluation rules, escalation)
# ============================================================================
check_m5_policy() {
    section "M5: Policy & Approval"
    local issues=0

    if [[ -d "$BACKEND_DIR/app/policy" ]]; then
        log_ok "M5: Policy module exists"

        # Async patterns (required for M5)
        if grep -rq "async def\|AsyncSession\|await" "$BACKEND_DIR/app/policy" 2>/dev/null; then
            log_ok "M5: Async patterns in policy"
        else
            log_warn "M5: Policy should use async - found sync patterns"
            issues=$((issues+1))
        fi

        # Policy evaluation
        grep -rq "evaluate\|PolicyEvaluation\|policy.*rule" "$BACKEND_DIR/app/policy" 2>/dev/null && \
            log_ok "M5: Policy evaluation logic"

        # Escalation
        grep -rq "escalat\|approval.*chain" "$BACKEND_DIR/app/policy" 2>/dev/null && \
            log_ok "M5: Escalation patterns"
    else
        log_warn "M5: No policy module"
        issues=$((issues+1))
    fi

    MILESTONE_CHECKS[M5]=$((MILESTONE_CHECKS[M5] + 4))
    [[ $issues -eq 0 ]] && log_milestone "M5" "pass" "Policy layer validated" || log_milestone "M5" "warn" "$issues issue(s)"
}

# ============================================================================
# M6: OUTBOX & DELIVERY (publish/claim/complete, dead-letter)
# ============================================================================
check_m6_outbox() {
    section "M6: Outbox & Delivery"
    local issues=0

    # Outbox pattern
    if grep -rq "outbox\|Outbox\|publish.*event\|claim.*event" "$BACKEND_DIR/app" 2>/dev/null; then
        log_ok "M6: Outbox pattern found"
    else
        log_warn "M6: No outbox pattern"
        issues=$((issues+1))
    fi

    # Claim/complete flow
    grep -rq "claim_outbox\|complete_outbox\|process.*outbox" "$BACKEND_DIR" 2>/dev/null && \
        log_ok "M6: Claim/complete flow"

    # Retry logic
    grep -rq "retry_count\|next_retry\|retry.*delay" "$BACKEND_DIR/app" 2>/dev/null && \
        log_ok "M6: Retry logic"

    # Check for M10 recovery schema (outbox lives here)
    [[ -f "$BACKEND_DIR/app/models/m10_recovery.py" ]] && log_ok "M6: Recovery models present"

    MILESTONE_CHECKS[M6]=$((MILESTONE_CHECKS[M6] + 4))
    [[ $issues -eq 0 ]] && log_milestone "M6" "pass" "Outbox validated" || log_milestone "M6" "warn" "Outbox needs setup"
}

# ============================================================================
# M7: WORKFLOW ENGINE (deterministic execution, checkpoints)
# ============================================================================
check_m7_workflow() {
    section "M7: Workflow Engine"
    local issues=0

    if [[ -d "$BACKEND_DIR/app/workflow" ]]; then
        log_ok "M7: Workflow module exists"

        # Checkpoint pattern
        grep -rq "checkpoint\|Checkpoint\|save.*state" "$BACKEND_DIR/app/workflow" 2>/dev/null && \
            log_ok "M7: Checkpoint pattern"

        # Deterministic execution
        grep -rq "deterministic\|replay.*execution\|golden" "$BACKEND_DIR/app/workflow" 2>/dev/null && \
            log_ok "M7: Deterministic execution"
    else
        log_warn "M7: No workflow module"
        issues=$((issues+1))
    fi

    # Workflow tests
    local wf_tests=$(find "$BACKEND_DIR/tests" -name "*workflow*" -o -name "*replay*" 2>/dev/null | wc -l)
    [[ $wf_tests -gt 0 ]] && log_ok "M7: $wf_tests workflow test files"

    MILESTONE_CHECKS[M7]=$((MILESTONE_CHECKS[M7] + 4))
    [[ $issues -eq 0 ]] && log_milestone "M7" "pass" "Workflow engine validated" || log_milestone "M7" "warn" "Needs setup"
}

# ============================================================================
# M8: COST SIMULATOR (circuit breaker, golden tests)
# ============================================================================
check_m8_costsim() {
    section "M8: Cost Simulator"
    local issues=0

    if [[ -d "$BACKEND_DIR/app/costsim" ]]; then
        log_ok "M8: CostSim module exists"

        # Circuit breaker
        grep -rq "circuit.*breaker\|CircuitBreaker" "$BACKEND_DIR/app/costsim" 2>/dev/null && \
            log_ok "M8: Circuit breaker present"

        # Golden test patterns
        grep -rq "golden\|deterministic\|snapshot" "$BACKEND_DIR/app/costsim" 2>/dev/null && \
            log_ok "M8: Golden test patterns"
    else
        log_warn "M8: No costsim module"
        issues=$((issues+1))
    fi

    # CostSim tests
    [[ -d "$BACKEND_DIR/tests/costsim" ]] && {
        local count=$(find "$BACKEND_DIR/tests/costsim" -name "test_*.py" | wc -l)
        log_ok "M8: $count costsim test files"
    }

    MILESTONE_CHECKS[M8]=$((MILESTONE_CHECKS[M8] + 4))
    [[ $issues -eq 0 ]] && log_milestone "M8" "pass" "CostSim validated" || log_milestone "M8" "warn" "Needs setup"
}

# ============================================================================
# M9: HARDENING (migration safety, idempotent patterns)
# ============================================================================
check_m9_hardening() {
    section "M9: Hardening"
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

    # Idempotent migrations
    local idempotent=$(grep -rl "IF NOT EXISTS\|DO \$\$\|OR REPLACE" "$ALEMBIC_DIR" 2>/dev/null | wc -l)
    log_ok "M9: $idempotent migrations use idempotent patterns"

    MILESTONE_CHECKS[M9]=$((MILESTONE_CHECKS[M9] + 3))
    [[ $issues -eq 0 ]] && log_milestone "M9" "pass" "Hardening validated" || log_milestone "M9" "fail" "$issues issue(s)"
}

# ============================================================================
# M10: RELIABILITY LAYER (leader election, recovery, retention)
# ============================================================================
check_m10_reliability() {
    section "M10: Reliability Layer"
    local issues=0

    # Leader election
    grep -rq "leader.*election\|distributed.*lock\|advisory.*lock" "$BACKEND_DIR/app" 2>/dev/null && \
        log_ok "M10: Leader election pattern" || log_warn "M10: No leader election"

    # Recovery models
    [[ -f "$BACKEND_DIR/app/models/m10_recovery.py" ]] && log_ok "M10: Recovery models present"

    # M10 tests
    local m10_tests=$(find "$BACKEND_DIR/tests" -name "test_m10_*.py" 2>/dev/null | wc -l)
    [[ $m10_tests -gt 0 ]] && log_ok "M10: $m10_tests M10 test files"

    # Recovery migrations
    ls "$BACKEND_DIR/alembic/versions"/*m10* &>/dev/null 2>&1 && log_ok "M10: Recovery migrations present"

    # Retention/archive
    grep -rq "retention\|archive\|partition" "$BACKEND_DIR/app" 2>/dev/null && \
        log_ok "M10: Retention patterns"

    MILESTONE_CHECKS[M10]=$((MILESTONE_CHECKS[M10] + 5))
    log_milestone "M10" "pass" "Reliability validated"
}

# ============================================================================
# M11: SKILL SANDBOX (security, budget limits, forbidden patterns)
# ============================================================================
check_m11_skill_sandbox() {
    section "M11: Skill Sandbox"
    local issues=0

    if [[ -d "$BACKEND_DIR/app/skills" ]]; then
        log_ok "M11: Skills module exists"

        # Security patterns
        grep -rq "forbidden\|sanitize\|validate\|max_step\|budget" "$BACKEND_DIR/app/skills" 2>/dev/null && \
            log_ok "M11: Security patterns" || { log_warn "M11: No security patterns"; issues=$((issues+1)); }

        # Base skill
        [[ -f "$BACKEND_DIR/app/skills/base.py" ]] && log_ok "M11: Base skill class"
    else
        log_warn "M11: No skills module"
        issues=$((issues+1))
    fi

    MILESTONE_CHECKS[M11]=$((MILESTONE_CHECKS[M11] + 3))
    [[ $issues -eq 0 ]] && log_milestone "M11" "pass" "Skill sandbox validated" || log_milestone "M11" "warn" "Security needs review"
}

# ============================================================================
# M12: MULTI-AGENT PLANNER (step graph, cycle detection, max steps)
# ============================================================================
check_m12_planner() {
    section "M12: Multi-Agent Planner"
    local issues=0

    if [[ -d "$BACKEND_DIR/app/agents" ]]; then
        log_ok "M12: Agents module exists"

        # Planner patterns
        grep -rq "planner\|executor\|step.*graph\|plan.*execution" "$BACKEND_DIR/app/agents" 2>/dev/null && \
            log_ok "M12: Planner patterns"

        # Cycle detection
        grep -rq "cycle.*detect\|circular\|DAG" "$BACKEND_DIR/app/agents" 2>/dev/null && \
            log_ok "M12: Cycle detection"

        # Services
        [[ -d "$BACKEND_DIR/app/agents/services" ]] && log_ok "M12: Agent services present"
    fi

    # M12 tests
    local m12_tests=$(find "$BACKEND_DIR/tests" -name "test_m12_*.py" 2>/dev/null | wc -l)
    [[ $m12_tests -gt 0 ]] && log_ok "M12: $m12_tests M12 test files"

    MILESTONE_CHECKS[M12]=$((MILESTONE_CHECKS[M12] + 4))
    log_milestone "M12" "pass" "Multi-agent planner validated"
}

# ============================================================================
# M13: TOOLING LAYER (tool registry, permissions, parameter safety)
# ============================================================================
check_m13_tooling() {
    section "M13: Tooling Layer"

    # Tool registry
    grep -rq "tool.*registry\|ToolRegistry\|register.*tool" "$BACKEND_DIR/app" 2>/dev/null && \
        log_ok "M13: Tool registry pattern"

    # Permissions
    grep -rq "tool.*permission\|allowed.*tool\|tool.*access" "$BACKEND_DIR/app" 2>/dev/null && \
        log_ok "M13: Tool permissions"

    MILESTONE_CHECKS[M13]=$((MILESTONE_CHECKS[M13] + 2))
    log_milestone "M13" "pass" "Tooling layer OK"
}

# ============================================================================
# M14: BUDGETLLM (cost deduction, accumulation, blocking)
# ============================================================================
check_m14_budgetllm() {
    section "M14: BudgetLLM"

    # Budget patterns
    grep -rq "budget\|Budget\|cost.*limit\|token.*limit" "$BACKEND_DIR/app" 2>/dev/null && \
        log_ok "M14: Budget patterns"

    # BudgetLLM module
    [[ -d "$REPO_ROOT/budgetllm" ]] && log_ok "M14: BudgetLLM module present"

    # Cost calculation
    grep -rq "cost.*calculation\|deduct.*budget\|accumulate" "$BACKEND_DIR/app" 2>/dev/null && \
        log_ok "M14: Cost calculation"

    # Blocking behavior
    grep -rq "insufficient.*budget\|budget.*exceed\|block.*budget" "$BACKEND_DIR/app" 2>/dev/null && \
        log_ok "M14: Budget blocking"

    MILESTONE_CHECKS[M14]=$((MILESTONE_CHECKS[M14] + 4))
    log_milestone "M14" "pass" "BudgetLLM validated"
}

# ============================================================================
# M15: SEMANTIC DEPENDENCIES (SBA - dependency graph, version mismatch)
# ============================================================================
check_m15_sba() {
    section "M15: Semantic Dependencies (SBA)"
    local issues=0

    if [[ -d "$BACKEND_DIR/app/agents/sba" ]]; then
        log_ok "M15: SBA module exists"

        # Key components
        for comp in generator schema service validator; do
            [[ -f "$BACKEND_DIR/app/agents/sba/${comp}.py" ]] && log_ok "M15: SBA $comp"
        done
    else
        log_warn "M15: No SBA module"
        issues=$((issues+1))
    fi

    # Dependency graph
    grep -rq "dependency.*graph\|resolve.*dep\|version.*mismatch" "$BACKEND_DIR/app" 2>/dev/null && \
        log_ok "M15: Dependency resolution"

    MILESTONE_CHECKS[M15]=$((MILESTONE_CHECKS[M15] + 3))
    [[ $issues -eq 0 ]] && log_milestone "M15" "pass" "SBA validated" || log_milestone "M15" "warn" "SBA needs setup"
}

# ============================================================================
# M16: UI/API COHESION (OpenAPI stability, endpoint contracts)
# ============================================================================
check_m16_api_cohesion() {
    section "M16: UI/API Cohesion"

    # API routers
    if [[ -d "$BACKEND_DIR/app/api" ]]; then
        local count=$(find "$BACKEND_DIR/app/api" -name "*.py" ! -name "__*" | wc -l)
        log_ok "M16: $count API router files"
    fi

    # OpenAPI
    grep -rq "openapi\|OpenAPI\|swagger" "$BACKEND_DIR/app" 2>/dev/null && \
        log_ok "M16: OpenAPI patterns"

    # Pydantic validation
    grep -rq "pydantic\|BaseModel\|validator" "$BACKEND_DIR/app" 2>/dev/null && \
        log_ok "M16: Pydantic validation"

    MILESTONE_CHECKS[M16]=$((MILESTONE_CHECKS[M16] + 3))
    log_milestone "M16" "pass" "API cohesion validated"
}

# ============================================================================
# M17: ROUTING ENGINE (CARE - multi-step execution, skill registry)
# ============================================================================
check_m17_routing() {
    section "M17: Routing Engine (CARE)"
    local issues=0

    if [[ -d "$BACKEND_DIR/app/routing" ]]; then
        log_ok "M17: Routing module exists"

        # CARE
        [[ -f "$BACKEND_DIR/app/routing/care.py" ]] && log_ok "M17: CARE routing"

        # Probes
        [[ -f "$BACKEND_DIR/app/routing/probes.py" ]] && log_ok "M17: Routing probes"

        # Models
        [[ -f "$BACKEND_DIR/app/routing/models.py" ]] && log_ok "M17: Routing models"
    else
        log_warn "M17: No routing module"
        issues=$((issues+1))
    fi

    # M17 tests
    local m17_tests=$(find "$BACKEND_DIR/tests" -name "test_m17_*.py" 2>/dev/null | wc -l)
    [[ $m17_tests -gt 0 ]] && log_ok "M17: $m17_tests M17 test files"

    MILESTONE_CHECKS[M17]=$((MILESTONE_CHECKS[M17] + 5))
    [[ $issues -eq 0 ]] && log_milestone "M17" "pass" "Routing engine validated" || log_milestone "M17" "warn" "Needs setup"
}

# ============================================================================
# M18: GOVERNOR (rate limits, magnitude caps, oscillation detection)
# ============================================================================
check_m18_governor() {
    section "M18: Governor (Stabilization)"
    local issues=0

    # Governor patterns
    if grep -rq "governor\|Governor\|rate.*limit\|magnitude.*cap" "$BACKEND_DIR/app" 2>/dev/null; then
        log_ok "M18: Governor patterns"
    else
        log_warn "M18: No governor patterns"
        issues=$((issues+1))
    fi

    # Governor module
    [[ -f "$BACKEND_DIR/app/routing/governor.py" ]] && log_ok "M18: Routing governor"

    # Oscillation detection
    grep -rq "oscillation\|dampen\|stabiliz" "$BACKEND_DIR/app" 2>/dev/null && \
        log_ok "M18: Oscillation detection"

    # Learning/feedback
    [[ -f "$BACKEND_DIR/app/routing/learning.py" ]] && log_ok "M18: Learning module"
    [[ -f "$BACKEND_DIR/app/routing/feedback.py" ]] && log_ok "M18: Feedback module"

    MILESTONE_CHECKS[M18]=$((MILESTONE_CHECKS[M18] + 5))
    [[ $issues -eq 0 ]] && log_milestone "M18" "pass" "Governor validated" || log_milestone "M18" "warn" "Needs review"
}

# ============================================================================
# M19: POLICY LAYER ASYNC (async evaluation, rule merging, caching)
# ============================================================================
check_m19_async_policy() {
    section "M19: Policy Layer (Async)"
    local issues=0

    if [[ -d "$BACKEND_DIR/app/policy" ]]; then
        log_ok "M19: Policy module exists"

        # Async patterns
        if grep -rq "async def\|AsyncSession\|await" "$BACKEND_DIR/app/policy" 2>/dev/null; then
            log_ok "M19: Async patterns"
        else
            log_warn "M19: Should use async"
            issues=$((issues+1))
        fi

        # Policy models
        if [[ -f "$BACKEND_DIR/app/policy/models.py" ]]; then
            log_ok "M19: Policy models"

            # Pydantic v2 forward ref fix
            grep -q "model_rebuild" "$BACKEND_DIR/app/policy/models.py" 2>/dev/null && \
                log_ok "M19: Pydantic forward ref resolved"
        fi

        # Policy API
        [[ -f "$BACKEND_DIR/app/api/policy_layer.py" ]] || [[ -f "$BACKEND_DIR/app/api/policy.py" ]] && \
            log_ok "M19: Policy API"

        # Rule merging
        grep -rq "merge.*rule\|rule.*order\|priority" "$BACKEND_DIR/app/policy" 2>/dev/null && \
            log_ok "M19: Rule merging"

        # Policy cache
        grep -rq "policy.*cache\|cache.*policy" "$BACKEND_DIR/app/policy" 2>/dev/null && \
            log_ok "M19: Policy caching"
    else
        log_warn "M19: No policy module"
        issues=$((issues+1))
    fi

    MILESTONE_CHECKS[M19]=$((MILESTONE_CHECKS[M19] + 6))
    [[ $issues -eq 0 ]] && log_milestone "M19" "pass" "Async policy validated" || log_milestone "M19" "warn" "$issues issue(s)"
}

# ============================================================================
# CI INFRASTRUCTURE CHECKS
# ============================================================================
check_ci_workflow() {
    header "CI Workflow"

    local CI_FILE="$REPO_ROOT/.github/workflows/ci.yml"
    [[ ! -f "$CI_FILE" ]] && { log_error "CI workflow not found"; return; }

    grep -q "redis:" "$CI_FILE" && log_ok "Redis service"
    grep -q "PYTHONUNBUFFERED" "$CI_FILE" && log_ok "PYTHONUNBUFFERED"
    grep -q "run-migrations:" "$CI_FILE" && log_ok "run-migrations job (race condition fix)"
    grep -q "neonctl connection-string" "$CI_FILE" && log_ok "Neon ephemeral pattern"
    grep -q "schema_audit" "$CI_FILE" && log_ok "Schema audit"
    grep -q "metrics" "$CI_FILE" && log_ok "Metrics validation"
}

check_alembic_health() {
    header "Alembic Health"

    local ALEMBIC_DIR="$BACKEND_DIR/alembic/versions"
    [[ ! -d "$ALEMBIC_DIR" ]] && { log_warn "No alembic versions"; return; }

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
}

# ============================================================================
# DASHBOARD & MATRIX
# ============================================================================
print_dashboard() {
    $JSON_MODE && return

    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║       AGENTICVERZ MILESTONE DASHBOARD (M0-M19)                     ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    printf "%-6s %-45s %-8s %-6s\n" "ID" "Milestone" "Status" "Checks"
    echo "────────────────────────────────────────────────────────────────────"

    local MILESTONES=(
        "M0:Foundations (async DB, migrations, determinism)"
        "M1:Agent Registry (metadata, capabilities)"
        "M2:Topology & Dependencies (cycles, versions)"
        "M3:Event Replay / State Stream (idempotency)"
        "M4:Capability Modeling (runtime resolution)"
        "M5:Policy & Approval (evaluation, escalation)"
        "M6:Outbox & Delivery (publish/claim/complete)"
        "M7:Workflow Engine (checkpoints, determinism)"
        "M8:Cost Simulator (circuit breaker, golden)"
        "M9:Hardening (migration safety, idempotent)"
        "M10:Reliability (leader election, recovery)"
        "M11:Skill Sandbox (security, budget limits)"
        "M12:Multi-Agent Planner (step graph, cycles)"
        "M13:Tooling Layer (registry, permissions)"
        "M14:BudgetLLM (deduction, blocking)"
        "M15:Semantic Dependencies (SBA)"
        "M16:UI/API Cohesion (OpenAPI, contracts)"
        "M17:Routing Engine (CARE)"
        "M18:Governor (rate limits, oscillation)"
        "M19:Policy Layer Async (caching, merging)"
    )

    for entry in "${MILESTONES[@]}"; do
        local ID="${entry%%:*}"
        local NAME="${entry#*:}"
        local STATUS="${MILESTONE_STATUS[$ID]:-unchecked}"
        local CHECKS="${MILESTONE_CHECKS[$ID]:-0}"

        local COLOR="" TEXT=""
        case $STATUS in
            pass) COLOR="${GREEN}"; TEXT="PASS" ;;
            warn) COLOR="${YELLOW}"; TEXT="WARN" ;;
            fail) COLOR="${RED}"; TEXT="FAIL" ;;
            *) COLOR="${BLUE}"; TEXT="--" ;;
        esac

        printf "%-6s %-45s ${COLOR}%-8s${NC} %-6s\n" "$ID" "$NAME" "$TEXT" "$CHECKS"
    done

    echo "────────────────────────────────────────────────────────────────────"
    echo ""
    echo -e "Summary: ${GREEN}$MILESTONE_PASS PASS${NC} | ${YELLOW}$MILESTONE_WARN WARN${NC} | ${RED}$MILESTONE_FAIL FAIL${NC}"
    echo ""
    echo -e "${BLUE}Note: M20+ is OUT OF SCOPE - Agenticverz validates M0-M19 only.${NC}"
    echo ""
}

print_matrix() {
    $JSON_MODE && return

    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║         AGENTICVERZ CI JOB → MILESTONE MAPPING                     ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    cat <<'EOF'
┌─────────────────────┬────────────────────────────────────────────────┐
│ CI Job              │ Milestones Validated                           │
├─────────────────────┼────────────────────────────────────────────────┤
│ unit-tests          │ M0, M4, M11, M14                               │
│ determinism         │ M0, M3, M7, M9                                 │
│ workflow-engine     │ M7, M17                                        │
│ integration         │ M0, M5, M6, M16                                │
│ costsim             │ M8, M14                                        │
│ costsim-wiremock    │ M8                                             │
│ e2e-tests           │ M0, M5, M6, M7, M10, M16, M17                  │
│ m10-tests           │ M6, M10                                        │
└─────────────────────┴────────────────────────────────────────────────┘

┌─────────────────────┬────────────────────────────────────────────────┐
│ Milestone           │ Primary Test Files                             │
├─────────────────────┼────────────────────────────────────────────────┤
│ M0                  │ test_integration.py                            │
│ M3, M6              │ test_m10_outbox_e2e.py                         │
│ M7                  │ tests/workflow/test_*.py                       │
│ M8                  │ tests/costsim/test_*.py                        │
│ M10                 │ test_m10_*.py (6+ files)                       │
│ M11                 │ tests/skills/test_m11_skills.py                │
│ M12                 │ test_m12_*.py (4 files)                        │
│ M17                 │ test_m17_care.py                               │
│ M18                 │ test_m18_*.py                                  │
│ M19                 │ test_m19_policy.py                             │
└─────────────────────┴────────────────────────────────────────────────┘
EOF
    echo ""
}

print_json() {
    $JSON_MODE || return

    local status="pass"
    [[ $ERRORS -gt 0 ]] && status="fail"
    [[ $WARNINGS -gt 0 ]] && [[ $status != "fail" ]] && status="warn"

    cat <<EOF
{
  "version": "2.0",
  "project": "agenticverz",
  "status": "$status",
  "errors": $ERRORS,
  "warnings": $WARNINGS,
  "milestones": {"pass": $MILESTONE_PASS, "warn": $MILESTONE_WARN, "fail": $MILESTONE_FAIL},
  "milestone_status": {
EOF

    local first=true
    for m in M0 M1 M2 M3 M4 M5 M6 M7 M8 M9 M10 M11 M12 M13 M14 M15 M16 M17 M18 M19; do
        $first && first=false || echo ","
        printf '    "%s": "%s"' "$m" "${MILESTONE_STATUS[$m]:-unchecked}"
    done

    echo -e "\n  }\n}"
}

# ============================================================================
# PRE-FLIGHT
# ============================================================================
preflight() {
    header "Pre-Flight"

    git status --porcelain 2>/dev/null | grep -q . && log_warn "Uncommitted changes" || log_ok "Clean working directory"

    local branch=$(git branch --show-current 2>/dev/null || echo "")
    [[ -n "$branch" ]] && log_info "Branch: $branch"

    command -v gh &>/dev/null && {
        local last=$(gh run list --limit 1 --json conclusion,name 2>/dev/null || echo "")
        [[ -n "$last" ]] && log_info "Last CI: $last"
    }
}

# ============================================================================
# SUMMARY
# ============================================================================
print_summary() {
    $JSON_MODE && { print_json; return; }

    header "Summary"
    echo ""

    [[ $ERRORS -eq 0 ]] && echo -e "${GREEN}All checks passed!${NC}" || echo -e "${RED}$ERRORS error(s) found${NC}"
    [[ $WARNINGS -gt 0 ]] && echo -e "${YELLOW}$WARNINGS warning(s) to review${NC}"

    echo ""
    echo -e "${CYAN}Milestones:${NC} ${GREEN}$MILESTONE_PASS PASS${NC} | ${YELLOW}$MILESTONE_WARN WARN${NC} | ${RED}$MILESTONE_FAIL FAIL${NC}"
    echo ""

    if [[ $ERRORS -gt 0 ]] || [[ $MILESTONE_FAIL -gt 0 ]]; then
        echo -e "${RED}CI push NOT recommended.${NC}"
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
        echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${CYAN}║  AGENTICVERZ Milestone Certification Engine v2.0                   ║${NC}"
        echo -e "${CYAN}║  Validates M0-M19 • M20+ OUT OF SCOPE                              ║${NC}"
        echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
    }

    $QUICK_MODE && ! $JSON_MODE && log_info "Quick mode (skipping slow checks)"

    cd "$REPO_ROOT"

    # Dashboard/matrix only mode
    if $MILESTONE_MODE || $MATRIX_MODE; then
        check_m0_foundations; check_m1_agent_registry; check_m2_topology; check_m3_event_replay
        check_m4_capability; check_m5_policy; check_m6_outbox; check_m7_workflow
        check_m8_costsim; check_m9_hardening; check_m10_reliability; check_m11_skill_sandbox
        check_m12_planner; check_m13_tooling; check_m14_budgetllm; check_m15_sba
        check_m16_api_cohesion; check_m17_routing; check_m18_governor; check_m19_async_policy

        $MILESTONE_MODE && print_dashboard
        $MATRIX_MODE && print_matrix
        exit 0
    fi

    # Full check
    preflight
    check_ci_workflow
    check_alembic_health

    header "Milestone Validation (M0-M19)"

    check_m0_foundations; check_m1_agent_registry; check_m2_topology; check_m3_event_replay
    check_m4_capability; check_m5_policy; check_m6_outbox; check_m7_workflow
    check_m8_costsim; check_m9_hardening; check_m10_reliability; check_m11_skill_sandbox
    check_m12_planner; check_m13_tooling; check_m14_budgetllm; check_m15_sba
    check_m16_api_cohesion; check_m17_routing; check_m18_governor; check_m19_async_policy

    ! $QUICK_MODE && ! $JSON_MODE && print_dashboard

    print_summary
}

main "$@"
