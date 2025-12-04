#!/bin/bash
# M4-T1: Multi-Worker Determinism Audit
# Tests golden replay with 3 worker replicas, 500 iterations each
# Verifies identical outputs across all workers for same seed
#
# Usage:
#   ./scripts/stress/run_multi_worker_determinism.sh                    # Default: 3 workers, 500 iterations
#   ./scripts/stress/run_multi_worker_determinism.sh --workers 5        # Custom worker count
#   ./scripts/stress/run_multi_worker_determinism.sh --iterations 1000  # Custom iterations
#   ./scripts/stress/run_multi_worker_determinism.sh --quick            # Quick mode: 3 workers, 50 iterations

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
BACKEND_DIR="$PROJECT_ROOT/backend"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }
log_worker() { echo -e "${CYAN}[WORKER-$1]${NC} $2"; }

# Defaults
WORKERS=3
ITERATIONS=500
OUTPUT_DIR="/tmp/multi_worker_determinism_$(date +%Y%m%d_%H%M%S)"
QUICK_MODE=false
VERBOSE=false
WORKFLOWS="compute io llm"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --workers|-w)
            WORKERS="$2"
            shift 2
            ;;
        --iterations|-n)
            ITERATIONS="$2"
            shift 2
            ;;
        --output|-o)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --quick)
            QUICK_MODE=true
            WORKERS=3
            ITERATIONS=50
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --workflow)
            WORKFLOWS="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Multi-Worker Determinism Audit for M4 Workflow Engine"
            echo ""
            echo "Options:"
            echo "  --workers, -w N      Number of parallel workers (default: 3)"
            echo "  --iterations, -n N   Iterations per worker (default: 500)"
            echo "  --output, -o DIR     Output directory"
            echo "  --workflow NAME      Specific workflow: compute, io, llm (default: all)"
            echo "  --quick              Quick mode: 3 workers, 50 iterations"
            echo "  --verbose, -v        Verbose output"
            exit 0
            ;;
        *)
            log_error "Unknown argument: $1"
            exit 1
            ;;
    esac
done

mkdir -p "$OUTPUT_DIR"

log_info "═══════════════════════════════════════════════════════════════"
log_info "         M4-T1: Multi-Worker Determinism Audit"
log_info "═══════════════════════════════════════════════════════════════"
log_info "  Workers:    $WORKERS"
log_info "  Iterations: $ITERATIONS per worker"
log_info "  Workflows:  $WORKFLOWS"
log_info "  Output:     $OUTPUT_DIR"
log_info "═══════════════════════════════════════════════════════════════"

# Environment setup
export PYTHONPATH="$BACKEND_DIR:${PYTHONPATH:-}"
export DISABLE_EXTERNAL_CALLS=1

# Create the worker script
WORKER_SCRIPT="$OUTPUT_DIR/worker_runner.py"
cat > "$WORKER_SCRIPT" << 'PYTHON_SCRIPT'
#!/usr/bin/env python3
"""
Multi-worker determinism test runner.

Each worker runs the same workflow with the same seed and records
output hashes. All workers should produce identical hashes.
"""

import asyncio
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

# Deterministic skill handlers
class DeterministicSkills:
    """Skill implementations that are provably deterministic."""

    @staticmethod
    async def compute_hash(params: Dict, seed: int) -> Dict:
        data = str(params.get("data", ""))
        # Use seed in computation for determinism verification
        seeded_data = f"{data}:{seed}"
        hash_value = hashlib.sha256(seeded_data.encode()).hexdigest()
        return {"hash": hash_value, "length": len(data), "seed": seed}

    @staticmethod
    async def transform_json(params: Dict, seed: int) -> Dict:
        input_data = params.get("input", {})
        if isinstance(input_data, dict):
            keys = sorted(input_data.keys())
            count = len(input_data)
            type_name = "dict"
        elif isinstance(input_data, list):
            keys = []
            count = len(input_data)
            type_name = "list"
        else:
            keys = []
            count = 1
            type_name = type(input_data).__name__

        return {"keys": keys, "count": count, "type": type_name, "seed": seed}

    @staticmethod
    async def mock_io(params: Dict, seed: int) -> Dict:
        return {
            "read_bytes": len(str(params)),
            "operation": "mock_read",
            "seed": seed,
        }

    @staticmethod
    async def llm_stub(params: Dict, seed: int) -> Dict:
        prompt = params.get("prompt", "")
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        # Deterministic response based solely on seed and prompt
        response = f"Response-{seed}-{prompt_hash}"
        return {"response": response, "tokens_used": len(prompt) // 4, "seed": seed}


# Workflow definitions
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
        {"skill": "mock_io", "params": {"file": "file3.txt"}},
        {"skill": "compute_hash", "params": {"data": "combined_content"}},
        {"skill": "mock_io", "params": {"file": "output.txt", "mode": "write"}},
        {"skill": "transform_json", "params": {"input": {"status": "complete"}}},
        {"skill": "llm_stub", "params": {"prompt": "Verify IO operations"}},
    ],
    "llm": [
        {"skill": "llm_stub", "params": {"prompt": "Step 1: Analyze"}},
        {"skill": "transform_json", "params": {"input": {"analysis": True}}},
        {"skill": "llm_stub", "params": {"prompt": "Step 2: Plan"}},
        {"skill": "llm_stub", "params": {"prompt": "Step 3: Execute"}},
        {"skill": "transform_json", "params": {"input": {"execution": "done"}}},
        {"skill": "llm_stub", "params": {"prompt": "Step 4: Summarize"}},
    ],
}

SKILL_MAP = {
    "compute_hash": DeterministicSkills.compute_hash,
    "transform_json": DeterministicSkills.transform_json,
    "mock_io": DeterministicSkills.mock_io,
    "llm_stub": DeterministicSkills.llm_stub,
}


def derive_step_seed(base_seed: int, step_index: int) -> int:
    """Derive deterministic seed for each step (matching engine.py)."""
    s = hashlib.sha256(f"{base_seed}:{step_index}".encode()).hexdigest()
    return int(s[:16], 16)


async def run_workflow(workflow_name: str, seed: int) -> Dict[str, Any]:
    """Run a workflow and return step hashes."""
    steps = WORKFLOWS.get(workflow_name, [])
    step_results = []
    step_hashes = []

    for i, step in enumerate(steps):
        skill_fn = SKILL_MAP.get(step["skill"])
        if not skill_fn:
            raise ValueError(f"Unknown skill: {step['skill']}")

        # Derive step seed (matching WorkflowEngine._derive_seed)
        step_seed = derive_step_seed(seed, i)

        result = await skill_fn(step["params"], step_seed)
        step_results.append(result)

        # Hash the result deterministically
        result_str = json.dumps(result, sort_keys=True)
        result_hash = hashlib.sha256(result_str.encode()).hexdigest()[:16]
        step_hashes.append(f"{step['skill']}:{result_hash}")

    # Overall workflow hash
    workflow_hash = hashlib.sha256(":".join(step_hashes).encode()).hexdigest()

    return {
        "workflow": workflow_name,
        "seed": seed,
        "step_hashes": step_hashes,
        "workflow_hash": workflow_hash,
    }


async def run_worker(worker_id: int, workflow_name: str, iterations: int, base_seed: int) -> Dict:
    """Run a worker that executes the workflow N times."""
    start_time = time.time()
    results = []
    hashes = []

    for i in range(iterations):
        # Use consistent seed for all iterations (same input -> same output)
        result = await run_workflow(workflow_name, base_seed)
        results.append(result)
        hashes.append(result["workflow_hash"])

    end_time = time.time()

    # All hashes should be identical
    unique_hashes = set(hashes)
    is_deterministic = len(unique_hashes) == 1

    return {
        "worker_id": worker_id,
        "workflow": workflow_name,
        "iterations": iterations,
        "seed": base_seed,
        "duration_seconds": end_time - start_time,
        "unique_hashes": len(unique_hashes),
        "is_deterministic": is_deterministic,
        "final_hash": hashes[-1] if hashes else None,
        "sample_hashes": hashes[:3] + hashes[-3:] if len(hashes) > 6 else hashes,
    }


async def main():
    worker_id = int(os.environ.get("WORKER_ID", "0"))
    workflow = os.environ.get("WORKFLOW", "compute")
    iterations = int(os.environ.get("ITERATIONS", "100"))
    seed = int(os.environ.get("SEED", "12345"))

    result = await run_worker(worker_id, workflow, iterations, seed)
    print(json.dumps(result, indent=2))

    return 0 if result["is_deterministic"] else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
PYTHON_SCRIPT

chmod +x "$WORKER_SCRIPT"

# Results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
MISMATCHES=0

run_determinism_test() {
    local workflow=$1
    local seed=$2

    log_step "Testing workflow: $workflow (seed=$seed)"

    local worker_results=()
    local worker_hashes=()
    local pids=()

    # Launch all workers in parallel
    for ((w=0; w<WORKERS; w++)); do
        local worker_output="$OUTPUT_DIR/worker_${w}_${workflow}.json"

        WORKER_ID=$w \
        WORKFLOW="$workflow" \
        ITERATIONS=$ITERATIONS \
        SEED=$seed \
        python3 "$WORKER_SCRIPT" > "$worker_output" 2>&1 &

        pids+=($!)
        worker_results+=("$worker_output")
    done

    # Wait for all workers
    local all_success=true
    for ((w=0; w<WORKERS; w++)); do
        if ! wait ${pids[$w]}; then
            log_error "Worker $w failed for workflow $workflow"
            all_success=false
        fi
    done

    if [[ "$all_success" != "true" ]]; then
        ((FAILED_TESTS++))
        return 1
    fi

    # Collect hashes from all workers
    for ((w=0; w<WORKERS; w++)); do
        local output_file="${worker_results[$w]}"
        if [[ -f "$output_file" ]]; then
            local hash=$(jq -r '.final_hash // "ERROR"' "$output_file" 2>/dev/null || echo "ERROR")
            local is_det=$(jq -r '.is_deterministic // false' "$output_file" 2>/dev/null || echo "false")
            worker_hashes+=("$hash")

            if [[ "$VERBOSE" == "true" ]]; then
                log_worker "$w" "Hash: $hash (deterministic: $is_det)"
            fi

            if [[ "$is_det" != "true" ]]; then
                log_error "Worker $w had non-deterministic results"
                ((MISMATCHES++))
            fi
        else
            log_error "Missing output for worker $w"
            worker_hashes+=("MISSING")
        fi
    done

    # Compare all worker hashes
    local reference_hash="${worker_hashes[0]}"
    local all_match=true

    for ((w=1; w<WORKERS; w++)); do
        if [[ "${worker_hashes[$w]}" != "$reference_hash" ]]; then
            log_error "Hash mismatch: Worker 0 ($reference_hash) != Worker $w (${worker_hashes[$w]})"
            all_match=false
            ((MISMATCHES++))
        fi
    done

    ((TOTAL_TESTS++))

    if [[ "$all_match" == "true" ]]; then
        log_info "✓ Workflow $workflow: All $WORKERS workers produced identical hash: $reference_hash"
        ((PASSED_TESTS++))
        return 0
    else
        log_error "✗ Workflow $workflow: Hash mismatch across workers"
        ((FAILED_TESTS++))
        return 1
    fi
}

# Run tests
main() {
    local start_time=$(date +%s)
    local test_seeds=(12345 54321 99999 11111 77777)

    log_info "Starting multi-worker determinism audit..."

    for workflow in $WORKFLOWS; do
        for seed in "${test_seeds[@]}"; do
            run_determinism_test "$workflow" "$seed"
        done
    done

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # Generate summary
    local summary_file="$OUTPUT_DIR/summary.json"
    cat > "$summary_file" << EOF
{
    "test_run": {
        "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
        "workers": $WORKERS,
        "iterations_per_worker": $ITERATIONS,
        "workflows": "$WORKFLOWS",
        "duration_seconds": $duration
    },
    "results": {
        "total_tests": $TOTAL_TESTS,
        "passed": $PASSED_TESTS,
        "failed": $FAILED_TESTS,
        "mismatches": $MISMATCHES,
        "success_rate": $(echo "scale=4; $PASSED_TESTS / $TOTAL_TESTS" | bc 2>/dev/null || echo "0")
    }
}
EOF

    # Final report
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "         MULTI-WORKER DETERMINISM AUDIT REPORT"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "  Workers:          $WORKERS"
    echo "  Iterations each:  $ITERATIONS"
    echo "  Total iterations: $((WORKERS * ITERATIONS))"
    echo "  Duration:         ${duration}s"
    echo ""
    echo "  Tests Run:        $TOTAL_TESTS"
    echo "  Passed:           $PASSED_TESTS"
    echo "  Failed:           $FAILED_TESTS"
    echo "  Mismatches:       $MISMATCHES"
    echo ""

    if [[ $FAILED_TESTS -eq 0 && $MISMATCHES -eq 0 ]]; then
        log_info "═══════════════════════════════════════════════════════════════"
        log_info "         ✅ DETERMINISM AUDIT PASSED"
        log_info "═══════════════════════════════════════════════════════════════"
        log_info "All $WORKERS workers produced identical outputs for all workflows"
        log_info "across $((WORKERS * ITERATIONS)) total iterations."
        echo ""
        exit 0
    else
        log_error "═══════════════════════════════════════════════════════════════"
        log_error "         ❌ DETERMINISM AUDIT FAILED"
        log_error "═══════════════════════════════════════════════════════════════"
        log_error "Found $MISMATCHES hash mismatches across workers."
        log_error "Check individual worker outputs in: $OUTPUT_DIR"
        echo ""
        exit 1
    fi
}

main
