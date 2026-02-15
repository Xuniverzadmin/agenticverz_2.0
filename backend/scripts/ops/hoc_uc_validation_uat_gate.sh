#!/usr/bin/env bash
# Layer: SCRIPT
# AUDIENCE: INTERNAL
# Role: Unified UC validation + UAT gate — runs all backend and frontend checks
# artifact_class: CODE
# Reference: UC_CODEBASE_ELICITATION_VALIDATION_UAT_TASKPACK_2026-02-15
#
# Usage: ./scripts/ops/hoc_uc_validation_uat_gate.sh
# Exit: 0 only when ALL stages pass

set -euo pipefail

BACKEND_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
WEBSITE_DIR="$(cd "$BACKEND_DIR/../website/app-shell" && pwd)"

PASS=0
FAIL=0
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

# ============================================================
# STAGE 1: Backend Deterministic Gate Pack
# ============================================================

cd "$BACKEND_DIR"

run_stage "CI Hygiene Checks" \
    python3 -c "
import subprocess, sys
result = subprocess.run(
    [sys.executable, 'scripts/ci/check_init_hygiene.py', '--ci'],
    env={**__import__('os').environ, 'PYTHONPATH': '.'},
    capture_output=True, text=True
)
print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
if result.returncode != 0:
    print(result.stderr[-500:] if result.stderr else '')
sys.exit(result.returncode)
"

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

if [ -d "$WEBSITE_DIR" ]; then
    cd "$WEBSITE_DIR"

    run_stage "App-Shell: Hygiene CI" \
        npm run hygiene:ci

    run_stage "App-Shell: Boundary CI" \
        npm run boundary:ci

    run_stage "App-Shell: TypeCheck" \
        npm run typecheck

    run_stage "App-Shell: Build" \
        npm run build
else
    RESULTS+=("SKIP  App-Shell (directory not found: $WEBSITE_DIR)")
fi

# ============================================================
# STAGE 5: Playwright Tests
# ============================================================

if [ -d "$WEBSITE_DIR/tests/bit" ]; then
    cd "$WEBSITE_DIR"

    run_stage "Playwright: BIT" \
        npx playwright test --config tests/bit/playwright.config.ts

    run_stage "Playwright: UAT" \
        npx playwright test --config tests/uat/playwright.config.ts
else
    RESULTS+=("SKIP  Playwright (tests directory not found)")
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
echo "TOTAL: $PASS passed, $FAIL failed"
echo ""

if [ "$FAIL" -gt 0 ]; then
    echo "GATE: FAILED"
    exit 1
else
    echo "GATE: PASSED"
    exit 0
fi
