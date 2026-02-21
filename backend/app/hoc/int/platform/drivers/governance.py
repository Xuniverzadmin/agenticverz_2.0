# capability_id: CAP-012
# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: GovernanceError for mandatory cross-domain governance
# Callers: L2, L3, L4 services
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L5, L6
# Reference: CROSS_DOMAIN_GOVERNANCE.md

"""
GovernanceError - Mandatory Governance Failure

PIN: Cross-Domain Governance (design/CROSS_DOMAIN_GOVERNANCE.md)

This exception is raised when a governance operation fails.
Governance operations are MANDATORY - they must succeed or the
entire operation must fail.

DOCTRINE (from CROSS_DOMAIN_GOVERNANCE.md):

Rule 1: Governance Must Throw
    - If a customer-visible invariant is violated, raise GovernanceError
    - Never log-and-continue
    - Never return None

Rule 2: No Optional Dependencies
    - Governance code cannot depend on optional services
    - dispatcher=None patterns are forbidden

Rule 3: Learning is Downstream Only
    - M25/LoopEvent may fail without affecting customers
    - GovernanceError never affects learning systems

COROLLARY: Governance Errors Must Surface
    Any GovernanceError MUST:
    - Fail the request, OR
    - Mark the operation as failed in a customer-visible way

    It must NEVER be:
    - Logged and ignored
    - Converted into a warning
    - Retried-hidden
    - Deferred to async repair

DOMAINS USING THIS:
    - Activity -> Incidents: Run failures create incidents
    - Analytics -> Incidents: Cost anomalies create incidents
    - Policies <-> Analytics: Limit breaches are recorded
    - Overview -> All: Aggregation degrades gracefully (does NOT use GovernanceError)
"""

from typing import Optional

from app.metrics import governance_invariant_violations_total


class GovernanceError(Exception):
    """
    Raised when a governance operation fails.

    Governance operations are MANDATORY - they must succeed or the
    entire operation must fail. This includes:
    - Incident creation from run failures
    - Incident creation from cost anomalies
    - Limit breach recording
    - Policy enforcement recording

    Attributes:
        domain: The domain where the error occurred (Activity, Analytics, Policies, etc.)
        operation: The specific operation that failed
        entity_id: Optional ID of the entity involved (run_id, anomaly_id, etc.)
        message: Human-readable error message

    Example:
        try:
            incident = Incident(...)
            session.add(incident)
            await session.flush()
        except Exception as e:
            raise GovernanceError(
                message=str(e),
                domain="Activity",
                operation="create_incident_from_run_failure",
                entity_id=run_id,
            ) from e

    HANDLING RULES:
        - This exception MUST propagate to fail the request
        - Do NOT catch and log this exception
        - Do NOT convert to a warning
        - Do NOT retry silently
    """

    def __init__(
        self,
        message: str,
        domain: str,
        operation: str,
        entity_id: Optional[str] = None,
    ):
        self.domain = domain
        self.operation = operation
        self.entity_id = entity_id
        self.message = message

        # Format: [Domain] operation: message (entity_id)
        formatted_msg = f"[{domain}] {operation}: {message}"
        if entity_id:
            formatted_msg += f" (entity_id={entity_id})"

        # METRIC: Track governance violations
        # A quiet system has this counter at 0. Any increment indicates
        # a real governance failure that surfaced correctly.
        governance_invariant_violations_total.labels(
            domain=domain,
            operation=operation,
        ).inc()

        super().__init__(formatted_msg)

    def __repr__(self) -> str:
        return (
            f"GovernanceError("
            f"domain={self.domain!r}, "
            f"operation={self.operation!r}, "
            f"entity_id={self.entity_id!r}, "
            f"message={self.message!r})"
        )
