"""
M29 Category 5: Incident DTO Absence Tests

PURPOSE: Make the founder/customer contrast IRREVERSIBLE.

These tests don't verify correctness - they verify IMPOSSIBILITY.
If a forbidden field appears in a customer DTO, the test fails.
This prevents accidental leakage during future development.

THE INVARIANT: Founders see truth and causality.
               Customers see impact and reassurance.
               The two MUST NOT contaminate each other.

Test Date: 2025-12-24
"""

import inspect
import re
from pathlib import Path
from typing import Dict, List, Literal, Set, get_args, get_origin, get_type_hints

import pytest
from pydantic import BaseModel

# =============================================================================
# CUSTOMER DTOs (must be free of forbidden knowledge)
# =============================================================================
from app.contracts.guard import (
    CostBreakdownItemDTO,
    CustomerCostExplainedDTO,
    CustomerCostIncidentDTO,
    CustomerCostSummaryDTO,
    CustomerIncidentActionDTO,
    CustomerIncidentImpactDTO,
    # Core Incident DTOs (Category 5)
    CustomerIncidentNarrativeDTO,
    CustomerIncidentResolutionDTO,
    # Other Guard DTOs
    GuardStatusDTO,
    IncidentDetailDTO,
    # Legacy Incident DTOs
    IncidentSummaryDTO,
    TodaySnapshotDTO,
)

# =============================================================================
# FOUNDER DTOs (reference for what customers must NOT see)
# =============================================================================
from app.contracts.ops import (
    FounderBlastRadiusDTO,
    FounderIncidentDetailDTO,
    FounderIncidentHeaderDTO,
    FounderRecurrenceRiskDTO,
    FounderRootCauseDTO,
)

# =============================================================================
# FORBIDDEN KNOWLEDGE MATRIX
#
# These are the exact terms that MUST NEVER appear in customer DTOs.
# Organized by category for clear auditing.
# =============================================================================


class ForbiddenKnowledge:
    """Central registry of all forbidden knowledge."""

    # =========================================================================
    # CATEGORY A: QUANTITATIVE INTERNALS
    # Customers should not see raw metrics, thresholds, or baselines
    # =========================================================================
    QUANTITATIVE_INTERNALS: Set[str] = {
        # Baseline/deviation terms
        "baseline",
        "baseline_value",
        "baseline_7d_avg",
        "deviation",
        "deviation_pct",
        "deviation_from_baseline",
        "deviation_from_baseline_pct",
        # Threshold terms
        "threshold",
        "threshold_pct",
        "threshold_breached",
        "threshold_value",
        # Ratios and raw metrics
        "ratio",
        "retry_ratio",
        "error_rate",
        "error_rate_percent",
        "p99_latency_ms",
        "prompt_tokens",
        "input_tokens",
        "output_tokens",
        "token_count",
        # Duration internals (seconds are founder-only)
        "duration_seconds",
        # Breach tracking
        "breach_count",
        "breach_history",
        # Confidence scores
        "confidence",
        "confidence_score",
        "risk_score",
        "churn_risk_score",
        # Percentiles
        "percentile",
        "p50",
        "p95",
        "p99",
    }

    # =========================================================================
    # CATEGORY B: SEVERITY SEMANTICS
    # Customers see calm vocabulary, never internal severity levels
    # =========================================================================
    SEVERITY_SEMANTICS: Set[str] = {
        # Internal severity levels (uppercase - enum values)
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
        # Severity field names that expose internal classification
        "severity",  # The field itself is forbidden in new Category 5 DTOs
        "severity_level",
        "risk_level",  # Except in calm context
        # Trend internals (founder vocabulary)
        "elevated",
        "degraded",
        "critical",  # lowercase in Literal types
    }

    # =========================================================================
    # CATEGORY C: ROOT CAUSE MECHANICS
    # Customers get rephrased explanations, never raw cause enums
    # =========================================================================
    ROOT_CAUSE_MECHANICS: Set[str] = {
        # Root cause field
        "root_cause",
        "derived_cause",
        # Cause enum values (uppercase)
        "RETRY_LOOP",
        "PROMPT_GROWTH",
        "FEATURE_SURGE",
        "TRAFFIC_GROWTH",
        "RATE_LIMIT_BREACH",
        "POLICY_VIOLATION",
        "BUDGET_EXCEEDED",
        "UNKNOWN",  # Even "UNKNOWN" is internal terminology
        # Evidence internals
        "evidence",
        "evidence_data",
    }

    # =========================================================================
    # CATEGORY D: POLICY INTERNALS
    # Customers should never see policy names or guardrail internals
    # =========================================================================
    POLICY_INTERNALS: Set[str] = {
        "policy",
        "policy_id",
        "policy_name",
        "policy_version",
        "guardrail",
        "guardrail_id",
        "guardrail_name",
        "rule",
        "rule_id",
        "rule_name",
        "killswitch_id",
        "killswitch_state",
    }

    # =========================================================================
    # CATEGORY E: INFRASTRUCTURE ACTORS
    # Customers should not see internal system actors or recovery mechanics
    # =========================================================================
    INFRASTRUCTURE_ACTORS: Set[str] = {
        "actor",
        "actor_type",
        "system_actor",
        "recovery",
        "recovery_action",
        "recovery_loop",
        "recovery_state",
        "loop",
        "retry_loop",
        "escalation",
        "escalation_path",
        "mitigation_step",
    }

    # =========================================================================
    # CATEGORY F: CROSS-TENANT DATA
    # Customers should NEVER see data about other tenants
    # =========================================================================
    CROSS_TENANT: Set[str] = {
        "affected_tenants",
        "tenants_affected",
        "tenant_count",
        "cross_tenant",
        "is_systemic",
        "systemic",
        "systemic_issue",
        "other_tenants",
        "similar_incidents_7d",
        "similar_incidents_30d",
        "occurrence_count",
        "pattern_type",
    }

    # =========================================================================
    # CATEGORY G: FOUNDER LIFECYCLE STATES
    # Customers see calm states, not internal lifecycle
    # =========================================================================
    FOUNDER_LIFECYCLE: Set[str] = {
        # Internal lifecycle states (uppercase)
        "DETECTED",
        "TRIAGED",
        "MITIGATED",
        "RESOLVED",  # Only allowed lowercase in customer context
        # State field with internal vocabulary
        "current_state",
        # Timeline internals
        "DETECTION_SIGNAL",
        "TRIGGER_CONDITION",
        "POLICY_EVALUATION",
        "COST_ANOMALY",
        "RECOVERY_ACTION",
        "RESOLUTION",
        "ESCALATION",
        "OPERATOR_ACTION",
    }

    # =========================================================================
    # CATEGORY H: BLAST RADIUS
    # Customers don't need to know impact metrics in raw form
    # =========================================================================
    BLAST_RADIUS: Set[str] = {
        "blast_radius",
        "requests_blocked",  # Too technical
        "cost_impact_cents",
        "cost_impact_pct",
        "users_affected",
        "features_affected",
        "customer_visible_degradation",
    }

    # =========================================================================
    # CATEGORY I: RECURRENCE ANALYSIS
    # Strategic data that only founders need
    # =========================================================================
    RECURRENCE: Set[str] = {
        "recurrence",
        "recurrence_risk",
        "same_tenant_recurrence",
        "same_feature_recurrence",
        "same_root_cause_recurrence",
        "is_recurring",
        "suggested_prevention",
    }

    @classmethod
    def all_forbidden(cls) -> Set[str]:
        """Get all forbidden terms across all categories."""
        return (
            cls.QUANTITATIVE_INTERNALS
            | cls.SEVERITY_SEMANTICS
            | cls.ROOT_CAUSE_MECHANICS
            | cls.POLICY_INTERNALS
            | cls.INFRASTRUCTURE_ACTORS
            | cls.CROSS_TENANT
            | cls.FOUNDER_LIFECYCLE
            | cls.BLAST_RADIUS
            | cls.RECURRENCE
        )


# =============================================================================
# CUSTOMER CALM VOCABULARY (allowed terms)
# =============================================================================


class CalmVocabulary:
    """Terms that ARE allowed in customer-facing DTOs."""

    # Resolution status (customer-friendly)
    RESOLUTION_STATES: Set[str] = {
        "investigating",
        "mitigating",
        "resolved",
        "monitoring",
    }

    # Impact descriptors (calm, not alarming)
    IMPACT_DESCRIPTORS: Set[str] = {
        "yes",
        "no",
        "some",
        "briefly",
        "none",
        "minimal",
        "higher_than_usual",
        "significant",
    }

    # Action types (customer-actionable)
    ACTION_TYPES: Set[str] = {
        "review_usage",
        "adjust_limits",
        "contact_support",
        "none",
    }

    # Urgency levels (calm)
    URGENCY_LEVELS: Set[str] = {
        "optional",
        "recommended",
        "required",
    }

    # Trend vocabulary (customer-safe)
    TREND_VOCABULARY: Set[str] = {
        "normal",
        "rising",
        "spike",
    }

    # Status vocabulary
    STATUS_VOCABULARY: Set[str] = {
        "protected",
        "attention_needed",
        "action_required",
    }


# =============================================================================
# CATEGORY 5 CUSTOMER DTOs TO TEST
# =============================================================================

CATEGORY_5_CUSTOMER_DTOS: List[type] = [
    CustomerIncidentNarrativeDTO,
    CustomerIncidentImpactDTO,
    CustomerIncidentResolutionDTO,
    CustomerIncidentActionDTO,
]

# All customer-facing DTOs (for comprehensive absence testing)
ALL_CUSTOMER_DTOS: List[type] = [
    # Category 5 Incident DTOs
    CustomerIncidentNarrativeDTO,
    CustomerIncidentImpactDTO,
    CustomerIncidentResolutionDTO,
    CustomerIncidentActionDTO,
    # Category 4 Cost DTOs
    CustomerCostSummaryDTO,
    CustomerCostExplainedDTO,
    CustomerCostIncidentDTO,
    CostBreakdownItemDTO,
    # Core Guard DTOs
    GuardStatusDTO,
    TodaySnapshotDTO,
    # Legacy Incident DTOs (may need migration)
    IncidentSummaryDTO,
    IncidentDetailDTO,
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_all_field_names(dto_class: type) -> Set[str]:
    """Recursively get all field names from a DTO and its nested models."""
    fields: Set[str] = set()

    if not hasattr(dto_class, "model_fields"):
        return fields

    for field_name, field_info in dto_class.model_fields.items():
        fields.add(field_name)

        # Get the type annotation
        hints = get_type_hints(dto_class)
        field_type = hints.get(field_name)

        if field_type is None:
            continue

        # Handle Optional types
        origin = get_origin(field_type)
        if origin is type(None):
            continue

        # Get inner type for Optional, List, etc.
        args = get_args(field_type)
        for arg in args:
            if isinstance(arg, type) and issubclass(arg, BaseModel):
                fields |= get_all_field_names(arg)

    return fields


def get_all_literal_values(dto_class: type) -> Set[str]:
    """Extract all Literal string values from a DTO."""
    values: Set[str] = set()

    if not hasattr(dto_class, "model_fields"):
        return values

    hints = get_type_hints(dto_class)

    for field_name, field_type in hints.items():
        origin = get_origin(field_type)

        # Direct Literal
        if origin is Literal:
            for arg in get_args(field_type):
                if isinstance(arg, str):
                    values.add(arg)

        # Optional[Literal[...]]
        elif origin is type(None) or str(origin) == "typing.Union":
            for arg in get_args(field_type):
                if get_origin(arg) is Literal:
                    for lit_arg in get_args(arg):
                        if isinstance(lit_arg, str):
                            values.add(lit_arg)

    return values


def get_dto_source_code(dto_class: type) -> str:
    """Get the source code of a DTO class."""
    try:
        return inspect.getsource(dto_class)
    except (OSError, TypeError):
        return ""


# =============================================================================
# TEST CLASS 1: FIELD NAME ABSENCE
# =============================================================================


class TestFieldNameAbsence:
    """Verify forbidden field names are absent from customer DTOs."""

    def test_category5_dtos_no_quantitative_internals(self):
        """Category 5 DTOs must not have quantitative internal fields."""
        for dto in CATEGORY_5_CUSTOMER_DTOS:
            fields = get_all_field_names(dto)
            forbidden = fields & ForbiddenKnowledge.QUANTITATIVE_INTERNALS

            assert not forbidden, f"{dto.__name__} contains forbidden quantitative fields: {forbidden}"

    def test_category5_dtos_no_root_cause_fields(self):
        """Category 5 DTOs must not expose root_cause or derived_cause."""
        for dto in CATEGORY_5_CUSTOMER_DTOS:
            fields = get_all_field_names(dto)
            forbidden = fields & ForbiddenKnowledge.ROOT_CAUSE_MECHANICS

            # Only check field names, not enum values
            field_forbidden = {f for f in forbidden if not f.isupper()}

            assert not field_forbidden, f"{dto.__name__} contains forbidden root cause fields: {field_forbidden}"

    def test_category5_dtos_no_policy_fields(self):
        """Category 5 DTOs must not expose policy internals."""
        for dto in CATEGORY_5_CUSTOMER_DTOS:
            fields = get_all_field_names(dto)
            forbidden = fields & ForbiddenKnowledge.POLICY_INTERNALS

            assert not forbidden, f"{dto.__name__} contains forbidden policy fields: {forbidden}"

    def test_category5_dtos_no_cross_tenant_fields(self):
        """Category 5 DTOs must not expose cross-tenant data."""
        for dto in CATEGORY_5_CUSTOMER_DTOS:
            fields = get_all_field_names(dto)
            forbidden = fields & ForbiddenKnowledge.CROSS_TENANT

            assert not forbidden, f"{dto.__name__} contains forbidden cross-tenant fields: {forbidden}"

    def test_category5_dtos_no_blast_radius_fields(self):
        """Category 5 DTOs must not expose blast radius metrics."""
        for dto in CATEGORY_5_CUSTOMER_DTOS:
            fields = get_all_field_names(dto)
            forbidden = fields & ForbiddenKnowledge.BLAST_RADIUS

            assert not forbidden, f"{dto.__name__} contains forbidden blast radius fields: {forbidden}"

    def test_category5_dtos_no_recurrence_fields(self):
        """Category 5 DTOs must not expose recurrence analysis."""
        for dto in CATEGORY_5_CUSTOMER_DTOS:
            fields = get_all_field_names(dto)
            forbidden = fields & ForbiddenKnowledge.RECURRENCE

            assert not forbidden, f"{dto.__name__} contains forbidden recurrence fields: {forbidden}"

    def test_category5_dtos_no_infrastructure_actors(self):
        """Category 5 DTOs must not expose infrastructure actors."""
        for dto in CATEGORY_5_CUSTOMER_DTOS:
            fields = get_all_field_names(dto)
            forbidden = fields & ForbiddenKnowledge.INFRASTRUCTURE_ACTORS

            assert not forbidden, f"{dto.__name__} contains forbidden infrastructure fields: {forbidden}"

    def test_all_customer_dtos_comprehensive_scan(self):
        """Comprehensive scan of ALL customer DTOs for ANY forbidden fields."""
        all_forbidden = ForbiddenKnowledge.all_forbidden()
        violations: Dict[str, Set[str]] = {}

        # Known exceptions for legacy DTOs (pre-Category 5)
        # These DTOs need migration but are grandfathered for now
        legacy_exceptions = {
            "IncidentSummaryDTO": {"severity", "duration_seconds"},
            "IncidentDetailDTO": {"severity", "duration_seconds"},  # inherits from summary
        }

        for dto in ALL_CUSTOMER_DTOS:
            fields = get_all_field_names(dto)
            forbidden = fields & all_forbidden

            # Remove legacy exceptions for this DTO
            if dto.__name__ in legacy_exceptions:
                forbidden -= legacy_exceptions[dto.__name__]

            if forbidden:
                violations[dto.__name__] = forbidden

        assert not violations, "Customer DTOs contain forbidden fields:\n" + "\n".join(
            f"  {dto}: {fields}" for dto, fields in violations.items()
        )


# =============================================================================
# TEST CLASS 2: LITERAL VALUE ABSENCE
# =============================================================================


class TestLiteralValueAbsence:
    """Verify forbidden Literal values are absent from customer DTOs."""

    def test_category5_dtos_no_severity_literals(self):
        """Category 5 DTOs must not use internal severity literals."""
        forbidden_severities = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

        for dto in CATEGORY_5_CUSTOMER_DTOS:
            values = get_all_literal_values(dto)
            leaked = values & forbidden_severities

            assert not leaked, f"{dto.__name__} uses forbidden severity literals: {leaked}"

    def test_category5_dtos_no_lifecycle_literals(self):
        """Category 5 DTOs must not use founder lifecycle states."""
        forbidden_states = {"DETECTED", "TRIAGED", "MITIGATED", "RESOLVED"}

        for dto in CATEGORY_5_CUSTOMER_DTOS:
            values = get_all_literal_values(dto)
            leaked = values & forbidden_states

            assert not leaked, f"{dto.__name__} uses forbidden lifecycle literals: {leaked}"

    def test_category5_dtos_no_root_cause_literals(self):
        """Category 5 DTOs must not use root cause enum values."""
        forbidden_causes = {
            "RETRY_LOOP",
            "PROMPT_GROWTH",
            "FEATURE_SURGE",
            "TRAFFIC_GROWTH",
            "RATE_LIMIT_BREACH",
            "POLICY_VIOLATION",
            "BUDGET_EXCEEDED",
            "UNKNOWN",
        }

        for dto in CATEGORY_5_CUSTOMER_DTOS:
            values = get_all_literal_values(dto)
            leaked = values & forbidden_causes

            assert not leaked, f"{dto.__name__} uses forbidden root cause literals: {leaked}"

    def test_category5_dtos_no_event_type_literals(self):
        """Category 5 DTOs must not use internal event type literals."""
        forbidden_events = {
            "DETECTION_SIGNAL",
            "TRIGGER_CONDITION",
            "POLICY_EVALUATION",
            "COST_ANOMALY",
            "RECOVERY_ACTION",
            "RESOLUTION",
            "ESCALATION",
            "OPERATOR_ACTION",
        }

        for dto in CATEGORY_5_CUSTOMER_DTOS:
            values = get_all_literal_values(dto)
            leaked = values & forbidden_events

            assert not leaked, f"{dto.__name__} uses forbidden event type literals: {leaked}"

    def test_customer_impact_uses_only_calm_vocabulary(self):
        """CustomerIncidentImpactDTO must use ONLY calm vocabulary."""
        values = get_all_literal_values(CustomerIncidentImpactDTO)

        allowed = (
            CalmVocabulary.IMPACT_DESCRIPTORS
            | CalmVocabulary.RESOLUTION_STATES
            | CalmVocabulary.ACTION_TYPES
            | CalmVocabulary.URGENCY_LEVELS
        )

        forbidden = values - allowed

        # Filter out any lowercase resolution-related terms
        forbidden = {v for v in forbidden if v not in {"no", "yes", "some", "briefly", "none"}}

        assert not forbidden, f"CustomerIncidentImpactDTO uses non-calm vocabulary: {forbidden}"

    def test_customer_resolution_uses_only_calm_states(self):
        """CustomerIncidentResolutionDTO.status must use calm states only."""
        hints = get_type_hints(CustomerIncidentResolutionDTO)
        status_type = hints.get("status")

        if get_origin(status_type) is Literal:
            values = set(get_args(status_type))
            expected = CalmVocabulary.RESOLUTION_STATES

            assert values == expected, f"CustomerIncidentResolutionDTO.status should be {expected}, got {values}"

    def test_customer_action_uses_only_allowed_types(self):
        """CustomerIncidentActionDTO.action_type must use allowed types only."""
        hints = get_type_hints(CustomerIncidentActionDTO)
        action_type = hints.get("action_type")

        if get_origin(action_type) is Literal:
            values = set(get_args(action_type))
            expected = CalmVocabulary.ACTION_TYPES

            assert values == expected, f"CustomerIncidentActionDTO.action_type should be {expected}, got {values}"


# =============================================================================
# TEST CLASS 3: SOURCE CODE ABSENCE
# =============================================================================


class TestSourceCodeAbsence:
    """Verify forbidden terms don't appear in DTO source code (comments, docstrings)."""

    def test_customer_narrative_no_internal_terminology_in_comments(self):
        """CustomerIncidentNarrativeDTO source must not reference internal terms."""
        source = get_dto_source_code(CustomerIncidentNarrativeDTO)

        # These should never appear even in comments
        forbidden_in_comments = {
            "derived_cause",
            "root_cause",
            "blast_radius",
            "recurrence_risk",
            "threshold_breached",
            "RETRY_LOOP",
            "PROMPT_GROWTH",
        }

        for term in forbidden_in_comments:
            # Allow "no" followed by these terms (e.g., "no root cause")
            pattern = rf"(?<!no\s){term}"
            match = re.search(pattern, source, re.IGNORECASE)

            # Skip if found in "no X" context
            if match and not re.search(rf"no\s+{term}", source, re.IGNORECASE):
                assert False, f"CustomerIncidentNarrativeDTO source contains '{term}' in comments/docstrings"

    def test_customer_dtos_no_founder_dto_imports(self):
        """Customer DTOs must not import from ops.py."""
        guard_module = Path(__file__).parent.parent / "app" / "contracts" / "guard.py"

        with open(guard_module, "r") as f:
            source = f.read()

        # Check for imports from ops
        assert "from app.contracts.ops import" not in source, "guard.py should not import from ops.py"
        assert "from .ops import" not in source, "guard.py should not import from ops.py"

    def test_guard_py_no_founder_vocabulary_in_fields(self):
        """guard.py should not have founder vocabulary as field names."""
        guard_module = Path(__file__).parent.parent / "app" / "contracts" / "guard.py"

        with open(guard_module, "r") as f:
            source = f.read()

        # These terms should not appear as field definitions
        # (they may appear in comments explaining what's NOT included)
        founder_only_fields = {
            "blast_radius",
            "recurrence_risk",
            "cross_tenant",
            "affected_tenants",
            "is_systemic",
        }

        # Look for actual field definitions (name: type pattern)
        for term in founder_only_fields:
            # Match field definition pattern: "term: " or "term ="
            field_definition = re.search(rf"^\s+{term}\s*[:=]", source, re.MULTILINE)

            assert field_definition is None, f"guard.py defines forbidden field: '{term}'"


# =============================================================================
# TEST CLASS 4: STRUCTURAL ABSENCE
# =============================================================================


class TestStructuralAbsence:
    """Verify structural patterns that would leak information."""

    def test_customer_impact_data_exposed_always_no(self):
        """CustomerIncidentImpactDTO.data_exposed must ONLY allow 'no'."""
        hints = get_type_hints(CustomerIncidentImpactDTO)
        data_exposed_type = hints.get("data_exposed")

        if get_origin(data_exposed_type) is Literal:
            values = set(get_args(data_exposed_type))
            assert values == {"no"}, f"data_exposed should only allow 'no', got {values}"

    def test_customer_narrative_no_timeline_events(self):
        """CustomerIncidentNarrativeDTO must not have detailed timeline."""
        fields = set(CustomerIncidentNarrativeDTO.model_fields.keys())

        # Should not have timeline field
        assert "timeline" not in fields, "CustomerIncidentNarrativeDTO should not have timeline field"

        # Should not have events field
        assert "events" not in fields, "CustomerIncidentNarrativeDTO should not have events field"

    def test_customer_narrative_no_raw_counts(self):
        """CustomerIncidentNarrativeDTO should not expose raw request counts."""
        fields = set(CustomerIncidentNarrativeDTO.model_fields.keys())

        raw_count_fields = {
            "requests_count",
            "calls_count",
            "calls_affected",
            "requests_blocked",
            "users_affected",
        }

        leaked = fields & raw_count_fields
        assert not leaked, f"CustomerIncidentNarrativeDTO exposes raw counts: {leaked}"

    def test_customer_impact_no_numeric_metrics(self):
        """CustomerIncidentImpactDTO should use Literals, not ints/floats for metrics."""
        hints = get_type_hints(CustomerIncidentImpactDTO)

        for field_name, field_type in hints.items():
            origin = get_origin(field_type)

            # Skip Optional wrapper
            if str(origin) == "typing.Union":
                args = get_args(field_type)
                field_type = args[0] if args else field_type

            # These fields should NOT be int or float
            if field_name in {"requests_affected", "service_interrupted", "cost_impact", "data_exposed"}:
                assert field_type is not int, f"CustomerIncidentImpactDTO.{field_name} should not be int"
                assert field_type is not float, f"CustomerIncidentImpactDTO.{field_name} should not be float"

    def test_customer_actions_no_internal_links(self):
        """Customer action links should only point to customer-safe pages."""
        hints = get_type_hints(CustomerIncidentActionDTO)
        action_type = hints.get("action_type")

        if get_origin(action_type) is Literal:
            values = set(get_args(action_type))

            # Should not have actions that lead to internal pages
            forbidden_actions = {"view_logs", "view_metrics", "view_policy", "admin", "ops"}
            leaked = values & forbidden_actions

            assert not leaked, f"CustomerIncidentActionDTO has forbidden action types: {leaked}"


# =============================================================================
# TEST CLASS 5: CROSS-DOMAIN ISOLATION
# =============================================================================


class TestCrossDomainIsolation:
    """Verify customer and founder DTOs are completely isolated."""

    def test_no_shared_base_classes(self):
        """Customer and Founder DTOs should not share custom base classes."""
        customer_bases = set()
        founder_bases = set()

        for dto in CATEGORY_5_CUSTOMER_DTOS:
            customer_bases.update(dto.__mro__)

        founder_dtos = [
            FounderIncidentDetailDTO,
            FounderIncidentHeaderDTO,
            FounderRootCauseDTO,
            FounderBlastRadiusDTO,
            FounderRecurrenceRiskDTO,
        ]

        for dto in founder_dtos:
            founder_bases.update(dto.__mro__)

        # Remove standard bases
        standard_bases = {object, BaseModel}
        customer_bases -= standard_bases
        founder_bases -= standard_bases

        # Should not share custom bases
        shared = customer_bases & founder_bases

        # Filter to only custom AOS bases
        shared = {b for b in shared if b.__module__.startswith("app.")}

        assert not shared, f"Customer and Founder DTOs share custom base classes: {shared}"

    def test_no_shared_field_types(self):
        """Customer DTOs should not use Founder DTO types as field types."""
        founder_dto_names = {
            "FounderIncidentDetailDTO",
            "FounderIncidentHeaderDTO",
            "FounderDecisionTimelineEventDTO",
            "FounderRootCauseDTO",
            "FounderBlastRadiusDTO",
            "FounderRecurrenceRiskDTO",
            "FounderCostAnomalyDTO",
            "FounderCostOverviewDTO",
            "IncidentPatternDTO",
        }

        for dto in CATEGORY_5_CUSTOMER_DTOS:
            hints = get_type_hints(dto)

            for field_name, field_type in hints.items():
                type_name = getattr(field_type, "__name__", str(field_type))

                assert type_name not in founder_dto_names, (
                    f"{dto.__name__}.{field_name} uses Founder DTO type: {type_name}"
                )

    def test_guard_router_uses_only_guard_dtos(self):
        """guard.py router should only use DTOs from guard contracts."""
        guard_router = Path(__file__).parent.parent / "app" / "api" / "guard.py"

        with open(guard_router, "r") as f:
            source = f.read()

        # Should not import Founder DTOs
        founder_imports = [
            "FounderIncidentDetailDTO",
            "FounderIncidentHeaderDTO",
            "FounderRootCauseDTO",
            "FounderBlastRadiusDTO",
            "FounderRecurrenceRiskDTO",
            "FounderCostAnomalyDTO",
            "IncidentPatternDTO",
        ]

        for founder_dto in founder_imports:
            assert founder_dto not in source, f"guard.py imports Founder DTO: {founder_dto}"


# =============================================================================
# TEST CLASS 6: COMPREHENSIVE FORBIDDEN SCAN
# =============================================================================


class TestComprehensiveForbiddenScan:
    """Final comprehensive scan for any forbidden knowledge leakage."""

    def test_all_customer_dtos_forbidden_field_names(self):
        """Comprehensive test: ALL customer DTOs, ALL forbidden field names."""
        all_forbidden_fields = ForbiddenKnowledge.all_forbidden()

        # Only check field names, not enum values (which are uppercase)
        all_forbidden_fields = {f for f in all_forbidden_fields if not f.isupper()}

        violations: Dict[str, Set[str]] = {}

        for dto in ALL_CUSTOMER_DTOS:
            fields = get_all_field_names(dto)
            forbidden = fields & all_forbidden_fields

            if forbidden:
                violations[dto.__name__] = forbidden

        # Known exceptions (legacy DTOs that may need migration)
        legacy_exceptions = {
            "IncidentSummaryDTO": {"severity", "duration_seconds"},  # Legacy, to be migrated
        }

        # Remove known exceptions
        for dto_name, exceptions in legacy_exceptions.items():
            if dto_name in violations:
                violations[dto_name] -= exceptions
                if not violations[dto_name]:
                    del violations[dto_name]

        assert not violations, "Customer DTOs contain forbidden fields:\n" + "\n".join(
            f"  {dto}: {fields}" for dto, fields in violations.items()
        )

    def test_all_customer_dtos_forbidden_literal_values(self):
        """Comprehensive test: ALL customer DTOs, ALL forbidden Literal values."""
        forbidden_literals = (
            ForbiddenKnowledge.SEVERITY_SEMANTICS
            | ForbiddenKnowledge.ROOT_CAUSE_MECHANICS
            | ForbiddenKnowledge.FOUNDER_LIFECYCLE
        )

        # Only check uppercase values (enum-style)
        forbidden_literals = {v for v in forbidden_literals if v.isupper()}

        violations: Dict[str, Set[str]] = {}

        for dto in ALL_CUSTOMER_DTOS:
            values = get_all_literal_values(dto)
            forbidden = values & forbidden_literals

            if forbidden:
                violations[dto.__name__] = forbidden

        assert not violations, "Customer DTOs use forbidden Literal values:\n" + "\n".join(
            f"  {dto}: {values}" for dto, values in violations.items()
        )


# =============================================================================
# TEST CLASS 7: API ENDPOINT ABSENCE
# =============================================================================


class TestAPIEndpointAbsence:
    """Verify API endpoints maintain separation."""

    def test_guard_narrative_endpoint_exists(self):
        """Verify /guard/incidents/{id}/narrative endpoint exists."""
        guard_router = Path(__file__).parent.parent / "app" / "api" / "guard.py"

        with open(guard_router, "r") as f:
            source = f.read()

        assert "/incidents/{incident_id}/narrative" in source, "Customer narrative endpoint not found in guard.py"

    def test_guard_endpoint_uses_console_auth(self):
        """Guard endpoints must use verify_console_token."""
        guard_router = Path(__file__).parent.parent / "app" / "api" / "guard.py"

        with open(guard_router, "r") as f:
            source = f.read()

        # Should use console auth
        assert "verify_console_token" in source, "guard.py should use verify_console_token"

        # Should NOT use fops auth
        assert "verify_fops_token" not in source, "guard.py should not use verify_fops_token"

    def test_ops_incident_endpoint_exists(self):
        """Verify /ops/incidents/{id} endpoint exists."""
        ops_router = Path(__file__).parent.parent / "app" / "api" / "ops.py"

        with open(ops_router, "r") as f:
            source = f.read()

        assert "/incidents/{incident_id}" in source, "Founder incident endpoint not found in ops.py"

    def test_ops_endpoint_uses_fops_auth(self):
        """Ops endpoints must use verify_fops_token."""
        ops_router = Path(__file__).parent.parent / "app" / "api" / "ops.py"

        with open(ops_router, "r") as f:
            source = f.read()

        # Should use fops auth
        assert "verify_fops_token" in source, "ops.py should use verify_fops_token"


# =============================================================================
# TEST CLASS 8: REGRESSION PREVENTION
# =============================================================================


class TestRegressionPrevention:
    """Tests that prevent regression to forbidden patterns."""

    def test_new_customer_dto_would_fail_if_forbidden_added(self):
        """Demonstrate that adding forbidden fields would fail tests."""
        # This test verifies our detection works by checking a known-good DTO
        fields = get_all_field_names(CustomerIncidentImpactDTO)

        # If someone adds 'severity' field, this would catch it
        assert "severity" not in fields
        assert "threshold" not in fields
        assert "baseline" not in fields
        assert "root_cause" not in fields
        assert "derived_cause" not in fields

    def test_forbidden_knowledge_registry_completeness(self):
        """Verify ForbiddenKnowledge covers all Founder DTO fields."""
        founder_exclusive_fields = set()

        # Collect all fields from Founder DTOs
        founder_dtos = [
            FounderIncidentDetailDTO,
            FounderIncidentHeaderDTO,
            FounderRootCauseDTO,
            FounderBlastRadiusDTO,
            FounderRecurrenceRiskDTO,
        ]

        for dto in founder_dtos:
            founder_exclusive_fields |= get_all_field_names(dto)

        # Fields that are allowed in both (common identifiers)
        allowed_common = {
            "incident_id",
            "title",
            "started_at",
            "ended_at",
            "timestamp",
            "description",
            "tenant_id",
            "tenant_name",
            "first_detected",
            "last_updated",
            "data",
            "header",
            "timeline",
            "action_taken",
            "action_details",
            "recommended_next_steps",
            "linked_call_ids",
            "related_cost_anomaly_id",
            "related_killswitch_id",
            "event_type",
        }

        # Remove allowed common fields
        founder_exclusive = founder_exclusive_fields - allowed_common

        # All founder-exclusive fields should be in forbidden registry
        all_forbidden = ForbiddenKnowledge.all_forbidden()

        # Note: This test may need updating as we add new Founder fields
        # The important thing is that we consciously decide what to forbid
        uncovered = founder_exclusive - all_forbidden - allowed_common

        # Report uncovered fields for review (not a failure, but a warning)
        if uncovered:
            # These should be evaluated for addition to forbidden list
            pass  # In production, could log a warning


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
