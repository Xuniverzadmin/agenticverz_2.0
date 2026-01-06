# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: RBAC v2 authority enforcement for capabilities
# Callers: API routes (replay, predictions, etc.)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: PIN-307 (CAP-006 Auth Gateway), PIN-271 (RBAC Authority Separation)
# capability_id: CAP-001, CAP-004

"""
Authority Enforcement Module

Provides FastAPI dependencies for RBAC v2 capability authorization.
Converts GatewayContext to ActorContext and enforces permissions.

Usage:
    from app.auth.authority import require_replay_execute, require_predictions_read

    @router.post("/replay/{run_id}")
    async def replay_run(
        run_id: str,
        _auth: AuthorityResult = Depends(require_replay_execute),
    ):
        # _auth contains the authorization result and actor
        pass

INVARIANTS:
1. All capability routes MUST use authority dependencies
2. Default deny - missing permission = 403
3. All decisions are audited
4. No permission checks outside this module (for these capabilities)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, Request

from .actor import ActorContext, ActorType, IdentitySource
from .authorization import authorize, get_authorization_engine
from .contexts import GatewayContext, HumanAuthContext, MachineCapabilityContext
from .gateway_middleware import get_auth_context

logger = logging.getLogger("nova.auth.authority")


@dataclass
class AuthorityResult:
    """
    Result of capability authority check.

    Contains the authorization decision and actor for downstream use.
    """

    allowed: bool
    actor: ActorContext
    resource: str
    action: str
    reason: str
    tenant_id: Optional[str] = None

    def __repr__(self) -> str:
        status = "ALLOWED" if self.allowed else "DENIED"
        return f"AuthorityResult({status}: {self.action}:{self.resource})"


def gateway_context_to_actor(context: GatewayContext) -> ActorContext:
    """
    Convert GatewayContext to ActorContext for RBAC v2.

    This bridges the authentication layer (gateway) to the
    authorization layer (RBAC v2 engine).
    """
    if isinstance(context, HumanAuthContext):
        # Human flow - determine actor type from context
        # For now, assume EXTERNAL_PAID unless we have role hints
        roles = frozenset({"viewer"})  # Default role

        # Check for operator/founder indicators
        if context.email and (context.email.endswith("@xuniverz.com") or context.email.endswith("@agenticverz.com")):
            actor_type = ActorType.OPERATOR
            roles = frozenset({"founder"})
        else:
            actor_type = ActorType.EXTERNAL_PAID

        return ActorContext(
            actor_id=context.actor_id,
            actor_type=actor_type,
            source=IdentitySource.CLERK if context.auth_source.value == "clerk" else IdentitySource.DEV,
            tenant_id=context.tenant_id,
            account_id=context.account_id,
            team_id=None,
            roles=roles,
            permissions=frozenset(),  # Computed by AuthorizationEngine
            email=context.email,
            display_name=context.display_name,
        )

    elif isinstance(context, MachineCapabilityContext):
        # Machine flow - use scopes to determine roles
        # API keys have explicit scopes
        roles_from_scopes: set[str] = set()

        # Map scopes to roles
        if "admin" in context.scopes:
            roles_from_scopes.add("admin")
        if "write" in context.scopes or "execute" in context.scopes:
            roles_from_scopes.add("machine")
        if "read" in context.scopes:
            roles_from_scopes.add("viewer")
        if "replay" in context.scopes:
            roles_from_scopes.add("replay")
        if "predictions" in context.scopes:
            roles_from_scopes.add("predictions")

        # Default to machine role if no specific mapping
        if not roles_from_scopes:
            roles_from_scopes.add("machine")

        return ActorContext(
            actor_id=context.key_id,
            actor_type=ActorType.SYSTEM,  # API keys are SYSTEM actors
            source=IdentitySource.INTERNAL,
            tenant_id=context.tenant_id,
            account_id=None,
            team_id=None,
            roles=frozenset(roles_from_scopes),
            permissions=frozenset(),  # Computed by AuthorizationEngine
        )

    else:
        raise ValueError(f"Unknown context type: {type(context)}")


async def _check_authority(
    request: Request,
    resource: str,
    action: str,
    tenant_id: Optional[str] = None,
) -> AuthorityResult:
    """
    Internal function to check authority.

    Returns AuthorityResult - does NOT raise exception.
    """
    # Get gateway context
    gateway_ctx = get_auth_context(request)
    if gateway_ctx is None:
        return AuthorityResult(
            allowed=False,
            actor=ActorContext(
                actor_id="anonymous",
                actor_type=ActorType.EXTERNAL_TRIAL,
                source=IdentitySource.DEV,
                tenant_id=None,
                account_id=None,
                team_id=None,
                roles=frozenset(),
                permissions=frozenset(),
            ),
            resource=resource,
            action=action,
            reason="not_authenticated",
        )

    # Convert to ActorContext
    actor = gateway_context_to_actor(gateway_ctx)

    # Compute permissions from roles
    engine = get_authorization_engine()
    actor_with_perms = engine.compute_permissions(actor)

    # Check authorization
    auth_result = authorize(
        actor_with_perms,
        resource=resource,
        action=action,
        tenant_id=tenant_id or actor_with_perms.tenant_id,
    )

    # Log the decision
    logger.info(
        "authority_check",
        extra={
            "resource": resource,
            "action": action,
            "actor_id": actor.actor_id,
            "actor_type": actor.actor_type.value,
            "tenant_id": tenant_id or actor.tenant_id,
            "decision": "allow" if auth_result.allowed else "deny",
            "reason": auth_result.reason,
        },
    )

    return AuthorityResult(
        allowed=auth_result.allowed,
        actor=actor_with_perms,
        resource=resource,
        action=action,
        reason=auth_result.reason,
        tenant_id=tenant_id or actor.tenant_id,
    )


def _require_authority(resource: str, action: str):
    """
    Factory for authority enforcement dependencies.

    Returns a FastAPI dependency that checks the specific permission.
    """

    async def dependency(request: Request) -> AuthorityResult:
        result = await _check_authority(request, resource, action)

        if not result.allowed:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "authority_denied",
                    "resource": resource,
                    "action": action,
                    "reason": result.reason,
                },
            )

        return result

    return dependency


# =============================================================================
# Replay Capability Authority (CAP-001)
# =============================================================================


async def require_replay_read(request: Request) -> AuthorityResult:
    """Require read:replay permission."""
    return await _require_authority("replay", "read")(request)


async def require_replay_execute(request: Request) -> AuthorityResult:
    """Require execute:replay permission."""
    return await _require_authority("replay", "execute")(request)


async def require_replay_audit(request: Request) -> AuthorityResult:
    """Require audit:replay permission."""
    return await _require_authority("replay", "audit")(request)


async def require_replay_admin(request: Request) -> AuthorityResult:
    """Require admin:replay permission."""
    return await _require_authority("replay", "admin")(request)


# =============================================================================
# Prediction Capability Authority (CAP-004)
# =============================================================================


async def require_predictions_read(request: Request) -> AuthorityResult:
    """Require read:predictions permission."""
    return await _require_authority("predictions", "read")(request)


async def require_predictions_execute(request: Request) -> AuthorityResult:
    """Require execute:predictions permission."""
    return await _require_authority("predictions", "execute")(request)


async def require_predictions_audit(request: Request) -> AuthorityResult:
    """Require audit:predictions permission."""
    return await _require_authority("predictions", "audit")(request)


async def require_predictions_admin(request: Request) -> AuthorityResult:
    """Require admin:predictions permission."""
    return await _require_authority("predictions", "admin")(request)


# =============================================================================
# Tenant Isolation Helpers
# =============================================================================


def verify_tenant_access(auth: AuthorityResult, target_tenant_id: str) -> None:
    """
    Verify actor can access resource in target tenant.

    Raises 403 if tenant mismatch (except for operators).
    """
    if auth.actor.actor_type == ActorType.OPERATOR:
        return  # Operators can access any tenant

    if auth.tenant_id != target_tenant_id:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "tenant_isolation",
                "actor_tenant": auth.tenant_id,
                "target_tenant": target_tenant_id,
            },
        )


# =============================================================================
# Prometheus Metrics for Authority Decisions
# =============================================================================

try:
    from prometheus_client import Counter

    AUTHORITY_ALLOW_COUNTER = Counter(
        "nova_authority_allow_total",
        "Total allowed authority decisions",
        ["capability", "action"],
    )

    AUTHORITY_DENY_COUNTER = Counter(
        "nova_authority_deny_total",
        "Total denied authority decisions",
        ["capability", "action", "reason"],
    )

    def _record_authority_metric(capability: str, action: str, allowed: bool, reason: str = "") -> None:
        """Record authority decision metric."""
        if allowed:
            AUTHORITY_ALLOW_COUNTER.labels(capability=capability, action=action).inc()
        else:
            AUTHORITY_DENY_COUNTER.labels(capability=capability, action=action, reason=reason[:50]).inc()

except ImportError:
    # Prometheus not installed
    def _record_authority_metric(capability: str, action: str, allowed: bool, reason: str = "") -> None:
        pass


# =============================================================================
# Audit Emission
# =============================================================================


async def emit_authority_audit(
    auth: AuthorityResult,
    capability: str,
    subject_id: Optional[str] = None,
    additional_context: Optional[dict] = None,
) -> None:
    """
    Emit audit event for authority decision.

    Called automatically by authority dependencies.
    Can be called explicitly for additional audit needs.
    """
    # Record Prometheus metric
    _record_authority_metric(
        capability=capability,
        action=auth.action,
        allowed=auth.allowed,
        reason=auth.reason if not auth.allowed else "",
    )

    try:
        from datetime import datetime

        from .gateway_audit import GatewayAuditEvent, _emit_event

        event = GatewayAuditEvent(
            event_type=f"authority.{capability}.{'allow' if auth.allowed else 'deny'}",
            timestamp=datetime.utcnow().isoformat(),
            request_id=None,  # Can be added from request context
            request_path=f"/{capability}/{subject_id}" if subject_id else f"/{capability}",
            request_method="CHECK",
            client_ip="internal",
            success=auth.allowed,
            auth_plane=None,
            auth_source=None,
            actor_id=auth.actor.actor_id,
            tenant_id=auth.tenant_id,
            error_code=None if auth.allowed else "DENIED",
            error_message=None if auth.allowed else auth.reason,
        )

        await _emit_event(event)

    except Exception as e:
        logger.warning(f"Failed to emit authority audit: {e}")
