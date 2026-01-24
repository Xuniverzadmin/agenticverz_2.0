# Layer: L2.1 — Panel Adapter Layer
# Product: ai-console
# Role: Two-phase semantic validation orchestrator
# Reference: PIN-420

"""
Validator Engine — Two-phase semantic validation orchestrator.

This engine runs:
    Phase A: Intent Guardrails (design-time, human-facing)
    Phase B: Semantic Reality (proof-time, system-facing)

Key Invariant:
    Phase A rules must NEVER depend on SDSR or APIs.
    Phase B rules must NEVER judge human intent quality.

The engine enforces ordering: Phase A MUST complete before Phase B runs.
If Phase A has BLOCKING violations, Phase B is skipped.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from .intent_guardrails import run_intent_guardrails
from .semantic_types import (
    SemanticContext,
    SemanticReport,
    SemanticSeverity,
    SemanticViolation,
    ViolationClass,
)

logger = logging.getLogger("nova.panel_adapter.validator_engine")


class TwoPhaseValidator:
    """
    Two-phase semantic validator.

    Phase A: Intent Guardrails
        - Runs at design-time (when intent YAML is created/modified)
        - Fix owners: Product, Architecture
        - NEVER depends on SDSR or APIs

    Phase B: Semantic Reality
        - Runs at proof-time (when panel data is fetched)
        - Fix owners: Panel Adapter, Backend, SDSR, Intent, System
        - Validates that reality matches declared meaning
    """

    def __init__(
        self,
        registered_panels: Optional[Set[str]] = None,
        known_capabilities: Optional[Set[str]] = None,
    ):
        """
        Initialize the two-phase validator.

        Args:
            registered_panels: Set of panel IDs declared in intent registry
            known_capabilities: Set of capability IDs in capability registry
        """
        self.registered_panels = registered_panels or set()
        self.known_capabilities = known_capabilities or set()
        self._phase_b_validator = None  # Lazy load to avoid circular imports

    def _get_phase_b_validator(self):
        """Lazy load Phase B validator to avoid circular imports."""
        if self._phase_b_validator is None:
            from .semantic_validator import SemanticValidator
            self._phase_b_validator = SemanticValidator()
        return self._phase_b_validator

    def validate_intent(
        self,
        intent: Dict[str, Any],
        all_intents: Optional[List[Dict[str, Any]]] = None,
    ) -> SemanticReport:
        """
        Run Phase A (Intent Guardrails) on a single intent.

        This is the design-time validation that checks if the intent is
        well-formed BEFORE any SDSR or API calls.

        Args:
            intent: The intent YAML to validate
            all_intents: All intents for cross-intent checks (optional)

        Returns:
            SemanticReport with Phase A violations
        """
        report = SemanticReport(validated_at=datetime.now(timezone.utc))
        report.intents_checked = 1

        all_intents = all_intents or [intent]

        violations = run_intent_guardrails(
            intent=intent,
            all_intents=all_intents,
            registered_panels=self.registered_panels,
            known_capabilities=self.known_capabilities,
        )

        for v in violations:
            report.add(v)

        report.phase_a_complete = True
        return report

    def validate_intents_batch(
        self,
        intents: List[Dict[str, Any]],
    ) -> SemanticReport:
        """
        Run Phase A on a batch of intents.

        Args:
            intents: List of intent YAMLs to validate

        Returns:
            SemanticReport with all Phase A violations
        """
        report = SemanticReport(validated_at=datetime.now(timezone.utc))
        report.intents_checked = len(intents)

        for intent in intents:
            violations = run_intent_guardrails(
                intent=intent,
                all_intents=intents,
                registered_panels=self.registered_panels,
                known_capabilities=self.known_capabilities,
            )
            for v in violations:
                report.add(v)

        report.phase_a_complete = True
        return report

    def validate_panel_data(
        self,
        panel_id: str,
        api_response: Dict[str, Any],
        panel_spec: Optional[Dict[str, Any]] = None,
        capability_status: Optional[Dict[str, str]] = None,
    ) -> SemanticReport:
        """
        Run Phase B (Semantic Reality) on panel data.

        This is the proof-time validation that checks if the API response
        matches the panel's semantic contract.

        Args:
            panel_id: The panel ID being validated
            api_response: The API response data
            panel_spec: Optional panel specification (signals, etc.)
            capability_status: Optional map of capability_id -> status

        Returns:
            SemanticReport with Phase B violations
        """
        validator = self._get_phase_b_validator()

        report = SemanticReport(validated_at=datetime.now(timezone.utc))
        report.panels_checked = 1

        # Use the existing Phase B validator
        # The semantic_validator.py handles SEM-001 to SEM-008 checks
        phase_b_report = validator.validate_panel(
            panel_id=panel_id,
            api_response=api_response,
            panel_spec=panel_spec,
            capability_status=capability_status,
        )

        # Merge Phase B results into our report
        for v in phase_b_report.violations:
            report.add(v)

        report.signals_checked = phase_b_report.signals_checked
        report.phase_b_complete = True

        return report

    def validate_full(
        self,
        intent: Dict[str, Any],
        api_response: Dict[str, Any],
        all_intents: Optional[List[Dict[str, Any]]] = None,
        capability_status: Optional[Dict[str, str]] = None,
        skip_phase_b_on_blocking: bool = True,
    ) -> SemanticReport:
        """
        Run full two-phase validation (Phase A + Phase B).

        IMPORTANT: Phase A runs first. If Phase A has BLOCKING violations
        and skip_phase_b_on_blocking is True (default), Phase B is skipped.

        Args:
            intent: The intent YAML
            api_response: The API response data
            all_intents: All intents for cross-intent checks
            capability_status: Map of capability_id -> status
            skip_phase_b_on_blocking: Skip Phase B if Phase A has blocking violations

        Returns:
            SemanticReport with both Phase A and Phase B violations
        """
        report = SemanticReport(validated_at=datetime.now(timezone.utc))

        # === PHASE A: Intent Guardrails ===
        logger.debug("Starting Phase A (Intent Guardrails)")

        all_intents = all_intents or [intent]
        phase_a_violations = run_intent_guardrails(
            intent=intent,
            all_intents=all_intents,
            registered_panels=self.registered_panels,
            known_capabilities=self.known_capabilities,
        )

        for v in phase_a_violations:
            report.add(v)

        report.intents_checked = 1
        report.phase_a_complete = True

        # Check if we should skip Phase B
        if skip_phase_b_on_blocking and len(report.phase_a_blocking()) > 0:
            logger.warning(
                f"Phase A has {len(report.phase_a_blocking())} blocking violations. "
                "Skipping Phase B."
            )
            return report

        # === PHASE B: Semantic Reality ===
        logger.debug("Starting Phase B (Semantic Reality)")

        panel_id = intent.get("panel_id", "")
        panel_spec = self._extract_panel_spec(intent)

        validator = self._get_phase_b_validator()
        phase_b_report = validator.validate_panel(
            panel_id=panel_id,
            api_response=api_response,
            panel_spec=panel_spec,
            capability_status=capability_status,
        )

        for v in phase_b_report.violations:
            report.add(v)

        report.panels_checked = 1
        report.signals_checked = phase_b_report.signals_checked
        report.phase_b_complete = True

        return report

    def _extract_panel_spec(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Extract panel specification from intent YAML."""
        spec = {}

        # Extract signals from consumed_capabilities
        signals = []
        for cap in intent.get("consumed_capabilities", []):
            cap_signals = cap.get("signals", [])
            for sig in cap_signals:
                if isinstance(sig, str):
                    signals.append({"name": sig})
                else:
                    signals.append(sig)

        if signals:
            spec["signals"] = signals

        # Extract capability binding
        cap_ids = []
        for cap in intent.get("consumed_capabilities", []):
            cap_id = cap.get("capability_id", "")
            if cap_id:
                cap_ids.append(cap_id)

        if cap_ids:
            spec["capability_ids"] = cap_ids

        # V1 compatibility
        if intent.get("capability_binding"):
            spec["capability_binding"] = intent["capability_binding"]

        return spec


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def validate_intent(
    intent: Dict[str, Any],
    all_intents: Optional[List[Dict[str, Any]]] = None,
    registered_panels: Optional[Set[str]] = None,
    known_capabilities: Optional[Set[str]] = None,
) -> SemanticReport:
    """
    Convenience function to run Phase A validation on an intent.

    Args:
        intent: The intent YAML to validate
        all_intents: All intents for cross-intent checks
        registered_panels: Set of registered panel IDs
        known_capabilities: Set of known capability IDs

    Returns:
        SemanticReport with Phase A violations
    """
    validator = TwoPhaseValidator(
        registered_panels=registered_panels,
        known_capabilities=known_capabilities,
    )
    return validator.validate_intent(intent, all_intents)


def validate_panel(
    panel_id: str,
    api_response: Dict[str, Any],
    panel_spec: Optional[Dict[str, Any]] = None,
    capability_status: Optional[Dict[str, str]] = None,
) -> SemanticReport:
    """
    Convenience function to run Phase B validation on panel data.

    Args:
        panel_id: The panel ID
        api_response: The API response data
        panel_spec: Optional panel specification
        capability_status: Optional capability status map

    Returns:
        SemanticReport with Phase B violations
    """
    validator = TwoPhaseValidator()
    return validator.validate_panel_data(
        panel_id=panel_id,
        api_response=api_response,
        panel_spec=panel_spec,
        capability_status=capability_status,
    )


def validate_full(
    intent: Dict[str, Any],
    api_response: Dict[str, Any],
    all_intents: Optional[List[Dict[str, Any]]] = None,
    registered_panels: Optional[Set[str]] = None,
    known_capabilities: Optional[Set[str]] = None,
    capability_status: Optional[Dict[str, str]] = None,
) -> SemanticReport:
    """
    Convenience function to run full two-phase validation.

    Args:
        intent: The intent YAML
        api_response: The API response data
        all_intents: All intents for cross-intent checks
        registered_panels: Set of registered panel IDs
        known_capabilities: Set of known capability IDs
        capability_status: Capability status map

    Returns:
        SemanticReport with Phase A and Phase B violations
    """
    validator = TwoPhaseValidator(
        registered_panels=registered_panels,
        known_capabilities=known_capabilities,
    )
    return validator.validate_full(
        intent=intent,
        api_response=api_response,
        all_intents=all_intents,
        capability_status=capability_status,
    )
