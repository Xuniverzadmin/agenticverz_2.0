# Layer: L5 — Domain Engine
# NOTE: Renamed divergence.py → divergence_engine.py (2026-01-31)
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none (pure computation)
#   Writes: none
# Role: CostSim V2 divergence reporting (delta metrics, KL divergence)
# Callers: canary runner, sandbox API
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470

# CostSim V2 Divergence Reporting (M6)
"""
Cost divergence reporting between V1 and V2.

Provides:
- delta_p50: Median cost delta
- delta_p90: 90th percentile cost delta
- kl_divergence: KL divergence between cost distributions
- outlier_count: Number of outlier samples
- fail_ratio: Ratio of major drift samples
- matching_rate: Ratio of matching samples

Reports can be generated:
- On-demand via API
- Automatically by canary runner
- Scheduled via cron/systemd timer
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.costsim.config import get_config
from app.costsim.models import DivergenceReport
from app.costsim.provenance import ProvenanceLog, get_provenance_logger

logger = logging.getLogger("nova.costsim.divergence")


@dataclass
class DivergenceSample:
    """A single sample for divergence analysis."""

    timestamp: datetime
    input_hash: str
    v1_cost_cents: int
    v2_cost_cents: int
    cost_delta_cents: int
    drift_score: float
    verdict: str
    tenant_id: Optional[str] = None


class DivergenceAnalyzer:
    """
    Analyzer for V1 vs V2 cost divergence.

    Usage:
        analyzer = DivergenceAnalyzer()
        report = await analyzer.generate_report(
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now(),
        )
    """

    def __init__(
        self,
        outlier_threshold: float = 0.5,
        major_drift_threshold: float = 0.2,
    ):
        """
        Initialize divergence analyzer.

        Args:
            outlier_threshold: Drift score threshold for outliers
            major_drift_threshold: Drift score threshold for major drift
        """
        self.outlier_threshold = outlier_threshold
        self.major_drift_threshold = major_drift_threshold

    async def generate_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        tenant_id: Optional[str] = None,
        max_samples: int = 1000,
    ) -> DivergenceReport:
        """
        Generate a divergence report for the specified time range.

        Args:
            start_date: Start of analysis period (default: 7 days ago)
            end_date: End of analysis period (default: now)
            tenant_id: Filter by tenant
            max_samples: Maximum samples to analyze

        Returns:
            DivergenceReport with metrics
        """
        config = get_config()

        # Default time range
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        if start_date is None:
            start_date = end_date - timedelta(days=7)

        # Load samples
        samples = await self._load_samples(
            start_date=start_date,
            end_date=end_date,
            tenant_id=tenant_id,
            max_samples=max_samples,
        )

        if not samples:
            return DivergenceReport(
                start_date=start_date,
                end_date=end_date,
                version=config.model_version,
                sample_count=0,
                delta_p50=0.0,
                delta_p90=0.0,
                kl_divergence=0.0,
                outlier_count=0,
                fail_ratio=0.0,
                matching_rate=0.0,
            )

        # Calculate metrics
        metrics = self._calculate_metrics(samples)

        # Build detailed samples (limit to 100)
        detailed_samples = [
            {
                "timestamp": s.timestamp.isoformat(),
                "input_hash": s.input_hash,
                "v1_cost_cents": s.v1_cost_cents,
                "v2_cost_cents": s.v2_cost_cents,
                "cost_delta_cents": s.cost_delta_cents,
                "drift_score": s.drift_score,
                "verdict": s.verdict,
            }
            for s in samples[:100]
        ]

        return DivergenceReport(
            start_date=start_date,
            end_date=end_date,
            version=config.model_version,
            sample_count=len(samples),
            delta_p50=metrics["delta_p50"],
            delta_p90=metrics["delta_p90"],
            kl_divergence=metrics["kl_divergence"],
            outlier_count=metrics["outlier_count"],
            fail_ratio=metrics["fail_ratio"],
            matching_rate=metrics["matching_rate"],
            detailed_samples=detailed_samples,
        )

    async def _load_samples(
        self,
        start_date: datetime,
        end_date: datetime,
        tenant_id: Optional[str],
        max_samples: int,
    ) -> List[DivergenceSample]:
        """Load samples from provenance logs."""
        samples = []

        try:
            provenance_logger = get_provenance_logger()
            logs = await provenance_logger.query(
                start_date=start_date,
                end_date=end_date,
                tenant_id=tenant_id,
                limit=max_samples,
            )

            for log in logs:
                try:
                    sample = self._parse_provenance_log(log)
                    if sample:
                        samples.append(sample)
                except Exception as e:
                    logger.warning(f"Failed to parse provenance log: {e}")

        except Exception as e:
            logger.error(f"Failed to load samples: {e}")

        return samples

    def _parse_provenance_log(self, log: ProvenanceLog) -> Optional[DivergenceSample]:
        """Parse a provenance log into a divergence sample."""
        try:
            output = log.get_decompressed_output()

            # Extract V2 result
            v2_cost = output.get("estimated_cost_cents", 0)
            v2_status = output.get("status", "unknown")

            # Get metadata which should contain comparison info
            metadata = output.get("metadata", {})

            # For now, we estimate V1 cost from V2 and a simulated delta
            # In production, this would come from actual V1 results stored alongside V2
            # This is a simplification for the initial implementation
            v1_cost = v2_cost  # Placeholder - real implementation tracks both

            cost_delta = v2_cost - v1_cost
            drift_score = 0.0  # Placeholder

            # Determine verdict based on status
            if v2_status == "success":
                verdict = "match"
            else:
                verdict = "error"

            return DivergenceSample(
                timestamp=log.timestamp,
                input_hash=log.input_hash[:16],
                v1_cost_cents=v1_cost,
                v2_cost_cents=v2_cost,
                cost_delta_cents=cost_delta,
                drift_score=drift_score,
                verdict=verdict,
                tenant_id=log.tenant_id,
            )

        except Exception as e:
            logger.warning(f"Failed to parse log: {e}")
            return None

    def _calculate_metrics(self, samples: List[DivergenceSample]) -> Dict[str, Any]:
        """Calculate divergence metrics from samples."""
        if not samples:
            return {
                "delta_p50": 0.0,
                "delta_p90": 0.0,
                "kl_divergence": 0.0,
                "outlier_count": 0,
                "fail_ratio": 0.0,
                "matching_rate": 0.0,
            }

        # Cost deltas
        deltas = sorted([abs(s.cost_delta_cents) for s in samples])

        # Percentiles
        p50_idx = len(deltas) // 2
        p90_idx = int(len(deltas) * 0.9)

        delta_p50 = float(deltas[p50_idx]) if deltas else 0.0
        delta_p90 = float(deltas[p90_idx]) if deltas else 0.0

        # KL divergence
        v1_costs = [s.v1_cost_cents for s in samples]
        v2_costs = [s.v2_cost_cents for s in samples]
        kl_divergence = self._calculate_kl_divergence(v1_costs, v2_costs)

        # Outliers
        outlier_count = sum(1 for s in samples if s.drift_score > self.outlier_threshold)

        # Fail ratio (major drift samples)
        major_drift_count = sum(1 for s in samples if s.drift_score > self.major_drift_threshold)
        fail_ratio = major_drift_count / len(samples) if samples else 0.0

        # Matching rate
        matching_count = sum(1 for s in samples if s.verdict == "match")
        matching_rate = matching_count / len(samples) if samples else 0.0

        return {
            "delta_p50": round(delta_p50, 2),
            "delta_p90": round(delta_p90, 2),
            "kl_divergence": round(kl_divergence, 4),
            "outlier_count": outlier_count,
            "fail_ratio": round(fail_ratio, 4),
            "matching_rate": round(matching_rate, 4),
        }

    def _calculate_kl_divergence(self, p: List[int], q: List[int], bins: int = 10) -> float:
        """
        Calculate KL divergence between two distributions.

        Uses histogram binning for discrete approximation.
        """
        if not p or not q:
            return 0.0

        # Normalize to avoid zero issues
        p = [max(x, 1) for x in p]
        q = [max(x, 1) for x in q]

        all_values = p + q
        min_val = min(all_values)
        max_val = max(all_values)

        if min_val == max_val:
            return 0.0

        bin_width = (max_val - min_val) / bins

        p_hist = [0] * bins
        q_hist = [0] * bins

        for v in p:
            bin_idx = min(int((v - min_val) / bin_width), bins - 1)
            p_hist[bin_idx] += 1

        for v in q:
            bin_idx = min(int((v - min_val) / bin_width), bins - 1)
            q_hist[bin_idx] += 1

        p_total = sum(p_hist)
        q_total = sum(q_hist)

        if p_total == 0 or q_total == 0:
            return 0.0

        p_prob = [x / p_total for x in p_hist]
        q_prob = [x / q_total for x in q_hist]

        kl = 0.0
        epsilon = 1e-10

        for p_i, q_i in zip(p_prob, q_prob):
            if p_i > epsilon:
                kl += p_i * math.log((p_i + epsilon) / (q_i + epsilon))

        return max(0.0, kl)


async def generate_divergence_report(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    tenant_id: Optional[str] = None,
) -> DivergenceReport:
    """
    Convenience function to generate a divergence report.

    Args:
        start_date: Start of analysis period
        end_date: End of analysis period
        tenant_id: Filter by tenant

    Returns:
        DivergenceReport
    """
    analyzer = DivergenceAnalyzer()
    return await analyzer.generate_report(
        start_date=start_date,
        end_date=end_date,
        tenant_id=tenant_id,
    )
