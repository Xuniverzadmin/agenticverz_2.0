# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api | worker | internal
#   Execution: sync
# Role: Authorization choke point (single entry for all authz decisions)
# Callers: API middleware, services, workers
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: docs/invariants/AUTHZ_AUTHORITY.md

"""
Authorization Choke Point

=============================================================================
INVARIANT: SINGLE AUTHORIZATION ENTRY POINT (I-AUTH-001)
=============================================================================
This module is the ONLY entry point for authorization decisions.

All callers MUST use `authorize_action()` from this module.
Direct calls to M7 (rbac_engine.py) or M28 (authorization.py) are FORBIDDEN.

Behavior:
1. Call M28 first (authoritative)
2. If M28 makes a decision → return it
3. If M28 cannot decide (unmapped resource) → fall back to M7 via mapping
4. Emit telemetry on every fallback
5. Eventually, all M7 fallbacks will be eliminated

Reference: docs/invariants/AUTHZ_AUTHORITY.md
=============================================================================

Usage:
    from app.auth.authorization_choke import authorize_action, AuthorizationDecision

    decision = authorize_action(
        actor=actor_context,
        resource="memory_pin",
        action="write",
        tenant_id=tenant_id,
    )

    if not decision.allowed:
        raise HTTPException(403, decision.reason)
"""

from __future__ import annotations

import logging
import os
import time
import traceback
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from app.auth.actor import ActorContext
from app.auth.authorization import (
    AuthorizationResult,
    get_authorization_engine,
)
from app.auth.authorization_metrics import (
    record_m7_fallback,
    record_tripwire_hit,
)
from app.auth.mappings import MappingResult, get_m28_equivalent

logger = logging.getLogger("nova.auth.choke")


# =============================================================================
# Enforcement Phases (T4)
# =============================================================================
# AUTHZ_PHASE controls how strictly M28 is enforced:
#   A = Read-only: Enforce M28 on reads, log M7 mismatch on writes
#   B = Write paths: Enforce M28 on writes, hard-fail on M7-only
#   C = Full: M28 only, M7 disabled
#
# Default is "A" for safe rollout.


class AuthzPhase(str, Enum):
    """Authorization enforcement phases."""

    PHASE_A = "A"  # Read-only enforcement, log writes
    PHASE_B = "B"  # Write path enforcement, hard-fail M7-only
    PHASE_C = "C"  # Full M28 enforcement, M7 disabled


def get_authz_phase() -> AuthzPhase:
    """Get current authorization phase from environment."""
    phase = os.getenv("AUTHZ_PHASE", "A").upper()
    try:
        return AuthzPhase(phase)
    except ValueError:
        logger.warning(f"Invalid AUTHZ_PHASE={phase}, defaulting to A")
        return AuthzPhase.PHASE_A


# Actions classified as "read" vs "write" for phased enforcement
READ_ACTIONS = frozenset(["read", "query", "suggest", "capabilities", "audit"])
WRITE_ACTIONS = frozenset(
    ["write", "delete", "admin", "execute", "approve", "heartbeat", "register", "reload", "simulate"]
)


# =============================================================================
# Strict Mode (LOCKED - PIN-310)
# =============================================================================
# AUTHZ_STRICT_MODE defaults to TRUE after M7 closure.
# M28 is the only authorization system. M7 fallback is forbidden.


def is_strict_mode() -> bool:
    """Check if strict mode is enabled. DEFAULT: TRUE after PIN-310."""
    return os.getenv("AUTHZ_STRICT_MODE", "true").lower() in ("true", "1", "yes")


def is_tripwire_mode() -> bool:
    """DEPRECATED: Tripwire mode was for M7 closure testing. Always returns False."""
    # PIN-310: Tripwire served its purpose. M7 closure complete.
    return False


class AuthorizationSource(str, Enum):
    """Source of the authorization decision."""

    M28_DIRECT = "m28_direct"  # M28 made the decision directly
    M28_VIA_MAPPING = "m28_via_mapping"  # M28 via M7→M28 mapping
    M7_FALLBACK = "m7_fallback"  # Fell back to M7 (DEPRECATED)
    DENIED_NO_MAPPING = "denied_no_mapping"  # No mapping exists
    DENIED_PHASE_C_NO_M7 = "denied_phase_c_no_m7"  # Phase C: M7 disabled
    LOGGED_WRITE_M7 = "logged_write_m7"  # Phase A: Write via M7, logged only


@dataclass(frozen=True)
class AuthorizationDecision:
    """
    Result of an authorization check through the choke point.

    Extends AuthorizationResult with source tracking for metrics.
    """

    allowed: bool
    reason: str
    source: AuthorizationSource
    actor: ActorContext
    resource: str
    action: str
    # Current enforcement phase
    phase: AuthzPhase = AuthzPhase.PHASE_A
    # Original M28 result if available
    m28_result: Optional[AuthorizationResult] = None
    # Mapping result if used
    mapping_result: Optional[MappingResult] = None
    # Latency tracking
    latency_ms: float = 0.0
    # Phase enforcement metadata
    would_fail_in_phase_b: bool = False  # Set if allowed in A but would fail in B
    would_fail_in_phase_c: bool = False  # Set if allowed in B but would fail in C

    def raise_if_denied(self) -> None:
        """
        Raise HTTPException if denied.

        Matches the interface of AuthorizationResult.
        """
        if not self.allowed:
            from fastapi import HTTPException

            raise HTTPException(status_code=403, detail=f"Denied: {self.reason}")

    def __repr__(self) -> str:
        status = "ALLOWED" if self.allowed else "DENIED"
        return f"AuthzDecision({status}: {self.action}:{self.resource} via {self.source.value})"


# =============================================================================
# M28-Known Resources (FROZEN SURFACE - PIN-310)
# =============================================================================
# These resources are natively supported by M28's ROLE_PERMISSIONS.
# For these, we call M28 directly without mapping.
#
# GUARDRAIL: Any new resource/action MUST be registered in:
#   docs/reports/AUTHZ_AUTHORITY_MATRIX.md
#
# This prevents quiet authority creep. No exceptions.

M28_NATIVE_RESOURCES = frozenset(
    [
        "runs",
        "agents",
        "skills",
        "traces",
        "metrics",
        "ops",
        "account",
        "team",
        "members",
        "members:team",
        "billing:account",
        "system",
        "policies",
        "replay",
        "predictions",
        "rbac",  # PIN-310: Added for rbac_api.py admin endpoints
    ]
)

# =============================================================================
# M7 Resources (require mapping to M28)
# =============================================================================
# These resources exist in M7 but not natively in M28.
# We map them to M28 equivalents.

M7_LEGACY_RESOURCES = frozenset(
    [
        "memory_pin",
        "prometheus",
        "costsim",
        "policy",  # Note: different from M28's "policies"
        "agent",  # M7 has extra actions (heartbeat, register)
        "runtime",
        "recovery",
    ]
)


def authorize_action(
    actor: ActorContext,
    resource: str,
    action: str,
    tenant_id: Optional[str] = None,
) -> AuthorizationDecision:
    """
    Authorize an action through the single entry point.

    ==========================================================================
    INVARIANT: This is the ONLY function that should be called for authorization.
    ==========================================================================

    Behavior:
    1. If resource is M28-native → call M28 directly
    2. If resource is M7-legacy → apply phased enforcement:
       - Phase A: Enforce reads, log writes (allow through)
       - Phase B: Enforce reads and writes, hard-fail M7-only
       - Phase C: Deny all M7 usage
    3. If no mapping exists → deny with telemetry
    4. Emit fallback metrics when M7 mapping is used

    Args:
        actor: The actor requesting access (from identity chain)
        resource: Resource being accessed (e.g., "runs", "memory_pin")
        action: Action being performed (e.g., "read", "write", "delete")
        tenant_id: Tenant context for the action (if applicable)

    Returns:
        AuthorizationDecision with decision, source, and telemetry data
    """
    start_time = time.perf_counter()
    engine = get_authorization_engine()
    phase = get_authz_phase()
    is_write = action in WRITE_ACTIONS

    # Fast path: M28-native resources (no phase restrictions)
    if resource in M28_NATIVE_RESOURCES:
        m28_result = engine.authorize(actor, resource, action, tenant_id)
        latency_ms = (time.perf_counter() - start_time) * 1000

        return AuthorizationDecision(
            allowed=m28_result.allowed,
            reason=m28_result.reason,
            source=AuthorizationSource.M28_DIRECT,
            actor=actor,
            resource=resource,
            action=action,
            phase=phase,
            m28_result=m28_result,
            latency_ms=latency_ms,
        )

    # Mapping path: M7-legacy resources (phased enforcement)
    if resource in M7_LEGACY_RESOURCES:
        strict_mode = is_strict_mode()

        # Strict mode: Hard-fail on any M7 usage
        if strict_mode:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "strict_mode_m7_blocked",
                extra={
                    "resource": resource,
                    "action": action,
                    "actor_id": actor.actor_id,
                    "phase": phase.value,
                    "strict_mode": True,
                },
            )
            return AuthorizationDecision(
                allowed=False,
                reason=f"strict_mode_m7_blocked:{resource}:{action}",
                source=AuthorizationSource.DENIED_PHASE_C_NO_M7,
                actor=actor,
                resource=resource,
                action=action,
                phase=phase,
                latency_ms=latency_ms,
            )

        # Phase C: M7 is disabled entirely
        if phase == AuthzPhase.PHASE_C:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.warning(
                "phase_c_m7_blocked",
                extra={
                    "resource": resource,
                    "action": action,
                    "actor_id": actor.actor_id,
                    "phase": phase.value,
                },
            )
            return AuthorizationDecision(
                allowed=False,
                reason=f"phase_c_m7_disabled:{resource}:{action}",
                source=AuthorizationSource.DENIED_PHASE_C_NO_M7,
                actor=actor,
                resource=resource,
                action=action,
                phase=phase,
                latency_ms=latency_ms,
            )

        mapping = get_m28_equivalent(resource, action)

        if mapping.is_valid or mapping.status.value == "deprecated":
            # Map to M28 and call M28
            m28_resource = mapping.resource
            m28_action = mapping.action

            # IMPORTANT: Even deprecated mappings work, they just emit warnings
            m28_result = engine.authorize(actor, m28_resource, m28_action, tenant_id)
            latency_ms = (time.perf_counter() - start_time) * 1000

            # Emit fallback telemetry (with tripwire support for T9)
            _emit_fallback_telemetry(
                original_resource=resource,
                original_action=action,
                mapped_resource=m28_resource,
                mapped_action=m28_action,
                actor_id=actor.actor_id,
                decision=m28_result.allowed,
                phase=phase.value,
                principal_type=actor.actor_type.value if actor.actor_type else "unknown",
                entry_point=actor.source or "unknown",
            )

            # Determine source based on phase and action type
            source = AuthorizationSource.M28_VIA_MAPPING
            if is_write and phase == AuthzPhase.PHASE_A:
                # Phase A: Log write operations but allow through
                source = AuthorizationSource.LOGGED_WRITE_M7
                logger.info(
                    "phase_a_write_logged",
                    extra={
                        "resource": resource,
                        "action": action,
                        "actor_id": actor.actor_id,
                        "allowed": m28_result.allowed,
                        "note": "Would be enforced in Phase B",
                    },
                )

            return AuthorizationDecision(
                allowed=m28_result.allowed,
                reason=m28_result.reason,
                source=source,
                actor=actor,
                resource=resource,
                action=action,
                phase=phase,
                m28_result=m28_result,
                mapping_result=mapping,
                latency_ms=latency_ms,
                would_fail_in_phase_c=True,  # All M7 usage would fail in Phase C
            )

        elif mapping.is_ambiguous:
            # HARD FAIL: Ambiguous mappings must be resolved
            latency_ms = (time.perf_counter() - start_time) * 1000

            logger.error(
                "ambiguous_mapping_denied",
                extra={
                    "resource": resource,
                    "action": action,
                    "actor_id": actor.actor_id,
                    "error": mapping.error,
                    "phase": phase.value,
                },
            )

            return AuthorizationDecision(
                allowed=False,
                reason=f"ambiguous_mapping:{resource}:{action}",
                source=AuthorizationSource.DENIED_NO_MAPPING,
                actor=actor,
                resource=resource,
                action=action,
                phase=phase,
                mapping_result=mapping,
                latency_ms=latency_ms,
            )

        else:
            # No mapping exists - behavior depends on phase
            latency_ms = (time.perf_counter() - start_time) * 1000

            # Phase B: Hard-fail on unmapped M7 patterns
            if phase == AuthzPhase.PHASE_B and is_write:
                logger.error(
                    "phase_b_unmapped_write_denied",
                    extra={
                        "resource": resource,
                        "action": action,
                        "actor_id": actor.actor_id,
                        "phase": phase.value,
                    },
                )
                return AuthorizationDecision(
                    allowed=False,
                    reason=f"phase_b_unmapped_write:{resource}:{action}",
                    source=AuthorizationSource.DENIED_NO_MAPPING,
                    actor=actor,
                    resource=resource,
                    action=action,
                    phase=phase,
                    mapping_result=mapping,
                    latency_ms=latency_ms,
                )

            # Phase A: Log but deny unmapped patterns
            logger.warning(
                "unmapped_resource_denied",
                extra={
                    "resource": resource,
                    "action": action,
                    "actor_id": actor.actor_id,
                    "phase": phase.value,
                },
            )

            return AuthorizationDecision(
                allowed=False,
                reason=f"unmapped:{resource}:{action}",
                source=AuthorizationSource.DENIED_NO_MAPPING,
                actor=actor,
                resource=resource,
                action=action,
                phase=phase,
                mapping_result=mapping,
                latency_ms=latency_ms,
            )

    # Unknown resource: Not in M28 native OR M7 legacy
    latency_ms = (time.perf_counter() - start_time) * 1000

    logger.warning(
        "unknown_resource_denied",
        extra={
            "resource": resource,
            "action": action,
            "actor_id": actor.actor_id,
            "phase": phase.value,
        },
    )

    return AuthorizationDecision(
        allowed=False,
        reason=f"unknown_resource:{resource}",
        source=AuthorizationSource.DENIED_NO_MAPPING,
        actor=actor,
        resource=resource,
        action=action,
        phase=phase,
        latency_ms=latency_ms,
    )


def _emit_fallback_telemetry(
    original_resource: str,
    original_action: str,
    mapped_resource: str,
    mapped_action: str,
    actor_id: str,
    decision: bool,
    phase: str = "A",
    principal_type: str = "unknown",
    entry_point: str = "unknown",
) -> None:
    """
    Emit telemetry when M7→M28 mapping fallback is used.

    This tracks:
    - Which M7 patterns are still in use
    - Which actors use legacy patterns
    - Fallback frequency for pruning decisions
    - Current enforcement phase

    Metrics:
    - Counter: authz_m7_fallback_total{resource, action, decision, phase}

    Tripwire Mode (T9):
    - When AUTHZ_TRIPWIRE=true, also captures:
      - Full stack trace
      - Principal type
      - Entry point
      - Counter: authz_m7_tripwire_total{resource, action, principal_type, entry_point}
    """
    # Record standard fallback metric
    record_m7_fallback(
        resource=original_resource,
        action=original_action,
        decision="allowed" if decision else "denied",
        phase=phase,
    )

    # Also log for structured logging pipelines
    logger.info(
        "authz_m7_fallback",
        extra={
            "original_resource": original_resource,
            "original_action": original_action,
            "mapped_resource": mapped_resource,
            "mapped_action": mapped_action,
            "actor_id": actor_id,
            "decision": "allowed" if decision else "denied",
            "phase": phase,
        },
    )

    # T9: Tripwire mode - capture full context for authority exhaustion
    if is_tripwire_mode():
        # Capture stack trace (skip this function and its callers in choke point)
        stack_frames = traceback.format_stack()
        # Filter to relevant frames (skip last 3: this function, caller, internal)
        relevant_stack = "".join(stack_frames[:-3]) if len(stack_frames) > 3 else "".join(stack_frames)

        # Record tripwire hit with full context
        record_tripwire_hit(
            resource=original_resource,
            action=original_action,
            principal_type=principal_type,
            entry_point=entry_point,
            actor_id=actor_id,
            stack_trace=relevant_stack,
        )


# =============================================================================
# Convenience Functions
# =============================================================================


def can_access(
    actor: ActorContext,
    resource: str,
    action: str,
    tenant_id: Optional[str] = None,
) -> bool:
    """
    Convenience function: returns True if authorized, False otherwise.

    Use authorize_action() when you need the full decision context.
    """
    decision = authorize_action(actor, resource, action, tenant_id)
    return decision.allowed


def require_permission(
    actor: ActorContext,
    resource: str,
    action: str,
    tenant_id: Optional[str] = None,
) -> AuthorizationDecision:
    """
    Require permission or raise HTTPException(403).

    Convenience function for API endpoints.
    """
    decision = authorize_action(actor, resource, action, tenant_id)
    decision.raise_if_denied()
    return decision


# =============================================================================
# Metrics Helpers (for T6: Metrics & Visibility)
# =============================================================================


def get_fallback_stats() -> dict:
    """
    Get statistics about M7 fallback usage.

    Returns summary for ops dashboard / pruning decisions.
    """
    # This will be enhanced in T6 with actual Prometheus queries
    return {
        "note": "Fallback stats will be populated from Prometheus metrics",
        "metric": "authz_m7_fallback_total",
        "labels": ["resource", "action", "decision"],
    }


# =============================================================================
# Self-Tests
# =============================================================================


# =============================================================================
# Request-Based Authorization (for API endpoints)
# =============================================================================


async def check_permission_request(
    resource: str,
    action: str,
    request,  # fastapi.Request - avoid import for L4 purity
    tenant_id: Optional[str] = None,
) -> AuthorizationDecision:
    """
    Async authorization check from a FastAPI Request.

    Extracts ActorContext from the request and routes through authorize_action().
    This is the replacement for M7's check_permission() function.

    Usage:
        from app.auth.authorization_choke import check_permission_request

        decision = await check_permission_request("rbac", "read", request)
        if not decision.allowed:
            raise HTTPException(status_code=403, detail=decision.reason)

    Args:
        resource: The resource to authorize (e.g., "rbac", "runs", "policies")
        action: The action to authorize (e.g., "read", "write", "admin")
        request: The FastAPI Request object
        tenant_id: Optional tenant scope

    Returns:
        AuthorizationDecision with allowed status and context
    """
    from app.auth.identity_chain import get_current_actor_optional

    # Extract actor from request
    actor = await get_current_actor_optional(request)

    if actor is None:
        # No identity - return denied decision
        return AuthorizationDecision(
            allowed=False,
            resource=resource,
            action=action,
            actor_id="anonymous",
            reason="No authentication context found",
            source=AuthorizationSource.DENIED_NO_MAPPING,
        )

    # Route through the canonical authorization path
    return authorize_action(actor, resource, action, tenant_id)


# =============================================================================
# Self-Tests
# =============================================================================


def _create_test_actor() -> ActorContext:
    """Create a test actor for self-tests."""
    from app.auth.actor import ActorType

    return ActorContext(
        actor_id="test-actor",
        actor_type=ActorType.OPERATOR,
        source="test",
        tenant_id="test-tenant",
        account_id="test-account",
        team_id="test-team",
        roles=frozenset(["operator"]),
        permissions=frozenset(["read:*", "write:*", "delete:*", "admin:*"]),
    )


def _test_m28_native_direct():
    """Test that M28-native resources go direct."""
    actor = _create_test_actor()

    decision = authorize_action(actor, "runs", "read")
    assert decision.source == AuthorizationSource.M28_DIRECT
    assert decision.allowed


def _test_m7_legacy_mapped():
    """Test that M7-legacy resources go through mapping."""
    actor = _create_test_actor()

    decision = authorize_action(actor, "memory_pin", "write")
    assert decision.source == AuthorizationSource.M28_VIA_MAPPING
    assert decision.mapping_result is not None


def _test_unknown_resource_denied():
    """Test that unknown resources are denied."""
    actor = _create_test_actor()

    decision = authorize_action(actor, "nonexistent", "read")
    assert not decision.allowed
    assert decision.source == AuthorizationSource.DENIED_NO_MAPPING


if __name__ == "__main__":
    _test_m28_native_direct()
    _test_m7_legacy_mapped()
    _test_unknown_resource_denied()
    print("All authorization choke point tests passed!")
