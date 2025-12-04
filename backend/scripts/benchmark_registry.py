#!/usr/bin/env python3
"""
Registry Performance Benchmark

Runs 10x iterations of registering 1000 skills.
Reports p50, p90, p99 latencies.
Fails CI if p50 > 3000ms.

Usage:
    python scripts/benchmark_registry.py

Exit codes:
    0 - p50 <= 3000ms (PASS)
    1 - p50 > 3000ms (FAIL)
"""

import json
import statistics
import sys
import time
from pathlib import Path

# Add backend to path
backend = Path(__file__).parent.parent
sys.path.insert(0, str(backend))


def run_benchmark(num_skills: int = 1000) -> float:
    """
    Single benchmark run - registers num_skills skills.

    Returns elapsed time in milliseconds.
    """
    from app.skills import registry

    # Clear existing registry
    registry._REGISTRY.clear()

    # Create mock skill class
    class MockSkill:
        VERSION = '1.0.0'
        DESCRIPTION = 'Benchmark test skill'

        @classmethod
        async def execute(cls, params):
            return {'ok': True}

    start = time.perf_counter()

    for i in range(num_skills):
        registry.register_skill(
            name=f'skill.bench_{i:04d}',
            cls=MockSkill
        )

    elapsed_ms = (time.perf_counter() - start) * 1000
    return elapsed_ms


def main():
    num_runs = 10
    num_skills = 1000
    threshold_ms = 3000  # 3 seconds

    print(f"Registry Performance Benchmark")
    print(f"Skills per run: {num_skills}")
    print(f"Number of runs: {num_runs}")
    print(f"Threshold (p50): {threshold_ms}ms")
    print("=" * 50)

    results = []
    for run in range(num_runs):
        elapsed = run_benchmark(num_skills)
        results.append(elapsed)
        print(f"Run {run + 1:2d}: {elapsed:8.2f} ms")

    # Calculate statistics
    sorted_results = sorted(results)
    p50 = statistics.median(results)
    p90_idx = int(0.9 * len(sorted_results))
    p99_idx = int(0.99 * len(sorted_results))
    p90 = sorted_results[min(p90_idx, len(sorted_results) - 1)]
    p99 = sorted_results[min(p99_idx, len(sorted_results) - 1)]

    print("=" * 50)
    print(f"Min:     {min(results):8.2f} ms")
    print(f"Max:     {max(results):8.2f} ms")
    print(f"Mean:    {statistics.mean(results):8.2f} ms")
    print(f"Stdev:   {statistics.stdev(results):8.2f} ms")
    print(f"p50:     {p50:8.2f} ms")
    print(f"p90:     {p90:8.2f} ms")
    print(f"p99:     {p99:8.2f} ms")

    # Output JSON artifact for CI
    artifact = {
        "benchmark": "registry_performance",
        "num_skills": num_skills,
        "num_runs": num_runs,
        "threshold_ms": threshold_ms,
        "results_ms": results,
        "stats": {
            "min_ms": min(results),
            "max_ms": max(results),
            "mean_ms": statistics.mean(results),
            "stdev_ms": statistics.stdev(results),
            "p50_ms": p50,
            "p90_ms": p90,
            "p99_ms": p99,
        },
        "passed": p50 <= threshold_ms
    }

    # Write artifact
    artifact_path = backend / "benchmark_results.json"
    with open(artifact_path, "w") as f:
        json.dump(artifact, f, indent=2)
    print(f"\nArtifact written to: {artifact_path}")

    # Acceptance check
    if p50 <= threshold_ms:
        print(f"\n✓ PASS: p50 ({p50:.2f}ms) <= {threshold_ms}ms")
        return 0
    else:
        print(f"\n✗ FAIL: p50 ({p50:.2f}ms) > {threshold_ms}ms")
        return 1


if __name__ == "__main__":
    sys.exit(main())
