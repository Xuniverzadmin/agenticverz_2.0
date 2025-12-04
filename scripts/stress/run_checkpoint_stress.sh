#!/bin/bash
# Checkpoint Concurrency Stress Test
# Tests checkpoint save/load under high concurrency with version conflicts
#
# Usage:
#   ./scripts/stress/run_checkpoint_stress.sh                     # Default: 10 workers, 1 hour
#   ./scripts/stress/run_checkpoint_stress.sh --workers 50 --hours 24  # Production stress
#   ./scripts/stress/run_checkpoint_stress.sh --quick             # Quick 5-min test

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
BACKEND_DIR="$PROJECT_ROOT/backend"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# Defaults
WORKERS=10
DURATION_HOURS=1
OPERATIONS_PER_WORKER=100
OUTPUT_DIR="/tmp/checkpoint_stress_$(date +%Y%m%d_%H%M%S)"
QUICK_MODE=false
VERBOSE=false
DB_URL="${DATABASE_URL:-postgresql://nova:novapass@localhost:5433/nova_aos}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --workers|-w)
            WORKERS="$2"
            shift 2
            ;;
        --hours|-h)
            DURATION_HOURS="$2"
            shift 2
            ;;
        --ops-per-worker|-o)
            OPERATIONS_PER_WORKER="$2"
            shift 2
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --quick)
            QUICK_MODE=true
            WORKERS=5
            DURATION_HOURS=0
            OPERATIONS_PER_WORKER=50
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --db-url)
            DB_URL="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --workers, -w N        Number of concurrent workers (default: 10)"
            echo "  --hours, -h N          Duration in hours (default: 1)"
            echo "  --ops-per-worker, -o N Operations per worker per cycle (default: 100)"
            echo "  --output DIR           Output directory for results"
            echo "  --quick                Quick mode: 5 workers, 50 ops, no duration limit"
            echo "  --verbose, -v          Verbose output"
            echo "  --db-url URL           Database URL"
            exit 0
            ;;
        *)
            log_error "Unknown argument: $1"
            exit 1
            ;;
    esac
done

mkdir -p "$OUTPUT_DIR"

log_info "Checkpoint Concurrency Stress Test Configuration:"
log_info "  Workers: $WORKERS"
log_info "  Duration: $DURATION_HOURS hours"
log_info "  Ops per worker: $OPERATIONS_PER_WORKER"
log_info "  Output: $OUTPUT_DIR"
log_info "  Quick mode: $QUICK_MODE"

# Environment setup
export PYTHONPATH="$BACKEND_DIR:${PYTHONPATH:-}"
export DATABASE_URL="$DB_URL"

# Results tracking
RESULTS_FILE="$OUTPUT_DIR/results.jsonl"
SUMMARY_FILE="$OUTPUT_DIR/summary.json"
touch "$RESULTS_FILE"

# Create the Python stress test script
STRESS_SCRIPT="$OUTPUT_DIR/stress_runner.py"
cat > "$STRESS_SCRIPT" << 'PYTHON_SCRIPT'
#!/usr/bin/env python3
"""
Checkpoint concurrency stress test runner.

Tests:
1. Concurrent checkpoint saves with version conflicts
2. Optimistic locking behavior under contention
3. Recovery from version conflicts
4. Status transitions under race conditions
"""

import asyncio
import json
import os
import random
import sys
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Add backend to path
sys.path.insert(0, os.environ.get("PYTHONPATH", ".").split(":")[0])

try:
    from app.workflow.checkpoint import CheckpointStore, CheckpointData, CheckpointVersionConflictError
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    print("Make sure PYTHONPATH includes the backend directory", file=sys.stderr)
    sys.exit(1)


@dataclass
class WorkerStats:
    worker_id: int
    saves_attempted: int = 0
    saves_succeeded: int = 0
    saves_failed: int = 0
    version_conflicts: int = 0
    loads_attempted: int = 0
    loads_succeeded: int = 0
    loads_failed: int = 0
    errors: List[str] = None
    start_time: float = 0
    end_time: float = 0

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class CheckpointStressRunner:
    """Run checkpoint stress test with multiple concurrent workers."""

    def __init__(
        self,
        num_workers: int,
        ops_per_worker: int,
        shared_run_ratio: float = 0.3,
        db_url: Optional[str] = None,
    ):
        self.num_workers = num_workers
        self.ops_per_worker = ops_per_worker
        self.shared_run_ratio = shared_run_ratio
        self.db_url = db_url or os.environ.get("DATABASE_URL")

        # Shared run IDs (workers will compete for these)
        self.shared_runs = [f"stress-shared-{uuid.uuid4().hex[:8]}" for _ in range(max(3, num_workers // 3))]

        # Stats per worker
        self.worker_stats: Dict[int, WorkerStats] = {}

    async def run_worker(self, worker_id: int) -> WorkerStats:
        """Run a single worker performing checkpoint operations."""
        stats = WorkerStats(worker_id=worker_id)
        stats.start_time = time.time()

        try:
            store = CheckpointStore(engine_url=self.db_url)

            for op_idx in range(self.ops_per_worker):
                # Decide whether to use shared or private run
                use_shared = random.random() < self.shared_run_ratio

                if use_shared:
                    run_id = random.choice(self.shared_runs)
                else:
                    run_id = f"stress-worker{worker_id}-{uuid.uuid4().hex[:8]}"

                # Perform operation
                try:
                    await self._perform_operation(store, run_id, op_idx, stats)
                except Exception as e:
                    stats.errors.append(f"op {op_idx}: {type(e).__name__}: {str(e)[:100]}")

                # Small random delay to create realistic contention patterns
                await asyncio.sleep(random.uniform(0.001, 0.01))

        except Exception as e:
            stats.errors.append(f"worker error: {type(e).__name__}: {str(e)[:200]}")

        stats.end_time = time.time()
        return stats

    async def _perform_operation(
        self,
        store: CheckpointStore,
        run_id: str,
        op_idx: int,
        stats: WorkerStats,
    ) -> None:
        """Perform a single checkpoint operation."""
        # Mix of operations
        op_type = random.choices(
            ["save", "load", "update", "status_change"],
            weights=[0.4, 0.3, 0.2, 0.1],
        )[0]

        if op_type == "save":
            stats.saves_attempted += 1
            try:
                await store.save(
                    run_id=run_id,
                    next_step_index=op_idx % 10,
                    step_outputs={"op": op_idx, "worker": stats.worker_id},
                    status="running",
                    workflow_id=f"wf-{stats.worker_id}",
                    tenant_id="tenant-stress",
                )
                stats.saves_succeeded += 1
            except CheckpointVersionConflictError:
                stats.version_conflicts += 1
                stats.saves_failed += 1
            except Exception:
                stats.saves_failed += 1
                raise

        elif op_type == "load":
            stats.loads_attempted += 1
            try:
                checkpoint = await store.load(run_id)
                if checkpoint:
                    stats.loads_succeeded += 1
                else:
                    stats.loads_failed += 1
            except Exception:
                stats.loads_failed += 1
                raise

        elif op_type == "update":
            # Load then update (will trigger version conflicts)
            stats.loads_attempted += 1
            stats.saves_attempted += 1
            try:
                checkpoint = await store.load(run_id)
                if checkpoint:
                    stats.loads_succeeded += 1
                    await store.save(
                        run_id=run_id,
                        next_step_index=checkpoint.next_step_index + 1,
                        step_outputs={"updated_by": stats.worker_id, "op": op_idx},
                        status=checkpoint.status,
                        workflow_id=checkpoint.workflow_id,
                        tenant_id=checkpoint.tenant_id,
                        expected_version=checkpoint.version,
                    )
                    stats.saves_succeeded += 1
                else:
                    stats.loads_failed += 1
                    stats.saves_failed += 1
            except CheckpointVersionConflictError:
                stats.version_conflicts += 1
                stats.saves_failed += 1
            except Exception:
                stats.saves_failed += 1
                raise

        elif op_type == "status_change":
            # Status transition test
            stats.saves_attempted += 1
            try:
                checkpoint = await store.load(run_id)
                if checkpoint:
                    # Random status transition
                    new_status = random.choice(["running", "paused", "completed", "failed"])
                    ended = datetime.now(timezone.utc) if new_status in ("completed", "failed") else None
                    await store.save(
                        run_id=run_id,
                        next_step_index=checkpoint.next_step_index,
                        status=new_status,
                        workflow_id=checkpoint.workflow_id,
                        tenant_id=checkpoint.tenant_id,
                        expected_version=checkpoint.version,
                        ended_at=ended,
                    )
                    stats.saves_succeeded += 1
                else:
                    stats.saves_failed += 1
            except CheckpointVersionConflictError:
                stats.version_conflicts += 1
                stats.saves_failed += 1
            except Exception:
                stats.saves_failed += 1
                raise

    async def run(self) -> Dict:
        """Run the full stress test."""
        print(f"Starting stress test with {self.num_workers} workers, {self.ops_per_worker} ops each")
        print(f"Shared runs: {len(self.shared_runs)}")
        print(f"Expected total operations: {self.num_workers * self.ops_per_worker}")

        start_time = time.time()

        # Run all workers concurrently
        tasks = [self.run_worker(i) for i in range(self.num_workers)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()

        # Aggregate stats
        total_stats = {
            "workers": self.num_workers,
            "ops_per_worker": self.ops_per_worker,
            "duration_seconds": end_time - start_time,
            "saves_attempted": 0,
            "saves_succeeded": 0,
            "saves_failed": 0,
            "version_conflicts": 0,
            "loads_attempted": 0,
            "loads_succeeded": 0,
            "loads_failed": 0,
            "worker_errors": 0,
            "error_samples": [],
        }

        for result in results:
            if isinstance(result, Exception):
                total_stats["worker_errors"] += 1
                total_stats["error_samples"].append(str(result)[:200])
            elif isinstance(result, WorkerStats):
                total_stats["saves_attempted"] += result.saves_attempted
                total_stats["saves_succeeded"] += result.saves_succeeded
                total_stats["saves_failed"] += result.saves_failed
                total_stats["version_conflicts"] += result.version_conflicts
                total_stats["loads_attempted"] += result.loads_attempted
                total_stats["loads_succeeded"] += result.loads_succeeded
                total_stats["loads_failed"] += result.loads_failed
                if result.errors:
                    total_stats["error_samples"].extend(result.errors[:3])

        # Calculate rates
        total_stats["ops_per_second"] = (
            (total_stats["saves_attempted"] + total_stats["loads_attempted"])
            / max(total_stats["duration_seconds"], 0.001)
        )
        total_stats["save_success_rate"] = (
            total_stats["saves_succeeded"] / max(total_stats["saves_attempted"], 1)
        )
        total_stats["version_conflict_rate"] = (
            total_stats["version_conflicts"] / max(total_stats["saves_attempted"], 1)
        )

        # Limit error samples
        total_stats["error_samples"] = total_stats["error_samples"][:10]

        return total_stats


async def main():
    workers = int(os.environ.get("STRESS_WORKERS", "10"))
    ops_per_worker = int(os.environ.get("STRESS_OPS_PER_WORKER", "100"))

    runner = CheckpointStressRunner(
        num_workers=workers,
        ops_per_worker=ops_per_worker,
    )

    results = await runner.run()

    # Output as JSON
    print(json.dumps(results, indent=2))

    # Check for success
    if results["version_conflict_rate"] > 0.5:
        print("\nWARNING: High version conflict rate (>50%)", file=sys.stderr)

    if results["worker_errors"] > 0:
        print(f"\nERROR: {results['worker_errors']} workers failed", file=sys.stderr)
        return 1

    if results["save_success_rate"] < 0.5:
        print(f"\nERROR: Low save success rate ({results['save_success_rate']:.1%})", file=sys.stderr)
        return 1

    print(f"\nSTRESS TEST PASSED")
    print(f"  Duration: {results['duration_seconds']:.2f}s")
    print(f"  Ops/sec: {results['ops_per_second']:.0f}")
    print(f"  Save success: {results['save_success_rate']:.1%}")
    print(f"  Version conflicts: {results['version_conflicts']} ({results['version_conflict_rate']:.1%})")

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
PYTHON_SCRIPT

chmod +x "$STRESS_SCRIPT"

# Run the stress test
run_stress_cycle() {
    local cycle=$1
    log_step "Running stress cycle $cycle"

    STRESS_WORKERS=$WORKERS \
    STRESS_OPS_PER_WORKER=$OPERATIONS_PER_WORKER \
    python3 "$STRESS_SCRIPT" > "$OUTPUT_DIR/cycle_${cycle}.json" 2>&1

    local exit_code=$?

    # Append to results
    if [[ -f "$OUTPUT_DIR/cycle_${cycle}.json" ]]; then
        echo "{\"cycle\": $cycle, \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\", \"result\": $(cat "$OUTPUT_DIR/cycle_${cycle}.json")}" >> "$RESULTS_FILE"
    fi

    return $exit_code
}

# Main execution
main() {
    local start_time=$(date +%s)
    local end_time=$((start_time + DURATION_HOURS * 3600))
    local cycle=0
    local passed=0
    local failed=0

    log_info "Starting checkpoint stress test at $(date -u +%Y-%m-%dT%H:%M:%SZ)"

    if [[ "$QUICK_MODE" == "true" ]]; then
        # Quick mode: run once
        if run_stress_cycle 0; then
            ((passed++))
        else
            ((failed++))
        fi
        ((cycle++))
    else
        # Time-based mode: run until duration expires
        while [[ $(date +%s) -lt $end_time ]]; do
            if run_stress_cycle $cycle; then
                ((passed++))
            else
                ((failed++))
            fi
            ((cycle++))

            # Brief pause between cycles
            sleep 5

            # Progress update every 10 cycles
            if [[ $((cycle % 10)) -eq 0 ]]; then
                local elapsed=$(($(date +%s) - start_time))
                local remaining=$((end_time - $(date +%s)))
                log_info "Progress: $cycle cycles ($passed passed, $failed failed), ${remaining}s remaining"
            fi
        done
    fi

    # Generate summary
    local total_duration=$(($(date +%s) - start_time))

    cat > "$SUMMARY_FILE" << EOF
{
    "test_run": {
        "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
        "workers": $WORKERS,
        "ops_per_worker": $OPERATIONS_PER_WORKER,
        "duration_hours": $DURATION_HOURS,
        "quick_mode": $QUICK_MODE
    },
    "results": {
        "total_cycles": $cycle,
        "passed": $passed,
        "failed": $failed,
        "duration_seconds": $total_duration,
        "success_rate": $(echo "scale=4; $passed / $cycle" | bc 2>/dev/null || echo "0")
    },
    "files": {
        "results": "$RESULTS_FILE",
        "output_dir": "$OUTPUT_DIR"
    }
}
EOF

    log_info "Summary written to: $SUMMARY_FILE"

    # Final report
    echo ""
    echo "=========================================="
    echo "    CHECKPOINT STRESS TEST REPORT"
    echo "=========================================="
    echo ""
    echo "  Total Cycles:  $cycle"
    echo "  Passed:        $passed"
    echo "  Failed:        $failed"
    echo "  Duration:      ${total_duration}s"
    echo ""

    if [[ $failed -gt 0 ]]; then
        log_error "STRESS TEST HAD FAILURES"
        echo ""
        echo "Check detailed results in: $OUTPUT_DIR"
        exit 1
    else
        log_info "STRESS TEST PASSED"
        exit 0
    fi
}

main
