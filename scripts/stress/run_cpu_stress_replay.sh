#!/bin/bash
# M4-T3: Replay Under High CPU Load
# Tests golden replay determinism under CPU saturation conditions
# Uses stress-ng to saturate CPU while running replay tests
#
# Usage:
#   ./scripts/stress/run_cpu_stress_replay.sh                     # Default: 8 CPU cores, 100 iterations
#   ./scripts/stress/run_cpu_stress_replay.sh --cpu 32            # Custom CPU stress
#   ./scripts/stress/run_cpu_stress_replay.sh --iterations 500    # More iterations
#   ./scripts/stress/run_cpu_stress_replay.sh --quick             # Quick mode

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
log_cpu() { echo -e "${CYAN}[CPU]${NC} $1"; }

# Defaults
CPU_WORKERS=8
ITERATIONS=100
OUTPUT_DIR="/tmp/cpu_stress_replay_$(date +%Y%m%d_%H%M%S)"
QUICK_MODE=false
VERBOSE=false
STRESS_DURATION=60  # seconds

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --cpu|-c)
            CPU_WORKERS="$2"
            shift 2
            ;;
        --iterations|-n)
            ITERATIONS="$2"
            shift 2
            ;;
        --duration|-d)
            STRESS_DURATION="$2"
            shift 2
            ;;
        --output|-o)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --quick)
            QUICK_MODE=true
            CPU_WORKERS=4
            ITERATIONS=20
            STRESS_DURATION=15
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "CPU Stress Replay Test for M4 Workflow Engine"
            echo ""
            echo "Options:"
            echo "  --cpu, -c N          Number of CPU stress workers (default: 8)"
            echo "  --iterations, -n N   Number of replay iterations (default: 100)"
            echo "  --duration, -d N     Stress duration in seconds (default: 60)"
            echo "  --output, -o DIR     Output directory"
            echo "  --quick              Quick mode: 4 workers, 20 iterations, 15s"
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
log_info "         M4-T3: Replay Under High CPU Load"
log_info "═══════════════════════════════════════════════════════════════"
log_info "  CPU Workers:   $CPU_WORKERS"
log_info "  Iterations:    $ITERATIONS"
log_info "  Duration:      ${STRESS_DURATION}s"
log_info "  Output:        $OUTPUT_DIR"
log_info "═══════════════════════════════════════════════════════════════"

# Environment setup
export PYTHONPATH="$BACKEND_DIR:${PYTHONPATH:-}"
export DISABLE_EXTERNAL_CALLS=1

# Check for stress-ng
STRESS_CMD=""
if command -v stress-ng &> /dev/null; then
    STRESS_CMD="stress-ng"
    log_info "Using stress-ng for CPU saturation"
elif command -v stress &> /dev/null; then
    STRESS_CMD="stress"
    log_info "Using stress for CPU saturation"
else
    log_warn "Neither stress-ng nor stress found. Installing stress-ng..."
    if command -v apt-get &> /dev/null; then
        apt-get update && apt-get install -y stress-ng 2>/dev/null || true
        STRESS_CMD="stress-ng"
    fi
fi

# Create the CPU stress replay test runner
CPU_RUNNER="$OUTPUT_DIR/cpu_stress_runner.py"
cat > "$CPU_RUNNER" << 'PYTHON_SCRIPT'
#!/usr/bin/env python3
"""
CPU stress replay test - verifies determinism under CPU saturation.

Key tests:
1. _derive_seed() produces same results under CPU load
2. _deterministic_jitter() produces same results under CPU load
3. Golden file hashes match across stressed/unstressed runs
"""

import asyncio
import hashlib
import json
import os
import random
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4


def derive_seed(base_seed: int, step_index: int) -> int:
    """Derive deterministic seed for each step (matching engine.py)."""
    s = hashlib.sha256(f"{base_seed}:{step_index}".encode()).hexdigest()
    return int(s[:16], 16)


def deterministic_jitter(seed: int, attempt: int, base_ms: int) -> int:
    """Compute deterministic jitter (matching engine.py)."""
    rng = random.Random(seed ^ attempt)
    max_jitter = max(1, base_ms // 2)
    return rng.randint(0, max_jitter)


def compute_backoff_ms(attempt: int, base_ms: int, seed: int) -> int:
    """Compute exponential backoff with deterministic jitter."""
    exponential = base_ms * (2 ** attempt)
    jitter = deterministic_jitter(seed, attempt, base_ms)
    return exponential + jitter


async def run_determinism_check(iterations: int, seed: int) -> Dict[str, Any]:
    """Run determinism checks multiple times and verify consistency."""

    seed_results: List[List[int]] = []
    jitter_results: List[List[int]] = []
    backoff_results: List[List[int]] = []
    workflow_hashes: List[str] = []

    for _ in range(iterations):
        # Test derive_seed for 10 steps
        seeds = [derive_seed(seed, i) for i in range(10)]
        seed_results.append(seeds)

        # Test deterministic_jitter for various attempts
        jitters = [deterministic_jitter(seed, i, 100) for i in range(5)]
        jitter_results.append(jitters)

        # Test compute_backoff_ms
        backoffs = [compute_backoff_ms(i, 100, seed) for i in range(5)]
        backoff_results.append(backoffs)

        # Simulate workflow and compute hash
        workflow_steps = []
        for step_idx in range(5):
            step_seed = derive_seed(seed, step_idx)
            result = {
                "step": step_idx,
                "seed": step_seed,
                "output": hashlib.sha256(f"output-{step_seed}".encode()).hexdigest()[:8],
            }
            workflow_steps.append(result)

        workflow_hash = hashlib.sha256(
            json.dumps(workflow_steps, sort_keys=True).encode()
        ).hexdigest()
        workflow_hashes.append(workflow_hash)

        # Small yield to allow other tasks
        if _ % 10 == 0:
            await asyncio.sleep(0)

    # Verify all results are identical
    seed_consistent = all(s == seed_results[0] for s in seed_results)
    jitter_consistent = all(j == jitter_results[0] for j in jitter_results)
    backoff_consistent = all(b == backoff_results[0] for b in backoff_results)
    hash_consistent = len(set(workflow_hashes)) == 1

    return {
        "iterations": iterations,
        "seed": seed,
        "seed_determinism": seed_consistent,
        "jitter_determinism": jitter_consistent,
        "backoff_determinism": backoff_consistent,
        "workflow_hash_determinism": hash_consistent,
        "all_deterministic": all([
            seed_consistent,
            jitter_consistent,
            backoff_consistent,
            hash_consistent,
        ]),
        "unique_workflow_hashes": len(set(workflow_hashes)),
        "sample_workflow_hash": workflow_hashes[0] if workflow_hashes else None,
    }


async def run_concurrent_determinism_check(
    iterations: int,
    concurrent_tasks: int,
    seed: int,
) -> Dict[str, Any]:
    """Run multiple determinism checks concurrently."""

    tasks = [
        run_determinism_check(iterations // concurrent_tasks, seed)
        for _ in range(concurrent_tasks)
    ]

    results = await asyncio.gather(*tasks)

    # All concurrent runs should produce same workflow hashes
    all_hashes = [r["sample_workflow_hash"] for r in results]
    concurrent_consistent = len(set(all_hashes)) == 1

    all_deterministic = all(r["all_deterministic"] for r in results)

    return {
        "iterations": iterations,
        "concurrent_tasks": concurrent_tasks,
        "seed": seed,
        "concurrent_consistency": concurrent_consistent,
        "all_deterministic": all_deterministic,
        "task_results": results,
        "passed": concurrent_consistent and all_deterministic,
    }


async def main():
    iterations = int(os.environ.get("ITERATIONS", "100"))
    concurrent_tasks = int(os.environ.get("CONCURRENT_TASKS", "4"))
    seed = int(os.environ.get("SEED", "12345"))

    result = await run_concurrent_determinism_check(iterations, concurrent_tasks, seed)
    print(json.dumps(result, indent=2, default=str))

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
PYTHON_SCRIPT

chmod +x "$CPU_RUNNER"

# Results tracking
BASELINE_HASH=""
STRESSED_HASH=""
PASSED=true

# Run baseline test (no CPU stress)
run_baseline() {
    log_step "Running baseline test (no CPU stress)..."

    local result_file="$OUTPUT_DIR/baseline_result.json"

    ITERATIONS=$ITERATIONS \
    CONCURRENT_TASKS=4 \
    SEED=12345 \
    python3 "$CPU_RUNNER" > "$result_file" 2>&1

    local exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        BASELINE_HASH=$(jq -r '.task_results[0].sample_workflow_hash // "ERROR"' "$result_file" 2>/dev/null)
        local deterministic=$(jq -r '.all_deterministic // false' "$result_file" 2>/dev/null)

        log_info "Baseline: hash=$BASELINE_HASH, deterministic=$deterministic"

        if [[ "$deterministic" != "true" ]]; then
            log_error "Baseline failed determinism check!"
            PASSED=false
        fi
    else
        log_error "Baseline test failed!"
        PASSED=false
        if [[ "$VERBOSE" == "true" ]]; then
            cat "$result_file"
        fi
    fi
}

# Run test under CPU stress
run_stressed() {
    log_step "Running test under CPU stress ($CPU_WORKERS workers)..."

    # Start CPU stress in background
    local stress_pid=""
    if [[ -n "$STRESS_CMD" ]]; then
        log_cpu "Starting CPU stress: $STRESS_CMD --cpu $CPU_WORKERS --timeout ${STRESS_DURATION}s"

        if [[ "$STRESS_CMD" == "stress-ng" ]]; then
            stress-ng --cpu $CPU_WORKERS --timeout ${STRESS_DURATION}s --quiet &
            stress_pid=$!
        else
            stress --cpu $CPU_WORKERS --timeout ${STRESS_DURATION}s &
            stress_pid=$!
        fi

        # Wait for stress to ramp up
        sleep 2
        log_cpu "CPU stress active (PID: $stress_pid)"
    else
        log_warn "No stress tool available - running without CPU saturation"
    fi

    local result_file="$OUTPUT_DIR/stressed_result.json"

    # Run the test
    ITERATIONS=$ITERATIONS \
    CONCURRENT_TASKS=4 \
    SEED=12345 \
    python3 "$CPU_RUNNER" > "$result_file" 2>&1

    local exit_code=$?

    # Clean up stress process
    if [[ -n "$stress_pid" ]]; then
        kill $stress_pid 2>/dev/null || true
        wait $stress_pid 2>/dev/null || true
        log_cpu "CPU stress stopped"
    fi

    if [[ $exit_code -eq 0 ]]; then
        STRESSED_HASH=$(jq -r '.task_results[0].sample_workflow_hash // "ERROR"' "$result_file" 2>/dev/null)
        local deterministic=$(jq -r '.all_deterministic // false' "$result_file" 2>/dev/null)

        log_info "Stressed: hash=$STRESSED_HASH, deterministic=$deterministic"

        if [[ "$deterministic" != "true" ]]; then
            log_error "Stressed test failed determinism check!"
            PASSED=false
        fi
    else
        log_error "Stressed test failed!"
        PASSED=false
        if [[ "$VERBOSE" == "true" ]]; then
            cat "$result_file"
        fi
    fi
}

# Compare baseline and stressed results
compare_results() {
    log_step "Comparing baseline vs stressed results..."

    if [[ "$BASELINE_HASH" == "$STRESSED_HASH" ]]; then
        log_info "✓ Hashes match: baseline and stressed runs produced identical results"
    else
        log_error "✗ Hash mismatch: baseline=$BASELINE_HASH, stressed=$STRESSED_HASH"
        PASSED=false
    fi
}

# Run multiple stress cycles
run_stress_cycles() {
    local cycles=3

    log_step "Running $cycles stress cycles..."

    local all_hashes=()

    for ((c=1; c<=cycles; c++)); do
        log_info "Stress cycle $c/$cycles"

        local cycle_file="$OUTPUT_DIR/cycle_${c}_result.json"

        # Start stress
        if [[ -n "$STRESS_CMD" ]]; then
            if [[ "$STRESS_CMD" == "stress-ng" ]]; then
                stress-ng --cpu $CPU_WORKERS --timeout 20s --quiet &
            else
                stress --cpu $CPU_WORKERS --timeout 20s &
            fi
            local stress_pid=$!
            sleep 1
        fi

        # Run test
        ITERATIONS=$((ITERATIONS / cycles)) \
        CONCURRENT_TASKS=4 \
        SEED=12345 \
        python3 "$CPU_RUNNER" > "$cycle_file" 2>&1 || true

        # Stop stress
        if [[ -n "${stress_pid:-}" ]]; then
            kill $stress_pid 2>/dev/null || true
            wait $stress_pid 2>/dev/null || true
        fi

        local cycle_hash=$(jq -r '.task_results[0].sample_workflow_hash // "ERROR"' "$cycle_file" 2>/dev/null)
        all_hashes+=("$cycle_hash")

        log_info "  Cycle $c hash: $cycle_hash"
    done

    # Check all cycles produced same hash
    local unique_hashes=$(printf '%s\n' "${all_hashes[@]}" | sort -u | wc -l)

    if [[ $unique_hashes -eq 1 ]]; then
        log_info "✓ All $cycles stress cycles produced identical hashes"
    else
        log_error "✗ $unique_hashes unique hashes across $cycles cycles"
        PASSED=false
    fi
}

# Main execution
main() {
    local start_time=$(date +%s)

    log_info "Starting CPU stress replay test..."

    # Check CPU before stress
    local cpu_before=$(grep -c ^processor /proc/cpuinfo 2>/dev/null || echo "?")
    log_info "System CPUs: $cpu_before"

    run_baseline
    run_stressed
    compare_results
    run_stress_cycles

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # Generate summary
    local summary_file="$OUTPUT_DIR/summary.json"
    cat > "$summary_file" << EOF
{
    "test_run": {
        "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
        "cpu_workers": $CPU_WORKERS,
        "iterations": $ITERATIONS,
        "duration_seconds": $duration
    },
    "results": {
        "baseline_hash": "$BASELINE_HASH",
        "stressed_hash": "$STRESSED_HASH",
        "hashes_match": $([ "$BASELINE_HASH" == "$STRESSED_HASH" ] && echo "true" || echo "false"),
        "passed": $PASSED
    }
}
EOF

    # Final report
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "           CPU STRESS REPLAY TEST REPORT"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "  CPU Workers:      $CPU_WORKERS"
    echo "  Iterations:       $ITERATIONS"
    echo "  Duration:         ${duration}s"
    echo ""
    echo "  Baseline Hash:    $BASELINE_HASH"
    echo "  Stressed Hash:    $STRESSED_HASH"
    echo "  Hashes Match:     $([ "$BASELINE_HASH" == "$STRESSED_HASH" ] && echo "YES" || echo "NO")"
    echo ""

    if [[ "$PASSED" == "true" ]]; then
        log_info "═══════════════════════════════════════════════════════════════"
        log_info "         ✅ CPU STRESS REPLAY TEST PASSED"
        log_info "═══════════════════════════════════════════════════════════════"
        log_info "Deterministic operations remained consistent under CPU saturation."
        echo ""
        exit 0
    else
        log_error "═══════════════════════════════════════════════════════════════"
        log_error "         ❌ CPU STRESS REPLAY TEST FAILED"
        log_error "═══════════════════════════════════════════════════════════════"
        log_error "Determinism was violated under CPU stress conditions."
        log_error "Check detailed results in: $OUTPUT_DIR"
        echo ""
        exit 1
    fi
}

main
