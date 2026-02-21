# capability_id: CAP-008
# Layer: L2.1 — Panel Adapter Layer
# Product: ai-console
# Role: Assemble final panel response envelope
# Reference: L2_1_PANEL_ADAPTER_SPEC.yaml

"""
Panel Response Assembler — Assemble spec-compliant response envelope

Constructs the final JSON response structure from evaluated slots,
consistency results, and metadata.
"""

import logging
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .panel_consistency_checker import ConsistencyCheckResult
from .panel_types import (
    Authority,
    PanelSlotResult,
    SlotState,
    VerificationSignals,
)

logger = logging.getLogger("nova.panel_adapter.assembler")


class PanelResponseAssembler:
    """
    Assembles the final panel response envelope.

    Usage:
        assembler = PanelResponseAssembler(adapter_version, schema_version)
        response = assembler.assemble(panel_id, slots, consistency, eval_time_ms)
    """

    def __init__(
        self,
        adapter_version: str = "1.0.0",
        schema_version: str = "2026-01-16",
    ):
        self.adapter_version = adapter_version
        self.schema_version = schema_version

    def assemble(
        self,
        panel_id: str,
        panel_contract_id: str,
        slot_results: List[PanelSlotResult],
        consistency: ConsistencyCheckResult,
        evaluation_time_ms: float,
        request_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Assemble complete panel response.

        Returns dict ready for JSON serialization.
        """
        now = datetime.now(timezone.utc)

        # Build slots array
        slots = [self._slot_to_dict(slot) for slot in slot_results]

        # Calculate aggregate verification
        aggregate_verification = self._aggregate_verification(slot_results)

        # Determine overall panel state and authority
        panel_state = self._determine_panel_state(slot_results)
        panel_authority = self._determine_panel_authority(slot_results, consistency)

        return {
            "response_metadata": {
                "adapter_version": self.adapter_version,
                "schema_version": self.schema_version,
                "generated_at": now.isoformat(),
                "evaluation_time_ms": round(evaluation_time_ms, 2),
            },
            "panel": {
                "panel_id": panel_id,
                "panel_contract_id": panel_contract_id,
                "state": panel_state,
                "authority": panel_authority,
                "slots": slots,
            },
            "verification": {
                "aggregate": {
                    "missing_input_count": aggregate_verification["missing_input_count"],
                    "stale_input_count": aggregate_verification["stale_input_count"],
                    "contradictory_signal_count": aggregate_verification["contradictory_signal_count"],
                },
                "consistency": {
                    "is_consistent": consistency.is_consistent,
                    "violation_count": len(consistency.violations),
                    "violations": [
                        {
                            "rule_id": v.rule_id,
                            "rule_name": v.rule_name,
                            "slots_involved": v.slots_involved,
                            "expected": v.expected,
                            "actual": v.actual,
                        }
                        for v in consistency.violations
                    ],
                },
            },
            "request_context": request_params or {},
        }

    def _slot_to_dict(self, slot: PanelSlotResult) -> Dict[str, Any]:
        """Convert PanelSlotResult to dict."""
        return {
            "slot_id": slot.slot_id,
            "slot_contract_id": slot.slot_contract_id,
            "output_signals": slot.output_signals,
            "truth_metadata": {
                "class": slot.truth_metadata.truth_class.value,
                "lens": slot.truth_metadata.lens.value,
                "capability": slot.truth_metadata.capability,
                "state": slot.truth_metadata.state.value,
                "authority": slot.truth_metadata.authority.value,
                "actionable": slot.truth_metadata.actionable,
                "negative_authority_value": (
                    slot.truth_metadata.negative_authority_value.value
                    if slot.truth_metadata.negative_authority_value
                    else None
                ),
            },
            "time_semantics": {
                "as_of": slot.time_semantics.as_of.isoformat(),
                "evaluation_window": slot.time_semantics.evaluation_window,
                "data_cutoff_time": slot.time_semantics.data_cutoff_time.isoformat(),
                "staleness_threshold": slot.time_semantics.staleness_threshold,
            },
            "verification": {
                "missing_input_count": slot.verification.missing_input_count,
                "stale_input_count": slot.verification.stale_input_count,
                "contradictory_signal_count": slot.verification.contradictory_signal_count,
                "unverified_signal_refs": slot.verification.unverified_signal_refs,
            },
            "provenance": {
                "derived_from": slot.provenance.derived_from,
                "aggregation": slot.provenance.aggregation,
                "generated_at": slot.provenance.generated_at.isoformat(),
                "adapter_version": slot.provenance.adapter_version,
            },
        }

    def _aggregate_verification(
        self,
        slot_results: List[PanelSlotResult],
    ) -> Dict[str, int]:
        """Aggregate verification signals across all slots."""
        totals = {
            "missing_input_count": 0,
            "stale_input_count": 0,
            "contradictory_signal_count": 0,
        }
        for slot in slot_results:
            totals["missing_input_count"] += slot.verification.missing_input_count
            totals["stale_input_count"] += slot.verification.stale_input_count
            totals["contradictory_signal_count"] += slot.verification.contradictory_signal_count
        return totals

    def _determine_panel_state(
        self,
        slot_results: List[PanelSlotResult],
    ) -> str:
        """Determine overall panel state from slots."""
        states = [slot.truth_metadata.state for slot in slot_results]

        if any(s == SlotState.MISSING for s in states):
            return SlotState.MISSING.value
        if any(s == SlotState.PARTIAL for s in states):
            return SlotState.PARTIAL.value
        return SlotState.AVAILABLE.value

    def _determine_panel_authority(
        self,
        slot_results: List[PanelSlotResult],
        consistency: ConsistencyCheckResult,
    ) -> str:
        """Determine overall panel authority."""
        # If consistency check failed, authority is indeterminate
        if not consistency.is_consistent:
            return Authority.INDETERMINATE.value

        authorities = [slot.truth_metadata.authority for slot in slot_results]

        # If any slot is indeterminate, panel is indeterminate
        if any(a == Authority.INDETERMINATE for a in authorities):
            return Authority.INDETERMINATE.value

        # If all negative, panel is negative
        if all(a == Authority.NEGATIVE for a in authorities):
            return Authority.NEGATIVE.value

        # Otherwise affirmative
        return Authority.AFFIRMATIVE.value

    def assemble_error(
        self,
        panel_id: str,
        error: str,
        request_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Assemble error response envelope."""
        now = datetime.now(timezone.utc)

        return {
            "response_metadata": {
                "adapter_version": self.adapter_version,
                "schema_version": self.schema_version,
                "generated_at": now.isoformat(),
                "evaluation_time_ms": 0,
            },
            "panel": {
                "panel_id": panel_id,
                "panel_contract_id": "ERROR",
                "state": SlotState.MISSING.value,
                "authority": Authority.INDETERMINATE.value,
                "slots": [],
            },
            "error": {
                "code": "PANEL_EVALUATION_ERROR",
                "message": error,
            },
            "verification": {
                "aggregate": {
                    "missing_input_count": 1,
                    "stale_input_count": 0,
                    "contradictory_signal_count": 0,
                },
                "consistency": {
                    "is_consistent": False,
                    "violation_count": 0,
                    "violations": [],
                },
            },
            "request_context": request_params or {},
        }


# Factory
def create_response_assembler(
    adapter_version: Optional[str] = None,
    schema_version: Optional[str] = None,
) -> PanelResponseAssembler:
    """Create response assembler."""
    return PanelResponseAssembler(
        adapter_version=adapter_version or "1.0.0",
        schema_version=schema_version or "2026-01-16",
    )
