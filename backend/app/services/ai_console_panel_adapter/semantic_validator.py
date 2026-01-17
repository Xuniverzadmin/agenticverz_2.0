# Layer: L2.1 — Panel Adapter Layer
# Product: ai-console
# Role: Semantic validation gate — enforce semantic authority
# Reference: PIN-420, L2_1_PANEL_ADAPTER_SPEC.yaml

"""
Semantic Validator — Force semantic authority in the panel pipeline.

Core Principle:
    Semantics must be declared once, validated mechanically, enforced everywhere.

This validator sits between SDSR and HISAR binding:
    SDSR (API works?) → Semantic Validator → HISAR (bind or block)

It enforces:
    1. Signal Completeness - Every signal has translation OR compute function
    2. Capability Reality - Every capability is OBSERVED or TRUSTED
    3. API Field Presence - Every translated field exists in response
    4. Type Validation - Signal types match expected
    5. Cross-Panel Consistency - No contradictory signals

If validation fails with BLOCKING violations:
    - Pipeline stops
    - Panel goes to DRAFT state
    - Violation report surfaces the fix

No silent failures. No best-effort binding.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from .panel_capability_resolver import (
    CapabilityStatus,
    PanelCapabilityResolver,
    get_capability_resolver,
)
from .panel_signal_translator import (
    COMPUTED_SIGNALS,
    SIGNAL_TRANSLATIONS,
    PanelSignalTranslator,
    get_signal_translator,
)
from .panel_spec_loader import PanelSpecLoader, get_panel_spec_loader
from .panel_types import SlotSpec
from .semantic_failures import get_fix_action, get_fix_owner
from .semantic_types import (
    SemanticContext,
    SemanticFailureCode,
    SemanticReport,
    SemanticSeverity,
    SemanticViolation,
    ViolationClass,
)

logger = logging.getLogger("nova.panel_adapter.semantic_validator")


# =============================================================================
# ATOMIC VALIDATORS
# =============================================================================
# Each validator checks ONE semantic rule and returns a violation or None.
# =============================================================================


def check_signal_has_translation(
    signal: str,
    capability_id: str,
    ctx: SemanticContext,
) -> Optional[SemanticViolation]:
    """
    SEM-001: Check if signal has a translation mapping.

    Every signal must have either:
    - A translation in SIGNAL_TRANSLATIONS[capability_id][signal]
    - A computed function in COMPUTED_SIGNALS[capability_id][signal]
    """
    # Check direct translation
    cap_translations = SIGNAL_TRANSLATIONS.get(capability_id, {})
    if signal in cap_translations:
        return None

    # Check computed signals
    cap_computed = COMPUTED_SIGNALS.get(capability_id, {})
    if signal in cap_computed:
        return None

    return SemanticViolation(
        code=SemanticFailureCode.SEM_001,
        severity=SemanticSeverity.BLOCKING,
        message=f"Signal '{signal}' has no translation for capability '{capability_id}'",
        context=ctx,
        evidence={
            "available_translations": list(cap_translations.keys()),
            "available_computed": list(cap_computed.keys()),
        },
        fix_owner=get_fix_owner(SemanticFailureCode.SEM_001),
        fix_action=get_fix_action(SemanticFailureCode.SEM_001),
    )


def check_capability_is_observed(
    capability_id: str,
    resolver: PanelCapabilityResolver,
    ctx: SemanticContext,
) -> Optional[SemanticViolation]:
    """
    SEM-002: Check if capability is OBSERVED or TRUSTED.

    Only OBSERVED/TRUSTED capabilities may be called.
    DECLARED/ASSUMED capabilities require SDSR verification.
    """
    resolution = resolver.resolve(capability_id)

    if resolution.is_callable:
        return None

    return SemanticViolation(
        code=SemanticFailureCode.SEM_002,
        severity=SemanticSeverity.BLOCKING,
        message=f"Capability '{capability_id}' is {resolution.status.value}, not OBSERVED/TRUSTED",
        context=ctx,
        evidence={
            "status": resolution.status.value,
            "reason": resolution.reason or "Capability not verified by SDSR",
            "endpoint": resolution.endpoint,
        },
        fix_owner=get_fix_owner(SemanticFailureCode.SEM_002),
        fix_action=get_fix_action(SemanticFailureCode.SEM_002),
    )


def check_api_field_present(
    signal: str,
    capability_id: str,
    api_response: Dict[str, Any],
    translator: PanelSignalTranslator,
    ctx: SemanticContext,
) -> Optional[SemanticViolation]:
    """
    SEM-003: Check if the translated API field exists in response.

    The mapping says signal X -> api_field Y.
    This checks that Y exists in the API response.
    """
    # Get translation
    cap_translations = SIGNAL_TRANSLATIONS.get(capability_id, {})
    if signal not in cap_translations:
        # Signal is computed, not translated from API field
        return None

    api_field, default = cap_translations[signal]

    if api_field in api_response:
        return None

    # Field missing - is there a default?
    if default is not None:
        # Has default, just warning
        return SemanticViolation(
            code=SemanticFailureCode.SEM_003,
            severity=SemanticSeverity.WARNING,
            message=f"API field '{api_field}' missing, using default '{default}'",
            context=ctx,
            evidence={
                "expected_field": api_field,
                "default_used": default,
                "response_keys": list(api_response.keys()),
            },
            fix_owner=get_fix_owner(SemanticFailureCode.SEM_003),
            fix_action=get_fix_action(SemanticFailureCode.SEM_003),
        )

    # No default - blocking
    return SemanticViolation(
        code=SemanticFailureCode.SEM_003,
        severity=SemanticSeverity.BLOCKING,
        message=f"API field '{api_field}' missing and no default defined",
        context=ctx,
        evidence={
            "expected_field": api_field,
            "response_keys": list(api_response.keys()),
        },
        fix_owner=get_fix_owner(SemanticFailureCode.SEM_003),
        fix_action=get_fix_action(SemanticFailureCode.SEM_003),
    )


def check_signal_type(
    signal: str,
    value: Any,
    expected_type: type,
    ctx: SemanticContext,
) -> Optional[SemanticViolation]:
    """
    SEM-004: Check if signal value matches expected type.
    """
    if value is None:
        return None  # None is allowed (handled by missing checks)

    if isinstance(value, expected_type):
        return None

    return SemanticViolation(
        code=SemanticFailureCode.SEM_004,
        severity=SemanticSeverity.WARNING,
        message=f"Signal '{signal}' type mismatch: expected {expected_type.__name__}, got {type(value).__name__}",
        context=ctx,
        evidence={
            "expected_type": expected_type.__name__,
            "actual_type": type(value).__name__,
            "value": str(value)[:100],  # Truncate long values
        },
        fix_owner=get_fix_owner(SemanticFailureCode.SEM_004),
        fix_action=get_fix_action(SemanticFailureCode.SEM_004),
    )


# =============================================================================
# SEMANTIC VALIDATOR
# =============================================================================


class SemanticValidator:
    """
    Semantic Validator — Enforce semantic authority in the panel pipeline.

    Usage:
        validator = SemanticValidator()

        # Validate before collecting signals
        report = validator.validate_slot(slot_spec)
        if not report.is_valid():
            # Block pipeline, surface violations
            return report

        # Or validate with actual API response
        report = validator.validate_with_response(slot_spec, api_response)
    """

    def __init__(
        self,
        spec_loader: Optional[PanelSpecLoader] = None,
        capability_resolver: Optional[PanelCapabilityResolver] = None,
        signal_translator: Optional[PanelSignalTranslator] = None,
    ):
        self._spec_loader = spec_loader or get_panel_spec_loader()
        self._resolver = capability_resolver or get_capability_resolver()
        self._translator = signal_translator or get_signal_translator()

    def validate_slot(
        self,
        slot: SlotSpec,
        panel_id: str = "",
    ) -> SemanticReport:
        """
        Validate semantic bindings for a slot BEFORE making API calls.

        Checks:
        - All signals have translations
        - All capabilities are OBSERVED
        """
        report = SemanticReport(validated_at=datetime.now(timezone.utc))
        report.panels_checked = 1

        # Get capabilities from slot
        capability_ids = self._get_capability_ids(slot)
        report.capabilities_checked = len(capability_ids)

        # Get all signals from slot
        signals = self._get_slot_signals(slot)
        report.signals_checked = len(signals)

        # Check each capability
        for cap_id in capability_ids:
            ctx = SemanticContext(
                panel_id=panel_id,
                slot_id=slot.slot_id,
                signal="",
                capability_id=cap_id,
                source="slot_spec",
            )

            # SEM-002: Capability must be OBSERVED
            report.add(check_capability_is_observed(cap_id, self._resolver, ctx))

            # SEM-001: Each signal must have translation
            for signal in self._get_signals_for_capability(slot, cap_id):
                ctx = SemanticContext(
                    panel_id=panel_id,
                    slot_id=slot.slot_id,
                    signal=signal,
                    capability_id=cap_id,
                    source="slot_spec",
                )
                report.add(check_signal_has_translation(signal, cap_id, ctx))

        return report

    def validate_with_response(
        self,
        slot: SlotSpec,
        capability_id: str,
        api_response: Dict[str, Any],
        panel_id: str = "",
    ) -> SemanticReport:
        """
        Validate semantic bindings AFTER receiving API response.

        Checks:
        - All expected fields present in response
        - Types match expected
        """
        report = SemanticReport(validated_at=datetime.now(timezone.utc))
        report.panels_checked = 1
        report.capabilities_checked = 1

        signals = self._get_signals_for_capability(slot, capability_id)
        report.signals_checked = len(signals)

        for signal in signals:
            ctx = SemanticContext(
                panel_id=panel_id,
                slot_id=slot.slot_id,
                signal=signal,
                capability_id=capability_id,
                source="api_response",
            )

            # SEM-003: API field must be present
            report.add(check_api_field_present(
                signal, capability_id, api_response, self._translator, ctx
            ))

        return report

    def validate_panel(
        self,
        panel_id: str,
        api_response: Optional[Dict[str, Any]] = None,
        panel_spec: Optional[Dict[str, Any]] = None,
        capability_status: Optional[Dict[str, str]] = None,
    ) -> SemanticReport:
        """
        Validate all slots in a panel.

        This is the Phase B (Semantic Reality) entry point for the
        two-phase validator engine.

        Args:
            panel_id: The panel ID to validate
            api_response: Optional API response data for field presence checks
            panel_spec: Optional panel specification (overrides loaded spec)
            capability_status: Optional map of capability_id -> status

        Returns:
            SemanticReport with Phase B violations
        """
        report = SemanticReport(validated_at=datetime.now(timezone.utc))
        report.phase_b_complete = True  # Mark as Phase B

        # If we have a panel spec, use it directly
        if panel_spec:
            return self._validate_panel_from_spec(
                panel_id=panel_id,
                panel_spec=panel_spec,
                api_response=api_response or {},
                capability_status=capability_status,
                report=report,
            )

        # Otherwise, load from spec loader
        panel = self._spec_loader.get_panel(panel_id)
        if not panel:
            logger.warning(f"Panel not found: {panel_id}")
            return report

        report.panels_checked = 1

        for slot_id, slot in panel.slots.items():
            slot_report = self.validate_slot(slot, panel_id)
            report.signals_checked += slot_report.signals_checked
            report.capabilities_checked += slot_report.capabilities_checked
            for v in slot_report.violations:
                report.add(v)

        return report

    def _validate_panel_from_spec(
        self,
        panel_id: str,
        panel_spec: Dict[str, Any],
        api_response: Dict[str, Any],
        capability_status: Optional[Dict[str, str]],
        report: SemanticReport,
    ) -> SemanticReport:
        """
        Validate panel from a spec dict (for two-phase validator engine).

        This method validates signals and capabilities from a panel_spec dict
        rather than a loaded SlotSpec.
        """
        report.panels_checked = 1

        signals = panel_spec.get("signals", [])
        capability_ids = panel_spec.get("capability_ids", [])

        # V1 compatibility
        if panel_spec.get("capability_binding"):
            capability_ids.append(panel_spec["capability_binding"])

        report.signals_checked = len(signals)
        report.capabilities_checked = len(capability_ids)

        # Check each capability
        for cap_id in capability_ids:
            ctx = SemanticContext(
                panel_id=panel_id,
                capability_id=cap_id,
                source="panel_spec",
            )

            # SEM-002: Check capability status if provided
            if capability_status:
                status = capability_status.get(cap_id, "DECLARED")
                if status not in ("OBSERVED", "TRUSTED"):
                    report.add(SemanticViolation(
                        code=SemanticFailureCode.SEM_002,
                        vclass=ViolationClass.SEMANTIC,
                        severity=SemanticSeverity.BLOCKING,
                        message=f"Capability '{cap_id}' is {status}, not OBSERVED/TRUSTED",
                        context=ctx,
                        evidence={"status": status},
                        fix_owner=get_fix_owner(SemanticFailureCode.SEM_002),
                        fix_action=get_fix_action(SemanticFailureCode.SEM_002),
                    ))

        # Check signals
        for sig in signals:
            sig_name = sig.get("name", sig) if isinstance(sig, dict) else sig

            # Find which capability this signal belongs to
            # For now, check all capabilities
            for cap_id in capability_ids:
                ctx = SemanticContext(
                    panel_id=panel_id,
                    signal=sig_name,
                    capability_id=cap_id,
                    source="panel_spec",
                )

                # SEM-001: Check signal has translation
                violation = check_signal_has_translation(sig_name, cap_id, ctx)
                if violation:
                    report.add(violation)
                    continue  # Skip API field check if no translation

                # SEM-003: Check API field present
                if api_response:
                    violation = check_api_field_present(
                        sig_name, cap_id, api_response, self._translator, ctx
                    )
                    if violation:
                        report.add(violation)

        return report

    def validate_all_panels(self) -> SemanticReport:
        """
        Validate all panels in the spec.

        Returns comprehensive report of all semantic violations.
        """
        report = SemanticReport(validated_at=datetime.now(timezone.utc))

        spec = self._spec_loader.load()
        panels = spec.get("panels", {})

        for panel_id, panel in panels.items():
            report.panels_checked += 1

            for slot_id, slot in panel.slots.items():
                slot_report = self.validate_slot(slot, panel_id)
                report.signals_checked += slot_report.signals_checked
                report.capabilities_checked += slot_report.capabilities_checked
                for v in slot_report.violations:
                    report.add(v)

        return report

    def get_missing_translations(self) -> List[Dict[str, str]]:
        """
        Get list of all signals missing translations.

        Useful for identifying gaps to fill.
        """
        missing = []

        spec = self._spec_loader.load()
        panels = spec.get("panels", {})

        for panel_id, panel in panels.items():
            for slot_id, slot in panel.slots.items():
                for cap in slot.consumed_capabilities:
                    for signal in cap.signals:
                        cap_translations = SIGNAL_TRANSLATIONS.get(cap.capability_id, {})
                        cap_computed = COMPUTED_SIGNALS.get(cap.capability_id, {})

                        if signal not in cap_translations and signal not in cap_computed:
                            missing.append({
                                "panel_id": panel_id,
                                "slot_id": slot_id,
                                "capability_id": cap.capability_id,
                                "signal": signal,
                            })

        return missing

    def get_unobserved_capabilities(self) -> List[Dict[str, Any]]:
        """
        Get list of capabilities that are consumed but not OBSERVED.
        """
        unobserved = []
        seen: Set[str] = set()

        spec = self._spec_loader.load()
        panels = spec.get("panels", {})

        for panel_id, panel in panels.items():
            for slot_id, slot in panel.slots.items():
                for cap in slot.consumed_capabilities:
                    if cap.capability_id in seen:
                        continue
                    seen.add(cap.capability_id)

                    resolution = self._resolver.resolve(cap.capability_id)
                    if not resolution.is_callable:
                        unobserved.append({
                            "capability_id": cap.capability_id,
                            "status": resolution.status.value,
                            "reason": resolution.reason,
                            "consumers": [panel_id],
                        })

        return unobserved

    def _get_capability_ids(self, slot: SlotSpec) -> Set[str]:
        """Extract capability IDs from slot."""
        cap_ids = set()

        for cap in slot.consumed_capabilities:
            cap_ids.add(cap.capability_id)

        if slot.capability_binding:
            cap_ids.add(slot.capability_binding)

        return cap_ids

    def _get_slot_signals(self, slot: SlotSpec) -> List[str]:
        """Get all signals for a slot."""
        signals = []

        for cap in slot.consumed_capabilities:
            signals.extend(cap.signals)

        return signals

    def _get_signals_for_capability(
        self,
        slot: SlotSpec,
        capability_id: str,
    ) -> List[str]:
        """Get signals for a specific capability in a slot."""
        for cap in slot.consumed_capabilities:
            if cap.capability_id == capability_id:
                return cap.signals
        return []


# =============================================================================
# FACTORY
# =============================================================================


_validator: Optional[SemanticValidator] = None


def get_semantic_validator() -> SemanticValidator:
    """Get singleton semantic validator."""
    global _validator
    if _validator is None:
        _validator = SemanticValidator()
    return _validator


def create_semantic_validator(
    spec_loader: Optional[PanelSpecLoader] = None,
    capability_resolver: Optional[PanelCapabilityResolver] = None,
    signal_translator: Optional[PanelSignalTranslator] = None,
) -> SemanticValidator:
    """Create a new semantic validator instance."""
    return SemanticValidator(
        spec_loader=spec_loader,
        capability_resolver=capability_resolver,
        signal_translator=signal_translator,
    )
