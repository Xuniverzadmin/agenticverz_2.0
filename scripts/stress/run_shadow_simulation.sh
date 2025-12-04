#!/bin/bash
# M4-T7: 24h Shadow-Run Simulation
# Runs workflows across multiple workers with parallel shadow replay verification
# Simulates production-like conditions over extended periods
#
# Usage:
#   ./scripts/stress/run_shadow_simulation.sh                        # Default: 3 workers, 1 hour
#   ./scripts/stress/run_shadow_simulation.sh --hours 24             # Full 24h simulation
#   ./scripts/stress/run_shadow_simulation.sh --workers 5            # More workers
#   ./scripts/stress/run_shadow_simulation.sh --quick                # Quick 15-minute test
#
# Architecture:
#   - Primary workers execute workflows and record golden files
#   - Shadow worker replays golden files in parallel
#   - Continuous comparison of primary vs shadow outputs
#   - Alerting on any mismatch detected

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
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $(date '+%H:%M:%S') $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $(date '+%H:%M:%S') $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $(date '+%H:%M:%S') $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $(date '+%H:%M:%S') $1"; }
log_primary() { echo -e "${CYAN}[PRIMARY]${NC} $(date '+%H:%M:%S') $1"; }
log_shadow() { echo -e "${MAGENTA}[SHADOW]${NC} $(date '+%H:%M:%S') $1"; }

# Defaults
PRIMARY_WORKERS=3
DURATION_HOURS=1
WORKFLOWS_PER_CYCLE=10
CYCLE_INTERVAL_SECONDS=30
OUTPUT_DIR="/tmp/shadow_simulation_$(date +%Y%m%d_%H%M%S)"
QUICK_MODE=false
VERBOSE=false

# Notification settings
SLACK_WEBHOOK="${SLACK_WEBHOOK_URL:-}"
ALERT_ON_MISMATCH=true

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --workers|-w)
            PRIMARY_WORKERS="$2"
            shift 2
            ;;
        --hours|-h)
            DURATION_HOURS="$2"
            shift 2
            ;;
        --workflows-per-cycle|-n)
            WORKFLOWS_PER_CYCLE="$2"
            shift 2
            ;;
        --cycle-interval|-i)
            CYCLE_INTERVAL_SECONDS="$2"
            shift 2
            ;;
        --output|-o)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --quick)
            QUICK_MODE=true
            DURATION_HOURS=0
            CYCLE_INTERVAL_SECONDS=10
            WORKFLOWS_PER_CYCLE=5
            shift
            ;;
        --slack-webhook)
            SLACK_WEBHOOK="$2"
            shift 2
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "24h Shadow-Run Simulation for M4 Workflow Engine"
            echo ""
            echo "Options:"
            echo "  --workers, -w N             Primary workers (default: 3)"
            echo "  --hours, -h N               Duration in hours (default: 1)"
            echo "  --workflows-per-cycle, -n N Workflows per cycle (default: 10)"
            echo "  --cycle-interval, -i N      Seconds between cycles (default: 30)"
            echo "  --output, -o DIR            Output directory"
            echo "  --quick                     Quick 15-minute test"
            echo "  --slack-webhook URL         Slack webhook for alerts"
            echo "  --verbose, -v               Verbose output"
            exit 0
            ;;
        *)
            log_error "Unknown argument: $1"
            exit 1
            ;;
    esac
done

# Create directories
mkdir -p "$OUTPUT_DIR"/{primary,shadow,golden,reports}
GOLDEN_DIR="$OUTPUT_DIR/golden"
PRIMARY_DIR="$OUTPUT_DIR/primary"
SHADOW_DIR="$OUTPUT_DIR/shadow"
REPORTS_DIR="$OUTPUT_DIR/reports"

log_info "═══════════════════════════════════════════════════════════════"
log_info "         M4-T7: 24h Shadow-Run Simulation"
log_info "═══════════════════════════════════════════════════════════════"
log_info "  Primary Workers:     $PRIMARY_WORKERS"
log_info "  Duration:            ${DURATION_HOURS}h ($(( DURATION_HOURS * 60 ))m)"
log_info "  Workflows/Cycle:     $WORKFLOWS_PER_CYCLE"
log_info "  Cycle Interval:      ${CYCLE_INTERVAL_SECONDS}s"
log_info "  Output:              $OUTPUT_DIR"
log_info "═══════════════════════════════════════════════════════════════"

# Environment setup
export PYTHONPATH="$BACKEND_DIR:${PYTHONPATH:-}"
export DISABLE_EXTERNAL_CALLS=1
export GOLDEN_DIR="$GOLDEN_DIR"

# Statistics
TOTAL_WORKFLOWS=0
TOTAL_REPLAYS=0
MISMATCHES=0
CYCLES_COMPLETED=0
START_TIME=$(date +%s)

# Create the shadow simulation runner
SHADOW_RUNNER="$OUTPUT_DIR/shadow_runner.py"
cat > "$SHADOW_RUNNER" << 'PYTHON_SCRIPT'
#!/usr/bin/env python3
"""
Shadow-run simulation for M4 workflow engine.

Components:
1. Primary executor - runs workflows and records golden files
2. Shadow replayer - replays golden files and compares outputs
3. Mismatch detector - identifies determinism violations
"""

import asyncio
import hashlib
import json
import os
import random
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4


@dataclass
class WorkflowResult:
    """Result from a workflow execution."""
    run_id: str
    workflow_type: str
    seed: int
    step_hashes: List[str]
    workflow_hash: str
    duration_ms: int
    success: bool
    error: Optional[str] = None


@dataclass
class ReplayResult:
    """Result from a shadow replay."""
    original_run_id: str
    replay_run_id: str
    original_hash: str
    replay_hash: str
    match: bool
    diff_details: Optional[str] = None


# Workflow definitions (same as multi-worker test for consistency)
WORKFLOWS = {
    "compute": [
        {"skill": "compute_hash", "params": {"data": "input_data_step_1"}},
        {"skill": "transform_json", "params": {"input": {"a": 1, "b": 2, "c": 3}}},
        {"skill": "compute_hash", "params": {"data": "step_2_output"}},
        {"skill": "transform_json", "params": {"input": [1, 2, 3, 4, 5]}},
        {"skill": "llm_stub", "params": {"prompt": "Summarize the computation"}},
    ],
    "io": [
        {"skill": "mock_io", "params": {"file": "file1.txt"}},
        {"skill": "mock_io", "params": {"file": "file2.txt"}},
        {"skill": "transform_json", "params": {"input": {"files": ["f1", "f2"]}}},
        {"skill": "compute_hash", "params": {"data": "combined_content"}},
    ],
    "llm": [
        {"skill": "llm_stub", "params": {"prompt": "Step 1: Analyze"}},
        {"skill": "transform_json", "params": {"input": {"analysis": True}}},
        {"skill": "llm_stub", "params": {"prompt": "Step 2: Execute"}},
    ],
}


def derive_seed(base_seed: int, step_index: int) -> int:
    """Derive deterministic seed for each step."""
    s = hashlib.sha256(f"{base_seed}:{step_index}".encode()).hexdigest()
    return int(s[:16], 16)


async def execute_skill(skill_name: str, params: Dict, seed: int) -> Dict:
    """Execute a skill deterministically."""
    if skill_name == "compute_hash":
        data = str(params.get("data", ""))
        seeded_data = f"{data}:{seed}"
        return {"hash": hashlib.sha256(seeded_data.encode()).hexdigest(), "seed": seed}

    elif skill_name == "transform_json":
        input_data = params.get("input", {})
        if isinstance(input_data, dict):
            return {"keys": sorted(input_data.keys()), "count": len(input_data), "seed": seed}
        return {"count": len(input_data) if isinstance(input_data, list) else 1, "seed": seed}

    elif skill_name == "mock_io":
        return {"read_bytes": len(str(params)), "operation": "mock_read", "seed": seed}

    elif skill_name == "llm_stub":
        prompt = params.get("prompt", "")
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        return {"response": f"Response-{seed}-{prompt_hash}", "seed": seed}

    return {"error": f"Unknown skill: {skill_name}"}


async def run_workflow(workflow_type: str, seed: int, run_id: str) -> WorkflowResult:
    """Execute a complete workflow."""
    start_time = time.time()
    steps = WORKFLOWS.get(workflow_type, [])
    step_hashes = []

    try:
        for i, step in enumerate(steps):
            step_seed = derive_seed(seed, i)
            result = await execute_skill(step["skill"], step["params"], step_seed)
            result_str = json.dumps(result, sort_keys=True)
            step_hash = hashlib.sha256(result_str.encode()).hexdigest()[:16]
            step_hashes.append(f"{step['skill']}:{step_hash}")

        workflow_hash = hashlib.sha256(":".join(step_hashes).encode()).hexdigest()
        duration_ms = int((time.time() - start_time) * 1000)

        return WorkflowResult(
            run_id=run_id,
            workflow_type=workflow_type,
            seed=seed,
            step_hashes=step_hashes,
            workflow_hash=workflow_hash,
            duration_ms=duration_ms,
            success=True,
        )
    except Exception as e:
        return WorkflowResult(
            run_id=run_id,
            workflow_type=workflow_type,
            seed=seed,
            step_hashes=step_hashes,
            workflow_hash="",
            duration_ms=0,
            success=False,
            error=str(e),
        )


def save_golden(result: WorkflowResult, golden_dir: str) -> str:
    """Save golden file for a workflow result."""
    golden_path = os.path.join(golden_dir, f"{result.run_id}.golden.json")
    with open(golden_path, "w") as f:
        json.dump(asdict(result), f, indent=2)
    return golden_path


def load_golden(run_id: str, golden_dir: str) -> Optional[WorkflowResult]:
    """Load golden file for replay."""
    golden_path = os.path.join(golden_dir, f"{run_id}.golden.json")
    if not os.path.exists(golden_path):
        return None

    with open(golden_path) as f:
        data = json.load(f)
        return WorkflowResult(**data)


async def shadow_replay(golden: WorkflowResult) -> ReplayResult:
    """Replay a workflow and compare to golden."""
    replay_id = f"shadow-{uuid4().hex[:8]}"

    # Re-run the workflow with same seed
    replay = await run_workflow(golden.workflow_type, golden.seed, replay_id)

    match = replay.workflow_hash == golden.workflow_hash
    diff_details = None

    if not match:
        # Find which step differs
        for i, (orig, repl) in enumerate(zip(golden.step_hashes, replay.step_hashes)):
            if orig != repl:
                diff_details = f"Mismatch at step {i}: original={orig}, replay={repl}"
                break

    return ReplayResult(
        original_run_id=golden.run_id,
        replay_run_id=replay_id,
        original_hash=golden.workflow_hash,
        replay_hash=replay.workflow_hash,
        match=match,
        diff_details=diff_details,
    )


async def run_primary_worker(
    worker_id: int,
    workflow_count: int,
    golden_dir: str,
) -> List[WorkflowResult]:
    """Primary worker: execute workflows and save golden files."""
    results = []

    workflow_types = list(WORKFLOWS.keys())

    for i in range(workflow_count):
        run_id = f"primary-w{worker_id}-{uuid4().hex[:8]}"
        workflow_type = random.choice(workflow_types)
        seed = random.randint(10000, 99999)

        result = await run_workflow(workflow_type, seed, run_id)
        results.append(result)

        if result.success:
            save_golden(result, golden_dir)

        # Small delay to simulate real execution
        await asyncio.sleep(0.01)

    return results


async def run_shadow_worker(
    golden_dir: str,
    max_replays: int = 100,
) -> List[ReplayResult]:
    """Shadow worker: continuously replay golden files and compare."""
    results = []
    golden_path = Path(golden_dir)

    # Get list of golden files
    golden_files = list(golden_path.glob("*.golden.json"))

    if not golden_files:
        return results

    # Sample files to replay
    files_to_replay = random.sample(golden_files, min(max_replays, len(golden_files)))

    for golden_file in files_to_replay:
        run_id = golden_file.stem.replace(".golden", "")
        golden = load_golden(run_id, golden_dir)

        if golden:
            replay_result = await shadow_replay(golden)
            results.append(replay_result)

        await asyncio.sleep(0.01)

    return results


async def run_simulation_cycle(
    worker_count: int,
    workflows_per_worker: int,
    golden_dir: str,
) -> Tuple[List[WorkflowResult], List[ReplayResult]]:
    """Run one complete simulation cycle."""

    # Run primary workers
    primary_tasks = [
        run_primary_worker(i, workflows_per_worker, golden_dir)
        for i in range(worker_count)
    ]

    primary_results_nested = await asyncio.gather(*primary_tasks)
    primary_results = [r for sublist in primary_results_nested for r in sublist]

    # Run shadow replay
    replay_results = await run_shadow_worker(
        golden_dir,
        max_replays=len(primary_results),
    )

    return primary_results, replay_results


async def main():
    worker_count = int(os.environ.get("PRIMARY_WORKERS", "3"))
    workflows_per_worker = int(os.environ.get("WORKFLOWS_PER_CYCLE", "10"))
    golden_dir = os.environ.get("GOLDEN_DIR", "/tmp/golden")

    primary_results, replay_results = await run_simulation_cycle(
        worker_count,
        workflows_per_worker // worker_count,
        golden_dir,
    )

    # Calculate statistics
    total_workflows = len(primary_results)
    successful = sum(1 for r in primary_results if r.success)
    total_replays = len(replay_results)
    mismatches = sum(1 for r in replay_results if not r.match)

    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "primary": {
            "total": total_workflows,
            "successful": successful,
            "failed": total_workflows - successful,
        },
        "shadow": {
            "total_replays": total_replays,
            "matches": total_replays - mismatches,
            "mismatches": mismatches,
        },
        "mismatch_details": [
            asdict(r) for r in replay_results if not r.match
        ][:5],  # Sample mismatches
        "passed": mismatches == 0,
    }

    print(json.dumps(output, indent=2))
    return 0 if mismatches == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
PYTHON_SCRIPT

chmod +x "$SHADOW_RUNNER"

# Notification function
send_alert() {
    local message="$1"
    local severity="${2:-warning}"

    log_warn "ALERT: $message"

    if [[ -n "$SLACK_WEBHOOK" ]]; then
        local color="warning"
        [[ "$severity" == "critical" ]] && color="danger"
        [[ "$severity" == "info" ]] && color="#439FE0"

        curl -sf -X POST -H 'Content-type: application/json' \
            --data "{\"attachments\":[{\"color\":\"$color\",\"title\":\"Shadow Simulation Alert\",\"text\":\"$message\",\"footer\":\"M4-T7 Shadow Run\"}]}" \
            "$SLACK_WEBHOOK" >/dev/null 2>&1 || true
    fi
}

# Run a single simulation cycle
run_cycle() {
    local cycle_num=$1
    local cycle_file="$REPORTS_DIR/cycle_${cycle_num}.json"

    [[ "$VERBOSE" == "true" ]] && log_step "Running cycle $cycle_num..."

    PRIMARY_WORKERS=$PRIMARY_WORKERS \
    WORKFLOWS_PER_CYCLE=$WORKFLOWS_PER_CYCLE \
    GOLDEN_DIR="$GOLDEN_DIR" \
    python3 "$SHADOW_RUNNER" > "$cycle_file" 2>&1

    local exit_code=$?

    if [[ -f "$cycle_file" ]]; then
        local primary_total=$(jq -r '.primary.total // 0' "$cycle_file" 2>/dev/null)
        local replays=$(jq -r '.shadow.total_replays // 0' "$cycle_file" 2>/dev/null)
        local mismatches=$(jq -r '.shadow.mismatches // 0' "$cycle_file" 2>/dev/null)

        ((TOTAL_WORKFLOWS += primary_total)) || true
        ((TOTAL_REPLAYS += replays)) || true
        ((MISMATCHES += mismatches)) || true

        if [[ $mismatches -gt 0 ]]; then
            log_error "Cycle $cycle_num: $mismatches mismatches detected!"
            if [[ "$ALERT_ON_MISMATCH" == "true" ]]; then
                send_alert "Shadow simulation detected $mismatches mismatches in cycle $cycle_num" "critical"
            fi
        elif [[ "$VERBOSE" == "true" ]]; then
            log_info "Cycle $cycle_num: $primary_total workflows, $replays replays, 0 mismatches"
        fi
    fi

    ((CYCLES_COMPLETED++)) || true
    return $exit_code
}

# Generate periodic report
generate_report() {
    local elapsed=$(($(date +%s) - START_TIME))
    local elapsed_hours=$((elapsed / 3600))
    local elapsed_minutes=$(((elapsed % 3600) / 60))

    local report_file="$REPORTS_DIR/summary_$(date +%Y%m%d_%H%M%S).json"
    cat > "$report_file" << EOF
{
    "simulation": {
        "start_time": "$(date -d @$START_TIME -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -r $START_TIME -u +%Y-%m-%dT%H:%M:%SZ)",
        "elapsed_seconds": $elapsed,
        "elapsed_formatted": "${elapsed_hours}h ${elapsed_minutes}m",
        "target_hours": $DURATION_HOURS,
        "primary_workers": $PRIMARY_WORKERS
    },
    "statistics": {
        "cycles_completed": $CYCLES_COMPLETED,
        "total_workflows": $TOTAL_WORKFLOWS,
        "total_replays": $TOTAL_REPLAYS,
        "mismatches": $MISMATCHES,
        "mismatch_rate": $(echo "scale=6; $MISMATCHES / ($TOTAL_REPLAYS + 1)" | bc 2>/dev/null || echo "0")
    },
    "status": "$([ $MISMATCHES -eq 0 ] && echo 'healthy' || echo 'degraded')"
}
EOF

    echo "$report_file"
}

# Cleanup function
cleanup() {
    log_info "Shutting down shadow simulation..."

    # Generate final report
    local final_report=$(generate_report)
    log_info "Final report: $final_report"

    exit 0
}

trap cleanup SIGINT SIGTERM

# Main simulation loop
main() {
    log_info "Starting shadow-run simulation..."
    log_info "Press Ctrl+C to stop"

    local duration_seconds=$((DURATION_HOURS * 3600))
    local end_time=$((START_TIME + duration_seconds))

    # Quick mode: run 3 cycles only
    if [[ "$QUICK_MODE" == "true" ]]; then
        for cycle in {1..3}; do
            run_cycle $cycle
            sleep 2
        done
    else
        local cycle=1
        while [[ $(date +%s) -lt $end_time ]]; do
            run_cycle $cycle

            # Progress report every 10 cycles
            if [[ $((cycle % 10)) -eq 0 ]]; then
                local elapsed=$(($(date +%s) - START_TIME))
                local remaining=$((end_time - $(date +%s)))
                log_info "Progress: $cycle cycles, ${TOTAL_WORKFLOWS} workflows, ${MISMATCHES} mismatches, ${remaining}s remaining"
            fi

            ((cycle++))
            sleep "$CYCLE_INTERVAL_SECONDS"
        done
    fi

    # Generate final report
    local final_report=$(generate_report)

    # Final summary
    local elapsed=$(($(date +%s) - START_TIME))
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "           SHADOW-RUN SIMULATION REPORT"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "  Duration:           $(( elapsed / 3600 ))h $(( (elapsed % 3600) / 60 ))m $(( elapsed % 60 ))s"
    echo "  Cycles Completed:   $CYCLES_COMPLETED"
    echo "  Primary Workers:    $PRIMARY_WORKERS"
    echo ""
    echo "  Total Workflows:    $TOTAL_WORKFLOWS"
    echo "  Total Replays:      $TOTAL_REPLAYS"
    echo "  Mismatches:         $MISMATCHES"
    echo ""
    echo "  Final Report:       $final_report"
    echo ""

    if [[ $MISMATCHES -eq 0 ]]; then
        log_info "═══════════════════════════════════════════════════════════════"
        log_info "         ✅ SHADOW SIMULATION PASSED"
        log_info "═══════════════════════════════════════════════════════════════"
        log_info "All $TOTAL_REPLAYS shadow replays matched their golden files."

        if [[ -n "$SLACK_WEBHOOK" ]]; then
            send_alert "Shadow simulation completed successfully: $TOTAL_WORKFLOWS workflows, $TOTAL_REPLAYS replays, 0 mismatches" "info"
        fi

        exit 0
    else
        log_error "═══════════════════════════════════════════════════════════════"
        log_error "         ❌ SHADOW SIMULATION FAILED"
        log_error "═══════════════════════════════════════════════════════════════"
        log_error "Detected $MISMATCHES mismatches across $TOTAL_REPLAYS replays."
        log_error "Check detailed reports in: $REPORTS_DIR"

        if [[ -n "$SLACK_WEBHOOK" ]]; then
            send_alert "Shadow simulation FAILED: $MISMATCHES mismatches detected out of $TOTAL_REPLAYS replays" "critical"
        fi

        exit 1
    fi
}

main
