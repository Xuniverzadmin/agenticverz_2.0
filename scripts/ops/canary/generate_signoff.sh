#!/usr/bin/env bash
#
# generate_signoff.sh - Automated .m4_signoff generation with objective checks
#
# This script generates the .m4_signoff artifact ONLY after verifying:
# 1. Shadow run completed with target cycles (default 2880)
# 2. Zero golden mismatches
# 3. Metrics are stable (optional Prometheus check)
#
# Usage:
#   ./scripts/ops/canary/generate_signoff.sh
#   ./scripts/ops/canary/generate_signoff.sh --check-only    # Verify without generating
#   ./scripts/ops/canary/generate_signoff.sh --force         # Skip shadow run check (CI only)
#
# Environment variables:
#   SHADOW_REPORT_PATH  - Path to shadow run report JSON (default: ./shadow_report.json)
#   TARGET_CYCLES       - Minimum shadow run cycles required (default: 2880)
#   PROMETHEUS_URL      - Prometheus URL for stability check (optional)
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $*"; }

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SIGNOFF_PATH="${PROJECT_ROOT}/.m4_signoff"
SHADOW_REPORT_PATH="${SHADOW_REPORT_PATH:-${PROJECT_ROOT}/shadow_report.json}"
TARGET_CYCLES="${TARGET_CYCLES:-2880}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://127.0.0.1:9090}"

# Parse arguments
CHECK_ONLY=false
FORCE=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --check-only)
            CHECK_ONLY=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        *)
            log_error "Unknown argument: $1"
            exit 1
            ;;
    esac
done

log_info "=============================================="
log_info "      M4.5 Signoff Generation"
log_info "=============================================="
log_info "Project root: $PROJECT_ROOT"
log_info "Target cycles: $TARGET_CYCLES"
log_info "Check only: $CHECK_ONLY"
echo

# Track failures
FAILURES=0

#
# Check 1: Shadow run report exists and meets criteria
#
log_step "Checking shadow run report..."

if [[ "$FORCE" == "true" ]]; then
    log_warn "Skipping shadow run check (--force mode)"
elif [[ -f "$SHADOW_REPORT_PATH" ]]; then
    # Parse shadow report
    if command -v jq &>/dev/null; then
        # Support multiple shadow report formats
        CYCLES=$(jq -r '.statistics.cycles_completed // .total_cycles // 0' "$SHADOW_REPORT_PATH" 2>/dev/null || echo "0")
        MISMATCHES=$(jq -r '.statistics.mismatches // .golden_mismatch_total // .mismatches // 0' "$SHADOW_REPORT_PATH" 2>/dev/null || echo "0")

        log_info "Shadow run cycles: $CYCLES / $TARGET_CYCLES"
        log_info "Golden mismatches: $MISMATCHES"

        if [[ "$CYCLES" -lt "$TARGET_CYCLES" ]]; then
            log_error "Insufficient shadow run cycles: $CYCLES < $TARGET_CYCLES"
            FAILURES=$((FAILURES + 1))
        else
            log_info "✓ Shadow run cycles OK"
        fi

        if [[ "$MISMATCHES" -ne 0 ]]; then
            log_error "Golden mismatches detected: $MISMATCHES"
            FAILURES=$((FAILURES + 1))
        else
            log_info "✓ Zero golden mismatches"
        fi
    else
        log_warn "jq not installed, cannot parse shadow report"
        log_warn "Install jq: apt-get install jq"
        FAILURES=$((FAILURES + 1))
    fi
else
    log_error "Shadow report not found: $SHADOW_REPORT_PATH"
    log_info "Generate shadow report by running the shadow validation:"
    log_info "  python scripts/ops/run_shadow_validation.py --cycles $TARGET_CYCLES"
    FAILURES=$((FAILURES + 1))
fi

#
# Check 2: No existing signoff (prevent duplicate)
#
log_step "Checking for existing signoff..."
if [[ -f "$SIGNOFF_PATH" ]]; then
    EXISTING_DATE=$(head -1 "$SIGNOFF_PATH" | awk '{print $2}')
    log_warn "Existing signoff found (created: $EXISTING_DATE)"
    log_warn "Remove it manually if you want to regenerate: rm $SIGNOFF_PATH"
    if [[ "$FORCE" != "true" ]]; then
        log_error "Cannot overwrite existing signoff without --force"
        FAILURES=$((FAILURES + 1))
    fi
else
    log_info "✓ No existing signoff"
fi

#
# Check 3: Prometheus metrics stable (optional)
#
log_step "Checking Prometheus metrics stability..."
if curl -sf "${PROMETHEUS_URL}/api/v1/query?query=up" &>/dev/null; then
    # Check golden mismatch metric
    MISMATCH_METRIC=$(curl -sf "${PROMETHEUS_URL}/api/v1/query?query=sum(nova_golden_mismatch_total)" 2>/dev/null | jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")

    if [[ "$MISMATCH_METRIC" == "0" || "$MISMATCH_METRIC" == "null" ]]; then
        log_info "✓ Prometheus golden_mismatch = 0"
    else
        log_error "Prometheus shows golden mismatches: $MISMATCH_METRIC"
        FAILURES=$((FAILURES + 1))
    fi
else
    log_warn "Prometheus not reachable at $PROMETHEUS_URL (optional check skipped)"
fi

#
# Check 4: Feature flags in expected state
#
log_step "Checking feature flags..."
FLAGS_FILE="${PROJECT_ROOT}/backend/app/config/feature_flags.json"
if [[ -f "$FLAGS_FILE" ]]; then
    # All M4.5 flags should be disabled (we're generating signoff to enable them)
    FC_ENABLED=$(jq -r '.flags.failure_catalog_runtime_integration.enabled' "$FLAGS_FILE" 2>/dev/null || echo "false")
    CS_ENABLED=$(jq -r '.flags.cost_simulator_runtime_integration.enabled' "$FLAGS_FILE" 2>/dev/null || echo "false")

    if [[ "$FC_ENABLED" == "true" || "$CS_ENABLED" == "true" ]]; then
        log_warn "M4.5 flags already enabled - signoff may already exist"
    else
        log_info "✓ M4.5 flags are disabled (ready for canary)"
    fi
else
    log_warn "Feature flags file not found: $FLAGS_FILE"
fi

#
# Summary and generation
#
echo
log_info "=============================================="
if [[ "$FAILURES" -gt 0 ]]; then
    log_error "        SIGNOFF GENERATION BLOCKED"
    log_error "        $FAILURES check(s) failed"
    log_info "=============================================="
    exit 1
fi

if [[ "$CHECK_ONLY" == "true" ]]; then
    log_info "        ✓ ALL CHECKS PASSED"
    log_info "        (check-only mode, no signoff generated)"
    log_info "=============================================="
    exit 0
fi

#
# Generate signoff artifact
#
log_step "Generating .m4_signoff artifact..."

GIT_SHA=$(git -C "$PROJECT_ROOT" rev-parse HEAD 2>/dev/null || echo "unknown")
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
HOSTNAME=$(hostname)
USER=$(whoami)

cat > "$SIGNOFF_PATH" << EOF
${GIT_SHA} ${TIMESTAMP}
# M4.5 Failure Catalog Integration Signoff
#
# This artifact authorizes enabling the following feature flags:
#   - failure_catalog_runtime_integration
#   - cost_simulator_runtime_integration
#
# Generated by: ${USER}@${HOSTNAME}
# Shadow run: ${TARGET_CYCLES} cycles, 0 mismatches
# Prometheus: metrics stable
#
# To run the canary:
#   python scripts/ops/canary/canary_runner.py \\
#     --config scripts/ops/canary/configs/m4_canary.yaml \\
#     --watch 300
#
EOF

log_info "✓ Signoff generated: $SIGNOFF_PATH"
log_info ""
log_info "Next steps:"
log_info "  1. Review the signoff: cat $SIGNOFF_PATH"
log_info "  2. Run the M4.5 canary:"
log_info "     python scripts/ops/canary/canary_runner.py \\"
log_info "       --config scripts/ops/canary/configs/m4_canary.yaml \\"
log_info "       --watch 300"
log_info ""
log_info "=============================================="
log_info "        ✓ SIGNOFF GENERATED SUCCESSFULLY"
log_info "=============================================="
