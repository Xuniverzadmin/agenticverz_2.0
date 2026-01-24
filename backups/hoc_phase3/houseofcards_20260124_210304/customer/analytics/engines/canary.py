# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: scheduler
#   Execution: async
# Role: CostSim V2 canary runner (daily validation, drift detection)
# Callers: systemd timer, cron
# Allowed Imports: L6, L7
# Forbidden Imports: L1, L2, L3, L4, sqlalchemy, sqlmodel

# CostSim V2 Canary Runner (M6)
"""
Daily canary runner for CostSim V2 validation.

The canary runner:
1. Acquires leader lock (only one instance runs at a time)
2. Loads a sample of historical simulation requests
3. Runs both V1 and V2 on each sample
4. Computes drift metrics (KL divergence, percentiles, outliers)
5. Compares V2 against golden reference datasets
6. Produces a CanaryReport with pass/fail verdict
7. Triggers circuit breaker if drift exceeds thresholds

Runs daily via systemd timer or cron.

Leader Election:
    Only one replica should run the canary at a time. The runner uses
    PostgreSQL advisory locks to ensure single execution across replicas.
    If another instance holds the lock, run() returns immediately with
    a skip status.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.costsim.circuit_breaker import get_circuit_breaker
from app.costsim.circuit_breaker_async import (
    report_drift as report_drift_async,
)
from app.costsim.config import get_config
from app.costsim.leader import (
    LOCK_CANARY_RUNNER,
    leader_election,
)
from app.costsim.models import (
    CanaryReport,
    ComparisonResult,
    ComparisonVerdict,
    DiffResult,
)
from app.costsim.provenance import get_provenance_logger
from app.costsim.v2_adapter import CostSimV2Adapter
from app.worker.simulate import CostSimulator

logger = logging.getLogger("nova.costsim.canary")


@dataclass
class CanarySample:
    """A single canary test sample."""

    id: str
    plan: List[Dict[str, Any]]
    budget_cents: int
    expected_cost_cents: Optional[int] = None  # For golden comparison
    expected_feasible: Optional[bool] = None


@dataclass
class CanaryRunConfig:
    """Configuration for a canary run."""

    sample_count: int = 100
    max_runtime_seconds: int = 300
    parallel_workers: int = 4

    # Thresholds
    drift_threshold: float = 0.2
    outlier_threshold: float = 0.5  # Individual samples
    outlier_max_pct: float = 0.05  # Max 5% outliers

    # Golden comparison
    golden_dir: Optional[str] = None

    # Artifacts
    save_artifacts: bool = True
    artifacts_dir: Optional[str] = None

    # Leader election
    require_leader_lock: bool = True  # Only run if we acquire the lock
    leader_lock_timeout: float = 5.0  # Timeout for lock acquisition
    use_async_circuit_breaker: bool = True  # Use async CB for drift reporting


class CanaryRunner:
    """
    Daily canary runner for V2 validation.

    Usage:
        runner = CanaryRunner()
        report = await runner.run()

        if report.passed:
            print("Canary passed!")
        else:
            print(f"Canary failed: {report.failure_reasons}")
    """

    def __init__(self, config: Optional[CanaryRunConfig] = None):
        """
        Initialize canary runner.

        Args:
            config: Canary run configuration
        """
        self.config = config or CanaryRunConfig()
        costsim_config = get_config()

        self.artifacts_dir = Path(self.config.artifacts_dir or costsim_config.artifacts_dir) / "canary"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

        self.golden_dir = (
            Path(self.config.golden_dir or costsim_config.artifacts_dir) / "golden"
            if self.config.golden_dir or costsim_config.artifacts_dir
            else None
        )

        # Simulators
        self._v1_simulator = CostSimulator(budget_cents=1000)
        self._v2_adapter = CostSimV2Adapter(
            budget_cents=1000,
            enable_provenance=True,
        )

    async def run(
        self,
        samples: Optional[List[CanarySample]] = None,
    ) -> CanaryReport:
        """
        Run canary validation.

        Acquires leader lock first (if configured) to ensure only one
        instance runs at a time across replicas.

        Args:
            samples: Optional pre-loaded samples (otherwise loads from provenance)

        Returns:
            CanaryReport with results
        """
        run_id = str(uuid.uuid4())[:12]
        start_time = datetime.now(timezone.utc)

        # Acquire leader lock if required
        if self.config.require_leader_lock:
            async with leader_election(
                LOCK_CANARY_RUNNER,
                timeout_seconds=self.config.leader_lock_timeout,
            ) as is_leader:
                if not is_leader:
                    logger.info(f"Skipping canary run: another instance holds leader lock, run_id={run_id}")
                    return CanaryReport(
                        run_id=run_id,
                        timestamp=start_time,
                        status="skipped",
                        total_samples=0,
                        matching_samples=0,
                        minor_drift_samples=0,
                        major_drift_samples=0,
                        median_cost_diff=0.0,
                        p90_cost_diff=0.0,
                        kl_divergence=0.0,
                        outlier_count=0,
                        passed=True,  # Not a failure - just skipped
                        failure_reasons=["Skipped: another instance is the leader"],
                    )

                # We are the leader - run the actual canary
                return await self._run_internal(run_id, start_time, samples)
        else:
            # No leader election - run directly
            return await self._run_internal(run_id, start_time, samples)

    async def _run_internal(
        self,
        run_id: str,
        start_time: datetime,
        samples: Optional[List[CanarySample]] = None,
    ) -> CanaryReport:
        """
        Internal canary run logic (called after leader election).

        Args:
            run_id: Unique run identifier
            start_time: Run start timestamp
            samples: Optional pre-loaded samples

        Returns:
            CanaryReport with results
        """
        logger.info(f"Starting canary run: run_id={run_id}")

        # Load samples
        if samples is None:
            samples = await self._load_samples()

        if not samples:
            logger.warning("No samples available for canary run")
            return CanaryReport(
                run_id=run_id,
                timestamp=start_time,
                status="error",
                total_samples=0,
                matching_samples=0,
                minor_drift_samples=0,
                major_drift_samples=0,
                median_cost_diff=0.0,
                p90_cost_diff=0.0,
                kl_divergence=0.0,
                outlier_count=0,
                passed=False,
                failure_reasons=["No samples available"],
            )

        # Run comparisons
        comparisons: List[ComparisonResult] = []
        diffs: List[DiffResult] = []

        # Process in batches for parallelism
        batch_size = self.config.parallel_workers
        for i in range(0, len(samples), batch_size):
            batch = samples[i : i + batch_size]
            batch_results = await asyncio.gather(
                *[self._run_single(sample) for sample in batch],
                return_exceptions=True,
            )

            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Canary sample error: {result}")
                else:
                    comparison, diff = result
                    comparisons.append(comparison)
                    if diff:
                        diffs.append(diff)

        # Calculate metrics
        metrics = self._calculate_metrics(comparisons)

        # Golden comparison
        golden_comparison = None
        if self.golden_dir and self.golden_dir.exists():
            golden_comparison = await self._compare_with_golden(samples, comparisons)

        # Determine pass/fail
        passed, failure_reasons = self._evaluate_results(metrics, golden_comparison)

        # Build report
        report = CanaryReport(
            run_id=run_id,
            timestamp=start_time,
            status="pass" if passed else "fail",
            total_samples=len(samples),
            matching_samples=metrics["matching_count"],
            minor_drift_samples=metrics["minor_drift_count"],
            major_drift_samples=metrics["major_drift_count"],
            median_cost_diff=metrics["median_cost_diff"],
            p90_cost_diff=metrics["p90_cost_diff"],
            kl_divergence=metrics["kl_divergence"],
            outlier_count=metrics["outlier_count"],
            passed=passed,
            failure_reasons=failure_reasons,
            golden_comparison=golden_comparison,
        )

        # Save artifacts
        if self.config.save_artifacts:
            artifact_paths = await self._save_artifacts(report, comparisons, diffs)
            report.artifact_paths = artifact_paths

        # Report to circuit breaker if failed
        if not passed:
            if self.config.use_async_circuit_breaker:
                # Use async circuit breaker (non-blocking)
                incident = await report_drift_async(
                    drift_score=metrics["kl_divergence"],
                    sample_count=len(samples),
                    details={
                        "run_id": run_id,
                        "failure_reasons": failure_reasons,
                        "outlier_count": metrics["outlier_count"],
                    },
                )
            else:
                # Use sync circuit breaker (legacy)
                circuit_breaker = get_circuit_breaker()
                incident = circuit_breaker.report_drift(
                    drift_score=metrics["kl_divergence"],
                    sample_count=len(samples),
                    details={
                        "run_id": run_id,
                        "failure_reasons": failure_reasons,
                        "outlier_count": metrics["outlier_count"],
                    },
                )
            if incident:
                logger.error(f"Circuit breaker tripped by canary: {incident.id}")

        logger.info(f"Canary run complete: run_id={run_id}, passed={passed}, samples={len(samples)}")

        return report

    async def _load_samples(self) -> List[CanarySample]:
        """Load samples from recent provenance logs."""
        samples = []

        try:
            provenance_logger = get_provenance_logger()
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=7)

            logs = await provenance_logger.query(
                start_date=start_date,
                end_date=end_date,
                status="success",
                limit=self.config.sample_count,
            )

            for log in logs:
                try:
                    input_data = log.get_decompressed_input()
                    plan = input_data.get("plan", [])
                    budget_cents = input_data.get("budget_cents", 1000)

                    if plan:
                        samples.append(
                            CanarySample(
                                id=log.id,
                                plan=plan,
                                budget_cents=budget_cents,
                            )
                        )
                except Exception as e:
                    logger.warning(f"Failed to parse provenance log: {e}")

        except Exception as e:
            logger.error(f"Failed to load canary samples: {e}")

        # If no provenance samples, use synthetic ones
        if not samples:
            samples = self._generate_synthetic_samples()

        return samples[: self.config.sample_count]

    def _generate_synthetic_samples(self) -> List[CanarySample]:
        """Generate synthetic test samples."""
        samples = []

        # Simple HTTP call
        samples.append(
            CanarySample(
                id="synthetic_1",
                plan=[{"skill": "http_call", "params": {"url": "https://api.example.com"}}],
                budget_cents=100,
            )
        )

        # LLM invoke
        samples.append(
            CanarySample(
                id="synthetic_2",
                plan=[{"skill": "llm_invoke", "params": {"prompt": "Hello world"}}],
                budget_cents=100,
            )
        )

        # Multi-step workflow
        samples.append(
            CanarySample(
                id="synthetic_3",
                plan=[
                    {"skill": "http_call", "params": {"url": "https://api.example.com"}},
                    {"skill": "json_transform", "params": {"expression": "$.data"}},
                    {"skill": "llm_invoke", "params": {"prompt": "Analyze this"}},
                ],
                budget_cents=100,
            )
        )

        # Budget-constrained
        samples.append(
            CanarySample(
                id="synthetic_4",
                plan=[
                    {"skill": "llm_invoke", "params": {"prompt": "A" * 5000}},
                    {"skill": "llm_invoke", "params": {"prompt": "B" * 5000}},
                ],
                budget_cents=5,  # Should fail budget check
            )
        )

        return samples

    async def _run_single(self, sample: CanarySample) -> Tuple[ComparisonResult, Optional[DiffResult]]:
        """Run comparison for a single sample."""
        # Update budget for this sample
        self._v1_simulator.budget_cents = sample.budget_cents
        self._v2_adapter = CostSimV2Adapter(
            budget_cents=sample.budget_cents,
            enable_provenance=False,  # Don't double-log in canary
        )

        # Run V2 with comparison
        v2_result, comparison = await self._v2_adapter.simulate_with_comparison(sample.plan)

        # Create diff if significant drift
        diff = None
        if comparison.verdict in (ComparisonVerdict.MAJOR_DRIFT, ComparisonVerdict.MISMATCH):
            diff = DiffResult(
                input_hash=sample.id,
                v1_output_hash=f"v1_{sample.id}",
                v2_output_hash=v2_result.compute_output_hash(),
                cost_diff=comparison.cost_delta_cents,
                duration_diff=comparison.duration_delta_ms,
                step_diffs=[],
                is_match=False,
                diff_summary=f"Drift: {comparison.drift_score:.4f}, Cost delta: {comparison.cost_delta_cents}",
            )

        return comparison, diff

    def _calculate_metrics(self, comparisons: List[ComparisonResult]) -> Dict[str, Any]:
        """Calculate aggregate metrics from comparisons."""
        if not comparisons:
            return {
                "matching_count": 0,
                "minor_drift_count": 0,
                "major_drift_count": 0,
                "median_cost_diff": 0.0,
                "p90_cost_diff": 0.0,
                "kl_divergence": 0.0,
                "outlier_count": 0,
            }

        # Count by verdict
        matching_count = sum(1 for c in comparisons if c.verdict == ComparisonVerdict.MATCH)
        minor_drift_count = sum(1 for c in comparisons if c.verdict == ComparisonVerdict.MINOR_DRIFT)
        major_drift_count = sum(
            1 for c in comparisons if c.verdict in (ComparisonVerdict.MAJOR_DRIFT, ComparisonVerdict.MISMATCH)
        )

        # Cost differences
        cost_diffs = sorted([abs(c.cost_delta_cents) for c in comparisons])
        median_idx = len(cost_diffs) // 2
        median_cost_diff = float(cost_diffs[median_idx]) if cost_diffs else 0.0

        p90_idx = int(len(cost_diffs) * 0.9)
        p90_cost_diff = float(cost_diffs[p90_idx]) if cost_diffs else 0.0

        # KL divergence approximation
        # Compare distribution of V1 vs V2 costs
        v1_costs = [c.v1_cost_cents for c in comparisons]
        v2_costs = [c.v2_cost_cents for c in comparisons]
        kl_divergence = self._approximate_kl_divergence(v1_costs, v2_costs)

        # Outliers (drift > threshold)
        outlier_count = sum(1 for c in comparisons if c.drift_score > self.config.outlier_threshold)

        return {
            "matching_count": matching_count,
            "minor_drift_count": minor_drift_count,
            "major_drift_count": major_drift_count,
            "median_cost_diff": median_cost_diff,
            "p90_cost_diff": p90_cost_diff,
            "kl_divergence": kl_divergence,
            "outlier_count": outlier_count,
        }

    def _approximate_kl_divergence(self, p: List[int], q: List[int], bins: int = 10) -> float:
        """
        Approximate KL divergence between two cost distributions.

        Uses histogram binning for discrete approximation.
        """
        if not p or not q:
            return 0.0

        # Normalize to avoid zero issues
        p = [max(x, 1) for x in p]
        q = [max(x, 1) for x in q]

        # Find range
        all_values = p + q
        min_val = min(all_values)
        max_val = max(all_values)

        if min_val == max_val:
            return 0.0

        # Create histogram
        bin_width = (max_val - min_val) / bins

        p_hist = [0] * bins
        q_hist = [0] * bins

        for v in p:
            bin_idx = min(int((v - min_val) / bin_width), bins - 1)
            p_hist[bin_idx] += 1

        for v in q:
            bin_idx = min(int((v - min_val) / bin_width), bins - 1)
            q_hist[bin_idx] += 1

        # Normalize to probabilities
        p_total = sum(p_hist)
        q_total = sum(q_hist)

        if p_total == 0 or q_total == 0:
            return 0.0

        p_prob = [x / p_total for x in p_hist]
        q_prob = [x / q_total for x in q_hist]

        # Calculate KL divergence
        # D_KL(P || Q) = sum(P(x) * log(P(x) / Q(x)))
        kl = 0.0
        epsilon = 1e-10  # Avoid log(0)

        for p_i, q_i in zip(p_prob, q_prob):
            if p_i > epsilon:
                kl += p_i * math.log((p_i + epsilon) / (q_i + epsilon))

        return round(max(0.0, kl), 4)

    async def _compare_with_golden(
        self,
        samples: List[CanarySample],
        comparisons: List[ComparisonResult],
    ) -> Dict[str, Any]:
        """Compare results against golden reference dataset."""
        # TODO: Implement golden dataset loading and comparison
        return {
            "golden_loaded": False,
            "message": "Golden comparison not yet implemented",
        }

    def _evaluate_results(
        self,
        metrics: Dict[str, Any],
        golden_comparison: Optional[Dict[str, Any]],
    ) -> Tuple[bool, List[str]]:
        """Evaluate results and determine pass/fail."""
        failure_reasons = []

        # Check KL divergence
        if metrics["kl_divergence"] > self.config.drift_threshold:
            failure_reasons.append(f"KL divergence {metrics['kl_divergence']:.4f} > {self.config.drift_threshold}")

        # Check outlier percentage
        total = metrics["matching_count"] + metrics["minor_drift_count"] + metrics["major_drift_count"]
        if total > 0:
            outlier_pct = metrics["outlier_count"] / total
            if outlier_pct > self.config.outlier_max_pct:
                failure_reasons.append(f"Outlier percentage {outlier_pct:.2%} > {self.config.outlier_max_pct:.2%}")

        # Check major drift count
        if metrics["major_drift_count"] > 0 and total > 0:
            major_drift_pct = metrics["major_drift_count"] / total
            if major_drift_pct > 0.1:  # More than 10% major drift
                failure_reasons.append(f"Major drift samples {major_drift_pct:.2%} > 10%")

        passed = len(failure_reasons) == 0
        return passed, failure_reasons

    async def _save_artifacts(
        self,
        report: CanaryReport,
        comparisons: List[ComparisonResult],
        diffs: List[DiffResult],
    ) -> List[str]:
        """Save canary run artifacts."""
        artifact_paths = []
        timestamp = report.timestamp.strftime("%Y%m%d_%H%M%S")

        try:
            # Save report
            report_path = self.artifacts_dir / f"canary_report_{timestamp}.json"
            with open(report_path, "w") as f:
                json.dump(report.to_dict(), f, indent=2)
            artifact_paths.append(str(report_path))

            # Save comparisons
            comparisons_path = self.artifacts_dir / f"canary_comparisons_{timestamp}.jsonl"
            with open(comparisons_path, "w") as f:
                for comp in comparisons:
                    f.write(json.dumps(comp.to_dict()) + "\n")
            artifact_paths.append(str(comparisons_path))

            # Save diffs
            if diffs:
                diffs_path = self.artifacts_dir / f"canary_diffs_{timestamp}.jsonl"
                with open(diffs_path, "w") as f:
                    for diff in diffs:
                        f.write(json.dumps(diff.to_dict()) + "\n")
                artifact_paths.append(str(diffs_path))

        except Exception as e:
            logger.error(f"Failed to save canary artifacts: {e}")

        return artifact_paths


async def run_canary(
    sample_count: int = 100,
    drift_threshold: float = 0.2,
) -> CanaryReport:
    """
    Convenience function to run canary.

    Args:
        sample_count: Number of samples to test
        drift_threshold: Maximum acceptable drift

    Returns:
        CanaryReport
    """
    config = CanaryRunConfig(
        sample_count=sample_count,
        drift_threshold=drift_threshold,
    )
    runner = CanaryRunner(config)
    return await runner.run()
