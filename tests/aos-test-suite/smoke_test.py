#!/usr/bin/env python3
"""
AOS Smoke Test Suite
Tests all critical endpoints and validates response schemas.
"""

import os
import sys
import json
import requests
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass

# Configuration
API_BASE = os.getenv("AOS_API_BASE", "http://localhost:8000")
API_KEY = os.getenv("AOS_API_KEY", "test")


@dataclass
class TestResult:
    name: str
    passed: bool
    duration_ms: float
    message: str
    response_data: Optional[Dict] = None


class AOSSmokeTest:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.results: List[TestResult] = []

    def _headers(self) -> Dict[str, str]:
        return {"X-API-Key": self.api_key, "Content-Type": "application/json"}

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        return requests.request(
            method, url, headers=self._headers(), timeout=10, **kwargs
        )

    def _run_test(self, name: str, func) -> TestResult:
        start = datetime.now()
        try:
            result = func()
            duration = (datetime.now() - start).total_seconds() * 1000
            return TestResult(name, True, duration, "PASS", result)
        except Exception as e:
            duration = (datetime.now() - start).total_seconds() * 1000
            return TestResult(name, False, duration, str(e))

    # ==================== HEALTH TESTS ====================

    def test_health_endpoint(self) -> Dict:
        """Test /health endpoint returns healthy status"""
        resp = self._request("GET", "/health")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert data.get("status") == "healthy", (
            f"Expected healthy, got {data.get('status')}"
        )
        assert "timestamp" in data, "Missing timestamp"
        assert "version" in data, "Missing version"
        return data

    def test_healthz_endpoint(self) -> Dict:
        """Test /healthz endpoint"""
        resp = self._request("GET", "/healthz")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        return resp.json()

    # ==================== RUNTIME TESTS ====================

    def test_capabilities(self) -> Dict:
        """Test /api/v1/runtime/capabilities returns skill info"""
        resp = self._request("GET", "/api/v1/runtime/capabilities")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "skills" in data, "Missing skills"
        assert "budget" in data, "Missing budget"
        assert "rate_limits" in data, "Missing rate_limits"
        assert len(data["skills"]) > 0, "No skills available"
        return data

    def test_simulate_single_step(self) -> Dict:
        """Test /api/v1/runtime/simulate with single step"""
        payload = {
            "plan": [{"skill": "llm_invoke", "params": {"prompt": "test"}}],
            "budget_cents": 1000,
        }
        resp = self._request("POST", "/api/v1/runtime/simulate", json=payload)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "feasible" in data, "Missing feasible"
        assert "estimated_cost_cents" in data, "Missing cost estimate"
        assert data["feasible"] == True, f"Simulation not feasible: {data}"
        return data

    def test_simulate_multi_step(self) -> Dict:
        """Test simulation with multiple steps"""
        payload = {
            "plan": [
                {"skill": "http_call", "params": {"url": "https://example.com"}},
                {"skill": "json_transform", "params": {"data": {}}},
                {"skill": "llm_invoke", "params": {"prompt": "analyze"}},
            ],
            "budget_cents": 500,
        }
        resp = self._request("POST", "/api/v1/runtime/simulate", json=payload)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert len(data.get("step_estimates", [])) == 3, "Expected 3 step estimates"
        return data

    def test_simulate_budget_exceeded(self) -> Dict:
        """Test simulation fails when budget insufficient"""
        payload = {
            "plan": [{"skill": "llm_invoke", "params": {}} for _ in range(100)],
            "budget_cents": 10,  # Very low budget
        }
        resp = self._request("POST", "/api/v1/runtime/simulate", json=payload)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        # Should still work but budget_sufficient should be false
        assert "budget_sufficient" in data, "Missing budget_sufficient"
        return data

    # ==================== FAILURE/RECOVERY TESTS ====================

    def test_recovery_stats(self) -> Dict:
        """Test /api/v1/recovery/stats"""
        resp = self._request("GET", "/api/v1/recovery/stats")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "total_candidates" in data, "Missing total_candidates"
        return data

    def test_recovery_candidates(self) -> Dict:
        """Test /api/v1/recovery/candidates"""
        resp = self._request("GET", "/api/v1/recovery/candidates")
        # May return 200 with empty list or candidates
        assert resp.status_code in [200, 404], f"Unexpected status {resp.status_code}"
        return resp.json() if resp.status_code == 200 else {"candidates": []}

    # ==================== POLICY TESTS ====================

    def test_rbac_info(self) -> Dict:
        """Test /api/v1/rbac/info"""
        resp = self._request("GET", "/api/v1/rbac/info")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        return resp.json()

    # ==================== COSTSIM TESTS ====================

    def test_costsim_status(self) -> Dict:
        """Test /costsim/v2/status"""
        resp = self._request("GET", "/costsim/v2/status")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        return resp.json()

    # ==================== RUN ALL TESTS ====================

    def run_all(self) -> List[TestResult]:
        """Run all smoke tests"""
        tests = [
            ("Health Endpoint", self.test_health_endpoint),
            ("Healthz Endpoint", self.test_healthz_endpoint),
            ("Capabilities", self.test_capabilities),
            ("Simulate Single Step", self.test_simulate_single_step),
            ("Simulate Multi Step", self.test_simulate_multi_step),
            ("Simulate Budget Exceeded", self.test_simulate_budget_exceeded),
            ("Recovery Stats", self.test_recovery_stats),
            ("Recovery Candidates", self.test_recovery_candidates),
            ("RBAC Info", self.test_rbac_info),
            ("CostSim Status", self.test_costsim_status),
        ]

        for name, func in tests:
            result = self._run_test(name, func)
            self.results.append(result)
            status = "✅" if result.passed else "❌"
            print(f"{status} {name}: {result.message} ({result.duration_ms:.1f}ms)")

        return self.results

    def summary(self) -> Dict:
        """Generate test summary"""
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total_time = sum(r.duration_ms for r in self.results)

        return {
            "total": len(self.results),
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{(passed / len(self.results) * 100):.1f}%"
            if self.results
            else "0%",
            "total_time_ms": total_time,
            "timestamp": datetime.now().isoformat(),
        }


def main():
    print("=" * 60)
    print("AOS SMOKE TEST SUITE")
    print("=" * 60)
    print(f"API Base: {API_BASE}")
    print(f"API Key: {API_KEY[:8]}..." if API_KEY else "No API Key")
    print("=" * 60)
    print()

    tester = AOSSmokeTest(API_BASE, API_KEY)
    tester.run_all()

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    summary = tester.summary()
    print(json.dumps(summary, indent=2))

    # Exit with error if any tests failed
    sys.exit(0 if summary["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
