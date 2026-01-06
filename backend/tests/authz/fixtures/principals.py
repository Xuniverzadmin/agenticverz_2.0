# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: test
#   Execution: sync
# Role: Synthetic principal fixtures for authority exhaustion testing
# Callers: test_authority_exhaustion.py
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-310 (Fast-Track M7 Closure), T11

"""
Synthetic Principal Fixtures

Provides test actors covering all principal types for authority exhaustion testing.

Principal Coverage:
- HUMAN: admin, operator, viewer, developer, team_admin
- MACHINE: internal-worker, system-job, ci-pipeline, webhook, replay

Usage:
    from tests.authz.fixtures.principals import (
        HUMAN_PRINCIPALS,
        MACHINE_PRINCIPALS,
        ALL_PRINCIPALS,
        get_principal,
    )

    for principal_id, actor in ALL_PRINCIPALS.items():
        result = authorize_action(actor, resource, action)
        # ...
"""

from __future__ import annotations

from typing import Dict

from app.auth.actor import ActorContext, ActorType, IdentitySource

# =============================================================================
# HUMAN PRINCIPALS
# =============================================================================
# Humans authenticate via Clerk JWT and are tenant-scoped (except operators)

HUMAN_PRINCIPALS: Dict[str, ActorContext] = {
    # Operator (founder) - full access, no tenant scope
    "operator": ActorContext(
        actor_id="human:operator:founder-001",
        actor_type=ActorType.OPERATOR,
        source=IdentitySource.CLERK,
        tenant_id=None,
        account_id=None,
        team_id=None,
        roles=frozenset({"founder", "operator"}),
        permissions=frozenset({"*"}),
        email="founder@agenticverz.com",
        display_name="Founder Admin",
    ),
    # Enterprise Admin - full tenant access
    "admin": ActorContext(
        actor_id="human:admin:admin-001",
        actor_type=ActorType.EXTERNAL_PAID,
        source=IdentitySource.CLERK,
        tenant_id="tenant-test-001",
        account_id="account-test-001",
        team_id="team-test-001",
        roles=frozenset({"admin"}),
        permissions=frozenset(
            {
                "read:*",
                "write:*",
                "delete:*",
                "admin:account",
                "admin:team",
                "admin:members",
                "read:billing:account",
                "write:billing:account",
                "admin:replay",
                "admin:predictions",
            }
        ),
        email="admin@customer.com",
        display_name="Customer Admin",
    ),
    # Team Admin - team-level admin
    "team_admin": ActorContext(
        actor_id="human:team_admin:teamadmin-001",
        actor_type=ActorType.EXTERNAL_PAID,
        source=IdentitySource.CLERK,
        tenant_id="tenant-test-001",
        account_id="account-test-001",
        team_id="team-test-001",
        roles=frozenset({"team_admin"}),
        permissions=frozenset(
            {
                "read:*",
                "write:*",
                "admin:team",
                "admin:members:team",
            }
        ),
        email="teamlead@customer.com",
        display_name="Team Lead",
    ),
    # Developer - write runs/agents, execute
    "developer": ActorContext(
        actor_id="human:developer:dev-001",
        actor_type=ActorType.EXTERNAL_PAID,
        source=IdentitySource.CLERK,
        tenant_id="tenant-test-001",
        account_id="account-test-001",
        team_id="team-test-001",
        roles=frozenset({"developer"}),
        permissions=frozenset(
            {
                "read:*",
                "write:runs",
                "write:agents",
                "write:skills",
                "execute:*",
                "execute:replay",
                "execute:predictions",
            }
        ),
        email="dev@customer.com",
        display_name="Developer",
    ),
    # Viewer - read-only
    "viewer": ActorContext(
        actor_id="human:viewer:viewer-001",
        actor_type=ActorType.EXTERNAL_PAID,
        source=IdentitySource.CLERK,
        tenant_id="tenant-test-001",
        account_id="account-test-001",
        team_id="team-test-001",
        roles=frozenset({"viewer"}),
        permissions=frozenset(
            {
                "read:*",
                "audit:*",
                "read:replay",
                "read:predictions",
                "audit:replay",
                "audit:predictions",
            }
        ),
        email="viewer@customer.com",
        display_name="Viewer",
    ),
    # Trial User - limited access
    "trial_user": ActorContext(
        actor_id="human:trial:trial-001",
        actor_type=ActorType.EXTERNAL_TRIAL,
        source=IdentitySource.CLERK,
        tenant_id="tenant-trial-001",
        account_id="account-trial-001",
        team_id="team-trial-001",
        roles=frozenset({"developer"}),
        permissions=frozenset(
            {
                "read:*",
                "write:runs",
                "write:agents",
                "execute:*",
            }
        ),
        email="trial@customer.com",
        display_name="Trial User",
    ),
}


# =============================================================================
# MACHINE PRINCIPALS
# =============================================================================
# Machines authenticate via API key or system identity, not Clerk

MACHINE_PRINCIPALS: Dict[str, ActorContext] = {
    # CI Pipeline - system actor
    "ci_pipeline": ActorContext(
        actor_id="system:ci:pipeline-001",
        actor_type=ActorType.SYSTEM,
        source=IdentitySource.SYSTEM,
        tenant_id=None,
        account_id=None,
        team_id=None,
        roles=frozenset({"ci", "automation"}),
        permissions=frozenset({"read:*", "write:metrics", "write:traces"}),
        email=None,
        display_name="CI Pipeline",
    ),
    # Background Worker - system actor
    "worker": ActorContext(
        actor_id="system:worker:worker-001",
        actor_type=ActorType.SYSTEM,
        source=IdentitySource.SYSTEM,
        tenant_id=None,
        account_id=None,
        team_id=None,
        roles=frozenset({"machine", "worker"}),
        permissions=frozenset({"read:*", "write:runs", "write:traces"}),
        email=None,
        display_name="Background Worker",
    ),
    # Replay System - read-only + execute:replay
    "replay": ActorContext(
        actor_id="system:replay:replay-001",
        actor_type=ActorType.SYSTEM,
        source=IdentitySource.SYSTEM,
        tenant_id=None,
        account_id=None,
        team_id=None,
        roles=frozenset({"replay", "readonly"}),
        permissions=frozenset({"read:*", "execute:replay"}),
        email=None,
        display_name="Replay System",
    ),
    # Internal Product (AI Console, Xuniverz, M12) - internal actor
    "internal_product": ActorContext(
        actor_id="system:internal:product-001",
        actor_type=ActorType.INTERNAL_PRODUCT,
        source=IdentitySource.INTERNAL,
        tenant_id=None,
        account_id=None,
        team_id=None,
        roles=frozenset({"internal", "product"}),
        permissions=frozenset({"read:*", "write:runs", "write:agents", "execute:*"}),
        email=None,
        display_name="Internal Product",
    ),
    # Webhook Handler - external caller with API key
    "webhook": ActorContext(
        actor_id="machine:webhook:webhook-001",
        actor_type=ActorType.INTERNAL_PRODUCT,
        source=IdentitySource.INTERNAL,
        tenant_id="tenant-webhook-001",
        account_id="account-webhook-001",
        team_id=None,
        roles=frozenset({"machine"}),
        permissions=frozenset(
            {
                "read:*",
                "write:runs",
                "write:traces",
                "write:metrics",
                "execute:*",
            }
        ),
        email=None,
        display_name="Webhook Handler",
    ),
    # System Job (Scheduled) - system actor
    "system_job": ActorContext(
        actor_id="system:job:job-001",
        actor_type=ActorType.SYSTEM,
        source=IdentitySource.SYSTEM,
        tenant_id=None,
        account_id=None,
        team_id=None,
        roles=frozenset({"automation", "infra"}),
        permissions=frozenset({"read:*", "write:ops", "write:metrics"}),
        email=None,
        display_name="System Job",
    ),
    # Infra Automation - ops-level system actor
    "infra_automation": ActorContext(
        actor_id="system:infra:infra-001",
        actor_type=ActorType.SYSTEM,
        source=IdentitySource.SYSTEM,
        tenant_id=None,
        account_id=None,
        team_id=None,
        roles=frozenset({"infra"}),
        permissions=frozenset({"read:*", "write:ops", "write:metrics"}),
        email=None,
        display_name="Infra Automation",
    ),
}


# =============================================================================
# COMBINED PRINCIPAL SETS
# =============================================================================

ALL_PRINCIPALS: Dict[str, ActorContext] = {
    **HUMAN_PRINCIPALS,
    **MACHINE_PRINCIPALS,
}

# Principals by ActorType (for targeted testing)
PRINCIPALS_BY_TYPE: Dict[ActorType, Dict[str, ActorContext]] = {
    ActorType.OPERATOR: {k: v for k, v in ALL_PRINCIPALS.items() if v.actor_type == ActorType.OPERATOR},
    ActorType.EXTERNAL_PAID: {k: v for k, v in ALL_PRINCIPALS.items() if v.actor_type == ActorType.EXTERNAL_PAID},
    ActorType.EXTERNAL_TRIAL: {k: v for k, v in ALL_PRINCIPALS.items() if v.actor_type == ActorType.EXTERNAL_TRIAL},
    ActorType.INTERNAL_PRODUCT: {k: v for k, v in ALL_PRINCIPALS.items() if v.actor_type == ActorType.INTERNAL_PRODUCT},
    ActorType.SYSTEM: {k: v for k, v in ALL_PRINCIPALS.items() if v.actor_type == ActorType.SYSTEM},
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_principal(principal_id: str) -> ActorContext:
    """
    Get a principal by ID.

    Args:
        principal_id: One of the keys in ALL_PRINCIPALS

    Returns:
        ActorContext

    Raises:
        KeyError if principal not found
    """
    if principal_id not in ALL_PRINCIPALS:
        raise KeyError(f"Unknown principal: {principal_id}. Valid: {list(ALL_PRINCIPALS.keys())}")
    return ALL_PRINCIPALS[principal_id]


def get_principals_by_type(actor_type: ActorType) -> Dict[str, ActorContext]:
    """
    Get all principals of a specific ActorType.

    Args:
        actor_type: The ActorType to filter by

    Returns:
        Dict of principal_id → ActorContext
    """
    return PRINCIPALS_BY_TYPE.get(actor_type, {})


def list_principal_ids() -> list[str]:
    """Get all available principal IDs."""
    return list(ALL_PRINCIPALS.keys())


def get_human_principal_ids() -> list[str]:
    """Get all human principal IDs."""
    return list(HUMAN_PRINCIPALS.keys())


def get_machine_principal_ids() -> list[str]:
    """Get all machine principal IDs."""
    return list(MACHINE_PRINCIPALS.keys())


# =============================================================================
# PRINCIPAL STATISTICS
# =============================================================================

PRINCIPAL_STATS = {
    "total": len(ALL_PRINCIPALS),
    "human": len(HUMAN_PRINCIPALS),
    "machine": len(MACHINE_PRINCIPALS),
    "by_type": {t.value: len(p) for t, p in PRINCIPALS_BY_TYPE.items()},
}


# =============================================================================
# SELF-TEST
# =============================================================================


def _test_all_principals_valid():
    """Verify all principals have required fields."""
    for pid, actor in ALL_PRINCIPALS.items():
        assert actor.actor_id, f"{pid}: missing actor_id"
        assert actor.actor_type, f"{pid}: missing actor_type"
        assert actor.source, f"{pid}: missing source"
        assert actor.roles, f"{pid}: missing roles"
        assert actor.permissions is not None, f"{pid}: permissions is None"


def _test_type_coverage():
    """Verify we have at least one principal per ActorType."""
    for actor_type in ActorType:
        assert PRINCIPALS_BY_TYPE.get(actor_type), f"No principals for {actor_type.value}"


if __name__ == "__main__":
    _test_all_principals_valid()
    _test_type_coverage()
    print("All principal tests passed!")
    print(f"Stats: {PRINCIPAL_STATS}")
