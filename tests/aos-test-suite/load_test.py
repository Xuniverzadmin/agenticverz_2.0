#!/usr/bin/env python3
"""
AOS Load Test Suite
Simulates concurrent agent workloads and measures performance.
"""

import os
import sys
import json
import time
import asyncio
import aiohttp
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from statistics import mean, median, stdev
import argparse

# Configuration
API_BASE = os.getenv("AOS_API_BASE", "http://localhost:8000")
API_KEY = os.getenv("AOS_API_KEY", "test")

@dataclass
class RequestResult:
    endpoint: str
    status_code: int
    latency_ms: float
    success: bool
    error: Optional[str] = None

@dataclass
class LoadTestResult:
    total_requests: int
    successful: int
    failed: int
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    requests_per_second: float
    duration_seconds: float
    errors: Dict[str, int] = field(default_factory=dict)

class AOSLoadTest:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.results: List[RequestResult] = []

    def _headers(self) -> Dict[str, str]:
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

    async def _make_request(
        self,
        session: aiohttp.ClientSession,
        method: str,
        path: str,
        json_data: Optional[Dict] = None
    ) -> RequestResult:
        url = f"{self.base_url}{path}"
        start = time.perf_counter()
        try:
            async with session.request(
                method, url,
                headers=self._headers(),
                json=json_data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                latency = (time.perf_counter() - start) * 1000
                await resp.read()
                return RequestResult(
                    endpoint=path,
                    status_code=resp.status,
                    latency_ms=latency,
                    success=resp.status < 400
                )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return RequestResult(
                endpoint=path,
                status_code=0,
                latency_ms=latency,
                success=False,
                error=str(e)
            )

    async def run_health_check_load(
        self,
        concurrency: int = 10,
        total_requests: int = 100
    ) -> LoadTestResult:
        """Load test the health endpoint"""
        print(f"\n📊 Health Check Load Test: {total_requests} requests, {concurrency} concurrent")

        async with aiohttp.ClientSession() as session:
            start = time.perf_counter()

            sem = asyncio.Semaphore(concurrency)
            async def bounded_request():
                async with sem:
                    return await self._make_request(session, "GET", "/health")

            tasks = [bounded_request() for _ in range(total_requests)]
            results = await asyncio.gather(*tasks)

            duration = time.perf_counter() - start

        return self._calculate_stats(results, duration)

    async def run_simulate_load(
        self,
        concurrency: int = 5,
        total_requests: int = 50
    ) -> LoadTestResult:
        """Load test the simulate endpoint"""
        print(f"\n📊 Simulate Load Test: {total_requests} requests, {concurrency} concurrent")

        payload = {
            "plan": [
                {"skill": "llm_invoke", "params": {"prompt": "test"}},
                {"skill": "json_transform", "params": {"data": {}}}
            ],
            "budget_cents": 1000
        }

        async with aiohttp.ClientSession() as session:
            start = time.perf_counter()

            sem = asyncio.Semaphore(concurrency)
            async def bounded_request():
                async with sem:
                    return await self._make_request(
                        session, "POST",
                        "/api/v1/runtime/simulate",
                        json_data=payload
                    )

            tasks = [bounded_request() for _ in range(total_requests)]
            results = await asyncio.gather(*tasks)

            duration = time.perf_counter() - start

        return self._calculate_stats(results, duration)

    async def run_capabilities_load(
        self,
        concurrency: int = 10,
        total_requests: int = 100
    ) -> LoadTestResult:
        """Load test the capabilities endpoint"""
        print(f"\n📊 Capabilities Load Test: {total_requests} requests, {concurrency} concurrent")

        async with aiohttp.ClientSession() as session:
            start = time.perf_counter()

            sem = asyncio.Semaphore(concurrency)
            async def bounded_request():
                async with sem:
                    return await self._make_request(
                        session, "GET",
                        "/api/v1/runtime/capabilities"
                    )

            tasks = [bounded_request() for _ in range(total_requests)]
            results = await asyncio.gather(*tasks)

            duration = time.perf_counter() - start

        return self._calculate_stats(results, duration)

    async def run_mixed_workload(
        self,
        duration_seconds: int = 30,
        concurrency: int = 10
    ) -> LoadTestResult:
        """Run mixed workload simulating real usage"""
        print(f"\n📊 Mixed Workload: {duration_seconds}s duration, {concurrency} concurrent")

        endpoints = [
            ("GET", "/health", None),
            ("GET", "/api/v1/runtime/capabilities", None),
            ("POST", "/api/v1/runtime/simulate", {
                "plan": [{"skill": "llm_invoke", "params": {}}],
                "budget_cents": 100
            }),
            ("GET", "/api/v1/recovery/stats", None),
        ]

        results = []
        start = time.perf_counter()
        end_time = start + duration_seconds

        async with aiohttp.ClientSession() as session:
            sem = asyncio.Semaphore(concurrency)

            async def worker():
                while time.perf_counter() < end_time:
                    import random
                    method, path, data = random.choice(endpoints)
                    async with sem:
                        result = await self._make_request(session, method, path, data)
                        results.append(result)
                    await asyncio.sleep(0.01)  # Small delay

            workers = [worker() for _ in range(concurrency)]
            await asyncio.gather(*workers)

        duration = time.perf_counter() - start
        return self._calculate_stats(results, duration)

    def _calculate_stats(
        self,
        results: List[RequestResult],
        duration: float
    ) -> LoadTestResult:
        """Calculate statistics from results"""
        latencies = sorted([r.latency_ms for r in results])
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        # Error aggregation
        errors = {}
        for r in failed:
            key = r.error or f"HTTP {r.status_code}"
            errors[key] = errors.get(key, 0) + 1

        return LoadTestResult(
            total_requests=len(results),
            successful=len(successful),
            failed=len(failed),
            avg_latency_ms=mean(latencies) if latencies else 0,
            p50_latency_ms=latencies[len(latencies)//2] if latencies else 0,
            p95_latency_ms=latencies[int(len(latencies)*0.95)] if latencies else 0,
            p99_latency_ms=latencies[int(len(latencies)*0.99)] if latencies else 0,
            requests_per_second=len(results) / duration if duration > 0 else 0,
            duration_seconds=duration,
            errors=errors
        )

    def print_result(self, name: str, result: LoadTestResult):
        """Print formatted result"""
        print(f"\n{'='*50}")
        print(f"📈 {name}")
        print(f"{'='*50}")
        print(f"  Total Requests:    {result.total_requests}")
        print(f"  Successful:        {result.successful}")
        print(f"  Failed:            {result.failed}")
        print(f"  Success Rate:      {(result.successful/result.total_requests*100):.1f}%")
        print(f"  Duration:          {result.duration_seconds:.2f}s")
        print(f"  RPS:               {result.requests_per_second:.1f}")
        print(f"  Avg Latency:       {result.avg_latency_ms:.1f}ms")
        print(f"  P50 Latency:       {result.p50_latency_ms:.1f}ms")
        print(f"  P95 Latency:       {result.p95_latency_ms:.1f}ms")
        print(f"  P99 Latency:       {result.p99_latency_ms:.1f}ms")
        if result.errors:
            print(f"  Errors:")
            for err, count in result.errors.items():
                print(f"    - {err}: {count}")

async def main():
    parser = argparse.ArgumentParser(description="AOS Load Test Suite")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrent requests")
    parser.add_argument("--requests", type=int, default=100, help="Total requests per test")
    parser.add_argument("--duration", type=int, default=30, help="Duration for mixed workload")
    parser.add_argument("--test", choices=["health", "simulate", "capabilities", "mixed", "all"],
                       default="all", help="Which test to run")
    args = parser.parse_args()

    print("=" * 60)
    print("AOS LOAD TEST SUITE")
    print("=" * 60)
    print(f"API Base: {API_BASE}")
    print(f"Concurrency: {args.concurrency}")
    print(f"Requests per test: {args.requests}")
    print("=" * 60)

    tester = AOSLoadTest(API_BASE, API_KEY)

    if args.test in ["health", "all"]:
        result = await tester.run_health_check_load(args.concurrency, args.requests)
        tester.print_result("Health Check Load Test", result)

    if args.test in ["capabilities", "all"]:
        result = await tester.run_capabilities_load(args.concurrency, args.requests)
        tester.print_result("Capabilities Load Test", result)

    if args.test in ["simulate", "all"]:
        result = await tester.run_simulate_load(args.concurrency // 2, args.requests // 2)
        tester.print_result("Simulate Load Test", result)

    if args.test in ["mixed", "all"]:
        result = await tester.run_mixed_workload(args.duration, args.concurrency)
        tester.print_result("Mixed Workload Test", result)

    print("\n" + "=" * 60)
    print("LOAD TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
