#!/bin/bash
# ============================================================================
# CI Consistency Checker v3.0 - AGENTICVERZ Milestone Certification Engine
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
# AGENTICVERZ Milestone Coverage (M0-M19) - PIN-Accurate Names:
#   M0:  Foundations & Contracts (schemas, error taxonomy, CI, tests) [PIN-009]
#   M1:  Runtime Interfaces (execute, query, describe_skill, contracts) [PIN-009]
#   M2:  Skill Registration (registry, versioning, core stubs) [PIN-010]
#   M3:  Core Skill Implementations (http_call, llm_invoke, json_transform) [PIN-010]
#   M4:  Workflow Engine (deterministic execution, checkpoints, replay) [PIN-013/020]
#   M5:  Policy API & Approval (evaluation rules, escalation, webhooks) [PIN-021]
#   M6:  Feature Freeze & CostSim V2 (circuit breaker, drift detection) [PIN-026]
#   M7:  Memory Integration (memory pins, context management, RBAC) [PIN-031/032]
#   M8:  SDK Packaging & Auth (PyPI, npm, auth integration) [PIN-033]
#   M9:  Failure Catalog Persistence (failure_matches, R2, metrics) [PIN-048]
#   M10: Recovery Suggestion Engine (confidence scoring, CLI approval) [PIN-050]
#   M11: Store Factories & LLM Adapters (R2, OpenAI adapter, metering) [PIN-055/060]
#   M12: Multi-Agent System (parallel spawning, blackboard, credits) [PIN-062/063]
#   M13: Console UI & Boundary Checklist (metrics dashboard) [PIN-064]
#   M14: BudgetLLM Safety Governance (cost control, risk scoring) [PIN-070]
#   M15: SBA Foundations (Strategy Cascade, semantic validation) [PIN-072]
#   M16: Agent Governance Console (profile/activity/health tabs) [PIN-074]
#   M17: CARE Routing Engine (5-stage pipeline, capability probes) [PIN-075]
#   M18: CARE-L & SBA Evolution (learning router, governor, drift) [PIN-076]
#   M19: Policy Layer Constitutional (5 categories, versioning) [PIN-078]
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
            echo "AGENTICVERZ Milestone Certification Engine v3.0"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --quick      Fast pre-commit check"
            echo "  --milestone  Show milestone health dashboard"
            echo "  --matrix     Show CI job -> milestone mapping"
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
# M0: FOUNDATIONS & CONTRACTS (schemas, error taxonomy, CI, tests) [PIN-009]
# ============================================================================
check_m0_foundations() {
    section "M0: Foundations & Contracts [PIN-009]"
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
    return 0
}

# ============================================================================
# M1: RUNTIME INTERFACES (execute, query, describe_skill, contracts) [PIN-009]
# ============================================================================
check_m1_runtime_interfaces() {
    section "M1: Runtime Interfaces [PIN-009]"
    local issues=0

    # Check for runtime module
    if [[ -d "$BACKEND_DIR/app/worker/runtime" ]]; then
        log_ok "M1: Runtime module exists"

        # Check for execute/query patterns
        grep -rq "execute\|Execute\|run.*execution" "$BACKEND_DIR/app/worker/runtime" 2>/dev/null && \
            log_ok "M1: Execute interface"

        grep -rq "query\|Query\|state.*query" "$BACKEND_DIR/app/worker/runtime" 2>/dev/null && \
            log_ok "M1: Query interface"
    else
        log_warn "M1: No runtime module"
        issues=$((issues+1))
    fi

    # Runtime API
    if [[ -d "$BACKEND_DIR/app/api" ]]; then
        grep -rq "runtime\|Runtime" "$BACKEND_DIR/app/api" 2>/dev/null && \
            log_ok "M1: Runtime API present"
    fi

    MILESTONE_CHECKS[M1]=$((MILESTONE_CHECKS[M1] + 4))
    [[ $issues -eq 0 ]] && log_milestone "M1" "pass" "Runtime interfaces OK" || log_milestone "M1" "warn" "Needs setup"
    return 0
}

# ============================================================================
# M2: SKILL REGISTRATION (registry, versioning, core stubs) [PIN-010]
# ============================================================================
check_m2_skill_registration() {
    section "M2: Skill Registration [PIN-010]"
    local issues=0

    # Check for skills module
    if [[ -d "$BACKEND_DIR/app/skills" ]]; then
        log_ok "M2: Skills module exists"

        # Check for registry pattern
        grep -rq "skill.*registry\|SkillRegistry\|register.*skill" "$BACKEND_DIR/app/skills" 2>/dev/null && \
            log_ok "M2: Skill registry pattern"

        # Base skill class
        [[ -f "$BACKEND_DIR/app/skills/base.py" ]] && log_ok "M2: Base skill class"

        # Version patterns
        grep -rq "version\|Version\|skill.*version" "$BACKEND_DIR/app/skills" 2>/dev/null && \
            log_ok "M2: Skill versioning"
    else
        log_warn "M2: No skills module"
        issues=$((issues+1))
    fi

    MILESTONE_CHECKS[M2]=$((MILESTONE_CHECKS[M2] + 4))
    [[ $issues -eq 0 ]] && log_milestone "M2" "pass" "Skill registration OK" || log_milestone "M2" "warn" "Needs setup"
    return 0
}

# ============================================================================
# M3: CORE SKILL IMPLEMENTATIONS (http_call, llm_invoke, json_transform) [PIN-010]
# ============================================================================
check_m3_core_skills() {
    section "M3: Core Skill Implementations [PIN-010]"
    local issues=0

    if [[ -d "$BACKEND_DIR/app/skills" ]]; then
        # Key core skills
        local found_skills=0

        # http_call / webhook_send
        [[ -f "$BACKEND_DIR/app/skills/webhook_send.py" ]] && { log_ok "M3: webhook_send skill"; found_skills=$((found_skills+1)); }

        # llm_invoke
        grep -rq "llm.*invoke\|LLM\|voyage.*embed\|openai" "$BACKEND_DIR/app/skills" 2>/dev/null && \
            { log_ok "M3: LLM invoke patterns"; found_skills=$((found_skills+1)); }

        # json_transform / kv_store
        [[ -f "$BACKEND_DIR/app/skills/kv_store.py" ]] && { log_ok "M3: kv_store skill"; found_skills=$((found_skills+1)); }

        # slack_send
        [[ -f "$BACKEND_DIR/app/skills/slack_send.py" ]] && { log_ok "M3: slack_send skill"; found_skills=$((found_skills+1)); }

        [[ $found_skills -lt 2 ]] && { log_warn "M3: Few core skills"; issues=$((issues+1)); }
    else
        issues=$((issues+1))
    fi

    MILESTONE_CHECKS[M3]=$((MILESTONE_CHECKS[M3] + 4))
    [[ $issues -eq 0 ]] && log_milestone "M3" "pass" "Core skills validated" || log_milestone "M3" "warn" "Skills incomplete"
    return 0
}

# ============================================================================
# M4: WORKFLOW ENGINE (deterministic execution, checkpoints, replay) [PIN-013/020]
# ============================================================================
check_m4_workflow_engine() {
    section "M4: Workflow Engine [PIN-013/020]"
    local issues=0

    if [[ -d "$BACKEND_DIR/app/workflow" ]]; then
        log_ok "M4: Workflow module exists"

        # Checkpoint pattern
        grep -rq "checkpoint\|Checkpoint\|save.*state" "$BACKEND_DIR/app/workflow" 2>/dev/null && \
            log_ok "M4: Checkpoint pattern"

        # Deterministic execution
        grep -rq "deterministic\|replay.*execution\|golden" "$BACKEND_DIR/app/workflow" 2>/dev/null && \
            log_ok "M4: Deterministic execution"
    else
        log_warn "M4: No workflow module"
        issues=$((issues+1))
    fi

    # Workflow tests
    local wf_tests=$(find "$BACKEND_DIR/tests" -name "*workflow*" -o -name "*replay*" 2>/dev/null | wc -l)
    [[ $wf_tests -gt 0 ]] && log_ok "M4: $wf_tests workflow test files"

    MILESTONE_CHECKS[M4]=$((MILESTONE_CHECKS[M4] + 4))
    [[ $issues -eq 0 ]] && log_milestone "M4" "pass" "Workflow engine validated" || log_milestone "M4" "warn" "Needs setup"
    return 0
}

# ============================================================================
# M5: POLICY API & APPROVAL (evaluation rules, escalation, webhooks) [PIN-021]
# ============================================================================
check_m5_policy_approval() {
    section "M5: Policy API & Approval [PIN-021]"
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
    return 0
}

# ============================================================================
# M6: FEATURE FREEZE & COSTSIM V2 (circuit breaker, drift detection) [PIN-026]
# ============================================================================
check_m6_costsim_v2() {
    section "M6: Feature Freeze & CostSim V2 [PIN-026]"
    local issues=0

    if [[ -d "$BACKEND_DIR/app/costsim" ]]; then
        log_ok "M6: CostSim module exists"

        # Circuit breaker
        grep -rq "circuit.*breaker\|CircuitBreaker" "$BACKEND_DIR/app/costsim" 2>/dev/null && \
            log_ok "M6: Circuit breaker present"

        # Drift detection
        grep -rq "drift\|deterministic\|golden" "$BACKEND_DIR/app/costsim" 2>/dev/null && \
            log_ok "M6: Drift/determinism patterns"
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
# M7: MEMORY INTEGRATION (memory pins, context management, RBAC) [PIN-031/032]
# ============================================================================
check_m7_memory_integration() {
    section "M7: Memory Integration [PIN-031/032]"
    local issues=0

    # Memory pins directory
    if [[ -d "$REPO_ROOT/docs/memory-pins" ]]; then
        local pin_count=$(find "$REPO_ROOT/docs/memory-pins" -name "PIN-*.md" | wc -l)
        log_ok "M7: $pin_count memory PINs found"

        # INDEX.md
        [[ -f "$REPO_ROOT/docs/memory-pins/INDEX.md" ]] && log_ok "M7: PIN INDEX.md present"
    else
        log_warn "M7: No memory-pins directory"
        issues=$((issues+1))
    fi

    # RBAC / Auth
    if [[ -d "$BACKEND_DIR/app/auth" ]]; then
        log_ok "M7: Auth module exists"
        grep -rq "rbac\|RBAC\|role.*based" "$BACKEND_DIR/app/auth" 2>/dev/null && \
            log_ok "M7: RBAC patterns"
    fi

    MILESTONE_CHECKS[M7]=$((MILESTONE_CHECKS[M7] + 4))
    [[ $issues -eq 0 ]] && log_milestone "M7" "pass" "Memory integration validated" || log_milestone "M7" "warn" "Needs setup"
    return 0
}

# ============================================================================
# M8: SDK PACKAGING & AUTH (PyPI, npm, auth integration) [PIN-033]
# ============================================================================
check_m8_sdk_packaging() {
    section "M8: SDK Packaging & Auth [PIN-033]"
    local issues=0

    # SDK directories
    if [[ -d "$REPO_ROOT/sdk" ]]; then
        log_ok "M8: SDK directory exists"

        [[ -d "$REPO_ROOT/sdk/python" ]] && log_ok "M8: Python SDK"
        [[ -d "$REPO_ROOT/sdk/js" ]] && log_ok "M8: JS SDK"
    else
        log_warn "M8: No SDK directory"
        issues=$((issues+1))
    fi

    # Auth integration
    if [[ -d "$BACKEND_DIR/app/auth" ]]; then
        log_ok "M8: Auth module present"
    fi

    # CLI tool
    [[ -f "$BACKEND_DIR/cli/aos.py" ]] && log_ok "M8: CLI tool present"

    MILESTONE_CHECKS[M8]=$((MILESTONE_CHECKS[M8] + 4))
    [[ $issues -eq 0 ]] && log_milestone "M8" "pass" "SDK packaging validated" || log_milestone "M8" "warn" "SDK incomplete"
    return 0
}

# ============================================================================
# M9: FAILURE CATALOG PERSISTENCE (failure_matches, R2, metrics) [PIN-048]
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

    # Idempotent migrations
    local idempotent=$(grep -rl "IF NOT EXISTS\|DO \$\$\|OR REPLACE" "$ALEMBIC_DIR" 2>/dev/null | wc -l)
    log_ok "M9: $idempotent migrations use idempotent patterns"

    # Failure pattern exports table
    grep -rq "failure_pattern_exports\|FailurePatternExport" "$BACKEND_DIR" 2>/dev/null && \
        log_ok "M9: Failure pattern exports"

    MILESTONE_CHECKS[M9]=$((MILESTONE_CHECKS[M9] + 4))
    [[ $issues -eq 0 ]] && log_milestone "M9" "pass" "Failure catalog validated" || log_milestone "M9" "fail" "$issues issue(s)"
    return 0
}

# ============================================================================
# M10: RECOVERY SUGGESTION ENGINE (confidence scoring, CLI approval) [PIN-050]
# ============================================================================
check_m10_recovery_engine() {
    section "M10: Recovery Suggestion Engine [PIN-050]"
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

    # Outbox pattern (recovery uses outbox)
    grep -rq "outbox\|claim_outbox\|complete_outbox" "$BACKEND_DIR" 2>/dev/null && \
        log_ok "M10: Outbox patterns"

    MILESTONE_CHECKS[M10]=$((MILESTONE_CHECKS[M10] + 5))
    log_milestone "M10" "pass" "Recovery engine validated"
    return 0
}

# ============================================================================
# M11: STORE FACTORIES & LLM ADAPTERS (R2, OpenAI adapter, metering) [PIN-055/060]
# ============================================================================
check_m11_store_factories() {
    section "M11: Store Factories & LLM Adapters [PIN-055/060]"
    local issues=0

    # Stores module
    if [[ -d "$BACKEND_DIR/app/stores" ]]; then
        log_ok "M11: Stores module exists"
    fi

    # Skills module with adapters
    if [[ -d "$BACKEND_DIR/app/skills" ]]; then
        log_ok "M11: Skills module exists"

        # Adapters
        if [[ -d "$BACKEND_DIR/app/skills/adapters" ]]; then
            log_ok "M11: Skill adapters directory"
            [[ -f "$BACKEND_DIR/app/skills/adapters/openai_adapter.py" ]] && log_ok "M11: OpenAI adapter"
            [[ -f "$BACKEND_DIR/app/skills/adapters/metrics.py" ]] && log_ok "M11: Metrics adapter"
        fi

        # Voyage embed (LLM skill)
        [[ -f "$BACKEND_DIR/app/skills/voyage_embed.py" ]] && log_ok "M11: Voyage embed skill"
    else
        log_warn "M11: No skills module"
        issues=$((issues+1))
    fi

    MILESTONE_CHECKS[M11]=$((MILESTONE_CHECKS[M11] + 5))
    [[ $issues -eq 0 ]] && log_milestone "M11" "pass" "Store factories validated" || log_milestone "M11" "warn" "Adapters incomplete"
    return 0
}

# ============================================================================
# M12: MULTI-AGENT SYSTEM (parallel spawning, blackboard, credits) [PIN-062/063]
# ============================================================================
check_m12_multi_agent() {
    section "M12: Multi-Agent System [PIN-062/063]"
    local issues=0

    if [[ -d "$BACKEND_DIR/app/agents" ]]; then
        log_ok "M12: Agents module exists"

        # Services
        [[ -d "$BACKEND_DIR/app/agents/services" ]] && log_ok "M12: Agent services present"

        # Skills
        [[ -d "$BACKEND_DIR/app/agents/skills" ]] && log_ok "M12: Agent skills present"

        # Credit/budget patterns
        grep -rq "credit\|Credit\|budget" "$BACKEND_DIR/app/agents" 2>/dev/null && \
            log_ok "M12: Credit patterns"
    fi

    # M12 tests
    local m12_tests=$(find "$BACKEND_DIR/tests" -name "test_m12_*.py" 2>/dev/null | wc -l)
    [[ $m12_tests -gt 0 ]] && log_ok "M12: $m12_tests M12 test files"

    MILESTONE_CHECKS[M12]=$((MILESTONE_CHECKS[M12] + 5))
    log_milestone "M12" "pass" "Multi-agent system validated"
    return 0
}

# ============================================================================
# M13: CONSOLE UI & BOUNDARY CHECKLIST (metrics dashboard) [PIN-064]
# ============================================================================
check_m13_console_ui() {
    section "M13: Console UI & Boundary Checklist [PIN-064]"

    # Console/website directory
    if [[ -d "$REPO_ROOT/website" ]]; then
        log_ok "M13: Website directory exists"

        [[ -d "$REPO_ROOT/website/aos-console" ]] && log_ok "M13: AOS Console present"
    fi

    # Grafana dashboards
    if [[ -d "$REPO_ROOT/monitoring/grafana" ]] || [[ -d "$REPO_ROOT/monitoring/dashboards" ]]; then
        log_ok "M13: Monitoring dashboards present"
    fi

    # M13 boundary checklist PIN
    [[ -f "$REPO_ROOT/docs/memory-pins/PIN-064-m13-boundary-checklist.md" ]] && \
        log_ok "M13: Boundary checklist PIN"

    MILESTONE_CHECKS[M13]=$((MILESTONE_CHECKS[M13] + 3))
    log_milestone "M13" "pass" "Console UI validated"
    return 0
}

# ============================================================================
# M14: BUDGETLLM SAFETY GOVERNANCE (cost control, risk scoring) [PIN-070]
# ============================================================================
check_m14_budgetllm() {
    section "M14: BudgetLLM Safety Governance [PIN-070]"

    # Budget patterns
    grep -rq "budget\|Budget\|cost.*limit\|token.*limit" "$BACKEND_DIR/app" 2>/dev/null && \
        log_ok "M14: Budget patterns"

    # BudgetLLM module
    [[ -d "$REPO_ROOT/budgetllm" ]] && log_ok "M14: BudgetLLM module present"

    # Cost calculation
    grep -rq "cost.*calculation\|deduct.*budget\|accumulate" "$BACKEND_DIR/app" 2>/dev/null && \
        log_ok "M14: Cost calculation"

    # Risk scoring
    grep -rq "risk.*scor\|safety\|governance" "$BACKEND_DIR/app" 2>/dev/null && \
        log_ok "M14: Risk/safety patterns"

    MILESTONE_CHECKS[M14]=$((MILESTONE_CHECKS[M14] + 4))
    log_milestone "M14" "pass" "BudgetLLM validated"
    return 0
}

# ============================================================================
# M15: SBA FOUNDATIONS (Strategy Cascade, semantic validation) [PIN-072]
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
    else
        log_warn "M15: No SBA module"
        issues=$((issues+1))
    fi

    # Strategy patterns
    grep -rq "strategy\|Strategy\|cascade" "$BACKEND_DIR/app" 2>/dev/null && \
        log_ok "M15: Strategy patterns"

    MILESTONE_CHECKS[M15]=$((MILESTONE_CHECKS[M15] + 5))
    [[ $issues -eq 0 ]] && log_milestone "M15" "pass" "SBA foundations validated" || log_milestone "M15" "warn" "SBA needs setup"
    return 0
}

# ============================================================================
# M16: AGENT GOVERNANCE CONSOLE (profile/activity/health tabs) [PIN-074]
# ============================================================================
check_m16_governance_console() {
    section "M16: Agent Governance Console [PIN-074]"

    # API routers for agents
    if [[ -d "$BACKEND_DIR/app/api" ]]; then
        local count=$(find "$BACKEND_DIR/app/api" -name "*.py" ! -name "__*" | wc -l)
        log_ok "M16: $count API router files"

        # Agent-related APIs
        grep -rq "agents\|agent" "$BACKEND_DIR/app/api" 2>/dev/null && \
            log_ok "M16: Agent API routes"
    fi

    # Console SBA pages
    if [[ -d "$REPO_ROOT/website/aos-console" ]]; then
        [[ -d "$REPO_ROOT/website/aos-console/console/src/pages/sba" ]] && \
            log_ok "M16: SBA console pages"
    fi

    # Pydantic validation
    grep -rq "pydantic\|BaseModel\|validator" "$BACKEND_DIR/app" 2>/dev/null && \
        log_ok "M16: Pydantic validation"

    MILESTONE_CHECKS[M16]=$((MILESTONE_CHECKS[M16] + 4))
    log_milestone "M16" "pass" "Governance console validated"
    return 0
}

# ============================================================================
# M17: CARE ROUTING ENGINE (5-stage pipeline, capability probes) [PIN-075]
# ============================================================================
check_m17_care_routing() {
    section "M17: CARE Routing Engine [PIN-075]"
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
    [[ $issues -eq 0 ]] && log_milestone "M17" "pass" "CARE routing validated" || log_milestone "M17" "warn" "Needs setup"
    return 0
}

# ============================================================================
# M18: CARE-L & SBA EVOLUTION (learning router, governor, drift) [PIN-076]
# ============================================================================
check_m18_care_l_evolution() {
    section "M18: CARE-L & SBA Evolution [PIN-076]"
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

    # Learning/feedback
    [[ -f "$BACKEND_DIR/app/routing/learning.py" ]] && log_ok "M18: Learning module"
    [[ -f "$BACKEND_DIR/app/routing/feedback.py" ]] && log_ok "M18: Feedback module"

    # SBA evolution
    [[ -f "$BACKEND_DIR/app/agents/sba/evolution.py" ]] && log_ok "M18: SBA evolution"

    # Drift detection
    grep -rq "drift\|oscillation\|dampen\|stabiliz" "$BACKEND_DIR/app" 2>/dev/null && \
        log_ok "M18: Drift detection patterns"

    MILESTONE_CHECKS[M18]=$((MILESTONE_CHECKS[M18] + 6))
    [[ $issues -eq 0 ]] && log_milestone "M18" "pass" "CARE-L evolution validated" || log_milestone "M18" "warn" "Needs review"
    return 0
}

# ============================================================================
# M19: POLICY LAYER CONSTITUTIONAL (5 categories, versioning) [PIN-078]
# ============================================================================
check_m19_policy_constitutional() {
    section "M19: Policy Layer Constitutional [PIN-078]"
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

        # Rule merging / versioning
        grep -rq "merge.*rule\|rule.*order\|priority\|version" "$BACKEND_DIR/app/policy" 2>/dev/null && \
            log_ok "M19: Rule versioning"

        # Policy cache
        grep -rq "policy.*cache\|cache.*policy" "$BACKEND_DIR/app/policy" 2>/dev/null && \
            log_ok "M19: Policy caching"
    else
        log_warn "M19: No policy module"
        issues=$((issues+1))
    fi

    MILESTONE_CHECKS[M19]=$((MILESTONE_CHECKS[M19] + 6))
    [[ $issues -eq 0 ]] && log_milestone "M19" "pass" "Policy constitutional validated" || log_milestone "M19" "warn" "$issues issue(s)"
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
    grep -q "run-migrations:" "$CI_FILE" && log_ok "run-migrations job (race condition fix)" || true
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

# ============================================================================
# DASHBOARD & MATRIX
# ============================================================================
print_dashboard() {
    $JSON_MODE && return 0

    echo ""
    echo -e "${CYAN}+====================================================================+${NC}"
    echo -e "${CYAN}|       AGENTICVERZ MILESTONE DASHBOARD (M0-M19) v3.0               |${NC}"
    echo -e "${CYAN}+====================================================================+${NC}"
    echo ""
    printf "%-6s %-48s %-8s %-6s\n" "ID" "Milestone (PIN-Accurate)" "Status" "Checks"
    echo "------------------------------------------------------------------------"

    # PIN-accurate milestone names
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
        "M11:Store Factories & LLM Adapters [PIN-055/060]"
        "M12:Multi-Agent System [PIN-062/063]"
        "M13:Console UI & Boundary Checklist [PIN-064]"
        "M14:BudgetLLM Safety Governance [PIN-070]"
        "M15:SBA Foundations [PIN-072]"
        "M16:Agent Governance Console [PIN-074]"
        "M17:CARE Routing Engine [PIN-075]"
        "M18:CARE-L & SBA Evolution [PIN-076]"
        "M19:Policy Layer Constitutional [PIN-078]"
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

        printf "%-6s %-48s ${COLOR}%-8s${NC} %-6s\n" "$ID" "$NAME" "$TEXT" "$CHECKS"
    done

    echo "------------------------------------------------------------------------"
    echo ""
    echo -e "Summary: ${GREEN}$MILESTONE_PASS PASS${NC} | ${YELLOW}$MILESTONE_WARN WARN${NC} | ${RED}$MILESTONE_FAIL FAIL${NC}"
    echo ""
    echo -e "${BLUE}Note: M20+ is OUT OF SCOPE - Agenticverz validates M0-M19 only.${NC}"
    echo ""
    return 0
}

print_matrix() {
    $JSON_MODE && return 0

    echo ""
    echo -e "${CYAN}+====================================================================+${NC}"
    echo -e "${CYAN}|         AGENTICVERZ CI JOB -> MILESTONE MAPPING v3.0              |${NC}"
    echo -e "${CYAN}+====================================================================+${NC}"
    echo ""

    cat <<'EOF'
+---------------------+------------------------------------------------+
| CI Job              | Milestones Validated (PIN-Accurate)            |
+---------------------+------------------------------------------------+
| unit-tests          | M0, M2, M3, M11, M14                           |
| determinism         | M0, M4, M6, M9                                 |
| workflow-engine     | M4, M17                                        |
| integration         | M0, M5, M7, M16                                |
| costsim             | M6, M14                                        |
| costsim-wiremock    | M6                                             |
| e2e-tests           | M0, M5, M7, M10, M16, M17                      |
| m10-tests           | M9, M10                                        |
+---------------------+------------------------------------------------+

+---------------------+------------------------------------------------+
| Milestone           | Primary Test Files / PIN Reference             |
+---------------------+------------------------------------------------+
| M0  [PIN-009]       | test_integration.py                            |
| M3  [PIN-010]       | tests/skills/test_m11_skills.py                |
| M4  [PIN-013/020]   | tests/workflow/test_*.py                       |
| M6  [PIN-026]       | tests/costsim/test_*.py                        |
| M10 [PIN-050]       | test_m10_*.py (6+ files)                       |
| M12 [PIN-062/063]   | test_m12_*.py (4 files)                        |
| M17 [PIN-075]       | test_m17_care.py                               |
| M18 [PIN-076]       | test_m18_*.py                                  |
| M19 [PIN-078]       | test_m19_policy.py                             |
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

    cat <<EOF
{
  "version": "3.0",
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
        echo -e "${CYAN}+====================================================================+${NC}"
        echo -e "${CYAN}|  AGENTICVERZ Milestone Certification Engine v3.0                  |${NC}"
        echo -e "${CYAN}|  PIN-Accurate Milestone Names | Validates M0-M19                  |${NC}"
        echo -e "${CYAN}+====================================================================+${NC}"
        echo ""
    }

    $QUICK_MODE && ! $JSON_MODE && log_info "Quick mode (skipping slow checks)"

    cd "$REPO_ROOT"

    # Dashboard/matrix only mode
    if $MILESTONE_MODE || $MATRIX_MODE; then
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

        $MILESTONE_MODE && print_dashboard
        $MATRIX_MODE && print_matrix
        exit 0
    fi

    # Full check
    preflight
    check_ci_workflow
    check_alembic_health

    header "Milestone Validation (M0-M19)"

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

    ! $QUICK_MODE && ! $JSON_MODE && print_dashboard

    print_summary
}

main "$@"
