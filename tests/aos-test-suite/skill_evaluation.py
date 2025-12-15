#!/usr/bin/env python3
"""
AOS Skill Evaluation Script
Performs dry-run evaluation of all skills and identifies potential issues.
"""

import os
import json
import requests
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime

API_BASE = os.getenv("AOS_API_BASE", "http://localhost:8000")
API_KEY = os.getenv("AOS_API_KEY", "test")

@dataclass
class SkillEvaluation:
    skill_id: str
    available: bool
    cost_cents: int
    latency_ms: int
    rate_limit_remaining: int
    known_failure_patterns: List[str]
    test_result: Optional[str] = None
    issues: List[str] = None

    def __post_init__(self):
        if self.issues is None:
            self.issues = []

class SkillEvaluator:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.evaluations: Dict[str, SkillEvaluation] = {}

    def _headers(self) -> Dict[str, str]:
        return {"X-API-Key": self.api_key, "Content-Type": "application/json"}

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        return requests.request(
            method,
            f"{self.base_url}{path}",
            headers=self._headers(),
            timeout=30,
            **kwargs
        )

    def get_capabilities(self) -> Dict:
        """Fetch current skill capabilities"""
        resp = self._request("GET", "/api/v1/runtime/capabilities")
        return resp.json()

    def simulate_skill(self, skill_id: str, params: Dict = None) -> Dict:
        """Simulate a single skill execution"""
        payload = {
            "plan": [{"skill": skill_id, "params": params or {}}],
            "budget_cents": 1000
        }
        resp = self._request("POST", "/api/v1/runtime/simulate", json=payload)
        return resp.json()

    def evaluate_skill(self, skill_id: str, skill_info: Dict) -> SkillEvaluation:
        """Evaluate a single skill"""
        evaluation = SkillEvaluation(
            skill_id=skill_id,
            available=skill_info.get("available", False),
            cost_cents=skill_info.get("cost_estimate_cents", 0),
            latency_ms=skill_info.get("avg_latency_ms", 0),
            rate_limit_remaining=skill_info.get("rate_limit_remaining", 0),
            known_failure_patterns=skill_info.get("known_failure_patterns", [])
        )

        # Identify potential issues
        if not evaluation.available:
            evaluation.issues.append("Skill is unavailable")

        if evaluation.rate_limit_remaining < 10:
            evaluation.issues.append(f"Low rate limit: {evaluation.rate_limit_remaining}")

        if evaluation.latency_ms > 5000:
            evaluation.issues.append(f"High latency: {evaluation.latency_ms}ms")

        if evaluation.cost_cents > 50:
            evaluation.issues.append(f"High cost: {evaluation.cost_cents}¢")

        if evaluation.known_failure_patterns:
            evaluation.issues.append(f"Known failures: {evaluation.known_failure_patterns}")

        # Test simulation
        try:
            result = self.simulate_skill(skill_id)
            if result.get("feasible"):
                evaluation.test_result = "PASS"
            else:
                evaluation.test_result = "FAIL"
                evaluation.issues.append(f"Simulation not feasible: {result.get('risks', [])}")
        except Exception as e:
            evaluation.test_result = "ERROR"
            evaluation.issues.append(f"Simulation error: {str(e)}")

        return evaluation

    def evaluate_all(self) -> Dict[str, SkillEvaluation]:
        """Evaluate all available skills"""
        print("=" * 60)
        print("AOS SKILL EVALUATION")
        print("=" * 60)
        print()

        capabilities = self.get_capabilities()
        skills = capabilities.get("skills", {})

        print(f"Found {len(skills)} skills to evaluate\n")

        for skill_id, skill_info in skills.items():
            print(f"Evaluating: {skill_id}...", end=" ")
            evaluation = self.evaluate_skill(skill_id, skill_info)
            self.evaluations[skill_id] = evaluation

            if evaluation.test_result == "PASS" and not evaluation.issues:
                print("✅ OK")
            elif evaluation.test_result == "PASS":
                print(f"⚠️ OK with warnings")
            else:
                print(f"❌ {evaluation.test_result}")

        return self.evaluations

    def generate_report(self) -> Dict:
        """Generate evaluation report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_skills": len(self.evaluations),
            "available": sum(1 for e in self.evaluations.values() if e.available),
            "passed": sum(1 for e in self.evaluations.values() if e.test_result == "PASS"),
            "with_issues": sum(1 for e in self.evaluations.values() if e.issues),
            "skills": {}
        }

        for skill_id, evaluation in self.evaluations.items():
            report["skills"][skill_id] = {
                "available": evaluation.available,
                "cost_cents": evaluation.cost_cents,
                "latency_ms": evaluation.latency_ms,
                "rate_limit": evaluation.rate_limit_remaining,
                "test_result": evaluation.test_result,
                "issues": evaluation.issues
            }

        return report

    def print_report(self):
        """Print detailed report"""
        report = self.generate_report()

        print()
        print("=" * 60)
        print("EVALUATION REPORT")
        print("=" * 60)
        print(f"Total Skills:     {report['total_skills']}")
        print(f"Available:        {report['available']}")
        print(f"Tests Passed:     {report['passed']}")
        print(f"With Issues:      {report['with_issues']}")
        print()

        print("Skill Details:")
        print("-" * 60)
        for skill_id, details in report["skills"].items():
            status = "✅" if details["test_result"] == "PASS" and not details["issues"] else "⚠️" if details["test_result"] == "PASS" else "❌"
            print(f"\n{status} {skill_id}")
            print(f"   Cost: {details['cost_cents']}¢ | Latency: {details['latency_ms']}ms | Rate Limit: {details['rate_limit']}")
            if details["issues"]:
                for issue in details["issues"]:
                    print(f"   ⚠ {issue}")

        # Recommendations
        print()
        print("=" * 60)
        print("RECOMMENDATIONS")
        print("=" * 60)

        high_cost = [s for s, d in report["skills"].items() if d["cost_cents"] > 10]
        if high_cost:
            print(f"\n📊 High cost skills (>10¢): {', '.join(high_cost)}")
            print("   Consider budget limits for these skills")

        high_latency = [s for s, d in report["skills"].items() if d["latency_ms"] > 1000]
        if high_latency:
            print(f"\n⏱️ High latency skills (>1s): {', '.join(high_latency)}")
            print("   Consider timeouts and async handling")

        low_rate = [s for s, d in report["skills"].items() if d["rate_limit"] < 20]
        if low_rate:
            print(f"\n🚦 Low rate limit skills (<20): {', '.join(low_rate)}")
            print("   Consider rate limiting in orchestration")

def main():
    evaluator = SkillEvaluator(API_BASE, API_KEY)
    evaluator.evaluate_all()
    evaluator.print_report()

    # Save report to file
    report = evaluator.generate_report()
    with open("/tmp/skill_evaluation_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nFull report saved to: /tmp/skill_evaluation_report.json")

if __name__ == "__main__":
    main()
