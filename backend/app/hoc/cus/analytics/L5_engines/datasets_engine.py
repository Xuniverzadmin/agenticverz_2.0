# capability_id: CAP-002
# Layer: L5 — Domain Engine
# NOTE: Renamed datasets.py → datasets_engine.py (2026-01-31)
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none (static reference data)
#   Writes: none
# Role: CostSim V2 reference datasets (validation samples)
# Callers: canary runner, divergence engine
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470

# CostSim V2 Reference Datasets (M6)
"""
Reference datasets for V2 validation.

Required datasets (5):
1. low_variance - Simple, predictable plans
2. high_variance - Complex, high-variance plans
3. mixed_city - Mixed workload patterns
4. noise_injected - Plans with deliberate noise
5. historical - Real historical data samples

Each dataset provides:
- Sample plans for testing
- Expected V2 behavior
- Validation metrics thresholds
"""

from __future__ import annotations

import logging
import math
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.hoc.cus.analytics.L5_engines.costsim_models import ValidationResult
from app.hoc.cus.analytics.L5_engines.v2_adapter import CostSimV2Adapter

logger = logging.getLogger("nova.costsim.datasets")


@dataclass
class DatasetSample:
    """A single sample in a reference dataset."""

    id: str
    plan: List[Dict[str, Any]]
    budget_cents: int
    expected_cost_cents: Optional[int] = None
    expected_feasible: Optional[bool] = None
    expected_confidence_min: Optional[float] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class ReferenceDataset:
    """A reference dataset for validation."""

    id: str
    name: str
    description: str
    samples: List[DatasetSample]
    validation_thresholds: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "sample_count": len(self.samples),
            "thresholds": self.validation_thresholds,
        }


class DatasetValidator:
    """
    Validator for V2 against reference datasets.

    Usage:
        validator = DatasetValidator()
        result = await validator.validate_dataset("low_variance")
    """

    def __init__(self):
        """Initialize validator with built-in datasets."""
        self._datasets = self._build_datasets()

    def _build_datasets(self) -> Dict[str, ReferenceDataset]:
        """Build all reference datasets."""
        return {
            "low_variance": self._build_low_variance_dataset(),
            "high_variance": self._build_high_variance_dataset(),
            "mixed_city": self._build_mixed_city_dataset(),
            "noise_injected": self._build_noise_injected_dataset(),
            "historical": self._build_historical_dataset(),
        }

    def _build_low_variance_dataset(self) -> ReferenceDataset:
        """
        Build low variance dataset.

        Simple, predictable plans with consistent behavior.
        Expected: High accuracy, low error, high confidence.
        """
        samples = []

        # Simple HTTP calls
        for i in range(10):
            samples.append(
                DatasetSample(
                    id=f"lv_http_{i}",
                    plan=[{"skill": "http_call", "params": {"url": f"https://api{i}.example.com"}}],
                    budget_cents=100,
                    expected_cost_cents=0,
                    expected_feasible=True,
                    expected_confidence_min=0.8,
                    tags=["http", "simple"],
                )
            )

        # Simple JSON transforms
        for i in range(10):
            samples.append(
                DatasetSample(
                    id=f"lv_json_{i}",
                    plan=[{"skill": "json_transform", "params": {"expression": f"$.field{i}"}}],
                    budget_cents=100,
                    expected_cost_cents=0,
                    expected_feasible=True,
                    expected_confidence_min=0.95,
                    tags=["json", "simple"],
                )
            )

        # Simple KV operations
        for i in range(5):
            samples.append(
                DatasetSample(
                    id=f"lv_kv_get_{i}",
                    plan=[{"skill": "kv_get", "params": {"key": f"key{i}"}}],
                    budget_cents=100,
                    expected_cost_cents=0,
                    expected_feasible=True,
                    expected_confidence_min=0.95,
                    tags=["kv", "simple"],
                )
            )

        for i in range(5):
            samples.append(
                DatasetSample(
                    id=f"lv_kv_set_{i}",
                    plan=[{"skill": "kv_set", "params": {"key": f"key{i}", "value": f"value{i}"}}],
                    budget_cents=100,
                    expected_cost_cents=0,
                    expected_feasible=True,
                    expected_confidence_min=0.95,
                    tags=["kv", "simple"],
                )
            )

        return ReferenceDataset(
            id="low_variance",
            name="Low Variance Dataset",
            description="Simple, predictable plans for baseline validation",
            samples=samples,
            validation_thresholds={
                "max_mean_error": 1.0,  # Max 1 cent mean error
                "max_median_error": 0.5,  # Max 0.5 cent median error
                "max_std_deviation": 2.0,  # Max 2 cent std deviation
                "max_outlier_pct": 0.02,  # Max 2% outliers
                "max_drift_score": 0.05,  # Max 5% drift
            },
        )

    def _build_high_variance_dataset(self) -> ReferenceDataset:
        """
        Build high variance dataset.

        Complex plans with variable costs and durations.
        Expected: Higher error tolerance, medium confidence.
        """
        samples = []

        # LLM calls with varying prompt lengths
        prompt_lengths = [100, 500, 1000, 2000, 4000, 8000]
        for i, length in enumerate(prompt_lengths):
            prompt = "A" * length
            samples.append(
                DatasetSample(
                    id=f"hv_llm_{i}",
                    plan=[{"skill": "llm_invoke", "params": {"prompt": prompt}}],
                    budget_cents=50,
                    expected_feasible=True,
                    expected_confidence_min=0.7,
                    tags=["llm", "variable"],
                )
            )

        # Multi-step workflows
        for i in range(5):
            steps = []
            for j in range(random.randint(3, 7)):
                skill = random.choice(["http_call", "json_transform", "llm_invoke"])
                if skill == "http_call":
                    steps.append({"skill": skill, "params": {"url": f"https://api.example.com/{j}"}})
                elif skill == "json_transform":
                    steps.append({"skill": skill, "params": {"expression": f"$.data[{j}]"}})
                else:
                    steps.append({"skill": skill, "params": {"prompt": f"Step {j} analysis"}})

            samples.append(
                DatasetSample(
                    id=f"hv_workflow_{i}",
                    plan=steps,
                    budget_cents=200,
                    expected_feasible=True,
                    expected_confidence_min=0.5,
                    tags=["workflow", "complex"],
                )
            )

        # External HTTP with timeouts
        for i in range(5):
            samples.append(
                DatasetSample(
                    id=f"hv_external_{i}",
                    plan=[
                        {
                            "skill": "http_call",
                            "params": {
                                "url": f"https://external-api-{i}.com/data",
                                "timeout": random.randint(10, 60),
                            },
                        }
                    ],
                    budget_cents=100,
                    expected_feasible=True,
                    expected_confidence_min=0.6,
                    tags=["http", "external", "variable"],
                )
            )

        return ReferenceDataset(
            id="high_variance",
            name="High Variance Dataset",
            description="Complex, variable plans for stress testing",
            samples=samples,
            validation_thresholds={
                "max_mean_error": 10.0,  # Higher tolerance
                "max_median_error": 5.0,
                "max_std_deviation": 15.0,
                "max_outlier_pct": 0.10,  # 10% outliers acceptable
                "max_drift_score": 0.15,
            },
        )

    def _build_mixed_city_dataset(self) -> ReferenceDataset:
        """
        Build mixed city dataset.

        Simulates real-world mixed workloads.
        Named "city" to represent diverse urban traffic patterns.
        """
        samples = []

        # Morning batch: Mostly simple reads
        for i in range(10):
            samples.append(
                DatasetSample(
                    id=f"mc_morning_{i}",
                    plan=[
                        {"skill": "kv_get", "params": {"key": f"config_{i}"}},
                        {"skill": "json_transform", "params": {"expression": "$.settings"}},
                    ],
                    budget_cents=50,
                    expected_feasible=True,
                    tags=["batch", "morning"],
                )
            )

        # Midday peak: Complex workflows
        for i in range(5):
            samples.append(
                DatasetSample(
                    id=f"mc_peak_{i}",
                    plan=[
                        {"skill": "http_call", "params": {"url": f"https://data-api.example.com/{i}"}},
                        {"skill": "llm_invoke", "params": {"prompt": "Analyze the response data"}},
                        {"skill": "json_transform", "params": {"expression": "$.result"}},
                        {"skill": "kv_set", "params": {"key": f"result_{i}", "value": "..."}},
                    ],
                    budget_cents=100,
                    expected_feasible=True,
                    tags=["workflow", "peak"],
                )
            )

        # Afternoon: Email and webhooks
        for i in range(5):
            samples.append(
                DatasetSample(
                    id=f"mc_afternoon_{i}",
                    plan=[
                        {"skill": "json_transform", "params": {"expression": "$.notification"}},
                        {"skill": "webhook_send", "params": {"url": f"https://notify.example.com/{i}"}},
                    ],
                    budget_cents=50,
                    expected_feasible=True,
                    tags=["notification", "afternoon"],
                )
            )

        # Evening: Heavy LLM usage
        for i in range(5):
            samples.append(
                DatasetSample(
                    id=f"mc_evening_{i}",
                    plan=[
                        {"skill": "llm_invoke", "params": {"prompt": "Generate daily report"}},
                        {"skill": "email_send", "params": {"to": f"user{i}@example.com"}},
                    ],
                    budget_cents=100,
                    expected_feasible=True,
                    tags=["report", "evening"],
                )
            )

        return ReferenceDataset(
            id="mixed_city",
            name="Mixed City Dataset",
            description="Real-world mixed workload patterns",
            samples=samples,
            validation_thresholds={
                "max_mean_error": 5.0,
                "max_median_error": 3.0,
                "max_std_deviation": 10.0,
                "max_outlier_pct": 0.05,
                "max_drift_score": 0.10,
            },
        )

    def _build_noise_injected_dataset(self) -> ReferenceDataset:
        """
        Build noise-injected dataset.

        Contains edge cases and invalid inputs to test robustness.
        """
        samples = []

        # Empty plan
        samples.append(
            DatasetSample(
                id="ni_empty",
                plan=[],
                budget_cents=100,
                expected_feasible=False,
                tags=["edge_case", "empty"],
            )
        )

        # Unknown skill
        samples.append(
            DatasetSample(
                id="ni_unknown_skill",
                plan=[{"skill": "unknown_skill_xyz", "params": {}}],
                budget_cents=100,
                expected_feasible=True,  # Should still work, with low confidence
                expected_confidence_min=0.3,
                tags=["edge_case", "unknown"],
            )
        )

        # Budget exactly zero
        samples.append(
            DatasetSample(
                id="ni_zero_budget",
                plan=[{"skill": "http_call", "params": {"url": "https://api.example.com"}}],
                budget_cents=0,
                expected_feasible=True,  # HTTP is free
                tags=["edge_case", "budget"],
            )
        )

        # Very small budget
        samples.append(
            DatasetSample(
                id="ni_tiny_budget",
                plan=[
                    {"skill": "llm_invoke", "params": {"prompt": "Hello"}},
                ],
                budget_cents=1,
                expected_feasible=False,  # LLM should exceed 1 cent
                tags=["edge_case", "budget"],
            )
        )

        # Very long plan
        samples.append(
            DatasetSample(
                id="ni_long_plan",
                plan=[{"skill": "json_transform", "params": {"expression": f"$.field{i}"}} for i in range(50)],
                budget_cents=100,
                expected_feasible=True,
                tags=["edge_case", "long"],
            )
        )

        # Very long prompt
        samples.append(
            DatasetSample(
                id="ni_long_prompt",
                plan=[{"skill": "llm_invoke", "params": {"prompt": "X" * 100000}}],
                budget_cents=1000,
                expected_feasible=True,
                expected_confidence_min=0.4,  # Lower confidence for extreme cases
                tags=["edge_case", "long_prompt"],
            )
        )

        # Missing params
        samples.append(
            DatasetSample(
                id="ni_missing_params",
                plan=[{"skill": "http_call", "params": {}}],  # Missing URL
                budget_cents=100,
                expected_feasible=True,  # Should handle gracefully
                tags=["edge_case", "missing"],
            )
        )

        # Duplicate steps
        samples.append(
            DatasetSample(
                id="ni_duplicate",
                plan=[
                    {"skill": "http_call", "params": {"url": "https://api.example.com"}},
                    {"skill": "http_call", "params": {"url": "https://api.example.com"}},
                    {"skill": "http_call", "params": {"url": "https://api.example.com"}},
                ],
                budget_cents=100,
                expected_feasible=True,
                tags=["edge_case", "duplicate"],
            )
        )

        return ReferenceDataset(
            id="noise_injected",
            name="Noise Injected Dataset",
            description="Edge cases and invalid inputs for robustness testing",
            samples=samples,
            validation_thresholds={
                "max_mean_error": 20.0,  # Higher tolerance for edge cases
                "max_median_error": 10.0,
                "max_std_deviation": 25.0,
                "max_outlier_pct": 0.30,  # Many outliers expected
                "max_drift_score": 0.25,
            },
        )

    def _build_historical_dataset(self) -> ReferenceDataset:
        """
        Build historical dataset.

        Samples derived from real production patterns.
        In production, this would load from historical logs.
        """
        samples = []

        # Typical API integration workflow
        samples.append(
            DatasetSample(
                id="hist_api_integration",
                plan=[
                    {"skill": "http_call", "params": {"url": "https://api.service.com/auth"}},
                    {"skill": "http_call", "params": {"url": "https://api.service.com/data"}},
                    {"skill": "json_transform", "params": {"expression": "$.results"}},
                    {"skill": "kv_set", "params": {"key": "cache_data", "value": "..."}},
                ],
                budget_cents=100,
                expected_cost_cents=0,
                expected_feasible=True,
                tags=["historical", "integration"],
            )
        )

        # Content generation workflow
        samples.append(
            DatasetSample(
                id="hist_content_gen",
                plan=[
                    {"skill": "kv_get", "params": {"key": "template"}},
                    {"skill": "llm_invoke", "params": {"prompt": "Generate content based on template"}},
                    {"skill": "json_transform", "params": {"expression": "$.content"}},
                ],
                budget_cents=100,
                expected_feasible=True,
                tags=["historical", "content"],
            )
        )

        # Data pipeline workflow
        samples.append(
            DatasetSample(
                id="hist_data_pipeline",
                plan=[
                    {"skill": "fs_read", "params": {"path": "/data/input.json"}},
                    {"skill": "json_transform", "params": {"expression": "$.records[*]"}},
                    {"skill": "llm_invoke", "params": {"prompt": "Summarize this data"}},
                    {"skill": "fs_write", "params": {"path": "/data/output.json"}},
                ],
                budget_cents=150,
                expected_feasible=True,
                tags=["historical", "pipeline"],
            )
        )

        # Notification workflow
        samples.append(
            DatasetSample(
                id="hist_notification",
                plan=[
                    {"skill": "kv_get", "params": {"key": "user_prefs"}},
                    {"skill": "json_transform", "params": {"expression": "$.notification_settings"}},
                    {"skill": "webhook_send", "params": {"url": "https://notify.service.com"}},
                ],
                budget_cents=50,
                expected_feasible=True,
                tags=["historical", "notification"],
            )
        )

        # Monitoring workflow
        samples.append(
            DatasetSample(
                id="hist_monitoring",
                plan=[
                    {"skill": "http_call", "params": {"url": "https://api.monitoring.com/metrics"}},
                    {"skill": "json_transform", "params": {"expression": "$.metrics"}},
                    {"skill": "shell_lite", "params": {"command": "echo 'Metrics logged'"}},
                ],
                budget_cents=50,
                expected_feasible=True,
                tags=["historical", "monitoring"],
            )
        )

        return ReferenceDataset(
            id="historical",
            name="Historical Dataset",
            description="Real production workflow patterns",
            samples=samples,
            validation_thresholds={
                "max_mean_error": 5.0,
                "max_median_error": 3.0,
                "max_std_deviation": 8.0,
                "max_outlier_pct": 0.05,
                "max_drift_score": 0.10,
            },
        )

    def list_datasets(self) -> List[Dict[str, Any]]:
        """List all available datasets."""
        return [ds.to_dict() for ds in self._datasets.values()]

    def get_dataset(self, dataset_id: str) -> Optional[ReferenceDataset]:
        """Get a dataset by ID."""
        return self._datasets.get(dataset_id)

    async def validate_dataset(self, dataset_id: str) -> ValidationResult:
        """
        Validate V2 against a reference dataset.

        Args:
            dataset_id: ID of the dataset to validate against

        Returns:
            ValidationResult with metrics
        """
        dataset = self._datasets.get(dataset_id)
        if not dataset:
            raise ValueError(f"Unknown dataset: {dataset_id}")

        # Run V2 on all samples
        adapter = CostSimV2Adapter(enable_provenance=False)
        errors: List[float] = []
        outliers = 0

        for sample in dataset.samples:
            try:
                adapter = CostSimV2Adapter(
                    budget_cents=sample.budget_cents,
                    enable_provenance=False,
                )
                result = await adapter.simulate(sample.plan)

                # Calculate error if expected cost is known
                if sample.expected_cost_cents is not None:
                    error = abs(result.estimated_cost_cents - sample.expected_cost_cents)
                    errors.append(error)

                # Check feasibility match
                if sample.expected_feasible is not None:
                    if result.feasible != sample.expected_feasible:
                        outliers += 1

                # Check confidence
                if sample.expected_confidence_min is not None:
                    if result.confidence_score < sample.expected_confidence_min:
                        outliers += 1

            except Exception as e:
                logger.error(f"Sample {sample.id} failed: {e}")
                outliers += 1

        # Calculate metrics
        if errors:
            mean_error = sum(errors) / len(errors)
            sorted_errors = sorted(errors)
            median_error = sorted_errors[len(sorted_errors) // 2]
            variance = sum((e - mean_error) ** 2 for e in errors) / len(errors)
            std_deviation = math.sqrt(variance)
        else:
            mean_error = 0.0
            median_error = 0.0
            std_deviation = 0.0

        outlier_pct = outliers / len(dataset.samples) if dataset.samples else 0.0

        # Calculate drift score
        drift_score = self._calculate_drift_score(
            mean_error=mean_error,
            median_error=median_error,
            std_deviation=std_deviation,
            outlier_pct=outlier_pct,
            thresholds=dataset.validation_thresholds,
        )

        # Determine verdict
        thresholds = dataset.validation_thresholds
        acceptable = (
            mean_error <= thresholds["max_mean_error"]
            and median_error <= thresholds["max_median_error"]
            and std_deviation <= thresholds["max_std_deviation"]
            and outlier_pct <= thresholds["max_outlier_pct"]
            and drift_score <= thresholds["max_drift_score"]
        )

        return ValidationResult(
            dataset_id=dataset_id,
            dataset_name=dataset.name,
            sample_count=len(dataset.samples),
            mean_error=round(mean_error, 4),
            median_error=round(median_error, 4),
            std_deviation=round(std_deviation, 4),
            outlier_pct=round(outlier_pct, 4),
            drift_score=round(drift_score, 4),
            verdict="acceptable" if acceptable else "not_acceptable",
            details={
                "thresholds": thresholds,
                "errors_count": len(errors),
                "outliers_count": outliers,
            },
        )

    def _calculate_drift_score(
        self,
        mean_error: float,
        median_error: float,
        std_deviation: float,
        outlier_pct: float,
        thresholds: Dict[str, float],
    ) -> float:
        """Calculate overall drift score."""
        # Normalize each metric against threshold
        mean_score = mean_error / thresholds["max_mean_error"] if thresholds["max_mean_error"] > 0 else 0
        median_score = median_error / thresholds["max_median_error"] if thresholds["max_median_error"] > 0 else 0
        std_score = std_deviation / thresholds["max_std_deviation"] if thresholds["max_std_deviation"] > 0 else 0
        outlier_score = outlier_pct / thresholds["max_outlier_pct"] if thresholds["max_outlier_pct"] > 0 else 0

        # Weighted average
        drift_score = 0.3 * mean_score + 0.3 * median_score + 0.2 * std_score + 0.2 * outlier_score

        return min(drift_score, 1.0)

    async def validate_all(self) -> Dict[str, ValidationResult]:
        """Validate V2 against all datasets."""
        results = {}
        for dataset_id in self._datasets:
            results[dataset_id] = await self.validate_dataset(dataset_id)
        return results


# Global validator instance
_validator: Optional[DatasetValidator] = None


def get_dataset_validator() -> DatasetValidator:
    """Get the global dataset validator."""
    global _validator
    if _validator is None:
        _validator = DatasetValidator()
    return _validator


async def validate_dataset(dataset_id: str) -> ValidationResult:
    """Convenience function to validate a dataset."""
    validator = get_dataset_validator()
    return await validator.validate_dataset(dataset_id)


async def validate_all_datasets() -> Dict[str, ValidationResult]:
    """Convenience function to validate all datasets."""
    validator = get_dataset_validator()
    return await validator.validate_all()
