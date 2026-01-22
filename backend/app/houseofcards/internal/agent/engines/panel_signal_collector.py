# Layer: L2.1 — Panel Adapter Layer
# Product: ai-console
# Role: Collect raw signals from backend APIs via capability resolution
# Reference: L2_1_PANEL_ADAPTER_SPEC.yaml

"""
Panel Signal Collector — Capability-Bound API I/O for panel evaluation

V2.0: Now resolves capabilities via AURORA registry instead of direct paths.

Core principle:
    - Slots declare capability IDs (semantic)
    - This collector resolves to endpoints via AURORA registry
    - Only OBSERVED/TRUSTED capabilities are callable
    - Non-callable capabilities surface as negative authority

This enforces:
    - GAP 6 fix: Capability registry now used
    - GAP 4 fix: SDSR observation status checked before calls
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

import httpx

from .panel_capability_resolver import (
    PanelCapabilityResolver,
    ResolvedCapability,
    get_capability_resolver,
)
from .panel_signal_translator import (
    PanelSignalTranslator,
    TranslatedSignal,
    TranslationOutcome,
    get_signal_translator,
)
from .panel_types import SlotSpec
from .semantic_validator import SemanticValidator, get_semantic_validator
from .semantic_types import SemanticReport

logger = logging.getLogger("nova.panel_adapter.signal_collector")


@dataclass
class CapabilityResolutionTrace:
    """Trace of capability resolution for a slot."""
    capabilities_resolved: List[str] = field(default_factory=list)
    capabilities_failed: List[str] = field(default_factory=list)
    non_callable_reasons: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class CollectedSignal:
    """A signal collected from an API."""
    signal_id: str
    value: Any
    source_capability: str
    collected_at: datetime
    is_fresh: bool
    translation_outcome: TranslationOutcome
    error: Optional[str] = None


@dataclass
class CollectedSignals:
    """All signals collected for a slot."""
    slot_id: str
    signals: Dict[str, Any]
    missing: List[str]
    stale: List[str]
    errors: List[str]
    collected_at: datetime
    resolution_trace: CapabilityResolutionTrace = field(
        default_factory=CapabilityResolutionTrace
    )
    semantic_report: Optional[SemanticReport] = None
    semantic_valid: bool = True


class PanelSignalCollector:
    """
    Collects signals via capability-bound resolution.

    V2.0 Changes:
    - Resolves capability IDs to endpoints via AURORA registry
    - Only calls OBSERVED/TRUSTED capabilities
    - Translates signal names via signal translator

    Usage:
        collector = PanelSignalCollector("http://localhost:8000")
        signals = await collector.collect_for_slot(slot_spec, params)

        # Check resolution trace for capability failures
        if signals.resolution_trace.capabilities_failed:
            # Some capabilities couldn't be called
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout_seconds: float = 10.0,
        staleness_minutes: int = 5,
        capability_resolver: Optional[PanelCapabilityResolver] = None,
        signal_translator: Optional[PanelSignalTranslator] = None,
        semantic_validator: Optional[SemanticValidator] = None,
        enforce_semantics: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_seconds
        self.staleness = timedelta(minutes=staleness_minutes)
        self._client: Optional[httpx.AsyncClient] = None
        self._resolver = capability_resolver or get_capability_resolver()
        self._translator = signal_translator or get_signal_translator()
        self._semantic_validator = semantic_validator or get_semantic_validator()
        self._enforce_semantics = enforce_semantics

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def collect_for_slot(
        self,
        slot_spec: SlotSpec,
        params: Optional[Dict[str, Any]] = None,
        panel_id: str = "",
    ) -> CollectedSignals:
        """
        Collect all signals required for a slot via capability resolution.

        V2.0: Uses capability_resolver to resolve capability IDs to endpoints.
        Only OBSERVED/TRUSTED capabilities are called.

        V2.1: Runs semantic validation BEFORE collecting signals.
        If semantic validation fails with BLOCKING violations and
        enforce_semantics=True, returns early with semantic errors.
        """
        now = datetime.now(timezone.utc)
        signals: Dict[str, Any] = {}
        missing: List[str] = []
        stale: List[str] = []
        errors: List[str] = []
        resolution_trace = CapabilityResolutionTrace()
        semantic_report: Optional[SemanticReport] = None
        semantic_valid = True

        # V2.1: Run semantic validation FIRST
        if self._enforce_semantics:
            semantic_report = self._semantic_validator.validate_slot(slot_spec, panel_id)
            semantic_valid = semantic_report.is_valid()

            if not semantic_valid:
                # Log blocking violations
                for v in semantic_report.blocking():
                    logger.error(
                        f"Semantic violation {v.code.value}: {v.message} "
                        f"[panel={panel_id}, slot={slot_spec.slot_id}]"
                    )
                    errors.append(f"SEMANTIC: {v.code.value} - {v.message}")

                # If blocking violations, return early with semantic errors
                return CollectedSignals(
                    slot_id=slot_spec.slot_id,
                    signals=signals,
                    missing=list(slot_spec.required_inputs),
                    stale=stale,
                    errors=errors,
                    collected_at=now,
                    resolution_trace=resolution_trace,
                    semantic_report=semantic_report,
                    semantic_valid=False,
                )

        # Get unique capability IDs from slot spec
        capability_ids = self._get_capability_ids_from_slot(slot_spec)

        # Resolve and call each capability
        for cap_id in capability_ids:
            resolution = self._resolver.resolve(cap_id)

            if resolution.is_callable:
                resolution_trace.capabilities_resolved.append(cap_id)

                # Call the API
                response = await self._call_capability(resolution, params)

                if response.get("error"):
                    errors.append(f"{cap_id}: {response['error']}")
                    continue

                # Extract and translate signals
                data = response.get("data", {})
                spec_signals = self._get_signals_for_capability(slot_spec, cap_id)

                for signal_id in spec_signals:
                    translated = self._translator.translate(cap_id, signal_id, data)

                    if translated.outcome in (
                        TranslationOutcome.DIRECT,
                        TranslationOutcome.TRANSLATED,
                        TranslationOutcome.COMPUTED,
                    ):
                        signals[signal_id] = translated.value
                    elif translated.outcome == TranslationOutcome.DEFAULT:
                        signals[signal_id] = translated.value
                        # Mark as potentially stale if using default
                        if translated.default_used:
                            stale.append(signal_id)
                    # MISSING signals are handled below

            else:
                # Capability not callable (DISCOVERED/DECLARED/DEPRECATED)
                resolution_trace.capabilities_failed.append(cap_id)
                resolution_trace.non_callable_reasons.append({
                    "capability_id": cap_id,
                    "status": resolution.status.value,
                    "reason": resolution.reason or "Capability not OBSERVED/TRUSTED",
                })
                logger.warning(
                    f"Capability '{cap_id}' not callable: {resolution.reason}"
                )

        # Check for missing required inputs
        for required in slot_spec.required_inputs:
            if required not in signals:
                missing.append(required)

        return CollectedSignals(
            slot_id=slot_spec.slot_id,
            signals=signals,
            missing=missing,
            stale=stale,
            errors=errors,
            collected_at=now,
            resolution_trace=resolution_trace,
            semantic_report=semantic_report,
            semantic_valid=semantic_valid,
        )

    async def collect_by_capability(
        self,
        capability_id: str,
        signal_ids: List[str],
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, TranslatedSignal]:
        """
        Collect specific signals from a capability.

        Returns dict of signal_id -> TranslatedSignal.
        """
        resolution = self._resolver.resolve(capability_id)

        if not resolution.is_callable:
            return {
                signal_id: TranslatedSignal(
                    spec_signal=signal_id,
                    api_field=None,
                    outcome=TranslationOutcome.MISSING,
                    value=None,
                    computation_note=f"Capability not callable: {resolution.reason}",
                )
                for signal_id in signal_ids
            }

        response = await self._call_capability(resolution, params)

        if response.get("error"):
            return {
                signal_id: TranslatedSignal(
                    spec_signal=signal_id,
                    api_field=None,
                    outcome=TranslationOutcome.MISSING,
                    value=None,
                    computation_note=f"API error: {response['error']}",
                )
                for signal_id in signal_ids
            }

        data = response.get("data", {})
        return self._translator.translate_all(capability_id, signal_ids, data)

    async def _call_capability(
        self,
        resolution: ResolvedCapability,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call an API for a resolved capability."""
        if not resolution.endpoint:
            return {"error": "No endpoint defined"}

        try:
            client = await self._get_client()

            if resolution.method.upper() == "GET":
                response = await client.get(resolution.endpoint, params=params or {})
            elif resolution.method.upper() == "POST":
                response = await client.post(resolution.endpoint, json=params or {})
            else:
                return {"error": f"Unsupported method: {resolution.method}"}

            if response.status_code >= 400:
                return {"error": f"HTTP {response.status_code}"}

            return {"data": response.json()}

        except httpx.TimeoutException:
            return {"error": "timeout"}
        except Exception as e:
            logger.error(f"API call failed: {resolution.endpoint}: {e}")
            return {"error": str(e)}

    def _get_capability_ids_from_slot(self, slot_spec: SlotSpec) -> Set[str]:
        """Extract unique capability IDs from slot spec."""
        cap_ids = set()

        # From consumed_capabilities (V2 spec)
        if hasattr(slot_spec, "consumed_capabilities") and slot_spec.consumed_capabilities:
            for cap in slot_spec.consumed_capabilities:
                if isinstance(cap, dict):
                    cap_ids.add(cap.get("capability_id", ""))
                elif hasattr(cap, "capability_id"):
                    cap_ids.add(cap.capability_id)

        # From input signals source_capability (V2 spec)
        for input_sig in slot_spec.required_inputs:
            if hasattr(slot_spec, "input_signals"):
                # Find source capability for this signal
                for raw_signal in getattr(slot_spec.input_signals, "raw", []):
                    if hasattr(raw_signal, "source_capability"):
                        cap_ids.add(raw_signal.source_capability)

        # Fallback: From capability_binding
        if hasattr(slot_spec, "capability_binding") and slot_spec.capability_binding:
            cap_ids.add(slot_spec.capability_binding)

        # Legacy fallback: From APIs (V1 spec - for backward compatibility)
        if hasattr(slot_spec, "apis") and slot_spec.apis:
            for api in slot_spec.apis:
                # Try to find capability from API domain
                if hasattr(api, "domain"):
                    # This is a heuristic - in V1 we don't have capability IDs
                    pass

        cap_ids.discard("")
        cap_ids.discard(None)
        return cap_ids

    def _get_signals_for_capability(
        self,
        slot_spec: SlotSpec,
        capability_id: str,
    ) -> List[str]:
        """Get signals that should be collected from a capability."""
        signals = []

        if hasattr(slot_spec, "consumed_capabilities") and slot_spec.consumed_capabilities:
            for cap in slot_spec.consumed_capabilities:
                cap_id = cap.get("capability_id", "") if isinstance(cap, dict) else getattr(cap, "capability_id", "")
                if cap_id == capability_id:
                    cap_signals = cap.get("signals", []) if isinstance(cap, dict) else getattr(cap, "signals", [])
                    signals.extend(cap_signals)

        return signals


# Factory
def create_signal_collector(
    base_url: Optional[str] = None,
    capability_resolver: Optional[PanelCapabilityResolver] = None,
) -> PanelSignalCollector:
    """Create signal collector."""
    import os
    url = base_url or os.getenv("PANEL_ADAPTER_API_URL", "http://localhost:8000")
    return PanelSignalCollector(
        base_url=url,
        capability_resolver=capability_resolver,
    )
