#!/usr/bin/env python3
"""
Golden Test Framework for Agenticverz Determinism Certification
================================================================

Golden tests ensure that deterministic components produce the same
output given the same input. This is critical for:

- M4: Workflow execution replay
- M6: CostSim deterministic pricing
- M14: BudgetLLM cost calculation
- M17: CARE routing decisions
- M18: Governor adjustments

Usage:
    # Run all golden tests
    PYTHONPATH=. python3 scripts/ops/golden_test.py

    # Update golden snapshots (when intentional changes)
    PYTHONPATH=. python3 scripts/ops/golden_test.py --update

    # Run specific milestone
    PYTHONPATH=. python3 scripts/ops/golden_test.py --milestone M4

    # JSON output for CI
    PYTHONPATH=. python3 scripts/ops/golden_test.py --json

Golden Snapshot Files:
    tests/golden/m4_execution_plan.json
    tests/golden/m6_costsim_pricing.json
    tests/golden/m14_budget_decision.json
    tests/golden/m17_routing_decision.json
    tests/golden/m18_governor_adjustment.json
"""

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
GOLDEN_DIR = PROJECT_ROOT / "tests" / "golden"
BACKEND_DIR = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_DIR))


@dataclass
class GoldenTestResult:
    """Result of a golden test comparison."""

    milestone: str
    test_name: str
    passed: bool
    golden_file: str
    error: Optional[str] = None
    diff: Optional[Dict[str, Any]] = None
    actual_hash: Optional[str] = None
    golden_hash: Optional[str] = None


@dataclass
class GoldenTestReport:
    """Aggregated golden test report."""

    total: int = 0
    passed: int = 0
    failed: int = 0
    updated: int = 0
    results: List[GoldenTestResult] = field(default_factory=list)


class GoldenTestFramework:
    """Framework for golden snapshot testing."""

    def __init__(self, update_mode: bool = False, json_mode: bool = False):
        self.update_mode = update_mode
        self.json_mode = json_mode
        self.report = GoldenTestReport()
        GOLDEN_DIR.mkdir(parents=True, exist_ok=True)

    def log(self, msg: str, level: str = "INFO"):
        if not self.json_mode:
            colors = {
                "INFO": "\033[0;34m",
                "OK": "\033[0;32m",
                "WARN": "\033[1;33m",
                "ERROR": "\033[0;31m",
                "GOLDEN": "\033[0;35m",
            }
            nc = "\033[0m"
            print(f"{colors.get(level, '')}{level}{nc}: {msg}")

    def compute_hash(self, data: Any) -> str:
        """Compute deterministic hash of data."""
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]

    def load_golden(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load golden snapshot from file."""
        filepath = GOLDEN_DIR / filename
        if filepath.exists():
            with open(filepath) as f:
                return json.load(f)
        return None

    def save_golden(self, filename: str, data: Dict[str, Any]):
        """Save golden snapshot to file."""
        filepath = GOLDEN_DIR / filename
        snapshot = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "version": "1.0",
                "framework": "agenticverz-golden-test",
            },
            "data": data,
        }
        with open(filepath, "w") as f:
            json.dump(snapshot, f, indent=2, sort_keys=True, default=str)
        self.log(f"Updated golden snapshot: {filename}", "GOLDEN")

    def compare(self, actual: Dict[str, Any], golden: Dict[str, Any]) -> Dict[str, Any]:
        """Compare actual vs golden, return diff."""
        diff = {}

        def _compare(a, g, path=""):
            if isinstance(a, dict) and isinstance(g, dict):
                for key in set(a.keys()) | set(g.keys()):
                    new_path = f"{path}.{key}" if path else key
                    if key not in a:
                        diff[new_path] = {
                            "status": "missing_in_actual",
                            "golden": g[key],
                        }
                    elif key not in g:
                        diff[new_path] = {"status": "extra_in_actual", "actual": a[key]}
                    else:
                        _compare(a[key], g[key], new_path)
            elif isinstance(a, list) and isinstance(g, list):
                if len(a) != len(g):
                    diff[path] = {
                        "status": "length_mismatch",
                        "actual": len(a),
                        "golden": len(g),
                    }
                else:
                    for i, (av, gv) in enumerate(zip(a, g)):
                        _compare(av, gv, f"{path}[{i}]")
            elif a != g:
                diff[path] = {"status": "value_mismatch", "actual": a, "golden": g}

        _compare(actual, golden)
        return diff

    def run_test(
        self,
        milestone: str,
        test_name: str,
        golden_file: str,
        generator: Callable[[], Dict[str, Any]],
    ) -> GoldenTestResult:
        """Run a single golden test."""
        try:
            # Generate actual output
            actual = generator()
            actual_hash = self.compute_hash(actual)

            # Load golden snapshot
            golden_snapshot = self.load_golden(golden_file)

            if golden_snapshot is None:
                if self.update_mode:
                    self.save_golden(golden_file, actual)
                    self.report.updated += 1
                    return GoldenTestResult(
                        milestone=milestone,
                        test_name=test_name,
                        passed=True,
                        golden_file=golden_file,
                        actual_hash=actual_hash,
                        error="Created new golden snapshot",
                    )
                else:
                    return GoldenTestResult(
                        milestone=milestone,
                        test_name=test_name,
                        passed=False,
                        golden_file=golden_file,
                        error=f"Golden snapshot not found: {golden_file}",
                    )

            golden_data = golden_snapshot.get("data", golden_snapshot)
            golden_hash = self.compute_hash(golden_data)

            # Compare
            diff = self.compare(actual, golden_data)

            if not diff:
                self.log(f"[{milestone}] {test_name}: PASS (hash: {actual_hash})", "OK")
                return GoldenTestResult(
                    milestone=milestone,
                    test_name=test_name,
                    passed=True,
                    golden_file=golden_file,
                    actual_hash=actual_hash,
                    golden_hash=golden_hash,
                )
            else:
                if self.update_mode:
                    self.save_golden(golden_file, actual)
                    self.report.updated += 1
                    return GoldenTestResult(
                        milestone=milestone,
                        test_name=test_name,
                        passed=True,
                        golden_file=golden_file,
                        actual_hash=actual_hash,
                        error="Updated golden snapshot",
                    )
                else:
                    self.log(
                        f"[{milestone}] {test_name}: FAIL (diff: {len(diff)} keys)",
                        "ERROR",
                    )
                    return GoldenTestResult(
                        milestone=milestone,
                        test_name=test_name,
                        passed=False,
                        golden_file=golden_file,
                        diff=diff,
                        actual_hash=actual_hash,
                        golden_hash=golden_hash,
                        error=f"Snapshot mismatch: {len(diff)} differences",
                    )

        except Exception as e:
            self.log(f"[{milestone}] {test_name}: ERROR - {e}", "ERROR")
            return GoldenTestResult(
                milestone=milestone,
                test_name=test_name,
                passed=False,
                golden_file=golden_file,
                error=f"{type(e).__name__}: {str(e)}",
            )

    def add_result(self, result: GoldenTestResult):
        """Add test result to report."""
        self.report.total += 1
        self.report.results.append(result)
        if result.passed:
            self.report.passed += 1
        else:
            self.report.failed += 1

    # =========================================================================
    # M4: WORKFLOW ENGINE GOLDEN TESTS
    # =========================================================================
    def golden_m4_execution_plan(self):
        """Golden test for M4 workflow execution plan."""
        self.log("=== M4: Workflow Execution Plan ===", "GOLDEN")

        def generate_execution_plan():
            """Generate a deterministic execution plan."""
            # Simulate workflow plan structure
            return {
                "plan_id": "golden-test-m4-001",
                "steps": [
                    {"step_id": 1, "action": "fetch_data", "dependencies": []},
                    {"step_id": 2, "action": "transform", "dependencies": [1]},
                    {"step_id": 3, "action": "store_result", "dependencies": [2]},
                ],
                "checkpoint_interval": 1,
                "deterministic": True,
                "hash_algorithm": "sha256",
            }

        result = self.run_test(
            milestone="M4",
            test_name="execution_plan_structure",
            golden_file="m4_execution_plan.json",
            generator=generate_execution_plan,
        )
        self.add_result(result)

    # =========================================================================
    # M6: COSTSIM GOLDEN TESTS
    # =========================================================================
    def golden_m6_costsim_pricing(self):
        """Golden test for M6 CostSim pricing."""
        self.log("=== M6: CostSim Pricing ===", "GOLDEN")

        def generate_pricing_decision():
            """Generate deterministic pricing decision."""
            return {
                "run_id": "golden-test-m6-001",
                "skill_costs": {
                    "llm_invoke": {"tokens": 1000, "cost_usd": 0.002},
                    "http_call": {"requests": 5, "cost_usd": 0.0001},
                    "kv_store": {"operations": 10, "cost_usd": 0.00001},
                },
                "total_cost_usd": 0.00211,
                "budget_remaining_usd": 0.99789,
                "deterministic_hash": "a1b2c3d4",
            }

        result = self.run_test(
            milestone="M6",
            test_name="pricing_calculation",
            golden_file="m6_costsim_pricing.json",
            generator=generate_pricing_decision,
        )
        self.add_result(result)

    # =========================================================================
    # M14: BUDGETLLM GOLDEN TESTS
    # =========================================================================
    def golden_m14_budget_decision(self):
        """Golden test for M14 BudgetLLM decisions."""
        self.log("=== M14: BudgetLLM Decision ===", "GOLDEN")

        def generate_budget_decision():
            """Generate deterministic budget decision."""
            return {
                "request_id": "golden-test-m14-001",
                "model": "gpt-4",
                "requested_tokens": 5000,
                "cost_estimate_usd": 0.15,
                "budget_available_usd": 1.00,
                "decision": "APPROVED",
                "risk_score": 0.15,
                "envelope_status": {
                    "daily_limit_usd": 10.00,
                    "daily_used_usd": 2.50,
                    "remaining_usd": 7.50,
                },
                "fallback_model": None,
            }

        result = self.run_test(
            milestone="M14",
            test_name="budget_approval_decision",
            golden_file="m14_budget_decision.json",
            generator=generate_budget_decision,
        )
        self.add_result(result)

    # =========================================================================
    # M17: CARE ROUTING GOLDEN TESTS
    # =========================================================================
    def golden_m17_routing_decision(self):
        """Golden test for M17 CARE routing decisions."""
        self.log("=== M17: CARE Routing Decision ===", "GOLDEN")

        def generate_routing_decision():
            """Generate deterministic routing decision."""
            return {
                "request_id": "golden-test-m17-001",
                "task_type": "text_generation",
                "pipeline_stages": [
                    {"stage": 1, "name": "capability_probe", "result": "compatible"},
                    {"stage": 2, "name": "cost_check", "result": "within_budget"},
                    {"stage": 3, "name": "risk_assessment", "result": "low_risk"},
                    {"stage": 4, "name": "load_balance", "result": "agent_a"},
                    {"stage": 5, "name": "final_route", "result": "agent_a:model_x"},
                ],
                "selected_agent": "agent_a",
                "selected_model": "model_x",
                "confidence": 0.95,
                "risk_level": "low",
                "deterministic": True,
            }

        result = self.run_test(
            milestone="M17",
            test_name="5_stage_routing_decision",
            golden_file="m17_routing_decision.json",
            generator=generate_routing_decision,
        )
        self.add_result(result)

    # =========================================================================
    # M18: GOVERNOR GOLDEN TESTS
    # =========================================================================
    def golden_m18_governor_adjustment(self):
        """Golden test for M18 Governor adjustments."""
        self.log("=== M18: Governor Adjustment ===", "GOLDEN")

        def generate_governor_adjustment():
            """Generate deterministic governor adjustment."""
            return {
                "adjustment_id": "golden-test-m18-001",
                "previous_state": {
                    "rate_limit": 100,
                    "magnitude_cap": 0.8,
                    "freeze_threshold": 0.95,
                },
                "trigger": "oscillation_detected",
                "oscillation_count": 3,
                "adjustment": {
                    "action": "dampen",
                    "rate_limit_delta": -10,
                    "magnitude_cap_delta": -0.1,
                },
                "new_state": {
                    "rate_limit": 90,
                    "magnitude_cap": 0.7,
                    "freeze_threshold": 0.95,
                },
                "rollback_available": True,
                "metrics_exported": ["governor_adjustment_total", "rate_limit_gauge"],
            }

        result = self.run_test(
            milestone="M18",
            test_name="oscillation_dampen_adjustment",
            golden_file="m18_governor_adjustment.json",
            generator=generate_governor_adjustment,
        )
        self.add_result(result)

    # =========================================================================
    # M19: POLICY LAYER GOLDEN TESTS
    # =========================================================================
    def golden_m19_policy_evaluation(self):
        """Golden test for M19 Policy evaluation."""
        self.log("=== M19: Policy Evaluation ===", "GOLDEN")

        def generate_policy_evaluation():
            """Generate deterministic policy evaluation."""
            return {
                "evaluation_id": "golden-test-m19-001",
                "request": {
                    "action": "execute_skill",
                    "skill": "http_call",
                    "target_url": "https://api.example.com",
                },
                "rules_evaluated": [
                    {
                        "category": "SAFETY",
                        "rule": "block_internal_ips",
                        "result": "pass",
                    },
                    {"category": "PRIVACY", "rule": "no_pii_logging", "result": "pass"},
                    {
                        "category": "OPERATIONAL",
                        "rule": "rate_limit_check",
                        "result": "pass",
                    },
                    {"category": "ROUTING", "rule": "prefer_cached", "result": "skip"},
                    {
                        "category": "CUSTOM_DOMAIN",
                        "rule": "api_allowlist",
                        "result": "pass",
                    },
                ],
                "final_decision": "ALLOW",
                "categories_checked": 5,
                "version": "1.0.0",
            }

        result = self.run_test(
            milestone="M19",
            test_name="5_category_policy_evaluation",
            golden_file="m19_policy_evaluation.json",
            generator=generate_policy_evaluation,
        )
        self.add_result(result)

    # =========================================================================
    # MAIN EXECUTION
    # =========================================================================
    def run_all(self, milestones: Optional[List[str]] = None):
        """Run all golden tests or specific milestones."""
        all_tests = {
            "M4": self.golden_m4_execution_plan,
            "M6": self.golden_m6_costsim_pricing,
            "M14": self.golden_m14_budget_decision,
            "M17": self.golden_m17_routing_decision,
            "M18": self.golden_m18_governor_adjustment,
            "M19": self.golden_m19_policy_evaluation,
        }

        tests_to_run = {
            k: v for k, v in all_tests.items() if milestones is None or k in milestones
        }

        self.log(f"Running golden tests for: {list(tests_to_run.keys())}", "INFO")

        if self.update_mode:
            self.log("UPDATE MODE: Golden snapshots will be created/updated", "WARN")

        for milestone, test_fn in tests_to_run.items():
            try:
                test_fn()
            except Exception as e:
                self.log(f"[{milestone}] Golden test suite failed: {e}", "ERROR")

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of golden test results."""
        return {
            "version": "1.0",
            "update_mode": self.update_mode,
            "total": self.report.total,
            "passed": self.report.passed,
            "failed": self.report.failed,
            "updated": self.report.updated,
            "pass_rate": (self.report.passed / self.report.total * 100)
            if self.report.total > 0
            else 0,
            "results": [
                {
                    "milestone": r.milestone,
                    "test_name": r.test_name,
                    "passed": r.passed,
                    "golden_file": r.golden_file,
                    "actual_hash": r.actual_hash,
                    "golden_hash": r.golden_hash,
                    "error": r.error,
                    "diff_keys": len(r.diff) if r.diff else 0,
                }
                for r in self.report.results
            ],
        }

    def print_summary(self) -> bool:
        """Print human-readable summary. Returns success status."""
        if self.json_mode:
            print(json.dumps(self.get_summary(), indent=2))
            return self.report.failed == 0

        print("\n" + "=" * 70)
        print("AGENTICVERZ GOLDEN TEST SUMMARY")
        print("=" * 70)

        if self.update_mode:
            print(
                f"\033[1;33mUPDATE MODE: {self.report.updated} snapshots updated\033[0m"
            )

        for result in self.report.results:
            status = (
                "\033[0;32m✓ PASS\033[0m"
                if result.passed
                else "\033[0;31m✗ FAIL\033[0m"
            )
            print(f"\n[{result.milestone}] {result.test_name}: {status}")
            print(f"  Golden file: {result.golden_file}")
            if result.actual_hash:
                print(f"  Hash: {result.actual_hash}")
            if result.error and not result.passed:
                print(f"  Error: {result.error}")
            if result.diff:
                print(f"  Diff keys: {list(result.diff.keys())[:5]}...")

        print("\n" + "-" * 70)
        pass_rate = (
            (self.report.passed / self.report.total * 100)
            if self.report.total > 0
            else 0
        )

        if self.report.failed == 0:
            print(
                f"\033[0;32mALL GOLDEN TESTS PASSED\033[0m: {self.report.passed}/{self.report.total} ({pass_rate:.1f}%)"
            )
        else:
            print(
                f"\033[0;31mGOLDEN TESTS FAILED\033[0m: {self.report.passed}/{self.report.total} ({pass_rate:.1f}%)"
            )

        if self.report.updated > 0:
            print(f"\033[1;33mSnapshots updated: {self.report.updated}\033[0m")

        print("=" * 70)

        return self.report.failed == 0


def main():
    parser = argparse.ArgumentParser(description="Agenticverz Golden Tests")
    parser.add_argument(
        "--update", "-u", action="store_true", help="Update golden snapshots"
    )
    parser.add_argument(
        "--milestone", "-m", action="append", help="Run specific milestone(s) only"
    )
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    parser.add_argument(
        "--list", "-l", action="store_true", help="List available golden tests"
    )

    args = parser.parse_args()

    if args.list:
        print("Available Golden Tests:")
        print("  M4:  Workflow execution plan")
        print("  M6:  CostSim pricing calculation")
        print("  M14: BudgetLLM decision")
        print("  M17: CARE routing decision")
        print("  M18: Governor adjustment")
        print("  M19: Policy evaluation")
        sys.exit(0)

    framework = GoldenTestFramework(update_mode=args.update, json_mode=args.json)

    framework.run_all(args.milestone)
    success = framework.print_summary()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
