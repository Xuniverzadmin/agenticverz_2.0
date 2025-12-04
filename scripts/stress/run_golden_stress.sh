#!/bin/bash
# Golden Stress Test Harness (Enhanced)
# Runs golden replay verification N times and reports any canonical diffs
# Includes Slack/webhook notifications and detailed diff capture
#
# Usage:
#   ./scripts/stress/run_golden_stress.sh                        # Run default 100x
#   ./scripts/stress/run_golden_stress.sh --iterations 500       # Custom iterations
#   ./scripts/stress/run_golden_stress.sh --workflow compute     # Specific workflow
#   ./scripts/stress/run_golden_stress.sh --parallel 4           # Parallel workers
#   ./scripts/stress/run_golden_stress.sh --slack-webhook $URL   # Report to Slack
#   ./scripts/stress/run_golden_stress.sh --nightly              # Nightly mode (7-day tracking)
#
# Environment Variables:
#   SLACK_WEBHOOK_URL     - Slack incoming webhook URL for notifications
#   PAGERDUTY_KEY         - PagerDuty routing key for critical alerts
#   OPS_WEBHOOK_URL       - Generic webhook for ops tooling
#   GOLDEN_STRESS_HISTORY - Path to store historical results (default: /var/lib/aos/stress-history)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
BACKEND_DIR="$PROJECT_ROOT/backend"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }
log_debug() { [[ "$VERBOSE" == "true" ]] && echo -e "${MAGENTA}[DEBUG]${NC} $1" || true; }

# Defaults
ITERATIONS=100
WORKFLOW="all"
PARALLEL=1
OUTPUT_DIR="/tmp/golden_stress_$(date +%Y%m%d_%H%M%S)"
FAIL_FAST=false
VERBOSE=false
NIGHTLY_MODE=false
HISTORY_DIR="${GOLDEN_STRESS_HISTORY:-/var/lib/aos/stress-history}"

# Notification settings (from env or args)
SLACK_WEBHOOK="${SLACK_WEBHOOK_URL:-}"
PAGERDUTY_KEY="${PAGERDUTY_KEY:-}"
OPS_WEBHOOK="${OPS_WEBHOOK_URL:-}"
NOTIFY_ON_SUCCESS=false
NOTIFY_ON_FAILURE=true

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --iterations|-n)
            ITERATIONS="$2"
            shift 2
            ;;
        --workflow|-w)
            WORKFLOW="$2"
            shift 2
            ;;
        --parallel|-p)
            PARALLEL="$2"
            shift 2
            ;;
        --output|-o)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --fail-fast)
            FAIL_FAST=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --nightly)
            NIGHTLY_MODE=true
            NOTIFY_ON_SUCCESS=true
            shift
            ;;
        --slack-webhook)
            SLACK_WEBHOOK="$2"
            shift 2
            ;;
        --pagerduty-key)
            PAGERDUTY_KEY="$2"
            shift 2
            ;;
        --ops-webhook)
            OPS_WEBHOOK="$2"
            shift 2
            ;;
        --notify-success)
            NOTIFY_ON_SUCCESS=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --iterations, -n N      Number of iterations (default: 100)"
            echo "  --workflow, -w NAME     Workflow to test: compute, io, llm, all (default: all)"
            echo "  --parallel, -p N        Number of parallel workers (default: 1)"
            echo "  --output, -o DIR        Output directory for results"
            echo "  --fail-fast             Stop on first failure"
            echo "  --verbose, -v           Verbose output"
            echo "  --nightly               Nightly mode with 7-day tracking and notifications"
            echo "  --slack-webhook URL     Slack webhook URL for notifications"
            echo "  --pagerduty-key KEY     PagerDuty routing key for critical alerts"
            echo "  --ops-webhook URL       Generic webhook for ops tooling"
            echo "  --notify-success        Also notify on success (default: only failures)"
            echo ""
            echo "Environment Variables:"
            echo "  SLACK_WEBHOOK_URL       Default Slack webhook"
            echo "  PAGERDUTY_KEY           Default PagerDuty key"
            echo "  OPS_WEBHOOK_URL         Default ops webhook"
            echo "  GOLDEN_STRESS_HISTORY   History directory (default: /var/lib/aos/stress-history)"
            exit 0
            ;;
        *)
            log_error "Unknown argument: $1"
            exit 1
            ;;
    esac
done

mkdir -p "$OUTPUT_DIR"
mkdir -p "$HISTORY_DIR"

log_info "Golden Stress Test Configuration:"
log_info "  Iterations: $ITERATIONS"
log_info "  Workflow: $WORKFLOW"
log_info "  Parallel: $PARALLEL"
log_info "  Output: $OUTPUT_DIR"
log_info "  Nightly Mode: $NIGHTLY_MODE"
log_info "  Slack Notifications: $([ -n "$SLACK_WEBHOOK" ] && echo 'enabled' || echo 'disabled')"

# Environment setup
export PYTHONPATH="$BACKEND_DIR:${PYTHONPATH:-}"
export DISABLE_EXTERNAL_CALLS=1

# Results tracking
TOTAL_RUNS=0
PASSED_RUNS=0
FAILED_RUNS=0
DIFF_COUNT=0
FAILURES_FILE="$OUTPUT_DIR/failures.log"
DIFFS_FILE="$OUTPUT_DIR/diffs.jsonl"
SUMMARY_FILE="$OUTPUT_DIR/summary.json"
RUN_ID="golden-stress-$(date +%Y%m%d-%H%M%S)"

touch "$FAILURES_FILE"
touch "$DIFFS_FILE"

# ============================================================================
# Notification Functions
# ============================================================================

send_slack_notification() {
    local status="$1"
    local message="$2"
    local color="$3"
    local details="${4:-}"

    if [[ -z "$SLACK_WEBHOOK" ]]; then
        log_debug "Slack webhook not configured, skipping notification"
        return 0
    fi

    local hostname=$(hostname -s 2>/dev/null || echo "unknown")
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    local payload=$(cat << EOF
{
    "attachments": [
        {
            "color": "$color",
            "title": "Golden Stress Test: $status",
            "text": "$message",
            "fields": [
                {"title": "Host", "value": "$hostname", "short": true},
                {"title": "Run ID", "value": "$RUN_ID", "short": true},
                {"title": "Workflow", "value": "$WORKFLOW", "short": true},
                {"title": "Iterations", "value": "$ITERATIONS", "short": true},
                {"title": "Passed", "value": "$PASSED_RUNS", "short": true},
                {"title": "Failed", "value": "$FAILED_RUNS", "short": true}
            ],
            "footer": "AOS Golden Stress Test",
            "ts": $(date +%s)
        }
    ]
}
EOF
)

    # Add details block if provided
    if [[ -n "$details" ]]; then
        payload=$(echo "$payload" | jq --arg details "$details" '.attachments[0].fields += [{"title": "Details", "value": $details, "short": false}]')
    fi

    curl -sf -X POST -H 'Content-type: application/json' \
        --data "$payload" \
        "$SLACK_WEBHOOK" >/dev/null 2>&1 || log_warn "Failed to send Slack notification"

    log_debug "Slack notification sent: $status"
}

send_pagerduty_alert() {
    local summary="$1"
    local severity="${2:-critical}"

    if [[ -z "$PAGERDUTY_KEY" ]]; then
        log_debug "PagerDuty key not configured, skipping alert"
        return 0
    fi

    local payload=$(cat << EOF
{
    "routing_key": "$PAGERDUTY_KEY",
    "event_action": "trigger",
    "dedup_key": "golden-stress-$RUN_ID",
    "payload": {
        "summary": "$summary",
        "severity": "$severity",
        "source": "$(hostname -s 2>/dev/null || echo 'aos-stress-test')",
        "component": "golden-stress-test",
        "group": "workflow-engine",
        "class": "stress-test-failure",
        "custom_details": {
            "run_id": "$RUN_ID",
            "workflow": "$WORKFLOW",
            "iterations": $ITERATIONS,
            "passed": $PASSED_RUNS,
            "failed": $FAILED_RUNS,
            "diff_count": $DIFF_COUNT,
            "output_dir": "$OUTPUT_DIR"
        }
    }
}
EOF
)

    curl -sf -X POST -H 'Content-type: application/json' \
        --data "$payload" \
        "https://events.pagerduty.com/v2/enqueue" >/dev/null 2>&1 || log_warn "Failed to send PagerDuty alert"

    log_info "PagerDuty alert triggered: $summary"
}

send_ops_webhook() {
    local event_type="$1"
    local data="$2"

    if [[ -z "$OPS_WEBHOOK" ]]; then
        log_debug "Ops webhook not configured, skipping"
        return 0
    fi

    local payload=$(cat << EOF
{
    "event_type": "$event_type",
    "run_id": "$RUN_ID",
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "data": $data
}
EOF
)

    curl -sf -X POST -H 'Content-type: application/json' \
        --data "$payload" \
        "$OPS_WEBHOOK" >/dev/null 2>&1 || log_warn "Failed to send ops webhook"
}

# ============================================================================
# Diff Capture Functions
# ============================================================================

capture_diff() {
    local iter="$1"
    local workflow="$2"
    local seed="$3"
    local actual_hash="$4"
    local expected_hash="$5"
    local diff_details="$6"

    ((DIFF_COUNT++))

    local diff_record=$(cat << EOF
{
    "iteration": $iter,
    "workflow": "$workflow",
    "seed": $seed,
    "actual_hash": "$actual_hash",
    "expected_hash": "$expected_hash",
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "details": "$diff_details"
}
EOF
)

    echo "$diff_record" >> "$DIFFS_FILE"
    log_warn "Canonical diff captured for iteration $iter (workflow=$workflow)"
}

# ============================================================================
# Test Execution
# ============================================================================

run_iteration() {
    local iter=$1
    local workflow=$2
    local seed=$((12345 + iter))

    local result_file="$OUTPUT_DIR/iter_${iter}_${workflow}.json"

    log_debug "Running iteration $iter for workflow $workflow (seed=$seed)"

    # Run pytest for specific test
    cd "$BACKEND_DIR"

    local test_name=""
    case "$workflow" in
        compute)
            test_name="test_compute_pipeline_100x"
            ;;
        io)
            test_name="test_io_heavy_100x"
            ;;
        llm)
            test_name="test_llm_intensive_100x"
            ;;
        all)
            test_name="test_all_workflows_stress"
            ;;
    esac

    # Run single test with specific seed via environment variable
    STRESS_ITERATIONS=1 GOLDEN_SEED=$seed python3 -m pytest \
        "tests/workflow/test_nightly_golden_stress.py::TestNightlyGoldenStress::$test_name" \
        -v --tb=short -q 2>&1 > "$result_file"

    local exit_code=$?

    # Create JSON result
    local status="passed"
    local error_msg=""
    if [[ $exit_code -ne 0 ]]; then
        status="failed"
        error_msg=$(grep -E "(FAILED|ERROR|AssertionError)" "$result_file" | head -3 | tr '\n' ' ')
    fi

    # Append JSON summary line for parsing
    echo "" >> "$result_file"
    echo "{\"iteration\": $iter, \"workflow\": \"$workflow\", \"seed\": $seed, \"status\": \"$status\", \"exit_code\": $exit_code}" >> "$result_file"

    if [[ $exit_code -eq 0 ]]; then
        log_debug "Iteration $iter passed"
        return 0
    else
        # Check for diff/mismatch errors
        if grep -qi "mismatch\|diff\|hash" "$result_file"; then
            local diff_msg=$(grep -i "mismatch\|diff\|hash" "$result_file" | head -1 | cut -c1-200)
            capture_diff "$iter" "$workflow" "$seed" "actual" "expected" "$diff_msg"
        fi

        echo "Iteration $iter ($workflow, seed=$seed): FAILED" >> "$FAILURES_FILE"
        cat "$result_file" >> "$FAILURES_FILE" 2>/dev/null || true
        echo "---" >> "$FAILURES_FILE"

        return 1
    fi
}

run_stress_test() {
    local workflow=$1
    local start_time=$(date +%s)

    log_info "Starting stress test for workflow: $workflow"

    # Send start notification for ops visibility
    send_ops_webhook "stress_test_started" "{\"workflow\": \"$workflow\", \"iterations\": $ITERATIONS}"

    if [[ "$PARALLEL" -gt 1 ]]; then
        # Parallel execution
        local pids=()
        local iter=0

        while [[ $iter -lt $ITERATIONS ]]; do
            # Launch up to $PARALLEL jobs
            for ((j=0; j<PARALLEL && iter<ITERATIONS; j++, iter++)); do
                run_iteration $iter "$workflow" &
                pids+=($!)
            done

            # Wait for batch to complete
            for pid in "${pids[@]}"; do
                wait $pid && ((PASSED_RUNS++)) || ((FAILED_RUNS++))
                ((TOTAL_RUNS++))

                if [[ "$FAIL_FAST" == "true" && $FAILED_RUNS -gt 0 ]]; then
                    log_error "Fail-fast triggered. Stopping."
                    return 1
                fi
            done
            pids=()

            # Progress update every 10 iterations
            if [[ $((iter % 10)) -eq 0 && $iter -gt 0 ]]; then
                log_info "Progress: $iter/$ITERATIONS (passed=$PASSED_RUNS, failed=$FAILED_RUNS, diffs=$DIFF_COUNT)"
            fi
        done
    else
        # Sequential execution
        for ((iter=0; iter<ITERATIONS; iter++)); do
            if run_iteration $iter "$workflow"; then
                ((PASSED_RUNS++))
            else
                ((FAILED_RUNS++))

                if [[ "$FAIL_FAST" == "true" ]]; then
                    log_error "Fail-fast triggered at iteration $iter"
                    return 1
                fi
            fi
            ((TOTAL_RUNS++))

            # Progress update every 10 iterations
            if [[ $((iter % 10)) -eq 0 && $iter -gt 0 ]]; then
                log_info "Progress: $iter/$ITERATIONS (passed=$PASSED_RUNS, failed=$FAILED_RUNS, diffs=$DIFF_COUNT)"
            fi
        done
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log_info "Completed $TOTAL_RUNS iterations in ${duration}s"
}

generate_summary() {
    local end_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local success_rate=0
    local duration_seconds=$(($(date +%s) - START_TIMESTAMP))

    if [[ $TOTAL_RUNS -gt 0 ]]; then
        success_rate=$(echo "scale=4; $PASSED_RUNS / $TOTAL_RUNS * 100" | bc 2>/dev/null || echo "0")
    fi

    cat > "$SUMMARY_FILE" << EOF
{
    "run_id": "$RUN_ID",
    "test_run": {
        "start_time": "$START_TIME",
        "end_time": "$end_time",
        "duration_seconds": $duration_seconds,
        "workflow": "$WORKFLOW",
        "iterations": $ITERATIONS,
        "parallel_workers": $PARALLEL,
        "nightly_mode": $NIGHTLY_MODE
    },
    "results": {
        "total_runs": $TOTAL_RUNS,
        "passed": $PASSED_RUNS,
        "failed": $FAILED_RUNS,
        "diff_count": $DIFF_COUNT,
        "success_rate_percent": $success_rate
    },
    "files": {
        "failures_log": "$FAILURES_FILE",
        "diffs_log": "$DIFFS_FILE",
        "output_dir": "$OUTPUT_DIR"
    },
    "environment": {
        "hostname": "$(hostname -s 2>/dev/null || echo 'unknown')",
        "python_version": "$(python3 --version 2>&1 | cut -d' ' -f2)"
    }
}
EOF

    log_info "Summary written to: $SUMMARY_FILE"

    # Store in history for nightly tracking
    if [[ "$NIGHTLY_MODE" == "true" ]]; then
        local history_file="$HISTORY_DIR/$(date +%Y-%m-%d).json"
        cp "$SUMMARY_FILE" "$history_file"
        log_info "History saved to: $history_file"

        # Check 7-day trend
        check_7day_trend
    fi
}

check_7day_trend() {
    log_info "Checking 7-day trend..."

    local days_with_failures=0
    local total_days=0

    for i in {0..6}; do
        local date_str=$(date -d "$i days ago" +%Y-%m-%d 2>/dev/null || date -v-${i}d +%Y-%m-%d 2>/dev/null || continue)
        local history_file="$HISTORY_DIR/${date_str}.json"

        if [[ -f "$history_file" ]]; then
            ((total_days++))
            local failures=$(jq -r '.results.failed // 0' "$history_file" 2>/dev/null || echo "0")
            if [[ "$failures" -gt 0 ]]; then
                ((days_with_failures++))
            fi
        fi
    done

    if [[ $total_days -gt 0 ]]; then
        log_info "7-day trend: $days_with_failures days with failures out of $total_days days tracked"

        if [[ $days_with_failures -eq 0 && $total_days -ge 7 ]]; then
            log_info "✅ GATE PASSED: 7 consecutive days with 0 canonical diffs!"
            send_slack_notification "7-Day Gate PASSED" \
                "Golden stress tests have passed for 7 consecutive days with 0 canonical diffs. Ready for canary rollout." \
                "good"
        elif [[ $days_with_failures -gt 3 ]]; then
            log_warn "⚠️ High failure rate: $days_with_failures out of $total_days days had failures"
        fi
    fi
}

send_final_notification() {
    local status="$1"

    if [[ "$status" == "passed" ]]; then
        if [[ "$NOTIFY_ON_SUCCESS" == "true" ]]; then
            send_slack_notification "PASSED ✅" \
                "All $TOTAL_RUNS iterations passed with 0 canonical diffs." \
                "good"
        fi

        send_ops_webhook "stress_test_completed" "{\"status\": \"passed\", \"total\": $TOTAL_RUNS, \"passed\": $PASSED_RUNS}"

    else
        local failure_sample=""
        if [[ -f "$FAILURES_FILE" ]]; then
            failure_sample=$(head -5 "$FAILURES_FILE" | tr '\n' ' ' | cut -c1-200)
        fi

        send_slack_notification "FAILED ❌" \
            "$FAILED_RUNS failures out of $TOTAL_RUNS iterations. $DIFF_COUNT canonical diffs detected." \
            "danger" \
            "$failure_sample"

        send_ops_webhook "stress_test_completed" "{\"status\": \"failed\", \"total\": $TOTAL_RUNS, \"failed\": $FAILED_RUNS, \"diffs\": $DIFF_COUNT}"

        # Trigger PagerDuty for critical failures in nightly mode
        if [[ "$NIGHTLY_MODE" == "true" && $DIFF_COUNT -gt 0 ]]; then
            send_pagerduty_alert "Golden Stress Test: $DIFF_COUNT canonical diffs detected" "warning"
        fi
    fi
}

# ============================================================================
# Main Execution
# ============================================================================

START_TIMESTAMP=$(date +%s)
START_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

main() {
    log_info "Starting golden stress test at $START_TIME"
    log_info "Run ID: $RUN_ID"

    # Send start notification
    if [[ -n "$SLACK_WEBHOOK" ]]; then
        send_slack_notification "STARTED" \
            "Golden stress test started with $ITERATIONS iterations for workflow '$WORKFLOW'." \
            "#439FE0"
    fi

    # Run the stress test
    if [[ "$WORKFLOW" == "all" ]]; then
        for wf in compute io llm; do
            run_stress_test "$wf"
        done
    else
        run_stress_test "$WORKFLOW"
    fi

    # Generate summary
    generate_summary

    # Final report
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "              GOLDEN STRESS TEST REPORT"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "  Run ID:        $RUN_ID"
    echo "  Workflow:      $WORKFLOW"
    echo "  Iterations:    $ITERATIONS"
    echo ""
    echo "  Total Runs:    $TOTAL_RUNS"
    echo "  Passed:        $PASSED_RUNS"
    echo "  Failed:        $FAILED_RUNS"
    echo "  Diffs:         $DIFF_COUNT"
    echo ""

    if [[ $FAILED_RUNS -gt 0 ]]; then
        log_error "STRESS TEST FAILED"
        echo ""
        echo "Failures logged to: $FAILURES_FILE"
        echo "Diffs logged to:    $DIFFS_FILE"
        echo ""
        echo "Sample failures:"
        echo "────────────────────────────────────────"
        head -20 "$FAILURES_FILE"
        echo ""

        send_final_notification "failed"
        exit 1
    else
        log_info "STRESS TEST PASSED ✅"
        echo ""
        echo "All iterations completed successfully with 0 canonical diffs."

        send_final_notification "passed"
        exit 0
    fi
}

main
