# Layer: L2.1 — Panel Adapter Layer
# Product: ai-console
# Role: Determinism verification and input validation
# Reference: L2_1_SLOT_DETERMINISM_MATRIX.csv

"""
Panel Verification Engine — Determinism enforcement

Verifies inputs and enforces determinism rules.
Hard failures on violations. No best-effort.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from .panel_types import (
    Authority,
    DeterminismRule,
    NegativeAuthorityValue,
    SlotState,
    VerificationSignals,
)

logger = logging.getLogger("nova.panel_adapter.verification")


class PanelVerificationEngine:
    """
    Verifies inputs and enforces determinism rules.

    Usage:
        engine = PanelVerificationEngine()
        verification = engine.verify_inputs(required, signals)
        engine.enforce_determinism(expected, actual)
    """

    def verify_inputs(
        self,
        required_inputs: List[str],
        signals: Dict[str, Any],
    ) -> VerificationSignals:
        """
        Verify input signals against requirements.

        Returns VerificationSignals with counts.
        """
        missing = [s for s in required_inputs if s not in signals or signals[s] is None]
        return VerificationSignals(
            missing_input_count=len(missing),
            stale_input_count=0,
            contradictory_signal_count=0,
            unverified_signal_refs=missing,
        )

    def check_contradictions(
        self,
        output_signals: Dict[str, Any],
    ) -> List[str]:
        """
        Check for contradictory signals.

        Returns list of contradiction descriptions.
        """
        contradictions: List[str] = []

        # Rule: near_threshold > 0 AND at_risk = 0
        near = output_signals.get("near_threshold_runs", 0)
        at_risk = output_signals.get("at_risk_runs", 0)
        if near > 0 and at_risk == 0:
            contradictions.append(f"near_threshold={near} but at_risk=0")

        # Rule: active_incidents > 0 AND attention_required = false
        incidents = output_signals.get("active_incidents", 0)
        attention = output_signals.get("attention_required", True)
        if incidents > 0 and not attention:
            contradictions.append(f"incidents={incidents} but attention=false")

        return contradictions

    def determine_state(
        self,
        verification: VerificationSignals,
    ) -> SlotState:
        """
        Determine slot state from verification signals.

        Rules:
        - missing_input_count > 0 → MISSING
        - stale_input_count > 0 → PARTIAL
        - Otherwise → AVAILABLE
        """
        if verification.missing_input_count > 0:
            return SlotState.MISSING
        if verification.stale_input_count > 0:
            return SlotState.PARTIAL
        return SlotState.AVAILABLE

    def determine_authority(
        self,
        verification: VerificationSignals,
        output_signals: Dict[str, Any],
    ) -> Tuple[Authority, Optional[NegativeAuthorityValue]]:
        """
        Determine authority from verification and output signals.

        Rules:
        - contradictory_signal_count > 0 → INDETERMINATE
        - missing_input_count > 0 → INDETERMINATE
        - Can prove absence → NEGATIVE with value
        - Otherwise → AFFIRMATIVE
        """
        # Check contradictions
        contradictions = self.check_contradictions(output_signals)
        if contradictions:
            verification.contradictory_signal_count = len(contradictions)
            return Authority.INDETERMINATE, None

        # Missing inputs → indeterminate
        if verification.missing_input_count > 0:
            return Authority.INDETERMINATE, None

        # Check for negative authority (proven absence)
        negative = self._check_negative_authority(output_signals)
        if negative:
            return Authority.NEGATIVE, negative

        return Authority.AFFIRMATIVE, None

    def _check_negative_authority(
        self,
        output_signals: Dict[str, Any],
    ) -> Optional[NegativeAuthorityValue]:
        """Check if outputs prove absence."""
        checks = {
            "active_incidents": (0, NegativeAuthorityValue.NO_INCIDENT),
            "active_incident_count": (0, NegativeAuthorityValue.NO_INCIDENT),
            "violation_count": (0, NegativeAuthorityValue.NO_VIOLATION),
            "at_risk_runs": (0, NegativeAuthorityValue.NO_ACTIVE_RISK),
            "near_threshold_runs": (0, NegativeAuthorityValue.NO_NEAR_THRESHOLD),
            "cost_anomalies": (0, NegativeAuthorityValue.NO_ANOMALY),
        }

        for signal, (zero_val, neg_auth) in checks.items():
            if signal in output_signals:
                val = output_signals[signal]
                if val == zero_val or val == [] or val is None:
                    return neg_auth

        return None

    def enforce_determinism(
        self,
        expected: Dict[str, str],
        actual: Dict[str, str],
    ) -> None:
        """
        Enforce determinism rules. Raises on violation.

        Args:
            expected: {"state": "...", "authority": "..."}
            actual: {"state": "...", "authority": "..."}

        Raises:
            RuntimeError: If determinism violated
        """
        if expected["state"] != actual["state"]:
            raise RuntimeError(
                f"DETERMINISM VIOLATION: expected state={expected['state']}, "
                f"got state={actual['state']}"
            )

        if expected["authority"] != actual["authority"]:
            raise RuntimeError(
                f"DETERMINISM VIOLATION: expected authority={expected['authority']}, "
                f"got authority={actual['authority']}"
            )

    def check_determinism_rule(
        self,
        rule: DeterminismRule,
        verification: VerificationSignals,
        state: SlotState,
        authority: Authority,
    ) -> List[str]:
        """
        Check against determinism matrix rule.

        Returns list of violations (empty if valid).
        """
        violations: List[str] = []

        # Check missing input effect
        if verification.missing_input_count > 0:
            expected_state = rule.missing_effect_state.lower()
            if expected_state == "missing" and state != SlotState.MISSING:
                violations.append(
                    f"{rule.test_id}: expected missing when input missing, got {state.value}"
                )

            expected_auth = rule.missing_effect_authority.lower()
            if expected_auth == "indeterminate" and authority != Authority.INDETERMINATE:
                violations.append(
                    f"{rule.test_id}: expected indeterminate when input missing, got {authority.value}"
                )

        return violations
