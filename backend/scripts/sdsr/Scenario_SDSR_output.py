"""
Scenario_SDSR_output.py

Epistemic boundary for SDSR.

Purpose:
    Convert implicit SDSR execution reality into an explicit,
    in-memory ScenarioSDSROutput object.

This module:
    - DOES NOT write files
    - DOES NOT modify the database
    - DOES NOT know about AURORA_L2
    - DOES NOT infer or guess truth

Truth is observed, not claimed.

Reference: CAPABILITY_STATUS_MODEL.yaml v2.0

=============================================================================
ARCHITECTURAL INVARIANT (LOCKED)
=============================================================================

This module is the SOLE AUTHORITY for declaring observed capabilities.
All other layers must treat this output as read-only truth.

Four locked rules:
1. SDSR_output is the sole authority for naming observed capabilities
2. SDSR never updates capability registry or belief state
3. Aurora never infers capabilities — it only applies belief transitions
4. Empty capabilities_observed is valid for INFRASTRUCTURE observations

SDSR_output names capabilities only as observed behavior, not as system belief.
=============================================================================
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Any, Literal, Dict


# =============================================================================
# AC v2 Evidence (BASELINE TRUST - SDSR-E2E-006)
# =============================================================================
# These dataclasses capture evidence required by Acceptance Criteria v2.
# Reference: SDSR-E2E-006.yaml expectations block
# =============================================================================

@dataclass
class RunRecordEvidence:
    """Evidence for AC-020, AC-021, AC-022: Run record metadata completeness."""
    # Fields present (with values or explicit null)
    fields_present: List[str] = field(default_factory=list)
    # Fields missing entirely (not just null)
    fields_missing: List[str] = field(default_factory=list)
    # Actual values for key fields
    run_id: Optional[str] = None
    actor_type: Optional[str] = None
    actor_id: Optional[str] = None
    auth_context: Optional[str] = None
    environment: Optional[str] = None
    sdk_version: Optional[str] = None
    operation_type: Optional[str] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    run_status: Optional[str] = None
    response_expected: Optional[bool] = None
    response_received: Optional[bool] = None
    timestamp_start: Optional[str] = None
    timestamp_end: Optional[str] = None


@dataclass
class ObservabilityEvidence:
    """Evidence for AC-024: Observability semantic integrity."""
    # Logs
    logs_exist: bool = False
    logs_correlated_to_run: bool = False
    entry_log_exists: bool = False
    exit_log_exists: bool = False
    # Traces
    trace_exists: bool = False
    trace_id: Optional[str] = None
    trace_steps_count: int = 0
    # Linkage verification
    steps_linked_to_trace: bool = False
    steps_linked_to_run: bool = False
    steps_linked_to_scenario: bool = False
    # Details
    orphan_step_ids: List[str] = field(default_factory=list)


@dataclass
class PolicyContextEvidence:
    """Evidence for AC-023: Policy evaluation explicitness."""
    policies_evaluated_exists: bool = False
    policies_evaluated_value: Optional[List[str]] = None
    policy_results_exists: bool = False
    policy_results_value: Optional[str] = None
    thresholds_checked_exists: bool = False
    thresholds_checked_value: Optional[bool] = None


@dataclass
class ExplicitOutcomeEvidence:
    """
    Evidence for AC-025: Explicit outcome assertions (PIN-407 CORRECTED).

    PIN-407 CORRECTION: "Success as First-Class Data"
    ------------------------------------------------
    Every run MUST produce incident and policy records.
    - For successful runs: incident=SUCCESS, policy=NO_VIOLATION
    - For failed runs: incident=FAILURE/PARTIAL/BLOCKED, policy=VIOLATION/NOT_APPLICABLE
    - Missing records indicate CAPTURE FAILURE, not "nothing happened"
    """
    # Incident outcome (MANDATORY for all runs)
    incident_created: bool = False  # Must be True for all runs
    incident_outcome: Optional[str] = None  # SUCCESS, FAILURE, PARTIAL, BLOCKED

    # Policy outcome (MANDATORY for all runs)
    policy_evaluated: bool = False  # Must be True for all runs
    policy_outcome: Optional[str] = None  # NO_VIOLATION, VIOLATION, ADVISORY, NOT_APPLICABLE

    # Policy proposal (created only when violation detected)
    policy_proposal_created: bool = False
    policy_proposal_needed: bool = False  # True only if violation occurred

    # For reference: table counts (observational, not authoritative)
    incidents_table_count: int = 0
    policies_table_count: int = 0
    proposals_table_count: int = 0

    # Capture validation (PIN-407: Missing success records = capture failure)
    capture_complete: bool = False  # True if all mandatory records exist
    capture_failures: List[str] = field(default_factory=list)


# Backward compatibility alias (DEPRECATED - use ExplicitOutcomeEvidence)
ExplicitAbsenceEvidence = ExplicitOutcomeEvidence


@dataclass
class IntegrityEvidence:
    """Evidence for AC-026: Integrity strictness."""
    expected_events: List[str] = field(default_factory=list)
    observed_events: List[str] = field(default_factory=list)
    missing_events: List[str] = field(default_factory=list)
    integrity_score: float = 0.0
    unknown_as_fail: bool = True  # Baseline rule: UNKNOWN ≡ FAIL


@dataclass
class ACv2Evidence:
    """
    Complete evidence package for AC v2 evaluation.

    BASELINE-ONLY: This is required for SDSR-E2E-006 certification.
    Other scenarios may have relaxed requirements.

    PIN-407 CORRECTION: Now uses ExplicitOutcomeEvidence (not absence).
    Success is data, not silence.
    """
    run_record: Optional[RunRecordEvidence] = None
    observability: Optional[ObservabilityEvidence] = None
    policy_context: Optional[PolicyContextEvidence] = None
    explicit_outcome: Optional[ExplicitOutcomeEvidence] = None  # PIN-407: renamed from explicit_absence
    integrity: Optional[IntegrityEvidence] = None
    # Evaluation timestamp
    evaluated_at: Optional[str] = None
    # Overall AC v2 result
    ac_v2_pass: Optional[bool] = None
    ac_v2_failures: List[str] = field(default_factory=list)

    # Backward compatibility property (DEPRECATED)
    @property
    def explicit_absence(self) -> Optional[ExplicitOutcomeEvidence]:
        """DEPRECATED: Use explicit_outcome instead."""
        return self.explicit_outcome


# =============================================================================
# Atomic truth units
# =============================================================================

@dataclass(frozen=True)
class ObservedEffect:
    """
    A concrete, observable state transition.

    This is the atomic unit of truth.
    Must represent a real state transition.
    Must be observable from system state.
    Must not be inferred.
    """
    entity: str                  # e.g. "policy_proposal", "incident", "run"
    field: str                   # e.g. "status", "severity"
    before: Optional[Any]        # None if newly created
    after: Optional[Any]         # None if deleted


@dataclass(frozen=True)
class ObservedCapability:
    """
    A capability demonstrably exercised by the scenario.

    Each entry must correspond to:
    - A real, named AURORA_L2 capability
    - A concrete system effect
    """
    capability_id: str           # e.g. "APPROVE" - must match AURORA_L2 capability_id
    effects: List[ObservedEffect]

    # Descriptive metadata only (non-authoritative)
    endpoint: Optional[str] = None
    method: Optional[str] = None


# =============================================================================
# Epistemic verdict object
# =============================================================================

@dataclass(frozen=True)
class ScenarioSDSROutput:
    """
    Authoritative in-memory truth object for a single SDSR scenario.

    This object represents what a single SDSR scenario actually proved
    about the system, independent of backend claims, UI needs, or
    governance decisions.

    Invariants:
    - One scenario → one ScenarioSDSROutput
    - No inference
    - No side effects
    - No AURORA_L2 knowledge
    - No file I/O
    - No DB mutation

    This object answers exactly one question:
    "What capabilities did this scenario demonstrably exercise,
     and what effects were observed?"

    Observation Classes:
    - INFRASTRUCTURE: Validates worker/execution/traces. Empty capabilities valid.
    - EFFECT: Produces irreversible state transitions. Non-empty capabilities expected.
    """

    # Identity
    scenario_id: str             # e.g. "SDSR-E2E-004" - from scenario YAML
    run_id: str                  # Execution run identifier

    # Verdict
    status: str                  # ENUM: "PASSED" | "FAILED" | "HALTED"

    # Observation classification (CRITICAL: mechanical discriminator)
    observation_class: Literal["INFRASTRUCTURE", "EFFECT"]

    # When this truth was materialized
    observed_at: datetime

    # Raw effects observed (state transitions)
    observed_effects: List[ObservedEffect]

    # What was proven (capabilities named by this module ONLY)
    realized_capabilities: List[ObservedCapability]

    # AC v2 evidence (BASELINE TRUST - SDSR-E2E-006)
    # Required for baseline certification, optional for other scenarios
    ac_v2_evidence: Optional[ACv2Evidence] = None

    # Optional, non-authoritative context
    notes: Optional[str] = None


# =============================================================================
# Capability Inference (SOLE AUTHORITY - Aurora must not duplicate this)
# =============================================================================

# Acceptance criteria mapping: effect patterns → capability IDs
# This is the ONLY place where capability names may be derived from effects
# Format: (entity, field, from_value, to_value): capability_id
CAPABILITY_ACCEPTANCE_CRITERIA: dict[tuple[str, str, str, str], str] = {
    # APPROVE capability: policy_proposal.status PENDING → APPROVED
    ("policy_proposal", "status", "PENDING", "APPROVED"): "APPROVE",
    # REJECT capability: policy_proposal.status PENDING → REJECTED
    ("policy_proposal", "status", "PENDING", "REJECTED"): "REJECT",
    # Additional capabilities can be added here as they are defined
}


def infer_capabilities_from_effects(
    observed_effects: List[ObservedEffect],
) -> List[ObservedCapability]:
    """
    Infer capabilities from observed effects using acceptance criteria.

    This function is the SOLE AUTHORITY for naming capabilities.
    Aurora must never duplicate this logic - it only receives the result.

    Parameters:
        observed_effects: List of state transitions observed during execution.

    Returns:
        List of ObservedCapability objects (may be empty).

    Note:
        Naming a capability ≠ asserting a capability exists in the registry.
        This is CLASSIFICATION, not belief mutation.
        Aurora decides belief transitions; SDSR only names proven behavior.
    """
    # Group effects by capability
    capability_effects: dict[str, List[ObservedEffect]] = {}

    for effect in observed_effects:
        # Skip effects with None values (not matching acceptance criteria patterns)
        if effect.before is None or effect.after is None:
            continue

        # Build the lookup key
        key = (effect.entity, effect.field, str(effect.before), str(effect.after))

        # Check if this effect matches any acceptance criteria
        capability_id = CAPABILITY_ACCEPTANCE_CRITERIA.get(key)

        if capability_id:
            if capability_id not in capability_effects:
                capability_effects[capability_id] = []
            capability_effects[capability_id].append(effect)

    # Build ObservedCapability objects
    result: List[ObservedCapability] = []

    for cap_id, effects in capability_effects.items():
        result.append(
            ObservedCapability(
                capability_id=cap_id,
                effects=effects,
            )
        )

    return result


# =============================================================================
# Factory / materializer
# =============================================================================

class ScenarioSDSROutputBuilder:
    """
    Builder responsible for materializing ScenarioSDSROutput
    from already-existing SDSR execution signals.

    This class does NOT execute logic.
    It only assembles observed truth.

    CRITICAL: This builder is the ONLY place where capabilities
    may be inferred from observed effects. Aurora never infers.
    """

    # Valid status values
    VALID_STATUSES = frozenset({"PASSED", "FAILED", "HALTED"})

    # Valid observation classes
    VALID_OBSERVATION_CLASSES = frozenset({"INFRASTRUCTURE", "EFFECT"})

    @staticmethod
    def from_execution(
        *,
        scenario_id: str,
        run_id: str,
        execution_status: str,
        observed_effects: List[ObservedEffect],
        ac_v2_evidence: Optional[ACv2Evidence] = None,
        notes: Optional[str] = None,
    ) -> ScenarioSDSROutput:
        """
        Materialize ScenarioSDSROutput from SDSR execution context.

        This method:
        1. Classifies the observation (INFRASTRUCTURE vs EFFECT)
        2. Infers capabilities from effects (if any)
        3. Builds the immutable output object

        Parameters:
            scenario_id:
                Stable scenario identifier from scenario YAML.

            run_id:
                Concrete execution run identifier.

            execution_status:
                Final execution status.
                Must already be normalized to:
                    "PASSED", "FAILED", or "HALTED".

            observed_effects:
                List of state transitions observed during execution.
                Empty list is valid (infrastructure scenario).

            notes:
                Optional human-readable context.

        Returns:
            ScenarioSDSROutput (in-memory only)

        Raises:
            ValueError: If execution_status is not valid.
        """
        if execution_status not in ScenarioSDSROutputBuilder.VALID_STATUSES:
            raise ValueError(
                f"Invalid execution_status: '{execution_status}'. "
                f"Must be one of: {ScenarioSDSROutputBuilder.VALID_STATUSES}"
            )

        # CAPABILITY INFERENCE: Only this module may do this
        # Aurora receives capabilities as read-only truth
        # Must happen BEFORE classification (classification depends on result)
        realized_capabilities: List[ObservedCapability] = []

        if execution_status == "PASSED" and observed_effects:
            realized_capabilities = infer_capabilities_from_effects(observed_effects)

        # =================================================================
        # MECHANICAL CLASSIFICATION (CORRECTED - 2026-01-11)
        # =================================================================
        # Classification is based on CAPABILITIES, not raw effects.
        #
        # Core rule:
        #   Observed effects are necessary but not sufficient for EFFECT.
        #   An EFFECT observation MUST prove at least one governed capability.
        #
        # If capabilities_observed is non-empty → EFFECT
        # Else → INFRASTRUCTURE
        #
        # This ensures:
        # - Internal state changes (incidents, etc.) stay as INFRASTRUCTURE
        # - Only governed, user-facing capabilities produce EFFECT observations
        # - Aurora capability registry remains clean
        # - No silent failures (EFFECT with zero capabilities)
        # =================================================================
        if realized_capabilities:
            observation_class: Literal["INFRASTRUCTURE", "EFFECT"] = "EFFECT"
        else:
            observation_class = "INFRASTRUCTURE"

        return ScenarioSDSROutput(
            scenario_id=scenario_id,
            run_id=run_id,
            status=execution_status,
            observation_class=observation_class,
            observed_at=datetime.now(timezone.utc),
            observed_effects=observed_effects,
            realized_capabilities=realized_capabilities,
            ac_v2_evidence=ac_v2_evidence,
            notes=notes,
        )


# =============================================================================
# Helper for building ObservedCapability (convenience, not required)
# =============================================================================

def build_observed_capability(
    capability_id: str,
    effects: List[tuple],
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
) -> ObservedCapability:
    """
    Convenience helper to build ObservedCapability from effect tuples.

    Parameters:
        capability_id: Capability ID (e.g. "APPROVE")
        effects: List of (entity, field, before, after) tuples
        endpoint: Optional API endpoint
        method: Optional HTTP method

    Returns:
        ObservedCapability instance

    Example:
        build_observed_capability(
            "APPROVE",
            [("policy_proposal", "status", "PENDING", "APPROVED")],
            endpoint="/api/v1/policy-proposals/{id}/approve",
            method="POST"
        )
    """
    observed_effects = [
        ObservedEffect(
            entity=e[0],
            field=e[1],
            before=e[2] if len(e) > 2 else None,
            after=e[3] if len(e) > 3 else None,
        )
        for e in effects
    ]

    return ObservedCapability(
        capability_id=capability_id,
        effects=observed_effects,
        endpoint=endpoint,
        method=method,
    )
