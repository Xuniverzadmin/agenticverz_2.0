# Layer: L4 — hoc_spine Authority
# AUDIENCE: SHARED
# Role: Business invariant model — runtime-checkable domain invariants (BA-03)
# Product: system-wide
# Temporal:
#   Trigger: import
#   Execution: sync
# Callers: L4 handlers, L5 engines (invariant enforcement points)
# Allowed Imports: stdlib only
# Forbidden Imports: FastAPI, Starlette, DB, ORM
# Reference: BA-03 Business Invariant Registry
# artifact_class: CODE

"""
Business Invariant Registry (BA-03)

Defines and enforces runtime business invariants across all HOC domains.
Each invariant encodes a domain rule that must hold at a specific operation
boundary. Violations are fail-closed: the operation MUST NOT proceed when
a CRITICAL or HIGH invariant is violated.

INVARIANT MODEL:
    invariant_id          — string, unique identifier (BI-{domain}-{seq})
    operation             — string, the operation this invariant guards
    severity              — "CRITICAL" | "HIGH" | "MEDIUM"
    condition_description — human-readable invariant statement
    remediation           — guidance for callers when the invariant fails

This module contains NO framework imports — it is pure contract data + validation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal

logger = logging.getLogger("nova.hoc.business_invariants")

# =============================================================================
# INVARIANT MODEL
# =============================================================================

Severity = Literal["CRITICAL", "HIGH", "MEDIUM"]


@dataclass(frozen=True)
class Invariant:
    """A single business invariant that must hold at an operation boundary."""

    invariant_id: str
    operation: str
    severity: Severity
    condition_description: str
    remediation: str


class BusinessInvariantViolation(Exception):
    """Raised when a business invariant check fails."""

    def __init__(self, invariant_id: str, operation: str, severity: str, message: str):
        self.invariant_id = invariant_id
        self.operation = operation
        self.severity = severity
        self.message = message
        super().__init__(
            f"Business invariant violation [{severity}] {invariant_id} "
            f"on '{operation}': {message}"
        )


# =============================================================================
# INVARIANT REGISTRY
# =============================================================================

BUSINESS_INVARIANTS: dict[str, Invariant] = {
    # --- Tenant Lifecycle ---
    "BI-TENANT-001": Invariant(
        invariant_id="BI-TENANT-001",
        operation="project.create",
        severity="CRITICAL",
        condition_description=(
            "Tenant must exist and be in ACTIVE state before any project "
            "can be created under it. A project without a valid tenant owner "
            "is an orphan and violates the tenant-scoping boundary."
        ),
        remediation=(
            "Verify tenant existence and status via L6 tenant driver before "
            "proceeding. If tenant is missing or suspended, reject the request "
            "with a 404/409 and do not create the project."
        ),
    ),
    "BI-TENANT-002": Invariant(
        invariant_id="BI-TENANT-002",
        operation="tenant.create",
        severity="HIGH",
        condition_description=(
            "Tenant creation requires a valid org_id and non-empty tenant_name. "
            "A tenant without an org scope is un-ownable and violates the "
            "organizational scoping boundary."
        ),
        remediation=(
            "Validate org_id presence and tenant_name non-emptiness before "
            "proceeding. If either is missing, reject with 400."
        ),
    ),
    "BI-TENANT-003": Invariant(
        invariant_id="BI-TENANT-003",
        operation="tenant.delete",
        severity="HIGH",
        condition_description=(
            "Tenant deletion requires the tenant to exist and not be in CREATING "
            "state. Deleting a tenant mid-creation causes orphaned resources. "
            "Deleting a non-existent tenant is a no-op violation."
        ),
        remediation=(
            "Verify tenant existence and confirm status is not CREATING before "
            "proceeding. If tenant does not exist, reject with 404. If tenant "
            "is in CREATING state, reject with 409."
        ),
    ),
    # --- Onboarding ---
    "BI-ONBOARD-001": Invariant(
        invariant_id="BI-ONBOARD-001",
        operation="onboarding.activate",
        severity="CRITICAL",
        condition_description=(
            "Activation of a tenant requires ALL activation predicates to be "
            "satisfied: at least one API key provisioned, at least one "
            "integration enabled, and SDK attestation recorded. Partial "
            "activation is forbidden."
        ),
        remediation=(
            "Query the authoritative tables (api_keys, cus_integrations, "
            "sdk_attestations) to confirm all predicates. If any predicate "
            "is unsatisfied, return the predicate status map to the caller "
            "and block activation."
        ),
    ),
    # --- API Keys ---
    "BI-APIKEY-001": Invariant(
        invariant_id="BI-APIKEY-001",
        operation="api_key.create",
        severity="CRITICAL",
        condition_description=(
            "An API key must be scoped to an existing, active tenant. Keys "
            "scoped to non-existent or suspended tenants create dangling "
            "credentials that bypass tenant isolation."
        ),
        remediation=(
            "Resolve the tenant_id via L6 driver and confirm tenant status "
            "is ACTIVE before provisioning the key. Reject with 404 if "
            "tenant does not exist, 409 if tenant is suspended."
        ),
    ),
    # --- Integrations ---
    "BI-INTEG-001": Invariant(
        invariant_id="BI-INTEG-001",
        operation="integration.enable",
        severity="HIGH",
        condition_description=(
            "A connector must be registered in the connector registry before "
            "it can be enabled for a tenant. Enabling an unregistered connector "
            "type leads to runtime failures when the integration is invoked."
        ),
        remediation=(
            "Check the cus_integrations table and ConnectorRegistry for the "
            "connector_type. If not registered, reject the enable request and "
            "guide the caller to register the connector first."
        ),
    ),
    "BI-INTEG-002": Invariant(
        invariant_id="BI-INTEG-002",
        operation="integration.disable",
        severity="HIGH",
        condition_description=(
            "An integration can only be disabled if it exists and is currently "
            "in 'enabled' status. Disabling a non-existent integration is a "
            "no-op that masks data loss. Disabling an already-disabled "
            "integration overwrites the disable timestamp and corrupts the "
            "audit trail."
        ),
        remediation=(
            "Verify the integration exists and its current status is 'enabled' "
            "before applying the disable. Return 404 if the integration does "
            "not exist, 409 if already disabled."
        ),
    ),
    "BI-INTEG-003": Invariant(
        invariant_id="BI-INTEG-003",
        operation="integrations.query",
        severity="MEDIUM",
        condition_description=(
            "An integrations query must be scoped to a valid, non-empty "
            "tenant_id. Queries without tenant scoping break multi-tenancy "
            "isolation and may return cross-tenant data."
        ),
        remediation=(
            "Validate that tenant_id is present and non-empty in the "
            "operation context before dispatching the query. Return 400 "
            "if tenant_id is missing or empty."
        ),
    ),
    # --- Policies ---
    "BI-POLICY-001": Invariant(
        invariant_id="BI-POLICY-001",
        operation="policy.activate",
        severity="HIGH",
        condition_description=(
            "A policy must have a valid, non-empty schema definition before "
            "it can be activated. Activating a policy with a missing or "
            "malformed schema produces undefined enforcement behavior."
        ),
        remediation=(
            "Validate the policy schema field is present, is valid JSON, and "
            "conforms to the expected policy schema structure. Reject "
            "activation with a 422 if schema validation fails."
        ),
    ),
    "BI-POLICY-002": Invariant(
        invariant_id="BI-POLICY-002",
        operation="policy.deactivate",
        severity="HIGH",
        condition_description=(
            "A system-level policy must not be deactivated by a tenant-scoped "
            "caller. System policies are platform-wide and their deactivation "
            "requires founder or platform authority."
        ),
        remediation=(
            "Check that the policy is not system-level, or that the caller "
            "has founder/platform authority. Reject deactivation with a 403 "
            "if a tenant-scoped caller attempts to deactivate a system policy."
        ),
    ),
    # --- Controls ---
    "BI-CTRL-001": Invariant(
        invariant_id="BI-CTRL-001",
        operation="control.set_threshold",
        severity="HIGH",
        condition_description=(
            "A control threshold must be numeric (int or float) and "
            "non-negative. Negative thresholds invert control logic and "
            "non-numeric values cause runtime type errors in evaluation."
        ),
        remediation=(
            "Validate the threshold value is an instance of (int, float) "
            "and >= 0 before persisting. Return 422 with a clear message "
            "if the value is invalid."
        ),
    ),
    "BI-CTRL-002": Invariant(
        invariant_id="BI-CTRL-002",
        operation="killswitch.activate",
        severity="HIGH",
        condition_description=(
            "Killswitch activation requires a valid entity_id. Activating a "
            "killswitch on a non-existent entity creates a phantom freeze that "
            "silently blocks operations. An already-frozen entity must not be "
            "double-frozen to avoid audit trail corruption."
        ),
        remediation=(
            "Verify entity_id is present and non-empty. Check entity_frozen "
            "status before applying. If already frozen, reject with 409."
        ),
    ),
    "BI-CTRL-003": Invariant(
        invariant_id="BI-CTRL-003",
        operation="override.apply",
        severity="HIGH",
        condition_description=(
            "A limit override requires a valid limit_id and a non-negative "
            "override value. Overriding a non-existent limit creates orphaned "
            "records. Negative override values invert safety constraints."
        ),
        remediation=(
            "Validate limit_id presence, limit_exists flag, and that override "
            "value is numeric and >= 0. Reject with 400/404 as appropriate."
        ),
    ),
    # --- Incidents ---
    "BI-INCIDENT-001": Invariant(
        invariant_id="BI-INCIDENT-001",
        operation="incident.transition",
        severity="MEDIUM",
        condition_description=(
            "An incident cannot transition directly from RESOLVED to ACTIVE. "
            "The valid path is RESOLVED -> REOPENED -> ACTIVE. Direct "
            "transitions skip the reopening audit trail and lose the "
            "resolution context."
        ),
        remediation=(
            "Check the current incident status before applying the "
            "transition. If current status is RESOLVED and target is ACTIVE, "
            "reject with 409 and instruct the caller to reopen first."
        ),
    ),
    "BI-INCIDENT-002": Invariant(
        invariant_id="BI-INCIDENT-002",
        operation="incident.create",
        severity="HIGH",
        condition_description=(
            "An incident must be scoped to a valid tenant_id and must have "
            "a non-empty severity classification. Incidents without tenant "
            "scoping break multi-tenancy isolation. Incidents without severity "
            "prevent triage prioritization and SLA enforcement."
        ),
        remediation=(
            "Validate that tenant_id is present and non-empty, and that "
            "severity is one of the accepted values (CRITICAL, HIGH, MEDIUM, "
            "LOW) before creating the incident. Return 422 if either is "
            "missing or invalid."
        ),
    ),
    "BI-INCIDENT-003": Invariant(
        invariant_id="BI-INCIDENT-003",
        operation="incident.resolve",
        severity="HIGH",
        condition_description=(
            "An incident can only be resolved if it exists and is not already "
            "in RESOLVED state. Resolving a non-existent incident is a no-op "
            "that masks data loss. Resolving an already-resolved incident "
            "overwrites the original resolution context and corrupts the "
            "audit trail."
        ),
        remediation=(
            "Verify the incident exists and its current status is not "
            "RESOLVED before applying resolution. Return 404 if the incident "
            "does not exist, 409 if already resolved."
        ),
    ),
    # --- Activity ---
    "BI-ACTIVITY-001": Invariant(
        invariant_id="BI-ACTIVITY-001",
        operation="run.create",
        severity="CRITICAL",
        condition_description=(
            "Every run must have both a tenant_id and a project_id. Runs "
            "without tenant scoping break multi-tenancy isolation. Runs "
            "without project scoping prevent cost attribution and audit."
        ),
        remediation=(
            "Validate that both tenant_id and project_id are non-empty "
            "strings before creating the run. Return 422 if either is "
            "missing or empty."
        ),
    ),
    # --- Analytics ---
    "BI-ANALYTICS-001": Invariant(
        invariant_id="BI-ANALYTICS-001",
        operation="cost_record.create",
        severity="HIGH",
        condition_description=(
            "A cost record must reference a valid, existing run_id. Orphaned "
            "cost records that point to non-existent runs cannot be "
            "attributed and corrupt cost analytics."
        ),
        remediation=(
            "Verify the run_id exists in the runs table via L6 driver "
            "before persisting the cost record. If the run does not exist, "
            "reject with 404."
        ),
    ),
    # --- Logs ---
    "BI-LOGS-001": Invariant(
        invariant_id="BI-LOGS-001",
        operation="trace.append",
        severity="MEDIUM",
        condition_description=(
            "A trace entry must have a monotonically increasing sequence_no "
            "within its (tenant_id, project_id, run_id) scope. Non-monotonic "
            "sequence numbers break causal ordering of trace events and "
            "corrupt trace reconstruction."
        ),
        remediation=(
            "Query the current max sequence_no for the scope before "
            "appending. If the incoming sequence_no is <= current max, "
            "reject with 409 or auto-assign the next value depending on "
            "the caller's idempotency contract."
        ),
    ),
}

# =============================================================================
# INVARIANT-OPERATION ALIAS MAP
# =============================================================================

# Maps dispatch operation names to invariant operation names when they differ.
# The OperationRegistry dispatches using fully-qualified names like
# "account.onboarding.advance", but invariants are registered under semantic
# names like "onboarding.activate". This alias ensures invariant enforcement
# fires on the real dispatch path without renaming invariant definitions.
INVARIANT_OPERATION_ALIASES: dict[str, str] = {
    "account.onboarding.advance": "onboarding.activate",
    "api_keys.write": "api_key.create",
}


# =============================================================================
# INVARIANT CHECKERS
# =============================================================================

# Checker registry: invariant_id -> callable(context) -> (passed, message)
# Callers may register domain-specific checkers; defaults are structural.
_CHECKERS: dict[str, Any] = {}


def _default_check(invariant: Invariant, context: dict[str, Any]) -> tuple[bool, str]:
    """
    Default structural check for an invariant.

    When no domain-specific checker is registered, this performs basic
    structural validation based on the invariant's operation. Returns
    (True, "ok") if the context contains the minimum required keys, or
    (False, reason) otherwise.
    """
    operation = invariant.operation

    if operation == "tenant.create":
        org_id = context.get("org_id")
        tenant_name = context.get("tenant_name")
        if not org_id:
            return False, "org_id is required but missing from context"
        if not tenant_name or (isinstance(tenant_name, str) and not tenant_name.strip()):
            return False, "tenant_name is required and must be non-empty"
        return True, "ok"

    if operation == "tenant.delete":
        tenant_exists = context.get("tenant_exists", True)
        tenant_status = context.get("tenant_status")
        if not tenant_exists:
            return False, "tenant does not exist"
        if tenant_status == "CREATING":
            return False, "cannot delete tenant in CREATING state; wait for creation to complete"
        return True, "ok"

    if operation == "project.create":
        tenant_id = context.get("tenant_id")
        tenant_status = context.get("tenant_status")
        if not tenant_id:
            return False, "tenant_id is required but missing from context"
        if tenant_status and tenant_status != "ACTIVE":
            return False, f"tenant_status must be ACTIVE, got '{tenant_status}'"
        return True, "ok"

    if operation == "onboarding.activate":
        predicates = context.get("predicates", {})
        missing = [k for k, v in predicates.items() if not v]
        if missing:
            return False, f"unsatisfied activation predicates: {missing}"
        if not predicates:
            return False, "predicates dict is required but empty or missing"
        return True, "ok"

    if operation == "api_key.create":
        # Method-aware gate: BI-APIKEY-001 scoped to create_api_key only.
        # The alias api_keys.write → api_key.create fires for ALL write
        # methods (create, revoke, list). Non-create methods pass through.
        method = context.get("method")
        if method and method != "create_api_key":
            return True, f"ok — BI-APIKEY-001 scoped to create only, skipping for '{method}'"

        tenant_id = context.get("tenant_id")
        tenant_status = context.get("tenant_status")
        if not tenant_id:
            return False, "tenant_id is required but missing from context"
        if not tenant_status:
            return False, "tenant_status is required but missing from context — fail-closed"
        if tenant_status != "ACTIVE":
            return False, f"tenant must be ACTIVE to provision keys, got '{tenant_status}'"
        return True, "ok"

    if operation == "integration.enable":
        connector_type = context.get("connector_type")
        registered = context.get("connector_registered", False)
        if not connector_type:
            return False, "connector_type is required but missing from context"
        if not registered:
            return False, f"connector_type '{connector_type}' is not registered"
        return True, "ok"

    if operation == "integration.disable":
        integration_exists = context.get("integration_exists")
        current_status = context.get("current_status")
        if integration_exists is None:
            return False, "integration_exists is required but missing from context"
        if not integration_exists:
            return False, "integration does not exist"
        if not current_status:
            return False, "current_status is required but missing from context"
        if current_status == "disabled":
            return False, "integration is already disabled; cannot disable again"
        if current_status != "enabled":
            return False, f"integration must be in 'enabled' status to disable, got '{current_status}'"
        return True, "ok"

    if operation == "integrations.query":
        tenant_id = context.get("tenant_id")
        if not tenant_id:
            return False, "tenant_id is required but missing from context"
        return True, "ok"

    if operation == "policy.activate":
        schema = context.get("policy_schema")
        if not schema:
            return False, "policy_schema is required but missing or empty"
        if not isinstance(schema, (str, dict)):
            return False, f"policy_schema must be str or dict, got {type(schema).__name__}"
        return True, "ok"

    if operation == "policy.deactivate":
        is_system = context.get("is_system_policy", False)
        caller_type = context.get("actor_type", "user")
        if is_system and caller_type not in ("founder", "platform"):
            return (
                False,
                f"system policy cannot be deactivated by '{caller_type}' caller",
            )
        return True, "ok"

    if operation == "control.set_threshold":
        threshold = context.get("threshold")
        if threshold is None:
            return False, "threshold is required but missing from context"
        if not isinstance(threshold, (int, float)):
            return False, f"threshold must be numeric, got {type(threshold).__name__}"
        if threshold < 0:
            return False, f"threshold must be non-negative, got {threshold}"
        return True, "ok"

    if operation == "killswitch.activate":
        entity_id = context.get("entity_id")
        already_frozen = context.get("entity_frozen", False)
        if not entity_id:
            return False, "entity_id is required but missing from context"
        if already_frozen:
            return False, "entity is already frozen; cannot double-freeze"
        return True, "ok"

    if operation == "override.apply":
        limit_id = context.get("limit_id")
        limit_exists = context.get("limit_exists", True)
        override_value = context.get("override_value")
        if not limit_id:
            return False, "limit_id is required but missing from context"
        if not limit_exists:
            return False, f"limit_id '{limit_id}' does not exist"
        if override_value is None:
            return False, "override_value is required but missing from context"
        if not isinstance(override_value, (int, float)):
            return False, f"override_value must be numeric, got {type(override_value).__name__}"
        if override_value < 0:
            return False, f"override_value must be non-negative, got {override_value}"
        return True, "ok"

    if operation == "incident.create":
        tenant_id = context.get("tenant_id")
        severity = context.get("severity")
        if not tenant_id:
            return False, "tenant_id is required but missing from context"
        valid_severities = ("CRITICAL", "HIGH", "MEDIUM", "LOW")
        if not severity:
            return False, "severity is required but missing from context"
        if severity not in valid_severities:
            return False, f"severity must be one of {valid_severities}, got '{severity}'"
        return True, "ok"

    if operation == "incident.resolve":
        incident_exists = context.get("incident_exists", True)
        current_status = context.get("current_status")
        if not incident_exists:
            return False, "incident does not exist"
        if current_status == "RESOLVED":
            return False, "incident is already resolved; cannot resolve again"
        return True, "ok"

    if operation == "incident.transition":
        current_status = context.get("current_status")
        target_status = context.get("target_status")
        if current_status == "RESOLVED" and target_status == "ACTIVE":
            return False, "cannot transition RESOLVED -> ACTIVE; must reopen first"
        return True, "ok"

    if operation == "run.create":
        tenant_id = context.get("tenant_id")
        project_id = context.get("project_id")
        missing_fields = []
        if not tenant_id:
            missing_fields.append("tenant_id")
        if not project_id:
            missing_fields.append("project_id")
        if missing_fields:
            return False, f"required fields missing: {missing_fields}"
        return True, "ok"

    if operation == "cost_record.create":
        run_id = context.get("run_id")
        run_exists = context.get("run_exists", False)
        if not run_id:
            return False, "run_id is required but missing from context"
        if not run_exists:
            return False, f"run_id '{run_id}' does not exist"
        return True, "ok"

    if operation == "trace.append":
        sequence_no = context.get("sequence_no")
        max_sequence_no = context.get("max_sequence_no")
        if sequence_no is None:
            return False, "sequence_no is required but missing from context"
        if not isinstance(sequence_no, int):
            return False, f"sequence_no must be int, got {type(sequence_no).__name__}"
        if max_sequence_no is not None and sequence_no <= max_sequence_no:
            return False, (
                f"sequence_no must be > current max ({max_sequence_no}), "
                f"got {sequence_no}"
            )
        return True, "ok"

    # Unknown operation — pass with advisory
    return True, f"no structural check registered for operation '{operation}'"


def register_checker(invariant_id: str, checker: Any) -> None:
    """
    Register a domain-specific checker for an invariant.

    The checker must be a callable with signature:
        checker(context: dict) -> tuple[bool, str]
    """
    if invariant_id not in BUSINESS_INVARIANTS:
        raise ValueError(f"Unknown invariant_id: {invariant_id}")
    _CHECKERS[invariant_id] = checker


def check_invariant(invariant_id: str, context: dict[str, Any]) -> tuple[bool, str]:
    """
    Check a single business invariant against the provided context.

    Returns:
        (passed, message) — True/"ok" on success, False/reason on failure.

    Raises:
        ValueError if invariant_id is not in the registry.
    """
    invariant = BUSINESS_INVARIANTS.get(invariant_id)
    if invariant is None:
        raise ValueError(f"Unknown invariant_id: {invariant_id}")

    # Use domain-specific checker if registered, else default
    checker = _CHECKERS.get(invariant_id)
    if checker is not None:
        passed, message = checker(context)
    else:
        passed, message = _default_check(invariant, context)

    if not passed:
        logger.warning(
            "business_invariant_violation",
            extra={
                "invariant_id": invariant_id,
                "operation": invariant.operation,
                "severity": invariant.severity,
                "violation_message": message,
                "context_keys": list(context.keys()),
            },
        )

    return passed, message


def check_all_for_operation(
    operation: str, context: dict[str, Any]
) -> list[tuple[str, bool, str]]:
    """
    Check ALL invariants that guard a given operation.

    Resolves INVARIANT_OPERATION_ALIASES so that dispatch operation names
    (e.g. "account.onboarding.advance") also trigger checks for invariants
    registered under their semantic alias (e.g. "onboarding.activate").

    Returns:
        List of (invariant_id, passed, message) tuples for every invariant
        whose operation field matches the given operation string or its alias.
    """
    ops_to_check = {operation}
    alias = INVARIANT_OPERATION_ALIASES.get(operation)
    if alias:
        ops_to_check.add(alias)

    results: list[tuple[str, bool, str]] = []
    for inv_id, invariant in BUSINESS_INVARIANTS.items():
        if invariant.operation in ops_to_check:
            passed, message = check_invariant(inv_id, context)
            results.append((inv_id, passed, message))
    return results


__all__ = [
    "Invariant",
    "BusinessInvariantViolation",
    "BUSINESS_INVARIANTS",
    "INVARIANT_OPERATION_ALIASES",
    "check_invariant",
    "check_all_for_operation",
    "register_checker",
]
