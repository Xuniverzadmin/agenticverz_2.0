"""
Drift Detection Service - M7 Implementation

Detects determinism drift between baseline and memory-enabled runs:
- Compare execution traces
- Identify divergence points
- Track drift metrics
- Generate reports

Usage:
    from app.memory.drift_detector import DriftDetector

    detector = DriftDetector()
    result = detector.compare(baseline_trace, memory_trace)
    if result.has_drift:
        print(f"Drift detected: {result.divergence_point}")
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from prometheus_client import REGISTRY, Counter, Gauge, Histogram

logger = logging.getLogger("nova.memory.drift_detector")

# =============================================================================
# Prometheus Metrics (with idempotent registration to prevent test conflicts)
# =============================================================================


def _find_existing_metric(name: str):
    """Find an existing metric in the registry by name.

    Note: Prometheus registers metrics under multiple keys (base name, _total, _created).
    The collector's _name attribute contains the base name, not the suffixed versions.
    So we check for both: the base name as _name attribute, or direct registry key lookup.
    """
    # First check if base name is in registry keys
    if name in REGISTRY._names_to_collectors:
        return REGISTRY._names_to_collectors[name]

    # Also check collector's _name attribute (for base name)
    for collector in list(REGISTRY._names_to_collectors.values()):
        if hasattr(collector, "_name") and collector._name == name:
            return collector
    return None


def _get_or_create_counter(name: str, documentation: str, labelnames: list) -> Counter:
    """Get existing counter or create new one - idempotent."""
    existing = _find_existing_metric(name)
    if existing is not None:
        return existing
    return Counter(name, documentation, labelnames)


def _get_or_create_gauge(name: str, documentation: str, labelnames: list) -> Gauge:
    """Get existing gauge or create new one - idempotent."""
    existing = _find_existing_metric(name)
    if existing is not None:
        return existing
    return Gauge(name, documentation, labelnames)


def _get_or_create_histogram(name: str, documentation: str, buckets: list) -> Histogram:
    """Get existing histogram or create new one - idempotent."""
    existing = _find_existing_metric(name)
    if existing is not None:
        return existing
    return Histogram(name, documentation, buckets=buckets)


DRIFT_COMPARISONS = _get_or_create_counter("drift_comparisons_total", "Total drift comparisons", ["status"])

DRIFT_DETECTED = _get_or_create_counter(
    "drift_detector_detected_total", "Total drift detections from DriftDetector", ["severity", "component"]
)

DRIFT_SCORE = _get_or_create_gauge("drift_score_current", "Current drift score (0-100)", ["workflow_id"])

DRIFT_LATENCY = _get_or_create_histogram(
    "drift_comparison_latency_seconds", "Drift comparison latency", [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class TraceStep:
    """Single step in an execution trace."""

    index: int
    skill: str
    params: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    status: str = "completed"
    duration_ms: float = 0.0
    timestamp: Optional[str] = None


@dataclass
class ExecutionTrace:
    """Complete execution trace."""

    workflow_id: str
    agent_id: Optional[str]
    steps: List[TraceStep]
    final_state: Dict[str, Any]
    memory_enabled: bool = False
    memory_context: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DriftPoint:
    """Point where drift was detected."""

    step_index: int
    field_path: str
    baseline_value: Any
    memory_value: Any
    severity: str  # low, medium, high, critical
    category: str  # output, timing, state, behavior


@dataclass
class DriftResult:
    """Result of drift comparison."""

    has_drift: bool
    drift_score: float  # 0-100, higher = more drift
    drift_points: List[DriftPoint]
    summary: str
    baseline_hash: str
    memory_hash: str
    comparison_time_ms: float
    ignored_fields: List[str] = field(default_factory=list)

    @property
    def severity(self) -> str:
        """Overall drift severity."""
        if not self.drift_points:
            return "none"
        severities = [p.severity for p in self.drift_points]
        if "critical" in severities:
            return "critical"
        if "high" in severities:
            return "high"
        if "medium" in severities:
            return "medium"
        return "low"


# =============================================================================
# Drift Detector
# =============================================================================


class DriftDetector:
    """
    Detects determinism drift between execution traces.

    Features:
    - Configurable ignored fields
    - Severity classification
    - Drift scoring
    - Prometheus metrics
    """

    # Default fields to ignore when comparing
    DEFAULT_IGNORED_FIELDS: Set[str] = {
        "timestamp",
        "ts",
        "created_at",
        "updated_at",
        "execution_time",
        "duration_ms",
        "latency_ms",
        "request_id",
        "trace_id",
        "span_id",
        "memory_context",
        "context_injected",
        "memories_loaded",
    }

    def __init__(self, ignored_fields: Optional[Set[str]] = None, drift_threshold: float = 5.0):
        """
        Initialize drift detector.

        Args:
            ignored_fields: Additional fields to ignore in comparison
            drift_threshold: Score threshold for considering drift significant
        """
        self._ignored = self.DEFAULT_IGNORED_FIELDS.copy()
        if ignored_fields:
            self._ignored.update(ignored_fields)
        self._threshold = drift_threshold

    def compare(self, baseline: ExecutionTrace, memory_enabled: ExecutionTrace) -> DriftResult:
        """
        Compare two traces for drift.

        Args:
            baseline: Trace without memory integration
            memory_enabled: Trace with memory integration

        Returns:
            DriftResult with comparison details
        """
        import time

        start_time = time.time()

        try:
            drift_points: List[DriftPoint] = []

            # Compare step counts
            if len(baseline.steps) != len(memory_enabled.steps):
                drift_points.append(
                    DriftPoint(
                        step_index=-1,
                        field_path="steps.length",
                        baseline_value=len(baseline.steps),
                        memory_value=len(memory_enabled.steps),
                        severity="high",
                        category="behavior",
                    )
                )

            # Compare steps
            for i, (b_step, m_step) in enumerate(zip(baseline.steps, memory_enabled.steps)):
                step_drifts = self._compare_steps(i, b_step, m_step)
                drift_points.extend(step_drifts)

            # Compare final state
            state_drifts = self._compare_dicts(baseline.final_state, memory_enabled.final_state, "final_state")
            drift_points.extend(state_drifts)

            # Calculate drift score
            drift_score = self._calculate_score(drift_points)

            # Compute hashes
            baseline_hash = self._compute_trace_hash(baseline)
            memory_hash = self._compute_trace_hash(memory_enabled)

            has_drift = drift_score > self._threshold

            result = DriftResult(
                has_drift=has_drift,
                drift_score=drift_score,
                drift_points=drift_points,
                summary=self._generate_summary(drift_points, drift_score),
                baseline_hash=baseline_hash,
                memory_hash=memory_hash,
                comparison_time_ms=(time.time() - start_time) * 1000,
                ignored_fields=list(self._ignored),
            )

            # Record metrics
            DRIFT_COMPARISONS.labels(status="drift" if has_drift else "no_drift").inc()

            if has_drift:
                DRIFT_DETECTED.labels(severity=result.severity, component="unknown").inc()
                DRIFT_SCORE.labels(workflow_id=baseline.workflow_id).set(drift_score)

            DRIFT_LATENCY.observe(time.time() - start_time)

            logger.info(
                "drift_comparison_complete",
                extra={
                    "workflow_id": baseline.workflow_id,
                    "has_drift": has_drift,
                    "drift_score": drift_score,
                    "drift_points": len(drift_points),
                    "baseline_hash": baseline_hash,
                    "memory_hash": memory_hash,
                },
            )

            return result

        except Exception as e:
            logger.error(f"Drift comparison error: {e}")
            DRIFT_COMPARISONS.labels(status="error").inc()
            raise

    def _compare_steps(self, index: int, baseline: TraceStep, memory: TraceStep) -> List[DriftPoint]:
        """Compare two trace steps."""
        drifts = []

        # Compare skill
        if baseline.skill != memory.skill:
            drifts.append(
                DriftPoint(
                    step_index=index,
                    field_path=f"steps[{index}].skill",
                    baseline_value=baseline.skill,
                    memory_value=memory.skill,
                    severity="critical",
                    category="behavior",
                )
            )

        # Compare params
        param_drifts = self._compare_dicts(baseline.params, memory.params, f"steps[{index}].params")
        drifts.extend(param_drifts)

        # Compare result
        if baseline.result and memory.result:
            result_drifts = self._compare_dicts(baseline.result, memory.result, f"steps[{index}].result")
            drifts.extend(result_drifts)
        elif baseline.result != memory.result:
            drifts.append(
                DriftPoint(
                    step_index=index,
                    field_path=f"steps[{index}].result",
                    baseline_value=baseline.result,
                    memory_value=memory.result,
                    severity="high",
                    category="output",
                )
            )

        # Compare status
        if baseline.status != memory.status:
            drifts.append(
                DriftPoint(
                    step_index=index,
                    field_path=f"steps[{index}].status",
                    baseline_value=baseline.status,
                    memory_value=memory.status,
                    severity="high",
                    category="state",
                )
            )

        return drifts

    def _compare_dicts(self, baseline: Dict[str, Any], memory: Dict[str, Any], path_prefix: str) -> List[DriftPoint]:
        """Recursively compare two dictionaries."""
        drifts = []

        all_keys = set(baseline.keys()) | set(memory.keys())

        for key in all_keys:
            # Skip ignored fields
            if key in self._ignored:
                continue

            field_path = f"{path_prefix}.{key}"
            b_val = baseline.get(key)
            m_val = memory.get(key)

            if b_val == m_val:
                continue

            # Recursive comparison for nested dicts
            if isinstance(b_val, dict) and isinstance(m_val, dict):
                nested_drifts = self._compare_dicts(b_val, m_val, field_path)
                drifts.extend(nested_drifts)
            elif isinstance(b_val, list) and isinstance(m_val, list):
                list_drifts = self._compare_lists(b_val, m_val, field_path)
                drifts.extend(list_drifts)
            else:
                # Different values
                severity = self._classify_severity(key, b_val, m_val)
                drifts.append(
                    DriftPoint(
                        step_index=-1,
                        field_path=field_path,
                        baseline_value=b_val,
                        memory_value=m_val,
                        severity=severity,
                        category=self._classify_category(key),
                    )
                )

        return drifts

    def _compare_lists(self, baseline: List[Any], memory: List[Any], path_prefix: str) -> List[DriftPoint]:
        """Compare two lists."""
        drifts = []

        if len(baseline) != len(memory):
            drifts.append(
                DriftPoint(
                    step_index=-1,
                    field_path=f"{path_prefix}.length",
                    baseline_value=len(baseline),
                    memory_value=len(memory),
                    severity="medium",
                    category="output",
                )
            )

        # Compare element by element
        for i, (b_item, m_item) in enumerate(zip(baseline, memory)):
            if isinstance(b_item, dict) and isinstance(m_item, dict):
                nested = self._compare_dicts(b_item, m_item, f"{path_prefix}[{i}]")
                drifts.extend(nested)
            elif b_item != m_item:
                drifts.append(
                    DriftPoint(
                        step_index=-1,
                        field_path=f"{path_prefix}[{i}]",
                        baseline_value=b_item,
                        memory_value=m_item,
                        severity="medium",
                        category="output",
                    )
                )

        return drifts

    def _classify_severity(self, key: str, baseline_value: Any, memory_value: Any) -> str:
        """Classify drift severity based on field and values."""
        # Critical fields
        critical_fields = {"status", "error", "success", "result_type"}
        if key in critical_fields:
            return "critical"

        # High importance fields
        high_fields = {"data", "output", "response", "value"}
        if key in high_fields:
            return "high"

        # Type changes are high severity
        if type(baseline_value) != type(memory_value):
            return "high"

        # Numeric drift
        if isinstance(baseline_value, (int, float)) and isinstance(memory_value, (int, float)):
            if baseline_value == 0:
                return "medium"
            ratio = abs(baseline_value - memory_value) / abs(baseline_value)
            if ratio > 0.5:
                return "high"
            if ratio > 0.1:
                return "medium"
            return "low"

        return "medium"

    def _classify_category(self, key: str) -> str:
        """Classify drift category based on field."""
        output_fields = {"data", "output", "response", "result", "value"}
        state_fields = {"status", "state", "phase", "stage"}
        timing_fields = {"duration", "latency", "time", "elapsed"}

        if key in output_fields:
            return "output"
        if key in state_fields:
            return "state"
        if key in timing_fields:
            return "timing"
        return "behavior"

    def _calculate_score(self, drift_points: List[DriftPoint]) -> float:
        """
        Calculate drift score (0-100).

        Weights:
        - critical: 25 points
        - high: 10 points
        - medium: 5 points
        - low: 2 points

        Capped at 100.
        """
        weights = {"critical": 25, "high": 10, "medium": 5, "low": 2}
        score = sum(weights.get(p.severity, 5) for p in drift_points)
        return min(score, 100.0)

    def _compute_trace_hash(self, trace: ExecutionTrace) -> str:
        """Compute deterministic hash of trace (excluding ignored fields)."""

        def filter_dict(d: Dict[str, Any]) -> Dict[str, Any]:
            return {
                k: filter_dict(v) if isinstance(v, dict) else v for k, v in sorted(d.items()) if k not in self._ignored
            }

        filtered_steps = []
        for step in trace.steps:
            filtered_steps.append(
                {
                    "skill": step.skill,
                    "params": filter_dict(step.params),
                    "result": filter_dict(step.result) if step.result else None,
                    "status": step.status,
                }
            )

        data = {
            "workflow_id": trace.workflow_id,
            "steps": filtered_steps,
            "final_state": filter_dict(trace.final_state),
        }

        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    def _generate_summary(self, drift_points: List[DriftPoint], score: float) -> str:
        """Generate human-readable summary."""
        if not drift_points:
            return "No drift detected"

        counts = {}
        for p in drift_points:
            counts[p.severity] = counts.get(p.severity, 0) + 1

        parts = [f"Drift score: {score:.1f}/100"]
        for severity in ["critical", "high", "medium", "low"]:
            if severity in counts:
                parts.append(f"{counts[severity]} {severity}")

        return ", ".join(parts)


# =============================================================================
# Global Instance
# =============================================================================

_detector: Optional[DriftDetector] = None


def get_drift_detector() -> DriftDetector:
    """Get or create global drift detector."""
    global _detector
    if _detector is None:
        _detector = DriftDetector()
    return _detector


def init_drift_detector(ignored_fields: Optional[Set[str]] = None, drift_threshold: float = 5.0) -> DriftDetector:
    """Initialize global drift detector."""
    global _detector
    _detector = DriftDetector(ignored_fields, drift_threshold)
    return _detector
