# Layer: L2.1 — Panel Adapter Layer
# Product: ai-console
# Role: Translate spec signals to API field names
# Reference: L2_1_PANEL_ADAPTER_SPEC.yaml

"""
Panel Signal Translator — Maps semantic signals to API fields.

Core principle:
    Spec signals are SEMANTIC (what customers understand).
    API fields are IMPLEMENTATION (what backend returns).
    This layer absorbs the translation.

Benefits:
    - Spec remains stable even when APIs change field names
    - Semantic naming in spec, implementation naming in backend
    - Single place to fix mismatches
    - API field changes don't break panel spec
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("nova.panel_adapter.signal_translator")


class TranslationOutcome(str, Enum):
    """Outcome of a signal translation attempt."""
    DIRECT = "direct"           # Field exists with same name
    TRANSLATED = "translated"   # Field exists with different name
    COMPUTED = "computed"       # Field derived from multiple sources
    MISSING = "missing"         # Field does not exist in response
    DEFAULT = "default"         # Used default value


@dataclass
class TranslatedSignal:
    """Result of translating a spec signal to an API field."""
    spec_signal: str
    api_field: Optional[str]
    outcome: TranslationOutcome
    value: Any
    default_used: bool = False
    computation_note: Optional[str] = None


# =============================================================================
# SIGNAL TRANSLATIONS
# =============================================================================
# Format: capability_id -> {spec_signal: (api_field, default_value)}
#
# These absorb backend inconsistency so the spec remains semantic.
# When APIs change field names, update HERE — not in the spec.
# =============================================================================

SIGNAL_TRANSLATIONS: Dict[str, Dict[str, Tuple[str, Any]]] = {
    # -------------------------------------------------------------------------
    # ACTIVITY DOMAIN
    # -------------------------------------------------------------------------
    "activity.summary": {
        # Spec signal -> (API field, default)
        "active_run_count": ("active_runs", 0),
        "completed_run_count_window": ("completed_runs", 0),
        "near_threshold_run_count": ("at_risk_runs", 0),
        "last_observation_timestamp": ("last_activity_at", None),
        "total_runs": ("total_runs", 0),
        "failed_runs": ("failed_runs", 0),
    },

    "activity.live_runs": {
        "live_run_count": ("running_count", 0),
        "pending_run_count": ("pending_count", 0),
    },

    "activity.runs_list": {
        "runs": ("runs", []),
        "total_count": ("total", 0),
        "page_size": ("page_size", 20),
        # Risk signal mappings
        "runs_near_threshold": ("near_threshold_count", 0),
        "runs_near_cost_limit": ("near_cost_limit_count", 0),
        "runs_near_time_limit": ("near_time_limit_count", 0),
        "runs_near_token_limit": ("near_token_limit_count", 0),
    },

    "activity.risk_signals": {
        # Risk signal aggregates
        "runs_near_threshold": ("at_risk_count", 0),
        "runs_near_cost_limit": ("cost_risk_count", 0),
        "runs_near_time_limit": ("time_risk_count", 0),
        "runs_near_token_limit": ("token_risk_count", 0),
        "total_at_risk": ("total_at_risk", 0),
    },

    "activity.jobs_list": {
        # Jobs/background tasks
        "jobs": ("items", []),
        "total_count": ("total", 0),
        "running_count": ("running", 0),
        "pending_count": ("pending", 0),
    },

    # -------------------------------------------------------------------------
    # INCIDENTS DOMAIN
    # -------------------------------------------------------------------------
    "incidents.summary": {
        "active_incident_count": ("active_count", 0),
        "max_severity_level": ("highest_severity", "NONE"),
        "prevented_violation_count": ("prevented_count", 0),
        "uncontained_count": ("uncontained_count", 0),
    },

    "incidents.list": {
        "incidents": ("items", []),
        "total_count": ("total", 0),
    },

    "incidents.guard_list": {
        # Guard/containment incident signals
        "incidents": ("items", []),
        "total_count": ("total", 0),
        "containment_status": ("containment_status", "UNKNOWN"),
        "override_applied": ("override_applied", False),
        "guardrail_status": ("guardrail_status", "ACTIVE"),
        "guard_actions": ("actions", []),
        "severity": ("severity", "NONE"),
    },

    "incidents.infra_summary": {
        # Infrastructure-level incident summary
        "total_incidents": ("total", 0),
        "by_severity": ("by_severity", {}),
        "by_type": ("by_type", {}),
        "containment_rate": ("containment_rate", 0.0),
    },

    # -------------------------------------------------------------------------
    # OVERVIEW DOMAIN
    # -------------------------------------------------------------------------
    "overview.activity_snapshot": {
        # Reuses activity.summary endpoint but may have different semantic signals
        "active_run_count": ("active_runs", 0),
        "completed_run_count_window": ("completed_runs", 0),
        "near_threshold_run_count": ("at_risk_runs", 0),
        "last_observation_timestamp": ("last_activity_at", None),
    },

    "overview.incident_snapshot": {
        "active_incident_count": ("active_count", 0),
        "max_severity_level": ("highest_severity", "NONE"),
        "prevented_violation_count": ("prevented_count", 0),
    },

    "overview.cost_summary": {
        "current_spend_rate": ("spend_rate", 0.0),
        "previous_spend_rate": ("previous_spend_rate", 0.0),
        "trend_direction": ("trend", "FLAT"),
        "cost_by_category": ("by_category", {}),
    },

    "overview.cost_anomalies": {
        "recent_cost_trend": ("trend_data", []),
        "projection_confidence": ("confidence", "LOW"),
        "anomaly_adjustments": ("anomalies", []),
    },

    "overview.policy_snapshot": {
        "high_severity_violations": ("violations", []),
        "cost_anomalies": ("anomalies", []),
        "overridden_violations_with_impact": ("overrides", []),
    },

    # -------------------------------------------------------------------------
    # POLICIES DOMAIN
    # -------------------------------------------------------------------------
    "policies.violations_list": {
        "violations": ("items", []),
        "total_count": ("total", 0),
        "by_severity": ("severity_distribution", {}),
    },

    "policies.cost_dashboard": {
        "total_spend": ("total", 0.0),
        "by_feature": ("by_feature", {}),
        "by_user": ("by_user", {}),
        "by_model": ("by_model", {}),
    },

    "policies.cost_projection": {
        "projected_spend": ("projected", 0.0),
        "confidence": ("confidence", "LOW"),
        "basis": ("basis", "INSUFFICIENT_DATA"),
    },

    "policies.cost_anomalies": {
        "anomalies": ("items", []),
        "total_impact": ("total_impact", 0.0),
    },

    "policies.quota_tokens": {
        "quota_headroom_percentage": ("remaining_percent", 100.0),
        "tokens_used": ("used", 0),
        "tokens_limit": ("limit", 0),
    },

    # -------------------------------------------------------------------------
    # PREDICTIONS DOMAIN
    # -------------------------------------------------------------------------
    "activity.predictions_summary": {
        "token_limit_breaches_predicted": ("token_limit_risk_count", 0),
        "cost_ceiling_approaches": ("cost_ceiling_risk_count", 0),
        "sla_timeout_risks": ("timeout_risk_count", 0),
        "rate_limit_pressure_score": ("rate_limit_pressure", 0.0),
    },

    # -------------------------------------------------------------------------
    # LOGS DOMAIN
    # -------------------------------------------------------------------------
    "logs.runtime_traces": {
        "trace_count": ("total", 0),
        "latest_trace_timestamp": ("latest_at", None),
    },

    "logs.guard_logs": {
        "logs": ("items", []),
        "total_count": ("total", 0),
    },
}

# =============================================================================
# COMPUTED SIGNALS
# =============================================================================
# These signals are derived from multiple API fields or computed values.
# Format: spec_signal -> (source_fields, computation_func)
# =============================================================================

def _compute_system_state(data: Dict[str, Any]) -> str:
    """Compute system state from activity data."""
    active = data.get("active_runs", 0)
    at_risk = data.get("at_risk_runs", 0)

    if at_risk > 0:
        return "STRESSED"
    elif active > 5:
        return "ACTIVE"
    else:
        return "CALM"


def _compute_attention_required(data: Dict[str, Any]) -> bool:
    """Compute if attention is required from incident data."""
    active = data.get("active_count", 0)
    severity = data.get("highest_severity", "NONE")

    if active > 0:
        return True
    if severity in ("HIGH", "CRITICAL"):
        return True
    return False


def _compute_has_near_threshold_runs(data: Dict[str, Any]) -> bool:
    """Compute if there are near-threshold runs."""
    return data.get("at_risk_runs", 0) > 0


def _compute_guardrails_holding(data: Dict[str, Any]) -> bool:
    """Compute if guardrails are holding (no uncontained incidents)."""
    uncontained = data.get("uncontained_count", 0)
    return uncontained == 0


from typing import Callable as CallableType

COMPUTED_SIGNALS: Dict[str, Dict[str, CallableType[[Dict[str, Any]], Any]]] = {
    "activity.summary": {
        "system_state": _compute_system_state,
    },
    "incidents.summary": {
        "attention_required": _compute_attention_required,
        "guardrails_holding": _compute_guardrails_holding,
    },
    "overview.activity_snapshot": {
        "system_state": _compute_system_state,
        "has_near_threshold_runs": _compute_has_near_threshold_runs,
    },
    "overview.incident_snapshot": {
        "attention_required": _compute_attention_required,
    },
}


class PanelSignalTranslator:
    """
    Translates spec signals to API field values.

    Usage:
        translator = PanelSignalTranslator()
        result = translator.translate(
            capability_id="activity.summary",
            spec_signal="active_run_count",
            api_response={"active_runs": 5, "total_runs": 100}
        )
        # result.value = 5, result.outcome = TRANSLATED
    """

    def __init__(
        self,
        custom_translations: Optional[Dict[str, Dict[str, Tuple[str, Any]]]] = None,
    ):
        """
        Args:
            custom_translations: Override default translations
        """
        self._translations = SIGNAL_TRANSLATIONS.copy()
        if custom_translations:
            for cap_id, signals in custom_translations.items():
                if cap_id not in self._translations:
                    self._translations[cap_id] = {}
                self._translations[cap_id].update(signals)

    def translate(
        self,
        capability_id: str,
        spec_signal: str,
        api_response: Dict[str, Any],
    ) -> TranslatedSignal:
        """
        Translate a spec signal to its value from an API response.

        Args:
            capability_id: The capability being queried
            spec_signal: The semantic signal name from spec
            api_response: The raw API response dict

        Returns:
            TranslatedSignal with the resolved value
        """
        # Check for computed signal first
        computed_funcs = COMPUTED_SIGNALS.get(capability_id, {})
        if spec_signal in computed_funcs:
            compute_func = computed_funcs[spec_signal]
            try:
                value = compute_func(api_response)
                return TranslatedSignal(
                    spec_signal=spec_signal,
                    api_field=None,
                    outcome=TranslationOutcome.COMPUTED,
                    value=value,
                    computation_note=f"Computed by {compute_func.__name__}",
                )
            except Exception as e:
                logger.warning(f"Computation failed for {spec_signal}: {e}")
                return TranslatedSignal(
                    spec_signal=spec_signal,
                    api_field=None,
                    outcome=TranslationOutcome.MISSING,
                    value=None,
                    computation_note=f"Computation error: {e}",
                )

        # Check translation table
        cap_translations = self._translations.get(capability_id, {})
        if spec_signal in cap_translations:
            api_field, default = cap_translations[spec_signal]

            if api_field in api_response:
                return TranslatedSignal(
                    spec_signal=spec_signal,
                    api_field=api_field,
                    outcome=TranslationOutcome.TRANSLATED,
                    value=api_response[api_field],
                )
            else:
                # Field not in response, use default
                return TranslatedSignal(
                    spec_signal=spec_signal,
                    api_field=api_field,
                    outcome=TranslationOutcome.DEFAULT,
                    value=default,
                    default_used=True,
                )

        # Try direct field match (spec signal == api field)
        if spec_signal in api_response:
            return TranslatedSignal(
                spec_signal=spec_signal,
                api_field=spec_signal,
                outcome=TranslationOutcome.DIRECT,
                value=api_response[spec_signal],
            )

        # Signal not found
        logger.warning(
            f"Signal '{spec_signal}' not found for capability '{capability_id}'. "
            f"Available fields: {list(api_response.keys())}"
        )
        return TranslatedSignal(
            spec_signal=spec_signal,
            api_field=None,
            outcome=TranslationOutcome.MISSING,
            value=None,
        )

    def translate_all(
        self,
        capability_id: str,
        spec_signals: List[str],
        api_response: Dict[str, Any],
    ) -> Dict[str, TranslatedSignal]:
        """Translate multiple signals at once."""
        return {
            signal: self.translate(capability_id, signal, api_response)
            for signal in spec_signals
        }

    def get_missing_signals(
        self,
        capability_id: str,
        spec_signals: List[str],
        api_response: Dict[str, Any],
    ) -> List[str]:
        """Get list of signals that couldn't be translated."""
        results = self.translate_all(capability_id, spec_signals, api_response)
        return [
            signal
            for signal, result in results.items()
            if result.outcome == TranslationOutcome.MISSING
        ]

    def get_api_fields_for_capability(self, capability_id: str) -> List[str]:
        """Get list of API fields needed for a capability."""
        cap_translations = self._translations.get(capability_id, {})
        return [api_field for api_field, _ in cap_translations.values()]

    def register_translation(
        self,
        capability_id: str,
        spec_signal: str,
        api_field: str,
        default: Any = None,
    ) -> None:
        """Register a new translation at runtime."""
        if capability_id not in self._translations:
            self._translations[capability_id] = {}
        self._translations[capability_id][spec_signal] = (api_field, default)


# Singleton
_translator: Optional[PanelSignalTranslator] = None


def get_signal_translator() -> PanelSignalTranslator:
    """Get singleton signal translator."""
    global _translator
    if _translator is None:
        _translator = PanelSignalTranslator()
    return _translator
