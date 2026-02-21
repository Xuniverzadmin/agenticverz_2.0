# capability_id: CAP-002
# Layer: L5 — Domain Engine
# NOTE: Renamed costsim_models.py → costsim_models_engine.py (2026-01-31) → costsim_models.py (2026-02-08, orphan demotion)
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none (pure data structures)
#   Writes: none
# Role: CostSim V2 data models (simulation status, results)
# Callers: sandbox, canary, divergence engines
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470

# CostSim V2 Models (M6)
"""
Data models for CostSim V2 sandbox evaluation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class V2SimulationStatus(str, Enum):
    """V2 simulation result status."""

    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    SCHEMA_ERROR = "schema_error"


class ComparisonVerdict(str, Enum):
    """Verdict from V1 vs V2 comparison."""

    MATCH = "match"  # Results within tolerance
    MINOR_DRIFT = "minor_drift"  # Small deviation
    MAJOR_DRIFT = "major_drift"  # Large deviation
    MISMATCH = "mismatch"  # Incompatible results


@dataclass
class V2SimulationResult:
    """Result from CostSim V2 simulation."""

    # Core estimates
    feasible: bool
    status: V2SimulationStatus
    estimated_cost_cents: int
    estimated_duration_ms: int
    budget_remaining_cents: int

    # V2-specific fields
    confidence_score: float = 0.0  # 0.0 to 1.0
    model_version: str = "2.0.0"

    # Step details
    step_estimates: List[Dict[str, Any]] = field(default_factory=list)

    # Risks and warnings
    risks: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    runtime_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "feasible": self.feasible,
            "status": self.status.value,
            "estimated_cost_cents": self.estimated_cost_cents,
            "estimated_duration_ms": self.estimated_duration_ms,
            "budget_remaining_cents": self.budget_remaining_cents,
            "confidence_score": self.confidence_score,
            "model_version": self.model_version,
            "step_estimates": self.step_estimates,
            "risks": self.risks,
            "warnings": self.warnings,
            "metadata": self.metadata,
            "runtime_ms": self.runtime_ms,
        }

    def compute_output_hash(self) -> str:
        """Compute deterministic hash of output."""
        # Exclude runtime_ms as it's non-deterministic
        hashable = {
            "feasible": self.feasible,
            "status": self.status.value,
            "estimated_cost_cents": self.estimated_cost_cents,
            "estimated_duration_ms": self.estimated_duration_ms,
            "step_estimates": self.step_estimates,
        }
        canonical = json.dumps(hashable, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


@dataclass
class ComparisonResult:
    """Result of comparing V2 vs V1 simulation."""

    verdict: ComparisonVerdict
    v1_cost_cents: int
    v2_cost_cents: int
    cost_delta_cents: int
    cost_delta_pct: float

    v1_duration_ms: int
    v2_duration_ms: int
    duration_delta_ms: int

    v1_feasible: bool
    v2_feasible: bool
    feasibility_match: bool

    drift_score: float  # 0.0 = perfect match, 1.0 = complete divergence

    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "verdict": self.verdict.value,
            "v1_cost_cents": self.v1_cost_cents,
            "v2_cost_cents": self.v2_cost_cents,
            "cost_delta_cents": self.cost_delta_cents,
            "cost_delta_pct": self.cost_delta_pct,
            "v1_duration_ms": self.v1_duration_ms,
            "v2_duration_ms": self.v2_duration_ms,
            "duration_delta_ms": self.duration_delta_ms,
            "v1_feasible": self.v1_feasible,
            "v2_feasible": self.v2_feasible,
            "feasibility_match": self.feasibility_match,
            "drift_score": self.drift_score,
            "details": self.details,
        }


@dataclass
class DiffResult:
    """Detailed diff between two simulation results."""

    input_hash: str
    v1_output_hash: str
    v2_output_hash: str

    cost_diff: int
    duration_diff: int
    step_diffs: List[Dict[str, Any]]

    is_match: bool
    diff_summary: str

    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "input_hash": self.input_hash,
            "v1_output_hash": self.v1_output_hash,
            "v2_output_hash": self.v2_output_hash,
            "cost_diff": self.cost_diff,
            "duration_diff": self.duration_diff,
            "step_diffs": self.step_diffs,
            "is_match": self.is_match,
            "diff_summary": self.diff_summary,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class CanaryReport:
    """Report from daily canary run."""

    run_id: str
    timestamp: datetime
    status: str  # "pass", "fail", "error"

    # Comparison stats
    total_samples: int
    matching_samples: int
    minor_drift_samples: int
    major_drift_samples: int

    # Metrics
    median_cost_diff: float
    p90_cost_diff: float
    kl_divergence: float
    outlier_count: int

    # Pass/fail decision
    passed: bool
    failure_reasons: List[str] = field(default_factory=list)

    # Artifacts
    artifact_paths: List[str] = field(default_factory=list)

    # V2 vs Golden comparison
    golden_comparison: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "total_samples": self.total_samples,
            "matching_samples": self.matching_samples,
            "minor_drift_samples": self.minor_drift_samples,
            "major_drift_samples": self.major_drift_samples,
            "median_cost_diff": self.median_cost_diff,
            "p90_cost_diff": self.p90_cost_diff,
            "kl_divergence": self.kl_divergence,
            "outlier_count": self.outlier_count,
            "passed": self.passed,
            "failure_reasons": self.failure_reasons,
            "artifact_paths": self.artifact_paths,
            "golden_comparison": self.golden_comparison,
        }


@dataclass
class DivergenceReport:
    """Cost divergence report between V1 and V2."""

    start_date: datetime
    end_date: datetime
    version: str
    sample_count: int

    # Core metrics
    delta_p50: float
    delta_p90: float
    kl_divergence: float
    outlier_count: int
    fail_ratio: float
    matching_rate: float

    # Detailed samples (up to 100)
    detailed_samples: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "version": self.version,
            "sample_count": self.sample_count,
            "delta_p50": self.delta_p50,
            "delta_p90": self.delta_p90,
            "kl_divergence": self.kl_divergence,
            "outlier_count": self.outlier_count,
            "fail_ratio": self.fail_ratio,
            "matching_rate": self.matching_rate,
            "detailed_samples": self.detailed_samples,
        }


@dataclass
class ValidationResult:
    """Result of validating V2 against a reference dataset."""

    dataset_id: str
    dataset_name: str
    sample_count: int

    # Error metrics
    mean_error: float
    median_error: float
    std_deviation: float
    outlier_pct: float
    drift_score: float

    # Verdict
    verdict: str  # "acceptable" or "not_acceptable"

    # Details
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "dataset_id": self.dataset_id,
            "dataset_name": self.dataset_name,
            "sample_count": self.sample_count,
            "mean_error": self.mean_error,
            "median_error": self.median_error,
            "std_deviation": self.std_deviation,
            "outlier_pct": self.outlier_pct,
            "drift_score": self.drift_score,
            "verdict": self.verdict,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }
