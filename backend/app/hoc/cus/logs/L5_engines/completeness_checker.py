# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api/worker
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none (pure validation)
#   Writes: none
# Role: Evidence PDF completeness validation for SOC2 compliance
# Callers: pdf_renderer, evidence_report, export APIs
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, GAP-027 (Evidence PDF Completeness)

"""
Module: completeness_checker
Purpose: Validate evidence bundle completeness before PDF generation.

Evidence PDF exports require specific fields for SOC2 compliance.
This module validates that all required fields are present and
non-empty before allowing PDF generation.

Required Fields (Standard):
    - incident_id, tenant_id, run_id, trace_id
    - policy_snapshot_id, termination_reason
    - total_steps, total_tokens, total_cost_cents

SOC2 Required Fields (Enhanced):
    - control_mappings, attestation_statement
    - compliance_period_start, compliance_period_end

Exports:
    - EvidenceCompletenessError: Raised when evidence is incomplete
    - EvidenceCompletenessChecker: Main checker class
    - check_evidence_completeness: Quick helper function
    - ensure_evidence_completeness: Helper that raises on incomplete
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Optional, Set


class CompletenessCheckResult(str, Enum):
    """Result of a completeness check."""

    COMPLETE = "complete"  # All required fields present
    INCOMPLETE = "incomplete"  # Missing required fields
    VALIDATION_DISABLED = "validation_disabled"  # Validation is disabled
    PARTIAL = "partial"  # Some optional fields missing


# Required fields for standard evidence PDF
REQUIRED_EVIDENCE_FIELDS: FrozenSet[str] = frozenset({
    "bundle_id",
    "incident_id",
    "run_id",
    "trace_id",
    "tenant_id",
    "policy_snapshot_id",
    "termination_reason",
    "total_steps",
    "total_tokens",
    "total_cost_cents",
    "created_at",
    "exported_by",
})

# Additional required fields for SOC2 exports
SOC2_REQUIRED_FIELDS: FrozenSet[str] = frozenset({
    "control_mappings",
    "attestation_statement",
    "compliance_period_start",
    "compliance_period_end",
})

# Optional but recommended fields
RECOMMENDED_FIELDS: FrozenSet[str] = frozenset({
    "content_hash",
    "violation_step_index",
    "export_reason",
    "total_duration_ms",
})


class EvidenceCompletenessError(Exception):
    """
    Raised when evidence bundle is incomplete for PDF generation.

    This error indicates that required fields are missing
    and the PDF cannot be generated without them.
    """

    def __init__(
        self,
        message: str,
        missing_fields: Set[str],
        export_type: str,
        validation_enabled: bool,
    ):
        super().__init__(message)
        self.missing_fields = missing_fields
        self.export_type = export_type
        self.validation_enabled = validation_enabled

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/API responses."""
        return {
            "error": "EvidenceCompletenessError",
            "message": str(self),
            "missing_fields": sorted(self.missing_fields),
            "export_type": self.export_type,
            "validation_enabled": self.validation_enabled,
        }


@dataclass
class CompletenessCheckResponse:
    """Response from a completeness check."""

    result: CompletenessCheckResult
    is_complete: bool
    validation_enabled: bool
    export_type: str
    missing_required: Set[str]
    missing_recommended: Set[str]
    completeness_percentage: float
    message: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "result": self.result.value,
            "is_complete": self.is_complete,
            "validation_enabled": self.validation_enabled,
            "export_type": self.export_type,
            "missing_required": sorted(self.missing_required),
            "missing_recommended": sorted(self.missing_recommended),
            "completeness_percentage": self.completeness_percentage,
            "message": self.message,
        }


class EvidenceCompletenessChecker:
    """
    Checks evidence bundle completeness before PDF generation.

    GAP-027: Ensure evidence PDFs contain all required fields for SOC2.

    The checker validates that all required fields are present
    and non-empty before allowing PDF generation.

    Usage:
        checker = EvidenceCompletenessChecker(validation_enabled=True)

        # Before generating PDF
        checker.ensure_complete(bundle, "evidence")

        # Or check without raising
        response = checker.check(bundle, "evidence")
        if not response.is_complete and response.validation_enabled:
            handle_incomplete_evidence()
    """

    def __init__(
        self,
        validation_enabled: bool = True,
        strict_mode: bool = False,
    ):
        """
        Initialize the completeness checker.

        Args:
            validation_enabled: Whether completeness validation is enforced
            strict_mode: If True, recommended fields also count as required
        """
        self._validation_enabled = validation_enabled
        self._strict_mode = strict_mode

    @classmethod
    def from_governance_config(cls, config: Any) -> "EvidenceCompletenessChecker":
        """
        Create checker from GovernanceConfig.

        Args:
            config: GovernanceConfig instance

        Returns:
            EvidenceCompletenessChecker configured from config
        """
        validation_enabled = getattr(config, "evidence_completeness_enforce", True)
        strict_mode = getattr(config, "evidence_strict_mode", False)
        return cls(validation_enabled=validation_enabled, strict_mode=strict_mode)

    @property
    def validation_enabled(self) -> bool:
        """Check if validation is enabled."""
        return self._validation_enabled

    @property
    def strict_mode(self) -> bool:
        """Check if strict mode is enabled."""
        return self._strict_mode

    def get_required_fields(self, export_type: str) -> FrozenSet[str]:
        """
        Get required fields for an export type.

        Args:
            export_type: Type of export ("evidence", "soc2", "executive")

        Returns:
            Frozenset of required field names
        """
        if export_type == "soc2":
            return REQUIRED_EVIDENCE_FIELDS | SOC2_REQUIRED_FIELDS
        elif export_type == "executive":
            # Executive debrief has different required fields
            return frozenset({
                "bundle_id",
                "incident_id",
                "risk_level",
                "incident_summary",
                "business_impact",
                "policy_violated",
                "violation_time",
                "detection_time",
                "remediation_status",
                "recommended_actions",
                "prepared_by",
            })
        else:
            return REQUIRED_EVIDENCE_FIELDS

    def get_field_value(self, bundle: Any, field_name: str) -> Any:
        """
        Get field value from bundle (dict or object).

        Args:
            bundle: Evidence bundle (dict or object)
            field_name: Field name to retrieve

        Returns:
            Field value or None if not found
        """
        if isinstance(bundle, dict):
            return bundle.get(field_name)
        return getattr(bundle, field_name, None)

    def is_field_present(self, bundle: Any, field_name: str) -> bool:
        """
        Check if a field is present and non-empty.

        Args:
            bundle: Evidence bundle
            field_name: Field to check

        Returns:
            True if field is present and non-empty
        """
        value = self.get_field_value(bundle, field_name)

        if value is None:
            return False

        # Check for empty collections
        if isinstance(value, (list, dict, set)):
            return len(value) > 0

        # Check for empty strings
        if isinstance(value, str):
            return len(value.strip()) > 0

        # Numeric zero is valid
        return True

    def check(
        self,
        bundle: Any,
        export_type: str = "evidence",
    ) -> CompletenessCheckResponse:
        """
        Check if a bundle is complete for PDF generation.

        Args:
            bundle: Evidence bundle to check (dict or object)
            export_type: Type of export ("evidence", "soc2", "executive")

        Returns:
            CompletenessCheckResponse with validation result
        """
        required_fields = self.get_required_fields(export_type)

        # Find missing required fields
        missing_required: Set[str] = set()
        for field_name in required_fields:
            if not self.is_field_present(bundle, field_name):
                missing_required.add(field_name)

        # Find missing recommended fields
        missing_recommended: Set[str] = set()
        for field_name in RECOMMENDED_FIELDS:
            if not self.is_field_present(bundle, field_name):
                missing_recommended.add(field_name)

        # Calculate completeness percentage
        total_fields = len(required_fields) + len(RECOMMENDED_FIELDS)
        present_count = total_fields - len(missing_required) - len(missing_recommended)
        completeness_pct = (present_count / total_fields * 100) if total_fields > 0 else 100.0

        # In strict mode, recommended fields are also required
        if self._strict_mode:
            missing_required = missing_required | missing_recommended
            missing_recommended = set()

        # Determine result
        if not self._validation_enabled:
            return CompletenessCheckResponse(
                result=CompletenessCheckResult.VALIDATION_DISABLED,
                is_complete=len(missing_required) == 0,
                validation_enabled=False,
                export_type=export_type,
                missing_required=missing_required,
                missing_recommended=missing_recommended,
                completeness_percentage=completeness_pct,
                message="Completeness validation is disabled",
            )

        if not missing_required:
            if missing_recommended:
                return CompletenessCheckResponse(
                    result=CompletenessCheckResult.PARTIAL,
                    is_complete=True,
                    validation_enabled=True,
                    export_type=export_type,
                    missing_required=missing_required,
                    missing_recommended=missing_recommended,
                    completeness_percentage=completeness_pct,
                    message=f"Evidence is complete but missing {len(missing_recommended)} recommended field(s)",
                )

            return CompletenessCheckResponse(
                result=CompletenessCheckResult.COMPLETE,
                is_complete=True,
                validation_enabled=True,
                export_type=export_type,
                missing_required=set(),
                missing_recommended=set(),
                completeness_percentage=100.0,
                message="Evidence is complete for PDF generation",
            )

        return CompletenessCheckResponse(
            result=CompletenessCheckResult.INCOMPLETE,
            is_complete=False,
            validation_enabled=True,
            export_type=export_type,
            missing_required=missing_required,
            missing_recommended=missing_recommended,
            completeness_percentage=completeness_pct,
            message=(
                f"Evidence is incomplete: missing {len(missing_required)} required field(s): "
                f"{sorted(missing_required)}"
            ),
        )

    def ensure_complete(
        self,
        bundle: Any,
        export_type: str = "evidence",
    ) -> None:
        """
        Ensure bundle is complete or raise error.

        This method should be called before PDF generation
        when validation is enabled.

        Args:
            bundle: Evidence bundle to validate
            export_type: Type of export

        Raises:
            EvidenceCompletenessError: If incomplete and validation enabled
        """
        response = self.check(bundle, export_type)

        if response.result == CompletenessCheckResult.INCOMPLETE:
            raise EvidenceCompletenessError(
                message=(
                    f"Evidence bundle incomplete for '{export_type}' PDF: "
                    f"missing {len(response.missing_required)} required field(s). "
                    f"Missing: {sorted(response.missing_required)}"
                ),
                missing_fields=response.missing_required,
                export_type=export_type,
                validation_enabled=True,
            )

    def should_allow_export(
        self,
        bundle: Any,
        export_type: str = "evidence",
    ) -> tuple[bool, str]:
        """
        Check if an export should be allowed.

        Returns a tuple with (allowed, reason) instead of raising.

        Args:
            bundle: Evidence bundle
            export_type: Type of export

        Returns:
            Tuple of (allowed, reason_message)
        """
        response = self.check(bundle, export_type)

        if response.is_complete:
            return True, response.message

        if not self._validation_enabled:
            return True, "Validation disabled - allowing incomplete export"

        return False, response.message

    def get_completeness_summary(
        self,
        bundle: Any,
        export_type: str = "evidence",
    ) -> Dict[str, Any]:
        """
        Get a summary of bundle completeness for reporting.

        Args:
            bundle: Evidence bundle
            export_type: Type of export

        Returns:
            Summary dict with field-level completeness info
        """
        required_fields = self.get_required_fields(export_type)

        field_status = {}
        for field_name in required_fields:
            field_status[field_name] = {
                "present": self.is_field_present(bundle, field_name),
                "required": True,
            }

        for field_name in RECOMMENDED_FIELDS:
            field_status[field_name] = {
                "present": self.is_field_present(bundle, field_name),
                "required": self._strict_mode,
            }

        present_count = sum(1 for f in field_status.values() if f["present"])
        total_count = len(field_status)

        return {
            "export_type": export_type,
            "total_fields": total_count,
            "present_fields": present_count,
            "completeness_percentage": (present_count / total_count * 100) if total_count > 0 else 100.0,
            "field_status": field_status,
        }


def check_evidence_completeness(
    bundle: Any,
    export_type: str = "evidence",
    validation_enabled: bool = True,
    strict_mode: bool = False,
) -> CompletenessCheckResponse:
    """
    Quick helper to check evidence completeness.

    Args:
        bundle: Evidence bundle to check
        export_type: Type of export
        validation_enabled: Whether validation is enforced
        strict_mode: Whether recommended fields are required

    Returns:
        CompletenessCheckResponse with validation result
    """
    checker = EvidenceCompletenessChecker(
        validation_enabled=validation_enabled,
        strict_mode=strict_mode,
    )
    return checker.check(bundle, export_type)


def ensure_evidence_completeness(
    bundle: Any,
    export_type: str = "evidence",
    validation_enabled: bool = True,
    strict_mode: bool = False,
) -> None:
    """
    Quick helper to ensure evidence completeness or raise error.

    Args:
        bundle: Evidence bundle to validate
        export_type: Type of export
        validation_enabled: Whether validation is enforced
        strict_mode: Whether recommended fields are required

    Raises:
        EvidenceCompletenessError: If incomplete and validation enabled
    """
    checker = EvidenceCompletenessChecker(
        validation_enabled=validation_enabled,
        strict_mode=strict_mode,
    )
    checker.ensure_complete(bundle, export_type)
