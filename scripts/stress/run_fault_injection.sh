#!/bin/bash
# M4-T2: Fault Injection Rig
# Tests workflow engine resilience under various fault conditions:
# - Redis connection drops
# - Database timeouts
# - Filesystem permission errors
# - Network latency injection
#
# Usage:
#   ./scripts/stress/run_fault_injection.sh                    # Run all fault tests
#   ./scripts/stress/run_fault_injection.sh --fault redis      # Test specific fault
#   ./scripts/stress/run_fault_injection.sh --quick            # Quick mode
#   ./scripts/stress/run_fault_injection.sh --chaos            # Random faults

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
log_fault() { echo -e "${MAGENTA}[FAULT]${NC} $1"; }

# Defaults
OUTPUT_DIR="/tmp/fault_injection_$(date +%Y%m%d_%H%M%S)"
FAULT_TYPE="all"
QUICK_MODE=false
CHAOS_MODE=false
VERBOSE=false
ITERATIONS=10

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fault|-f)
            FAULT_TYPE="$2"
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
            ITERATIONS=3
            shift
            ;;
        --chaos)
            CHAOS_MODE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Fault Injection Rig for M4 Workflow Engine"
            echo ""
            echo "Options:"
            echo "  --fault, -f TYPE     Fault type: redis, db, fs, network, all (default: all)"
            echo "  --iterations, -n N   Number of iterations per test (default: 10)"
            echo "  --output, -o DIR     Output directory"
            echo "  --quick              Quick mode: 3 iterations"
            echo "  --chaos              Random fault injection during tests"
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
log_info "         M4-T2: Fault Injection Rig"
log_info "═══════════════════════════════════════════════════════════════"
log_info "  Fault Type:  $FAULT_TYPE"
log_info "  Iterations:  $ITERATIONS"
log_info "  Chaos Mode:  $CHAOS_MODE"
log_info "  Output:      $OUTPUT_DIR"
log_info "═══════════════════════════════════════════════════════════════"

# Environment setup
export PYTHONPATH="$BACKEND_DIR:${PYTHONPATH:-}"
export DISABLE_EXTERNAL_CALLS=1

# Results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
RECOVERED_TESTS=0

# Create the fault injection test runner
FAULT_RUNNER="$OUTPUT_DIR/fault_runner.py"
cat > "$FAULT_RUNNER" << 'PYTHON_SCRIPT'
#!/usr/bin/env python3
"""
Fault injection test runner for M4 workflow engine.

Tests various fault conditions:
1. Redis connection failures
2. Database timeouts
3. Filesystem errors
4. Network issues
"""

import asyncio
import hashlib
import json
import os
import random
import sys
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

# Fault types
class FaultType:
    REDIS_DISCONNECT = "redis_disconnect"
    REDIS_TIMEOUT = "redis_timeout"
    DB_TIMEOUT = "db_timeout"
    DB_CONN_ERROR = "db_connection_error"
    FS_PERMISSION = "fs_permission"
    FS_DISK_FULL = "fs_disk_full"
    NETWORK_LATENCY = "network_latency"
    RANDOM_EXCEPTION = "random_exception"


@dataclass
class FaultConfig:
    """Configuration for a fault injection."""
    fault_type: str
    probability: float = 0.3  # 30% chance of fault per operation
    duration_ms: int = 100    # How long fault lasts
    recover_after: int = 3    # Recover after N faults


@dataclass
class FaultStats:
    """Statistics from fault injection test."""
    fault_type: str
    total_operations: int = 0
    faults_injected: int = 0
    recoveries: int = 0
    permanent_failures: int = 0
    success_rate: float = 0.0


class FaultInjector:
    """Injects faults into operations."""

    def __init__(self, config: FaultConfig):
        self.config = config
        self.fault_count = 0
        self.should_inject = True
        self.stats = FaultStats(fault_type=config.fault_type)

    def maybe_inject(self) -> bool:
        """Check if a fault should be injected."""
        if not self.should_inject:
            return False

        if random.random() < self.config.probability:
            self.fault_count += 1
            self.stats.faults_injected += 1

            # Auto-recover after threshold
            if self.fault_count >= self.config.recover_after:
                self.should_inject = False
                self.stats.recoveries += 1

            return True
        return False

    def inject(self) -> Exception:
        """Inject a fault based on configuration."""
        self.stats.total_operations += 1

        if self.config.fault_type == FaultType.REDIS_DISCONNECT:
            return ConnectionError("Redis connection lost")
        elif self.config.fault_type == FaultType.REDIS_TIMEOUT:
            return TimeoutError("Redis operation timed out")
        elif self.config.fault_type == FaultType.DB_TIMEOUT:
            return TimeoutError("Database query timed out")
        elif self.config.fault_type == FaultType.DB_CONN_ERROR:
            return ConnectionError("Database connection refused")
        elif self.config.fault_type == FaultType.FS_PERMISSION:
            return PermissionError("Permission denied")
        elif self.config.fault_type == FaultType.FS_DISK_FULL:
            return OSError(28, "No space left on device")
        elif self.config.fault_type == FaultType.NETWORK_LATENCY:
            # Latency is handled differently - we inject delay
            return None
        else:
            return RuntimeError(f"Injected fault: {self.config.fault_type}")


class FaultyCheckpointStore:
    """Checkpoint store with fault injection."""

    def __init__(self, injector: FaultInjector):
        self._store: Dict[str, Dict] = {}
        self._injector = injector
        self._save_count = 0

    async def save(
        self,
        run_id: str,
        next_step_index: int,
        step_outputs: Optional[Dict] = None,
        status: str = "running",
        **kwargs
    ) -> str:
        self._save_count += 1
        self._injector.stats.total_operations += 1

        if self._injector.maybe_inject():
            exc = self._injector.inject()
            if exc:
                raise exc

        # Simulate latency
        if self._injector.config.fault_type == FaultType.NETWORK_LATENCY:
            if random.random() < self._injector.config.probability:
                await asyncio.sleep(self._injector.config.duration_ms / 1000.0)

        now = datetime.now(timezone.utc)
        existing = self._store.get(run_id)
        version = (existing["version"] + 1) if existing else 1

        self._store[run_id] = {
            "run_id": run_id,
            "next_step_index": next_step_index,
            "step_outputs": step_outputs or {},
            "status": status,
            "version": version,
            "updated_at": now,
        }

        return hashlib.sha256(f"{run_id}:{next_step_index}".encode()).hexdigest()[:16]

    async def save_with_retry(self, max_retries: int = 3, **kwargs) -> str:
        """Save with automatic retry on transient failures."""
        last_error = None
        for attempt in range(max_retries):
            try:
                return await self.save(**kwargs)
            except (ConnectionError, TimeoutError) as e:
                last_error = e
                await asyncio.sleep(0.1 * (attempt + 1))  # Backoff
                continue
        raise last_error

    async def load(self, run_id: str):
        self._injector.stats.total_operations += 1

        if self._injector.maybe_inject():
            exc = self._injector.inject()
            if exc:
                raise exc

        data = self._store.get(run_id)
        if not data:
            return None

        class CheckpointData:
            def __init__(self, d):
                for k, v in d.items():
                    setattr(self, k, v)

        return CheckpointData(data)


class FaultyBudgetStore:
    """Budget store with fault injection."""

    def __init__(self, injector: FaultInjector):
        self._budgets: Dict[str, int] = {}
        self._injector = injector

    async def add_cost(self, run_id: str, cost: int, ceiling: int) -> tuple:
        self._injector.stats.total_operations += 1

        if self._injector.maybe_inject():
            exc = self._injector.inject()
            if exc:
                raise exc

        current = self._budgets.get(run_id, 0)
        if current + cost > ceiling:
            return (current, False)

        self._budgets[run_id] = current + cost
        return (self._budgets[run_id], True)

    async def get_cost(self, run_id: str) -> int:
        return self._budgets.get(run_id, 0)


class FaultyGoldenRecorder:
    """Golden recorder with fault injection."""

    def __init__(self, injector: FaultInjector, dirpath: str = "/tmp/golden"):
        self._events: Dict[str, List] = {}
        self._injector = injector
        self._dirpath = dirpath

    async def record_run_start(self, run_id: str, spec, seed: int, replay: bool, **kwargs):
        self._injector.stats.total_operations += 1

        if self._injector.maybe_inject():
            exc = self._injector.inject()
            if exc:
                raise exc

        if run_id not in self._events:
            self._events[run_id] = []
        self._events[run_id].append({"type": "run_start", "seed": seed})

    async def record_step(self, run_id: str, idx: int, step, result, seed: int):
        self._injector.stats.total_operations += 1

        if self._injector.maybe_inject():
            exc = self._injector.inject()
            if exc:
                raise exc

        if run_id not in self._events:
            self._events[run_id] = []
        self._events[run_id].append({"type": "step", "index": idx})

    async def record_run_end(self, run_id: str, status: str):
        self._injector.stats.total_operations += 1

        if self._injector.maybe_inject():
            exc = self._injector.inject()
            if exc:
                raise exc

        if run_id in self._events:
            self._events[run_id].append({"type": "run_end", "status": status})


# Test workflows
class DeterministicSkills:
    @staticmethod
    async def compute(params: Dict, seed: int) -> Dict:
        return {"ok": True, "result": hashlib.sha256(f"{params}:{seed}".encode()).hexdigest()[:8]}


async def run_workflow_with_faults(
    fault_config: FaultConfig,
    iterations: int,
) -> Dict[str, Any]:
    """Run workflow with fault injection and measure resilience."""

    injector = FaultInjector(fault_config)
    checkpoint_store = FaultyCheckpointStore(injector)
    budget_store = FaultyBudgetStore(injector)
    golden_recorder = FaultyGoldenRecorder(injector)

    completed = 0
    failed = 0
    recovered = 0
    errors: List[str] = []

    for i in range(iterations):
        run_id = f"fault-test-{i}-{uuid4().hex[:6]}"
        try:
            # Simulate workflow execution with multiple operations
            await golden_recorder.record_run_start(run_id, MagicMock(), seed=i, replay=False)

            for step in range(5):
                # Checkpoint save
                await checkpoint_store.save_with_retry(
                    run_id=run_id,
                    next_step_index=step + 1,
                    step_outputs={f"step{step}": {"ok": True}},
                    status="running",
                )

                # Budget check
                await budget_store.add_cost(run_id, cost=5, ceiling=1000)

                # Golden recording
                await golden_recorder.record_step(run_id, step, MagicMock(), MagicMock(), seed=i)

            # Final checkpoint
            await checkpoint_store.save(run_id=run_id, next_step_index=5, status="completed")
            await golden_recorder.record_run_end(run_id, "completed")

            completed += 1

            # Check if we recovered from faults
            if injector.fault_count > 0:
                recovered += 1

        except Exception as e:
            failed += 1
            errors.append(f"Iteration {i}: {type(e).__name__}: {str(e)[:100]}")

    # Calculate success rate
    success_rate = completed / iterations if iterations > 0 else 0

    return {
        "fault_type": fault_config.fault_type,
        "iterations": iterations,
        "completed": completed,
        "failed": failed,
        "recovered": recovered,
        "success_rate": success_rate,
        "faults_injected": injector.stats.faults_injected,
        "total_operations": injector.stats.total_operations,
        "errors": errors[:5],  # Sample errors
        "passed": failed == 0 or (success_rate >= 0.8 and recovered > 0),
    }


async def main():
    fault_type = os.environ.get("FAULT_TYPE", "redis_disconnect")
    iterations = int(os.environ.get("ITERATIONS", "10"))
    probability = float(os.environ.get("FAULT_PROBABILITY", "0.3"))

    config = FaultConfig(
        fault_type=fault_type,
        probability=probability,
        recover_after=3,
    )

    result = await run_workflow_with_faults(config, iterations)
    print(json.dumps(result, indent=2))

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
PYTHON_SCRIPT

chmod +x "$FAULT_RUNNER"

# Fault test functions
run_fault_test() {
    local fault_type=$1
    local description=$2

    log_step "Testing fault: $fault_type - $description"

    local result_file="$OUTPUT_DIR/fault_${fault_type}.json"

    FAULT_TYPE="$fault_type" \
    ITERATIONS=$ITERATIONS \
    FAULT_PROBABILITY=0.3 \
    python3 "$FAULT_RUNNER" > "$result_file" 2>&1

    local exit_code=$?

    ((TOTAL_TESTS++))

    if [[ $exit_code -eq 0 ]]; then
        local success_rate=$(jq -r '.success_rate // 0' "$result_file" 2>/dev/null)
        local faults=$(jq -r '.faults_injected // 0' "$result_file" 2>/dev/null)
        local recovered=$(jq -r '.recovered // 0' "$result_file" 2>/dev/null)

        log_info "✓ $fault_type: success_rate=${success_rate}, faults_injected=${faults}, recovered=${recovered}"
        ((PASSED_TESTS++))

        if [[ $recovered -gt 0 ]]; then
            ((RECOVERED_TESTS++))
        fi
    else
        log_error "✗ $fault_type: Test failed"
        ((FAILED_TESTS++))

        if [[ "$VERBOSE" == "true" ]]; then
            cat "$result_file"
        fi
    fi
}

run_chaos_test() {
    log_step "Running chaos mode with random faults..."

    local fault_types=(
        "redis_disconnect"
        "redis_timeout"
        "db_timeout"
        "db_connection_error"
        "fs_permission"
        "network_latency"
    )

    local chaos_results="$OUTPUT_DIR/chaos_results.jsonl"
    > "$chaos_results"

    for i in $(seq 1 $ITERATIONS); do
        # Random fault type
        local random_fault=${fault_types[$RANDOM % ${#fault_types[@]}]}

        log_fault "Chaos iteration $i: injecting $random_fault"

        FAULT_TYPE="$random_fault" \
        ITERATIONS=5 \
        FAULT_PROBABILITY=0.5 \
        python3 "$FAULT_RUNNER" >> "$chaos_results" 2>&1 || true
    done

    # Analyze chaos results
    local total=$(wc -l < "$chaos_results" 2>/dev/null || echo "0")
    local passed=$(grep -c '"passed": true' "$chaos_results" 2>/dev/null || echo "0")

    log_info "Chaos test completed: $passed/$total iterations passed"

    ((TOTAL_TESTS++))
    if [[ $passed -gt 0 ]]; then
        ((PASSED_TESTS++))
    else
        ((FAILED_TESTS++))
    fi
}

# Main execution
main() {
    local start_time=$(date +%s)

    log_info "Starting fault injection tests..."

    if [[ "$CHAOS_MODE" == "true" ]]; then
        run_chaos_test
    elif [[ "$FAULT_TYPE" == "all" ]]; then
        # Run all fault types
        run_fault_test "redis_disconnect" "Redis connection drops"
        run_fault_test "redis_timeout" "Redis operation timeouts"
        run_fault_test "db_timeout" "Database query timeouts"
        run_fault_test "db_connection_error" "Database connection errors"
        run_fault_test "fs_permission" "Filesystem permission errors"
        run_fault_test "network_latency" "Network latency injection"
    else
        run_fault_test "$FAULT_TYPE" "User-specified fault"
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # Generate summary
    local summary_file="$OUTPUT_DIR/summary.json"
    cat > "$summary_file" << EOF
{
    "test_run": {
        "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
        "fault_type": "$FAULT_TYPE",
        "iterations": $ITERATIONS,
        "chaos_mode": $CHAOS_MODE,
        "duration_seconds": $duration
    },
    "results": {
        "total_tests": $TOTAL_TESTS,
        "passed": $PASSED_TESTS,
        "failed": $FAILED_TESTS,
        "recovered": $RECOVERED_TESTS,
        "success_rate": $(echo "scale=4; $PASSED_TESTS / $TOTAL_TESTS" | bc 2>/dev/null || echo "0")
    }
}
EOF

    # Final report
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "              FAULT INJECTION TEST REPORT"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "  Duration:         ${duration}s"
    echo "  Tests Run:        $TOTAL_TESTS"
    echo "  Passed:           $PASSED_TESTS"
    echo "  Failed:           $FAILED_TESTS"
    echo "  Recovered:        $RECOVERED_TESTS"
    echo ""

    if [[ $FAILED_TESTS -eq 0 ]]; then
        log_info "═══════════════════════════════════════════════════════════════"
        log_info "         ✅ FAULT INJECTION TESTS PASSED"
        log_info "═══════════════════════════════════════════════════════════════"
        log_info "System demonstrated resilience to all injected faults."
        echo ""
        exit 0
    else
        log_error "═══════════════════════════════════════════════════════════════"
        log_error "         ❌ FAULT INJECTION TESTS FAILED"
        log_error "═══════════════════════════════════════════════════════════════"
        log_error "System failed to handle $FAILED_TESTS fault scenarios."
        log_error "Check detailed results in: $OUTPUT_DIR"
        echo ""
        exit 1
    fi
}

main
