#!/usr/bin/env python3
"""
Load Test Script for Approval Workflow

Tests concurrent approval request creation, approval, and rejection
to verify DB performance and detect contention issues.

Usage:
    # Basic test (10 concurrent requests)
    python scripts/load_test_approvals.py

    # Heavy test (100 concurrent requests)
    python scripts/load_test_approvals.py --concurrent 100 --total 500

    # Custom endpoint
    python scripts/load_test_approvals.py --base-url http://staging:8000

Requirements:
    pip install httpx asyncio
"""

import argparse
import asyncio
import json
import statistics
import sys
import time
from dataclasses import dataclass
from typing import List, Optional

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    sys.exit(1)


@dataclass
class RequestResult:
    """Result of a single request."""
    success: bool
    latency_ms: float
    status_code: int
    request_id: Optional[str] = None
    error: Optional[str] = None


@dataclass
class LoadTestReport:
    """Summary report of load test."""
    total_requests: int
    successful: int
    failed: int
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    latency_max_ms: float
    requests_per_second: float
    duration_seconds: float
    errors: List[str]


async def create_approval_request(
    client: httpx.AsyncClient,
    base_url: str,
    request_num: int
) -> RequestResult:
    """Create a single approval request."""
    start = time.perf_counter()
    try:
        response = await client.post(
            f"{base_url}/api/v1/policy/requests",
            json={
                "policy_type": "cost",
                "skill_id": f"test_skill_{request_num % 10}",
                "tenant_id": f"tenant_{request_num % 5}",
                "requested_by": f"load_test_user_{request_num}",
                "justification": f"Load test request {request_num}",
                "expires_in_seconds": 3600,
            },
            timeout=30.0
        )
        latency = (time.perf_counter() - start) * 1000

        if response.status_code == 200:
            data = response.json()
            return RequestResult(
                success=True,
                latency_ms=latency,
                status_code=response.status_code,
                request_id=data.get("request_id")
            )
        else:
            return RequestResult(
                success=False,
                latency_ms=latency,
                status_code=response.status_code,
                error=response.text[:200]
            )
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return RequestResult(
            success=False,
            latency_ms=latency,
            status_code=0,
            error=str(e)[:200]
        )


async def approve_request(
    client: httpx.AsyncClient,
    base_url: str,
    request_id: str
) -> RequestResult:
    """Approve a single request."""
    start = time.perf_counter()
    try:
        response = await client.post(
            f"{base_url}/api/v1/policy/requests/{request_id}/approve",
            json={
                "approver_id": "load_test_approver",
                "level": 4,
                "notes": "Load test approval"
            },
            timeout=30.0
        )
        latency = (time.perf_counter() - start) * 1000

        return RequestResult(
            success=response.status_code == 200,
            latency_ms=latency,
            status_code=response.status_code,
            request_id=request_id,
            error=response.text[:200] if response.status_code != 200 else None
        )
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return RequestResult(
            success=False,
            latency_ms=latency,
            status_code=0,
            request_id=request_id,
            error=str(e)[:200]
        )


async def run_create_batch(
    base_url: str,
    batch_size: int,
    batch_num: int
) -> List[RequestResult]:
    """Run a batch of create requests concurrently."""
    async with httpx.AsyncClient() as client:
        tasks = [
            create_approval_request(client, base_url, batch_num * batch_size + i)
            for i in range(batch_size)
        ]
        return await asyncio.gather(*tasks)


async def run_approve_batch(
    base_url: str,
    request_ids: List[str]
) -> List[RequestResult]:
    """Run a batch of approve requests concurrently."""
    async with httpx.AsyncClient() as client:
        tasks = [
            approve_request(client, base_url, request_id)
            for request_id in request_ids
        ]
        return await asyncio.gather(*tasks)


def compute_report(
    results: List[RequestResult],
    duration_seconds: float
) -> LoadTestReport:
    """Compute summary statistics from results."""
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    latencies = sorted([r.latency_ms for r in results])

    def percentile(data: List[float], p: float) -> float:
        if not data:
            return 0.0
        k = (len(data) - 1) * p / 100
        f = int(k)
        c = f + 1 if f + 1 < len(data) else f
        return data[f] + (k - f) * (data[c] - data[f])

    return LoadTestReport(
        total_requests=len(results),
        successful=len(successful),
        failed=len(failed),
        latency_p50_ms=percentile(latencies, 50),
        latency_p95_ms=percentile(latencies, 95),
        latency_p99_ms=percentile(latencies, 99),
        latency_max_ms=max(latencies) if latencies else 0,
        requests_per_second=len(results) / duration_seconds if duration_seconds > 0 else 0,
        duration_seconds=duration_seconds,
        errors=list(set(r.error for r in failed if r.error))[:10]
    )


def print_report(report: LoadTestReport, phase: str):
    """Print a formatted report."""
    print(f"\n{'=' * 60}")
    print(f"  {phase} Results")
    print(f"{'=' * 60}")
    print(f"  Total Requests:    {report.total_requests}")
    print(f"  Successful:        {report.successful} ({100 * report.successful / report.total_requests:.1f}%)")
    print(f"  Failed:            {report.failed}")
    print(f"  Duration:          {report.duration_seconds:.2f}s")
    print(f"  Throughput:        {report.requests_per_second:.1f} req/s")
    print(f"\n  Latency:")
    print(f"    p50:             {report.latency_p50_ms:.1f}ms")
    print(f"    p95:             {report.latency_p95_ms:.1f}ms")
    print(f"    p99:             {report.latency_p99_ms:.1f}ms")
    print(f"    max:             {report.latency_max_ms:.1f}ms")

    if report.errors:
        print(f"\n  Errors ({len(report.errors)} unique):")
        for err in report.errors[:5]:
            print(f"    - {err[:80]}")

    print(f"{'=' * 60}\n")


async def main():
    parser = argparse.ArgumentParser(description="Load test approval workflow")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--concurrent", type=int, default=10, help="Concurrent requests per batch")
    parser.add_argument("--total", type=int, default=50, help="Total requests to create")
    parser.add_argument("--skip-approve", action="store_true", help="Skip approval phase")
    args = parser.parse_args()

    print(f"\nLoad Test Configuration:")
    print(f"  Base URL:      {args.base_url}")
    print(f"  Concurrent:    {args.concurrent}")
    print(f"  Total:         {args.total}")
    print(f"  Skip Approve:  {args.skip_approve}")

    # Phase 1: Create requests
    print(f"\n[Phase 1] Creating {args.total} approval requests...")
    all_create_results: List[RequestResult] = []
    start_time = time.perf_counter()

    num_batches = (args.total + args.concurrent - 1) // args.concurrent
    for batch_num in range(num_batches):
        batch_size = min(args.concurrent, args.total - batch_num * args.concurrent)
        results = await run_create_batch(args.base_url, batch_size, batch_num)
        all_create_results.extend(results)
        print(f"  Batch {batch_num + 1}/{num_batches}: {sum(1 for r in results if r.success)}/{batch_size} succeeded")

    create_duration = time.perf_counter() - start_time
    create_report = compute_report(all_create_results, create_duration)
    print_report(create_report, "CREATE REQUESTS")

    # Phase 2: Approve requests (if not skipped)
    if not args.skip_approve:
        created_ids = [r.request_id for r in all_create_results if r.success and r.request_id]

        if created_ids:
            print(f"\n[Phase 2] Approving {len(created_ids)} requests...")
            all_approve_results: List[RequestResult] = []
            start_time = time.perf_counter()

            # Batch approvals
            for i in range(0, len(created_ids), args.concurrent):
                batch = created_ids[i:i + args.concurrent]
                results = await run_approve_batch(args.base_url, batch)
                all_approve_results.extend(results)
                batch_num = i // args.concurrent + 1
                total_batches = (len(created_ids) + args.concurrent - 1) // args.concurrent
                print(f"  Batch {batch_num}/{total_batches}: {sum(1 for r in results if r.success)}/{len(batch)} succeeded")

            approve_duration = time.perf_counter() - start_time
            approve_report = compute_report(all_approve_results, approve_duration)
            print_report(approve_report, "APPROVE REQUESTS")
        else:
            print("\n[Phase 2] Skipped - no requests to approve")

    # Final summary
    print("\n" + "=" * 60)
    print("  LOAD TEST COMPLETE")
    print("=" * 60)

    # Pass/fail criteria
    success_rate = create_report.successful / create_report.total_requests if create_report.total_requests > 0 else 0
    p95_ok = create_report.latency_p95_ms < 500  # p95 under 500ms

    if success_rate >= 0.99 and p95_ok:
        print("  Status: PASS")
        print(f"  - Success rate: {success_rate * 100:.1f}% (>= 99%)")
        print(f"  - p95 latency: {create_report.latency_p95_ms:.1f}ms (< 500ms)")
        return 0
    else:
        print("  Status: FAIL")
        if success_rate < 0.99:
            print(f"  - Success rate: {success_rate * 100:.1f}% (< 99%)")
        if not p95_ok:
            print(f"  - p95 latency: {create_report.latency_p95_ms:.1f}ms (>= 500ms)")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
