# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Bridge RBACv1 → RBACv2 for shadow comparison
# Callers: RBACMiddleware
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L2
# Reference: PIN-271 (RBAC Authority Separation), PIN-273 (Phase 1 Complete)

"""
RBAC Integration Layer: RBACv1 ↔ RBACv2 Shadow Comparison.

=============================================================================
TERMINOLOGY (LOCKED - PIN-273)
=============================================================================

| Concept                      | Name                          |
|------------------------------|-------------------------------|
| Existing enforcement path    | RBACv1 (Enforcement Authority)|
| ActorContext + AuthEngine    | RBACv2 (Reference Authority)  |
| Shadow comparison            | RBACv2 Reference Mode         |
| Cutover                      | RBACv2 Enforcement Promotion  |

RBACv1 is the active enforcement authority.
RBACv2 is the reference authorization engine operating in shadow mode.
Promotion from reference → enforcement occurs only after equivalence is proven.

=============================================================================
COEXISTENCE INVARIANTS (MANDATORY)
=============================================================================

1. RBACv2 MUST NEVER enforce while RBACv1 is active
2. RBACv2 MUST ALWAYS run when shadow mode is enabled
3. Any discrepancy MUST be observable (log + metric)
4. No endpoint may bypass the integration layer
5. Promotion is a HUMAN-GOVERNED action, not a code flag
6. RBACv1 and RBACv2 MUST NEVER co-decide (no hybrid decisions)

=============================================================================

This module provides the bridge between:
- RBACv1: PolicyObject, RBAC_MATRIX, extract_roles_from_request()
- RBACv2: ActorContext, AuthorizationEngine, IdentityChain

During coexistence:
- RBACv1 controls enforcement (authority)
- RBACv2 runs in reference mode (shadow)
- Discrepancies are tracked for promotion gate decisions

Usage:
    from app.auth.rbac_integration import (
        extract_actor_from_request,
        authorize_with_v2_engine,
        compare_decisions,
    )

    # In RBACMiddleware.dispatch():
    v1_decision = enforce(policy, request)           # RBACv1
    actor = await extract_actor_from_request(request)
    v2_result = authorize_with_v2_engine(actor, policy)  # RBACv2
    comparison = compare_decisions(v1_decision, v2_result)

Layer: L6 (Platform Substrate)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from fastapi import Request

from app.auth.actor import ActorContext, ActorType, IdentitySource
from app.auth.authorization import (
    AuthorizationResult,
    get_authorization_engine,
)
from app.auth.authorization import (
    Decision as V2Decision,
)
from app.auth.identity_chain import get_identity_chain

# Import RBACv1 types for comparison
from app.auth.rbac_middleware import (
    Decision as V1Decision,
)
from app.auth.rbac_middleware import (
    PolicyObject,
)

logger = logging.getLogger("nova.auth.rbac_integration")


# =============================================================================
# Decision Comparison
# =============================================================================


@dataclass
class DecisionComparison:
    """
    Comparison between RBACv1 and RBACv2 authorization decisions.

    Used for shadow audit to identify discrepancies before promotion.

    INVARIANT: This comparison is for observation only.
    RBACv1 and RBACv2 must NEVER co-decide based on this comparison.
    """

    v1_allowed: bool
    v2_allowed: bool
    match: bool
    discrepancy_type: Optional[str]  # None if match, else describes difference
    v1_reason: Optional[str]
    v2_reason: str
    actor_id: Optional[str]
    resource: str
    action: str

    def to_dict(self) -> dict:
        """Convert to dict for logging/metrics."""
        return {
            "v1_allowed": self.v1_allowed,
            "v2_allowed": self.v2_allowed,
            "match": self.match,
            "discrepancy_type": self.discrepancy_type,
            "v1_reason": self.v1_reason,
            "v2_reason": self.v2_reason,
            "actor_id": self.actor_id,
            "resource": self.resource,
            "action": self.action,
        }

    # Aliases for backward compatibility with tests
    @property
    def old_allowed(self) -> bool:
        return self.v1_allowed

    @property
    def new_allowed(self) -> bool:
        return self.v2_allowed

    @property
    def old_reason(self) -> Optional[str]:
        return self.v1_reason

    @property
    def new_reason(self) -> str:
        return self.v2_reason


# =============================================================================
# Actor Extraction
# =============================================================================


async def extract_actor_from_request(request: Request) -> Optional[ActorContext]:
    """
    Extract ActorContext from request using new IdentityChain.

    This is the primary integration point - converts request → ActorContext.
    Returns None if no valid identity can be extracted.

    Layer: L6 (calls L3 adapters via L6 chain)
    """
    chain = get_identity_chain()
    return await chain.extract_actor(request)


def build_fallback_actor_from_v1_roles(roles: list[str], request: Request) -> Optional[ActorContext]:
    """
    Build ActorContext from RBACv1 roles (fallback for comparison).

    This is used when IdentityChain cannot extract identity but RBACv1
    has roles. Allows comparison during coexistence.

    REMOVAL CONDITION: Remove after RBACv2 Enforcement Promotion.
    """
    if not roles:
        return None

    # Determine actor type from roles
    primary_role = roles[0].lower() if roles else ""

    if primary_role in ("founder", "operator"):
        actor_type = ActorType.OPERATOR
    elif primary_role == "machine":
        actor_type = ActorType.SYSTEM
    else:
        actor_type = ActorType.EXTERNAL_PAID

    # Determine source from how auth was done
    auth_header = request.headers.get("Authorization", "")
    machine_token = request.headers.get("X-Machine-Token", "")
    roles_header = request.headers.get("X-Roles", "")

    if machine_token:
        source = IdentitySource.SYSTEM
    elif auth_header.startswith("Bearer "):
        source = IdentitySource.CLERK
    elif roles_header:
        source = IdentitySource.DEV
    else:
        source = IdentitySource.INTERNAL

    # Get tenant from header (if present)
    tenant_id = request.headers.get("X-Tenant-ID")

    return ActorContext(
        actor_id=f"legacy:{primary_role}",
        actor_type=actor_type,
        source=source,
        tenant_id=tenant_id,
        account_id=None,
        team_id=None,
        roles=frozenset(roles),
        permissions=frozenset(),  # Will be computed by engine
        email=None,
        display_name=None,
    )


# =============================================================================
# Authorization
# =============================================================================


def authorize_with_v2_engine(
    actor: Optional[ActorContext],
    policy: PolicyObject,
    tenant_id: Optional[str] = None,
) -> AuthorizationResult:
    """
    Authorize using RBACv2 AuthorizationEngine (Reference Mode).

    Maps PolicyObject to AuthorizationEngine.authorize() call.
    Returns synthetic DENY result if actor is None.

    INVARIANT: This runs in reference mode only.
    RBACv2 must NEVER enforce while RBACv1 is active.

    Layer: L6 (calls L4 engine)
    """
    engine = get_authorization_engine()

    if actor is None:
        # No actor = no identity = deny
        return AuthorizationResult(
            allowed=False,
            decision=V2Decision.DENY,
            reason="no_actor:identity_extraction_failed",
            actor=_create_anonymous_actor(),
            resource=policy.resource,
            action=policy.action,
        )

    # Compute permissions if not already done
    if not actor.permissions:
        actor = engine.compute_permissions(actor)

    return engine.authorize(actor, policy.resource, policy.action, tenant_id)


# Backward compatibility alias
authorize_with_new_engine = authorize_with_v2_engine
build_fallback_actor_from_old_roles = build_fallback_actor_from_v1_roles


def _create_anonymous_actor() -> ActorContext:
    """Create a placeholder actor for denied anonymous requests."""
    return ActorContext(
        actor_id="anonymous",
        actor_type=ActorType.EXTERNAL_TRIAL,
        source=IdentitySource.INTERNAL,
        tenant_id=None,
        account_id=None,
        team_id=None,
        roles=frozenset(),
        permissions=frozenset(),
        email=None,
        display_name=None,
    )


# =============================================================================
# Decision Comparison
# =============================================================================


def compare_decisions(
    v1_decision: V1Decision,
    v2_result: AuthorizationResult,
    policy: PolicyObject,
) -> DecisionComparison:
    """
    Compare RBACv1 and RBACv2 authorization decisions.

    Identifies discrepancies for shadow audit before promotion.

    INVARIANT: This comparison is for observation only.
    RBACv1 and RBACv2 must NEVER co-decide based on this comparison.
    """
    v1_allowed = v1_decision.allowed
    v2_allowed = v2_result.allowed
    match = v1_allowed == v2_allowed

    discrepancy_type = None
    if not match:
        if v1_allowed and not v2_allowed:
            discrepancy_type = "v2_more_restrictive"
        else:
            discrepancy_type = "v2_more_permissive"

    return DecisionComparison(
        v1_allowed=v1_allowed,
        v2_allowed=v2_allowed,
        match=match,
        discrepancy_type=discrepancy_type,
        v1_reason=v1_decision.reason,
        v2_reason=v2_result.reason,
        actor_id=v2_result.actor.actor_id if v2_result.actor else None,
        resource=policy.resource,
        action=policy.action,
    )


# =============================================================================
# Resource/Action Mapping
# =============================================================================


def map_policy_to_permission(policy: PolicyObject) -> str:
    """
    Map PolicyObject to permission string.

    PolicyObject has (resource, action).
    Permission format is {action}:{resource}.
    """
    return f"{policy.action}:{policy.resource}"


def map_old_roles_to_new_roles(old_roles: list[str]) -> frozenset[str]:
    """
    Map old RBAC matrix roles to new role names.

    Most roles are identical, but some need mapping for consistency.
    """
    role_mapping = {
        # Old → New
        "infra": "admin",  # infra had admin-like perms
        "readonly": "viewer",  # readonly maps to viewer
        # These stay the same
        "founder": "founder",
        "operator": "operator",
        "admin": "admin",
        "machine": "machine",
        "dev": "developer",
    }

    new_roles = set()
    for role in old_roles:
        mapped = role_mapping.get(role.lower(), role.lower())
        new_roles.add(mapped)

    return frozenset(new_roles)


# =============================================================================
# Integration Helpers
# =============================================================================


async def parallel_authorize(
    request: Request,
    policy: PolicyObject,
) -> tuple[V1Decision, AuthorizationResult, DecisionComparison]:
    """
    Run RBACv1 and RBACv2 authorization in parallel (Reference Mode).

    Returns (v1_decision, v2_result, comparison).

    INVARIANT: RBACv1 is enforcement authority.
    RBACv2 is reference only - used for comparison, never for enforcement.
    """
    from app.auth.rbac_middleware import enforce

    # RBACv1 path (enforcement authority)
    v1_decision = enforce(policy, request)

    # RBACv2 path (reference mode)
    actor = await extract_actor_from_request(request)

    # Fallback: if RBACv2 chain didn't get actor but RBACv1 did
    if actor is None and v1_decision.roles:
        actor = build_fallback_actor_from_v1_roles(v1_decision.roles, request)
        if actor:
            engine = get_authorization_engine()
            actor = engine.compute_permissions(actor)

    v2_result = authorize_with_v2_engine(actor, policy)

    # Compare (observation only - never co-decide)
    comparison = compare_decisions(v1_decision, v2_result, policy)

    return v1_decision, v2_result, comparison


def log_decision_comparison(
    comparison: DecisionComparison,
    path: str,
    method: str,
) -> None:
    """
    Log RBACv1 ↔ RBACv2 decision comparison for shadow audit.

    Called by middleware to track discrepancies before promotion.

    INVARIANT: Logging is observation only.
    This must NEVER trigger enforcement changes.
    """
    if comparison.match:
        logger.debug(
            "rbac_v1_v2_match",
            extra={
                "path": path,
                "method": method,
                "allowed": comparison.v1_allowed,
                "resource": comparison.resource,
                "action": comparison.action,
                "actor_id": comparison.actor_id,
            },
        )
    else:
        logger.warning(
            "rbac_v1_v2_discrepancy",
            extra={
                "path": path,
                "method": method,
                "discrepancy": comparison.discrepancy_type,
                "v1_allowed": comparison.v1_allowed,
                "v2_allowed": comparison.v2_allowed,
                "v1_reason": comparison.v1_reason,
                "v2_reason": comparison.v2_reason,
                "resource": comparison.resource,
                "action": comparison.action,
                "actor_id": comparison.actor_id,
            },
        )
