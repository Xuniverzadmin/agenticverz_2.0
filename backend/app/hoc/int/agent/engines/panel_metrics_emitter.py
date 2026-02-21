# capability_id: CAP-008
# Layer: L2.1 — Panel Adapter Layer
# Product: ai-console
# Role: Emit Prometheus metrics for panel evaluation
# Reference: L2_1_PANEL_ADAPTER_SPEC.yaml

"""
Panel Metrics Emitter — Prometheus metrics for panel adapter

Emits counters, histograms, and gauges for:
- Panel evaluation latency
- Slot evaluation counts
- Verification signal counts
- Consistency violation counts
- Authority distribution
"""

import logging
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from .panel_consistency_checker import ConsistencyCheckResult
from .panel_types import Authority, PanelSlotResult, SlotState

logger = logging.getLogger("nova.panel_adapter.metrics")

# Try to import prometheus_client, fall back to no-op if not available
try:
    from prometheus_client import Counter, Histogram, Gauge, REGISTRY
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client not available, metrics will be no-ops")


class PanelMetricsEmitter:
    """
    Emits Prometheus metrics for panel evaluation.

    Usage:
        emitter = PanelMetricsEmitter()
        with emitter.measure_evaluation("OVR-SUM-HL"):
            # evaluate panel
        emitter.record_slot_result(slot_result)
        emitter.record_consistency(consistency_result)
    """

    def __init__(self, prefix: str = "panel_adapter"):
        self.prefix = prefix
        self._initialized = False

        if PROMETHEUS_AVAILABLE:
            self._init_metrics()
        else:
            self._init_noop_metrics()

    def _init_metrics(self):
        """Initialize Prometheus metrics."""
        try:
            # Evaluation latency histogram
            self.evaluation_duration = Histogram(
                f"{self.prefix}_evaluation_duration_seconds",
                "Panel evaluation duration in seconds",
                ["panel_id"],
                buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
            )

            # Slot evaluation counter
            self.slots_evaluated = Counter(
                f"{self.prefix}_slots_evaluated_total",
                "Total number of slots evaluated",
                ["panel_id", "slot_id", "state", "authority"],
            )

            # Verification signal counters
            self.missing_inputs = Counter(
                f"{self.prefix}_missing_inputs_total",
                "Total count of missing inputs",
                ["panel_id", "slot_id"],
            )

            self.stale_inputs = Counter(
                f"{self.prefix}_stale_inputs_total",
                "Total count of stale inputs",
                ["panel_id", "slot_id"],
            )

            self.contradictions = Counter(
                f"{self.prefix}_contradictions_total",
                "Total count of contradictory signals",
                ["panel_id", "slot_id"],
            )

            # Consistency violations
            self.consistency_violations = Counter(
                f"{self.prefix}_consistency_violations_total",
                "Total count of consistency violations",
                ["panel_id", "rule_id"],
            )

            # Panel state gauge
            self.panel_state = Gauge(
                f"{self.prefix}_panel_state",
                "Current panel state (1=available, 0.5=partial, 0=missing)",
                ["panel_id"],
            )

            # Error counter
            self.errors = Counter(
                f"{self.prefix}_errors_total",
                "Total count of evaluation errors",
                ["panel_id", "error_type"],
            )

            self._initialized = True
            logger.info("Panel metrics initialized")

        except Exception as e:
            logger.warning(f"Failed to initialize metrics: {e}")
            self._init_noop_metrics()

    def _init_noop_metrics(self):
        """Initialize no-op metrics when Prometheus unavailable."""
        self._initialized = False

    @contextmanager
    def measure_evaluation(self, panel_id: str):
        """Context manager to measure panel evaluation duration."""
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            if self._initialized:
                self.evaluation_duration.labels(panel_id=panel_id).observe(duration)
            logger.debug(f"Panel {panel_id} evaluation took {duration:.3f}s")

    def record_slot_result(
        self,
        panel_id: str,
        slot_result: PanelSlotResult,
    ):
        """Record metrics for a slot evaluation result."""
        if not self._initialized:
            return

        slot_id = slot_result.slot_id
        state = slot_result.truth_metadata.state.value
        authority = slot_result.truth_metadata.authority.value

        # Slot evaluation counter
        self.slots_evaluated.labels(
            panel_id=panel_id,
            slot_id=slot_id,
            state=state,
            authority=authority,
        ).inc()

        # Verification signals
        verification = slot_result.verification

        if verification.missing_input_count > 0:
            self.missing_inputs.labels(
                panel_id=panel_id,
                slot_id=slot_id,
            ).inc(verification.missing_input_count)

        if verification.stale_input_count > 0:
            self.stale_inputs.labels(
                panel_id=panel_id,
                slot_id=slot_id,
            ).inc(verification.stale_input_count)

        if verification.contradictory_signal_count > 0:
            self.contradictions.labels(
                panel_id=panel_id,
                slot_id=slot_id,
            ).inc(verification.contradictory_signal_count)

    def record_consistency(
        self,
        consistency: ConsistencyCheckResult,
    ):
        """Record metrics for consistency check result."""
        if not self._initialized:
            return

        panel_id = consistency.panel_id

        for violation in consistency.violations:
            self.consistency_violations.labels(
                panel_id=panel_id,
                rule_id=violation.rule_id,
            ).inc()

    def record_panel_state(
        self,
        panel_id: str,
        state: SlotState,
    ):
        """Record the current panel state gauge."""
        if not self._initialized:
            return

        state_value = {
            SlotState.AVAILABLE: 1.0,
            SlotState.PARTIAL: 0.5,
            SlotState.MISSING: 0.0,
        }.get(state, 0.0)

        self.panel_state.labels(panel_id=panel_id).set(state_value)

    def record_error(
        self,
        panel_id: str,
        error_type: str,
    ):
        """Record an evaluation error."""
        if not self._initialized:
            return

        self.errors.labels(
            panel_id=panel_id,
            error_type=error_type,
        ).inc()

    def record_evaluation_complete(
        self,
        panel_id: str,
        slot_results: List[PanelSlotResult],
        consistency: ConsistencyCheckResult,
    ):
        """Record all metrics for a complete panel evaluation."""
        # Record each slot
        for slot_result in slot_results:
            self.record_slot_result(panel_id, slot_result)

        # Record consistency
        self.record_consistency(consistency)

        # Record overall panel state
        if slot_results:
            states = [s.truth_metadata.state for s in slot_results]
            if any(s == SlotState.MISSING for s in states):
                overall = SlotState.MISSING
            elif any(s == SlotState.PARTIAL for s in states):
                overall = SlotState.PARTIAL
            else:
                overall = SlotState.AVAILABLE
            self.record_panel_state(panel_id, overall)


# Singleton
_emitter: Optional[PanelMetricsEmitter] = None


def get_panel_metrics_emitter() -> PanelMetricsEmitter:
    """Get singleton metrics emitter."""
    global _emitter
    if _emitter is None:
        _emitter = PanelMetricsEmitter()
    return _emitter
