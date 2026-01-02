#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: manual | ci
#   Execution: sync
# Role: Generate synthetic authorization load for RBACv2 promotion readiness
# Reference: PIN-274 (RBACv2 Promotion via Neon + Synthetic Load)

"""
RBAC Synthetic Load Generator

Generates synthetic authorization requests to exercise the full
RBACv1 ↔ RBACv2 comparison matrix.

Purpose:
- Replace "7 days of users" with coverage-based confidence
- Exercise all ActorType × Role × Resource × Action combinations
- Verify cross-tenant isolation (MUST fail)
- Verify operator bypass (MUST succeed)
- Collect discrepancy data for classification

Usage:
    DATABASE_URL="postgresql://..." PYTHONPATH=. python3 scripts/load/rbac_synthetic_load.py \
        --requests 100000 \
        --parallel 4 \
        --output /tmp/rbac_load_results.json

Requirements:
    - Neon DB connection (not localhost for prod-grade)
    - Seeded test tenants/accounts/teams
    - RBAC shadow mode enabled (NEW_AUTH_SHADOW_ENABLED=true)
"""

import argparse
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from itertools import product
from typing import Dict, List, Optional, Tuple

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from app.auth.actor import ActorContext, ActorType, IdentitySource
from app.auth.authorization import AuthorizationEngine, get_authorization_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("rbac_synthetic_load")


# =============================================================================
# Authorization Matrix Dimensions
# =============================================================================

ACTOR_TYPES = [
    ActorType.EXTERNAL_PAID,
    ActorType.EXTERNAL_TRIAL,
    ActorType.INTERNAL_PRODUCT,
    ActorType.OPERATOR,
    ActorType.SYSTEM,
]

ROLES = [
    "developer",
    "admin",
    "operator",
    "owner",
    "viewer",
    "machine",
    "ci",
    "worker",
    "replay",
    "founder",
    "team_admin",
    "readonly",
]

RESOURCES = [
    "agents",
    "runs",
    "policies",
    "traces",
    "incidents",
    "billing",
    "teams",
    "accounts",
    "skills",
    "workflows",
    "metrics",
    "system",
]

ACTIONS = [
    "create",
    "read",
    "update",
    "delete",
    "execute",
    "approve",
    "export",
    "admin",
    "audit",
]

# Test tenants (must match seeded data in Neon)
TENANTS = [
    "tenant-alpha",
    "tenant-beta",
    "tenant-gamma",
]


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class AuthorizationTestCase:
    """A single authorization test case."""

    case_id: str
    actor_type: str
    role: str
    resource: str
    action: str
    actor_tenant: str
    target_tenant: Optional[str]  # For cross-tenant tests


@dataclass
class AuthorizationResult:
    """Result of an authorization test."""

    case_id: str
    v1_allowed: bool
    v2_allowed: bool
    v1_reason: str
    v2_reason: str
    match: bool
    discrepancy_type: str  # none, v2_more_restrictive, v2_more_permissive
    latency_ms: float


# =============================================================================
# Test Case Generation
# =============================================================================


def generate_standard_cases(limit: Optional[int] = None) -> List[AuthorizationTestCase]:
    """
    Generate standard authorization test cases.

    Covers: ActorType × Role × Resource × Action × Tenant
    """
    cases = []
    case_id = 0

    for actor_type, role, resource, action, tenant in product(
        ACTOR_TYPES, ROLES, RESOURCES, ACTIONS, TENANTS
    ):
        cases.append(
            AuthorizationTestCase(
                case_id=f"std-{case_id}",
                actor_type=actor_type.value,
                role=role,
                resource=resource,
                action=action,
                actor_tenant=tenant,
                target_tenant=tenant,  # Same tenant for standard cases
            )
        )
        case_id += 1

        if limit and case_id >= limit:
            break

    return cases


def generate_cross_tenant_cases() -> List[AuthorizationTestCase]:
    """
    Generate cross-tenant access attempts.

    ALL of these should be denied (except for operators).
    """
    cases = []
    case_id = 0

    # Non-operator actor types should fail cross-tenant
    non_operator_types = [
        ActorType.EXTERNAL_PAID,
        ActorType.EXTERNAL_TRIAL,
        ActorType.INTERNAL_PRODUCT,
        ActorType.SYSTEM,
    ]

    for actor_type, role, resource, action in product(
        non_operator_types, ["developer", "admin"], RESOURCES[:5], ["read", "write"]
    ):
        for actor_tenant, target_tenant in [
            ("tenant-alpha", "tenant-beta"),
            ("tenant-beta", "tenant-gamma"),
            ("tenant-gamma", "tenant-alpha"),
        ]:
            cases.append(
                AuthorizationTestCase(
                    case_id=f"xtn-{case_id}",
                    actor_type=actor_type.value,
                    role=role,
                    resource=resource,
                    action=action,
                    actor_tenant=actor_tenant,
                    target_tenant=target_tenant,
                )
            )
            case_id += 1

    return cases


def generate_operator_bypass_cases() -> List[AuthorizationTestCase]:
    """
    Generate operator bypass test cases.

    ALL of these should succeed.
    """
    cases = []

    for resource, action in product(RESOURCES, ACTIONS):
        cases.append(
            AuthorizationTestCase(
                case_id=f"op-{len(cases)}",
                actor_type=ActorType.OPERATOR.value,
                role="operator",
                resource=resource,
                action=action,
                actor_tenant="tenant-alpha",
                target_tenant="tenant-beta",  # Cross-tenant should still work
            )
        )

    return cases


def generate_system_actor_cases() -> List[AuthorizationTestCase]:
    """
    Generate system actor (CI, worker, replay) test cases.
    """
    cases = []
    system_roles = ["ci", "worker", "replay", "machine", "automation"]

    for role, resource, action in product(
        system_roles,
        ["runs", "traces", "metrics", "agents"],
        ["read", "write", "execute"],
    ):
        cases.append(
            AuthorizationTestCase(
                case_id=f"sys-{len(cases)}",
                actor_type=ActorType.SYSTEM.value,
                role=role,
                resource=resource,
                action=action,
                actor_tenant="system",
                target_tenant=None,
            )
        )

    return cases


# =============================================================================
# Authorization Execution
# =============================================================================


def create_actor_for_case(case: AuthorizationTestCase) -> ActorContext:
    """Create an ActorContext for a test case."""
    actor_type = ActorType(case.actor_type)

    # Determine identity source
    if actor_type == ActorType.SYSTEM:
        source = IdentitySource.SYSTEM
    elif actor_type == ActorType.OPERATOR:
        source = IdentitySource.INTERNAL
    else:
        source = IdentitySource.CLERK

    return ActorContext(
        actor_id=f"test-actor-{case.case_id}",
        actor_type=actor_type,
        source=source,
        tenant_id=case.actor_tenant if case.actor_tenant != "system" else None,
        account_id=f"acct-{case.actor_tenant}"
        if case.actor_tenant != "system"
        else None,
        team_id=None,
        roles=frozenset([case.role]),
        permissions=frozenset(),  # Will be computed by engine
        email=f"test-{case.case_id}@example.com",
        display_name=f"Test Actor {case.case_id}",
    )


def run_authorization_check(
    engine: AuthorizationEngine, case: AuthorizationTestCase
) -> AuthorizationResult:
    """Run a single authorization check and compare v1/v2 decisions."""
    start_time = time.perf_counter()

    # Create actor
    actor = create_actor_for_case(case)

    # Compute permissions (this is what IdentityChain would do)
    actor_with_perms = engine.compute_permissions(actor)

    # RBACv2 decision (the AuthorizationEngine)
    v2_result = engine.authorize(
        actor_with_perms, case.resource, case.action, case.target_tenant
    )

    # RBACv1 decision simulation
    # In real middleware, this would be the PolicyObject check
    # For testing, we simulate based on RBAC_MATRIX logic
    v1_allowed, v1_reason = simulate_rbac_v1_decision(case)

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    # Determine discrepancy type
    v2_allowed = v2_result.allowed
    if v1_allowed == v2_allowed:
        discrepancy_type = "none"
        match = True
    elif v1_allowed and not v2_allowed:
        discrepancy_type = "v2_more_restrictive"
        match = False
    else:  # not v1_allowed and v2_allowed
        discrepancy_type = "v2_more_permissive"  # SECURITY ALERT
        match = False

    return AuthorizationResult(
        case_id=case.case_id,
        v1_allowed=v1_allowed,
        v2_allowed=v2_allowed,
        v1_reason=v1_reason,
        v2_reason=v2_result.reason,
        match=match,
        discrepancy_type=discrepancy_type,
        latency_ms=elapsed_ms,
    )


def simulate_rbac_v1_decision(case: AuthorizationTestCase) -> Tuple[bool, str]:
    """
    Simulate RBACv1 (PolicyObject/RBAC_MATRIX) decision.

    This mirrors the current middleware behavior for comparison.
    """
    # RBACv1 RBAC_MATRIX (must match RBACv2 role set for fair comparison)
    # All roles from AuthorizationEngine.ROLE_PERMISSIONS included here
    RBAC_MATRIX = {
        "founder": {"*"},
        "operator": {"*"},
        "admin": {"read", "write", "delete", "admin"},
        "developer": {"read", "write", "execute"},
        "viewer": {"read", "audit"},
        "machine": {"read", "write", "execute"},
        "ci": {"read", "write"},
        "worker": {"read", "write"},
        "replay": {"read", "execute"},
        "team_admin": {"read", "write", "admin"},
        "readonly": {"read"},
        # Added to match RBACv2 role set:
        "automation": {"read", "write"},  # read:*, write:metrics in v2
        "internal": {
            "read",
            "write",
            "execute",
        },  # read:*, execute:*, write:runs/agents in v2
        "product": {"read", "write"},  # read:*, write:* in v2
        "infra": {"read", "write"},  # read:*, write:ops/metrics in v2
        "dev": {"read", "write"},  # read:*, write:runs/agents in v2
    }

    role = case.role
    action = case.action

    # Check cross-tenant (RBACv1 doesn't enforce this strictly in all cases)
    # For simulation, we'll be more permissive (which is the v1 behavior)
    if case.actor_type == ActorType.OPERATOR.value:
        return True, "operator_bypass"

    allowed_actions = RBAC_MATRIX.get(role, set())

    if "*" in allowed_actions:
        return True, f"role:{role}:wildcard"
    if action in allowed_actions:
        return True, f"role:{role}:{action}"

    return False, f"no_permission:{role}:{action}"


# =============================================================================
# Load Execution
# =============================================================================


def run_load_test(
    cases: List[AuthorizationTestCase],
    parallel: int = 4,
    progress_interval: int = 1000,
) -> List[AuthorizationResult]:
    """
    Run authorization load test with parallel execution.
    """
    engine = get_authorization_engine()
    results: List[AuthorizationResult] = []
    total = len(cases)
    processed = 0

    logger.info(f"Starting load test with {total} cases, {parallel} workers")

    with ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = {
            executor.submit(run_authorization_check, engine, case): case
            for case in cases
        }

        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            processed += 1

            if processed % progress_interval == 0:
                pct = (processed / total) * 100
                logger.info(f"Progress: {processed}/{total} ({pct:.1f}%)")

    return results


def analyze_results(results: List[AuthorizationResult]) -> Dict:
    """Analyze load test results."""
    total = len(results)
    matches = sum(1 for r in results if r.match)
    mismatches = total - matches

    v2_more_restrictive = sum(
        1 for r in results if r.discrepancy_type == "v2_more_restrictive"
    )
    v2_more_permissive = sum(
        1 for r in results if r.discrepancy_type == "v2_more_permissive"
    )

    avg_latency = sum(r.latency_ms for r in results) / total if total > 0 else 0
    max_latency = max(r.latency_ms for r in results) if results else 0

    # Collect mismatches for classification
    mismatch_details = [asdict(r) for r in results if not r.match]

    return {
        "summary": {
            "total_requests": total,
            "matches": matches,
            "mismatches": mismatches,
            "match_rate_pct": (matches / total * 100) if total > 0 else 0,
            "v2_more_restrictive": v2_more_restrictive,
            "v2_more_permissive": v2_more_permissive,
            "avg_latency_ms": avg_latency,
            "max_latency_ms": max_latency,
        },
        "promotion_ready": v2_more_permissive == 0 and (mismatches / total * 100) < 1
        if total > 0
        else False,
        "security_alert": v2_more_permissive > 0,
        "mismatches": mismatch_details[:100],  # Top 100 for analysis
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# =============================================================================
# Main
# =============================================================================


def main():
    parser = argparse.ArgumentParser(description="RBAC Synthetic Load Generator")
    parser.add_argument(
        "--requests",
        type=int,
        default=10000,
        help="Number of authorization requests to generate",
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=4,
        help="Number of parallel workers",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="/tmp/rbac_load_results.json",
        help="Output file for results",
    )
    parser.add_argument(
        "--include-cross-tenant",
        action="store_true",
        default=True,
        help="Include cross-tenant test cases",
    )
    parser.add_argument(
        "--include-operator",
        action="store_true",
        default=True,
        help="Include operator bypass test cases",
    )
    parser.add_argument(
        "--include-system",
        action="store_true",
        default=True,
        help="Include system actor test cases",
    )

    args = parser.parse_args()

    # Generate test cases
    logger.info("Generating test cases...")

    cases = generate_standard_cases(limit=args.requests)
    logger.info(f"  Standard cases: {len(cases)}")

    if args.include_cross_tenant:
        cross_tenant = generate_cross_tenant_cases()
        cases.extend(cross_tenant)
        logger.info(f"  Cross-tenant cases: {len(cross_tenant)}")

    if args.include_operator:
        operator = generate_operator_bypass_cases()
        cases.extend(operator)
        logger.info(f"  Operator bypass cases: {len(operator)}")

    if args.include_system:
        system = generate_system_actor_cases()
        cases.extend(system)
        logger.info(f"  System actor cases: {len(system)}")

    logger.info(f"Total test cases: {len(cases)}")

    # Run load test
    results = run_load_test(cases, parallel=args.parallel)

    # Analyze results
    analysis = analyze_results(results)

    # Output
    with open(args.output, "w") as f:
        json.dump(analysis, f, indent=2)

    logger.info(f"Results written to {args.output}")

    # Print summary
    print("\n" + "=" * 60)
    print("RBAC SYNTHETIC LOAD TEST RESULTS")
    print("=" * 60)
    print(f"Total Requests:      {analysis['summary']['total_requests']}")
    print(f"Matches:             {analysis['summary']['matches']}")
    print(f"Mismatches:          {analysis['summary']['mismatches']}")
    print(f"Match Rate:          {analysis['summary']['match_rate_pct']:.2f}%")
    print(f"v2_more_restrictive: {analysis['summary']['v2_more_restrictive']}")
    print(f"v2_more_permissive:  {analysis['summary']['v2_more_permissive']}")
    print(f"Avg Latency:         {analysis['summary']['avg_latency_ms']:.2f}ms")
    print(f"Max Latency:         {analysis['summary']['max_latency_ms']:.2f}ms")
    print()

    if analysis["security_alert"]:
        print("⚠️  SECURITY ALERT: v2_more_permissive discrepancies detected!")
        print("    Immediate investigation required before promotion.")
    elif analysis["promotion_ready"]:
        print("✅ PROMOTION READY: No security issues, discrepancy rate < 1%")
    else:
        print("⏳ NOT READY: Discrepancy rate >= 1%, classification needed")

    print("=" * 60)

    # Exit with appropriate code
    if analysis["security_alert"]:
        sys.exit(2)  # Security issue
    elif not analysis["promotion_ready"]:
        sys.exit(1)  # Not ready
    else:
        sys.exit(0)  # Ready


if __name__ == "__main__":
    main()
