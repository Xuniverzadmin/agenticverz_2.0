# capability_id: CAP-008
# Layer: L2.1 — Panel Adapter Layer
# Product: ai-console
# Role: Evaluate individual panel slots
# Reference: L2_1_PANEL_ADAPTER_SPEC.yaml

"""
Panel Slot Evaluator — Execute slot evaluation logic

Evaluates a slot given collected signals and verification results.
Computes derived output signals.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

from .panel_types import (
    Authority,
    NegativeAuthorityValue,
    PanelSlotResult,
    SlotProvenance,
    SlotSpec,
    SlotState,
    TimeSemantics,
    TruthMetadata,
    VerificationSignals,
)

logger = logging.getLogger("nova.panel_adapter.slot_evaluator")


class PanelSlotEvaluator:
    """
    Evaluates individual panel slots.

    Usage:
        evaluator = PanelSlotEvaluator(adapter_version)
        result = evaluator.evaluate(slot_spec, signals, verification)
    """

    def __init__(self, adapter_version: str):
        self.adapter_version = adapter_version
        self._computations: Dict[str, Callable] = {
            "system_state": self._compute_system_state,
            "attention_required": self._compute_attention_required,
            "highest_severity": self._compute_highest_severity,
        }

    def evaluate(
        self,
        slot_spec: SlotSpec,
        signals: Dict[str, Any],
        verification: VerificationSignals,
        state: SlotState,
        authority: Authority,
        negative_value: Optional[NegativeAuthorityValue] = None,
    ) -> PanelSlotResult:
        """
        Evaluate a slot and return complete result.
        """
        now = datetime.now(timezone.utc)

        # Compute output signals
        output_signals = self._compute_outputs(slot_spec, signals)

        # Build truth metadata
        truth = TruthMetadata(
            truth_class=slot_spec.truth_class,
            lens=slot_spec.lens,
            capability=slot_spec.capability,
            state=state,
            authority=authority,
            actionable=False,
            negative_authority_value=negative_value,
        )

        # Build time semantics
        time = TimeSemantics(
            as_of=now,
            evaluation_window=slot_spec.evaluation_window,
            data_cutoff_time=now,
            staleness_threshold=slot_spec.staleness_threshold,
        )

        # Build provenance
        provenance = SlotProvenance(
            derived_from=[api.path for api in slot_spec.apis],
            aggregation=self._determine_aggregation(slot_spec),
            generated_at=now,
            adapter_version=self.adapter_version,
        )

        return PanelSlotResult(
            slot_id=slot_spec.slot_id,
            slot_contract_id=slot_spec.slot_contract_id,
            output_signals=output_signals,
            truth_metadata=truth,
            time_semantics=time,
            verification=verification,
            provenance=provenance,
        )

    def evaluate_missing(
        self,
        slot_spec: SlotSpec,
        error: str,
    ) -> PanelSlotResult:
        """Create result for missing/error state."""
        now = datetime.now(timezone.utc)

        return PanelSlotResult(
            slot_id=slot_spec.slot_id,
            slot_contract_id=slot_spec.slot_contract_id,
            output_signals={"error": error},
            truth_metadata=TruthMetadata(
                truth_class=slot_spec.truth_class,
                lens=slot_spec.lens,
                capability=slot_spec.capability,
                state=SlotState.MISSING,
                authority=Authority.INDETERMINATE,
                actionable=False,
            ),
            time_semantics=TimeSemantics(
                as_of=now,
                evaluation_window=slot_spec.evaluation_window,
                data_cutoff_time=now,
                staleness_threshold=slot_spec.staleness_threshold,
            ),
            verification=VerificationSignals(
                missing_input_count=1,
                stale_input_count=0,
                contradictory_signal_count=0,
                unverified_signal_refs=[f"error:{error}"],
            ),
            provenance=SlotProvenance(
                derived_from=[],
                aggregation="ERROR",
                generated_at=now,
                adapter_version=self.adapter_version,
            ),
        )

    def _compute_outputs(
        self,
        slot_spec: SlotSpec,
        signals: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compute output signals from inputs."""
        outputs: Dict[str, Any] = {}

        for output in slot_spec.output_signals:
            signal_id = output.signal_id

            # Direct mapping
            if signal_id in signals:
                outputs[signal_id] = signals[signal_id]
                continue

            # Computed value
            if signal_id in self._computations:
                outputs[signal_id] = self._computations[signal_id](signals)
                continue

            # Try path-based mapping
            value = self._map_signal(signal_id, signals)
            if value is not None:
                outputs[signal_id] = value

        return outputs

    def _map_signal(
        self,
        signal_id: str,
        signals: Dict[str, Any],
    ) -> Any:
        """Map common signal names to API response paths."""
        mappings = {
            "active_runs": ["runs.by_status.running", "running"],
            "completed_runs_in_window": ["runs.by_status.completed", "completed"],
            "at_risk_runs": ["attention.at_risk_count", "at_risk_count"],
            "active_incidents": ["incidents.by_lifecycle_state.active", "active"],
            "near_threshold_runs": ["attention.count", "near_threshold_count"],
            "prevented_violations": ["incidents.by_lifecycle_state.resolved", "resolved"],
        }

        paths = mappings.get(signal_id, [])
        for path in paths:
            value = self._get_nested(signals, path)
            if value is not None:
                return value
        return None

    def _get_nested(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value using dot notation."""
        parts = path.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    def _compute_system_state(self, signals: Dict[str, Any]) -> str:
        """Compute system state (CALM/ACTIVE/STRESSED)."""
        running = signals.get("runs.by_status.running", 0)
        at_risk = signals.get("attention.at_risk_count", 0)

        if at_risk > 0:
            return "STRESSED"
        if running > 5:
            return "ACTIVE"
        return "CALM"

    def _compute_attention_required(self, signals: Dict[str, Any]) -> bool:
        """Compute attention_required flag."""
        incidents = signals.get("incidents.by_lifecycle_state.active", 0)
        at_risk = signals.get("attention.at_risk_count", 0)
        return incidents > 0 or at_risk > 0

    def _compute_highest_severity(self, signals: Dict[str, Any]) -> str:
        """Compute highest severity."""
        active = signals.get("incidents.by_lifecycle_state.active", 0)
        return "NONE" if active == 0 else "MEDIUM"

    def _determine_aggregation(self, slot_spec: SlotSpec) -> str:
        """Determine aggregation type for provenance."""
        # Based on capability name
        cap = slot_spec.capability.lower()
        if "snapshot" in cap:
            return "SNAPSHOT"
        if "aggregation" in cap:
            return "AGGREGATION"
        if "analysis" in cap:
            return "ANALYSIS"
        return "DIRECT_MAPPING"
