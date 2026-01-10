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
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Any


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
    entity: str                  # e.g. "policy", "incident", "run"
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
    """

    # Identity
    scenario_id: str             # e.g. "SDSR-E2E-004" - from scenario YAML
    run_id: str                  # Execution run identifier

    # Verdict
    status: str                  # ENUM: "PASSED" | "FAILED" | "HALTED"

    # When this truth was materialized
    observed_at: datetime

    # What was proven
    realized_capabilities: List[ObservedCapability]

    # Optional, non-authoritative context
    notes: Optional[str] = None


# =============================================================================
# Factory / materializer
# =============================================================================

class ScenarioSDSROutputBuilder:
    """
    Builder responsible for materializing ScenarioSDSROutput
    from already-existing SDSR execution signals.

    This class does NOT execute logic.
    It only assembles observed truth.
    """

    # Valid status values
    VALID_STATUSES = frozenset({"PASSED", "FAILED", "HALTED"})

    @staticmethod
    def from_execution(
        *,
        scenario_id: str,
        run_id: str,
        execution_status: str,
        observed_capabilities: List[ObservedCapability],
        notes: Optional[str] = None,
    ) -> ScenarioSDSROutput:
        """
        Materialize ScenarioSDSROutput from SDSR execution context.

        Parameters:
            scenario_id:
                Stable scenario identifier from scenario YAML.

            run_id:
                Concrete execution run identifier.

            execution_status:
                Final execution status.
                Must already be normalized to:
                    "PASSED", "FAILED", or "HALTED".

            observed_capabilities:
                Explicit list of capabilities that were
                demonstrably exercised.

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

        return ScenarioSDSROutput(
            scenario_id=scenario_id,
            run_id=run_id,
            status=execution_status,
            observed_at=datetime.now(timezone.utc),
            realized_capabilities=observed_capabilities,
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
            [("policy", "status", "PENDING", "APPROVED")],
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
