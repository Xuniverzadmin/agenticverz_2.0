#!/usr/bin/env bash
# Layer: SCRIPT
# AUDIENCE: INTERNAL
# Role: Unified UC validation + UAT gate — runs all backend and frontend checks
# artifact_class: CODE
# Reference: UC_UAT_FINDINGS_CLEARANCE_DETOUR_PLAN_2026-02-15
#
# Run from repo root:   backend/scripts/ops/hoc_uc_validation_uat_gate.sh
# Run from backend/:    ./scripts/ops/hoc_uc_validation_uat_gate.sh
#
# Exit: 0 only when ALL blocking stages pass

set -uo pipefail

BACKEND_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
WEBSITE_DIR="$(cd "$BACKEND_DIR/../website/app-shell" 2>/dev/null && pwd)" || WEBSITE_DIR=""

PASS=0
FAIL=0
WARN=0
RESULTS=()

run_stage() {
    local name="$1"
    shift
    echo ""
    echo "============================================================"
    echo "STAGE: $name"
    echo "============================================================"
    if "$@" 2>&1; then
        RESULTS+=("PASS  $name")
        PASS=$((PASS + 1))
    else
        RESULTS+=("FAIL  $name")
        FAIL=$((FAIL + 1))
    fi
}

run_stage_nonblocking() {
    local name="$1"
    shift
    echo ""
    echo "============================================================"
    echo "STAGE (non-blocking): $name"
    echo "============================================================"
    if "$@" 2>&1; then
        RESULTS+=("PASS  $name (non-blocking)")
        PASS=$((PASS + 1))
    else
        RESULTS+=("WARN  $name (non-blocking, informational only)")
        WARN=$((WARN + 1))
    fi
}

# ============================================================
# STAGE 1: Backend Deterministic Gate Pack
# ============================================================

cd "$BACKEND_DIR"
export PYTHONPATH="${BACKEND_DIR}"

run_stage "CI Hygiene Checks" \
    python3 scripts/ci/check_init_hygiene.py --ci

run_stage "UC Operation Manifest Validator" \
    python3 scripts/verification/uc_operation_manifest_check.py --strict

# ============================================================
# STAGE 2: Governance Tests (mapping + manifest integrity)
# ============================================================

run_stage "Governance: UC Mapping Decision Table" \
    python3 -m pytest tests/governance/t4/test_uc_mapping_decision_table.py -v --tb=short

run_stage "Governance: UC Operation Manifest Integrity" \
    python3 -m pytest tests/governance/t4/test_uc_operation_manifest_integrity.py -v --tb=short

# ============================================================
# STAGE 3: UAT Backend Scenario Tests
# ============================================================

run_stage "UAT: UC-002 Onboarding Flow" \
    python3 -m pytest tests/uat/test_uc002_onboarding_flow.py -v --tb=short

run_stage "UAT: UC-004 Controls Evidence" \
    python3 -m pytest tests/uat/test_uc004_controls_evidence.py -v --tb=short

run_stage "UAT: UC-006 Signal Feedback Flow" \
    python3 -m pytest tests/uat/test_uc006_signal_feedback_flow.py -v --tb=short

run_stage "UAT: UC-008 Analytics Artifacts" \
    python3 -m pytest tests/uat/test_uc008_analytics_artifacts.py -v --tb=short

run_stage "UAT: UC-017 Trace Replay Integrity" \
    python3 -m pytest tests/uat/test_uc017_trace_replay_integrity.py -v --tb=short

run_stage "UAT: UC-032 Redaction Export Safety" \
    python3 -m pytest tests/uat/test_uc032_redaction_export_safety.py -v --tb=short

# ============================================================
# STAGE 4: App-Shell Guardrails
# ============================================================

if [ -n "$WEBSITE_DIR" ] && [ -d "$WEBSITE_DIR" ]; then
    cd "$WEBSITE_DIR"

    run_stage "App-Shell: Hygiene CI" \
        npm run hygiene:ci

    run_stage "App-Shell: Boundary CI" \
        npm run boundary:ci

    # UAT-scoped typecheck (BLOCKING — only UAT feature files)
    run_stage "App-Shell: TypeCheck UAT" \
        npm run typecheck:uat

    # Global typecheck (NON-BLOCKING — pre-existing debt, informational)
    run_stage_nonblocking "App-Shell: TypeCheck Global (debt report)" \
        npm run typecheck

    run_stage "App-Shell: Build" \
        npm run build
else
    echo ""
    echo "WARNING: App-Shell directory not found at expected path."
    echo "  Expected: $BACKEND_DIR/../website/app-shell"
    echo "  Action:   Ensure website/app-shell exists relative to backend/"
    RESULTS+=("FAIL  App-Shell (directory not found)")
    FAIL=$((FAIL + 1))
fi

# ============================================================
# STAGE 5: Playwright Tests
# ============================================================

if [ -n "$WEBSITE_DIR" ] && [ -d "$WEBSITE_DIR/tests" ]; then
    cd "$WEBSITE_DIR"

    # Check if Playwright browsers are installed
    if npx playwright --version >/dev/null 2>&1; then
        PLAYWRIGHT_AVAILABLE=true
    else
        PLAYWRIGHT_AVAILABLE=false
    fi

    if [ "$PLAYWRIGHT_AVAILABLE" = true ]; then
        # Check if browsers are installed
        if npx playwright test --config tests/uat/playwright.config.ts --list >/dev/null 2>&1; then
            run_stage "Playwright: BIT" \
                npx playwright test --config tests/bit/playwright.config.ts

            run_stage "Playwright: UAT" \
                npx playwright test --config tests/uat/playwright.config.ts
        else
            echo ""
            echo "ERROR: Playwright browsers not installed."
            echo "  Action: Run 'npx playwright install chromium' in website/app-shell/"
            RESULTS+=("FAIL  Playwright: Browsers not installed (run: npx playwright install chromium)")
            FAIL=$((FAIL + 1))
        fi
    else
        echo ""
        echo "ERROR: @playwright/test not found in devDependencies."
        echo "  Action: Run 'npm install --save-dev @playwright/test' in website/app-shell/"
        RESULTS+=("FAIL  Playwright: Package not installed (run: npm install --save-dev @playwright/test)")
        FAIL=$((FAIL + 1))
    fi
else
    echo ""
    echo "WARNING: Playwright tests directory not found."
    RESULTS+=("FAIL  Playwright (tests directory not found)")
    FAIL=$((FAIL + 1))
fi

# ============================================================
# SUMMARY
# ============================================================

echo ""
echo "============================================================"
echo "UC VALIDATION UAT GATE — SUMMARY"
echo "============================================================"

for r in "${RESULTS[@]}"; do
    echo "  $r"
done

echo ""
echo "TOTAL: $PASS passed, $FAIL failed, $WARN warnings (non-blocking)"
echo ""

if [ "$FAIL" -gt 0 ]; then
    echo "GATE: FAILED"
    exit 1
else
    echo "GATE: PASSED"
    exit 0
fi
