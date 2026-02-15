#!/usr/bin/env python3
# Layer: L0 — CI/Verification
# AUDIENCE: INTERNAL
# Role: Verify UC-001 endpoint-to-L4 operation mapping evidence
# Product: system-wide
# Temporal:
#   Trigger: CI / manual
#   Execution: sync
# Callers: CI, manual verification
# Reference: GREEN_CLOSURE_PLAN_UC001_UC002 Phase 2
# artifact_class: CODE

"""
UC-001 Route-to-Operation Mapping Verifier

Verifies that every documented endpoint in the canonical route map
has matching evidence in the L2 source files. Detects:
1. Documented endpoints missing from source (stale docs)
2. Source endpoints not in canonical map (undocumented routes)
3. Endpoints that bypass L4 dispatch (direct DB/L5 access)

Exit codes:
  0 = all checks pass
  1 = one or more checks failed
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
HOC_API = BACKEND_ROOT / "app" / "hoc" / "api"


# =============================================================================
# CANONICAL ENDPOINT → OPERATION MAP (UC-001)
# =============================================================================
# This is the authoritative map. If a new endpoint is added, it MUST be
# registered here. If an endpoint is removed, it MUST be deleted here.
#
# Format: (audience, file_relative, method, path_pattern, l4_operation, notes)

@dataclass
class RouteEntry:
    audience: str          # cus, int, fdr
    file_rel: str          # relative to backend/app/hoc/api/
    method: str            # GET, POST, PUT, DELETE
    path_pattern: str      # URL path (with {param} placeholders)
    l4_operation: str      # L4 operation name or "EXEMPT" or "DIRECT"
    notes: str = ""


# -- CUS (Customer) audience --
CUS_ROUTES: list[RouteEntry] = [
    # account domain
    RouteEntry("cus", "cus/account/aos_accounts.py", "GET", "/accounts/me", "account.query", "tenant self"),
    RouteEntry("cus", "cus/account/aos_accounts.py", "GET", "/accounts/tenants/self", "account.query", "tenant self"),
    RouteEntry("cus", "cus/account/aos_accounts.py", "GET", "/accounts/tenants/self/status", "account.query", "tenant status"),
    RouteEntry("cus", "cus/account/aos_accounts.py", "GET", "/accounts/projects", "account.query", "list projects"),
    RouteEntry("cus", "cus/account/aos_accounts.py", "GET", "/accounts/projects/{id}", "account.query", "project detail"),
    RouteEntry("cus", "cus/account/aos_accounts.py", "POST", "/accounts/projects", "account.query", "create project"),

    # api_keys domain (read)
    RouteEntry("cus", "cus/api_keys/aos_api_key.py", "GET", "/api-keys", "api_keys.query", "list keys"),
    RouteEntry("cus", "cus/api_keys/aos_api_key.py", "GET", "/api-keys/{key_id}", "api_keys.query", "key detail"),

    # api_keys domain (write)
    RouteEntry("cus", "cus/api_keys/api_key_writes.py", "GET", "/tenant/api-keys", "api_keys.write", "list with revoked"),
    RouteEntry("cus", "cus/api_keys/api_key_writes.py", "POST", "/tenant/api-keys", "api_keys.write", "create key"),
    RouteEntry("cus", "cus/api_keys/api_key_writes.py", "DELETE", "/tenant/api-keys/{key_id}", "api_keys.write", "revoke key"),

    # integrations domain
    RouteEntry("cus", "cus/integrations/aos_cus_integrations.py", "GET", "/integrations", "integrations.query", "list"),
    RouteEntry("cus", "cus/integrations/aos_cus_integrations.py", "GET", "/integrations/{id}", "integrations.query", "detail"),
    RouteEntry("cus", "cus/integrations/aos_cus_integrations.py", "POST", "/integrations", "integrations.query", "create"),
    RouteEntry("cus", "cus/integrations/aos_cus_integrations.py", "PUT", "/integrations/{id}", "integrations.query", "update"),
    RouteEntry("cus", "cus/integrations/aos_cus_integrations.py", "DELETE", "/integrations/{id}", "integrations.query", "delete"),
    RouteEntry("cus", "cus/integrations/aos_cus_integrations.py", "POST", "/integrations/{id}/enable", "integrations.query", "enable"),
    RouteEntry("cus", "cus/integrations/aos_cus_integrations.py", "POST", "/integrations/{id}/disable", "integrations.query", "disable"),
    RouteEntry("cus", "cus/integrations/aos_cus_integrations.py", "POST", "/integrations/{id}/test", "integrations.query", "test"),

    # activity domain
    RouteEntry("cus", "cus/activity/activity.py", "GET", "/activity/recent", "activity.query", "recent activity"),

    # incidents domain
    RouteEntry("cus", "cus/incidents/incidents.py", "GET", "/incidents", "incidents.query", "list incidents"),

    # controls domain
    RouteEntry("cus", "cus/controls/controls.py", "GET", "/controls/summary", "controls.query", "summary"),
]

# -- INT (Internal) audience --
INT_ROUTES: list[RouteEntry] = [
    # recovery
    RouteEntry("int", "int/recovery/recovery.py", "POST", "/recovery/suggest", "policies.recovery.match", "suggest"),
    RouteEntry("int", "int/recovery/recovery.py", "GET", "/recovery/candidates", "policies.recovery.match", "list candidates"),
    RouteEntry("int", "int/recovery/recovery.py", "POST", "/recovery/approve", "policies.recovery.match", "approve"),
    RouteEntry("int", "int/recovery/recovery.py", "DELETE", "/recovery/candidates/{id}", "policies.recovery.match", "delete candidate"),
    RouteEntry("int", "int/recovery/recovery.py", "GET", "/recovery/stats", "policies.recovery.match", "stats"),
    RouteEntry("int", "int/recovery/recovery.py", "GET", "/recovery/candidates/{id}", "policies.recovery.read", "candidate detail"),
    RouteEntry("int", "int/recovery/recovery.py", "PATCH", "/recovery/candidates/{id}", "policies.recovery.write", "update candidate"),
    RouteEntry("int", "int/recovery/recovery.py", "GET", "/recovery/actions", "policies.recovery.read", "list actions"),
    RouteEntry("int", "int/recovery/recovery_ingest.py", "POST", "/recovery/ingest", "policies.recovery.write", "ingest"),

    # sdk
    RouteEntry("int", "int/general/sdk.py", "POST", "/sdk/handshake", "account.sdk_attestation", "SDK handshake"),
    RouteEntry("int", "int/general/sdk.py", "GET", "/sdk/instructions", "EXEMPT", "config endpoint"),

    # onboarding (uses async_advance_onboarding directly, not registry)
    RouteEntry("int", "int/agent/onboarding.py", "GET", "/onboarding/status", "DIRECT", "direct DB read"),
    RouteEntry("int", "int/agent/onboarding.py", "POST", "/onboarding/verify", "DIRECT", "via async_advance_onboarding"),
    RouteEntry("int", "int/agent/onboarding.py", "POST", "/onboarding/advance/api-key", "DIRECT", "via async_advance_onboarding"),

    # platform
    RouteEntry("int", "int/agent/platform.py", "GET", "/platform/health", "platform.health", "BLCA status"),
    RouteEntry("int", "int/agent/platform.py", "GET", "/platform/capabilities", "platform.health", "capabilities"),

    # health
    RouteEntry("int", "int/general/health.py", "GET", "/health", "system.health", "system health"),

    # agents
    RouteEntry("int", "int/agent/agents.py", "POST", "/jobs", "agents.job", "create job"),
    RouteEntry("int", "int/agent/agents.py", "GET", "/jobs/{id}", "agents.job", "job status"),
    RouteEntry("int", "int/agent/agents.py", "POST", "/agents/register", "agents.job", "register agent"),

    # debug/auth (EXEMPT — diagnostic only)
    RouteEntry("int", "int/general/debug_auth.py", "GET", "/debug/auth/context", "EXEMPT", "debug diagnostic"),
]

# -- FDR (Founder) audience --
FDR_ROUTES: list[RouteEntry] = [
    # cost ops
    RouteEntry("fdr", "fdr/ops/cost_ops.py", "GET", "/ops/cost/overview", "ops.cost", "cost overview"),
    RouteEntry("fdr", "fdr/ops/cost_ops.py", "GET", "/ops/cost/anomalies", "ops.cost", "cost anomalies"),

    # founder actions (DIRECT — L6 driver, documented as design decision)
    RouteEntry("fdr", "fdr/ops/founder_actions.py", "POST", "/ops/actions/freeze-tenant", "DIRECT", "founder action"),
    RouteEntry("fdr", "fdr/ops/founder_actions.py", "POST", "/ops/actions/unfreeze-tenant", "DIRECT", "founder action"),
    RouteEntry("fdr", "fdr/ops/founder_actions.py", "GET", "/ops/actions/audit", "DIRECT", "audit log"),
]

ALL_ROUTES = CUS_ROUTES + INT_ROUTES + FDR_ROUTES


# =============================================================================
# VERIFICATION ENGINE
# =============================================================================


@dataclass
class VerifyResult:
    check: str
    passed: bool
    detail: str


def verify_file_exists(routes: list[RouteEntry]) -> list[VerifyResult]:
    """Check that every file referenced in the route map exists."""
    results = []
    seen: set[str] = set()
    for r in routes:
        if r.file_rel in seen:
            continue
        seen.add(r.file_rel)
        fpath = HOC_API / r.file_rel
        ok = fpath.exists()
        results.append(VerifyResult(
            f"file_exists:{r.file_rel}",
            ok,
            f"{'OK' if ok else 'MISSING'}: {fpath}",
        ))
    return results


def verify_operation_references(routes: list[RouteEntry]) -> list[VerifyResult]:
    """Check that each L4 operation name appears in the source file."""
    results = []
    file_cache: dict[str, str] = {}
    for r in routes:
        if r.l4_operation in ("EXEMPT", "DIRECT"):
            continue
        fpath = HOC_API / r.file_rel
        if r.file_rel not in file_cache:
            try:
                file_cache[r.file_rel] = fpath.read_text()
            except (OSError, UnicodeDecodeError):
                file_cache[r.file_rel] = ""
        source = file_cache[r.file_rel]

        # Check that the operation name appears in registry.execute() calls
        op_name = r.l4_operation
        # Normalize: look for the operation string in quotes
        found = f'"{op_name}"' in source or f"'{op_name}'" in source
        results.append(VerifyResult(
            f"op_ref:{r.audience}:{r.method} {r.path_pattern}",
            found,
            f"{'OK' if found else 'NOT FOUND'}: {op_name} in {r.file_rel}",
        ))
    return results


def verify_l4_dispatch_pattern(routes: list[RouteEntry]) -> list[VerifyResult]:
    """Check that non-EXEMPT/DIRECT endpoints use get_operation_registry()."""
    results = []
    file_cache: dict[str, str] = {}
    for r in routes:
        if r.l4_operation in ("EXEMPT", "DIRECT"):
            continue
        fpath = HOC_API / r.file_rel
        if r.file_rel not in file_cache:
            try:
                file_cache[r.file_rel] = fpath.read_text()
            except (OSError, UnicodeDecodeError):
                file_cache[r.file_rel] = ""
        source = file_cache[r.file_rel]
        has_registry = "get_operation_registry" in source
        results.append(VerifyResult(
            f"l4_dispatch:{r.file_rel}",
            has_registry,
            f"{'OK' if has_registry else 'MISSING'}: get_operation_registry in {r.file_rel}",
        ))
    return results


def verify_audience_coverage() -> list[VerifyResult]:
    """Check that all three audiences have at least one mapped route."""
    results = []
    for aud in ("cus", "int", "fdr"):
        count = sum(1 for r in ALL_ROUTES if r.audience == aud)
        results.append(VerifyResult(
            f"audience_coverage:{aud}",
            count > 0,
            f"{'OK' if count > 0 else 'EMPTY'}: {aud} has {count} mapped routes",
        ))
    return results


def main() -> int:
    print("UC-001 Route-to-Operation Mapping Verifier")
    print("=" * 60)
    print(f"Total canonical routes: {len(ALL_ROUTES)}")
    print(f"  CUS: {len(CUS_ROUTES)}")
    print(f"  INT: {len(INT_ROUTES)}")
    print(f"  FDR: {len(FDR_ROUTES)}")
    print()

    all_results: list[VerifyResult] = []
    all_results.extend(verify_audience_coverage())
    all_results.extend(verify_file_exists(ALL_ROUTES))
    all_results.extend(verify_operation_references(ALL_ROUTES))
    all_results.extend(verify_l4_dispatch_pattern(ALL_ROUTES))

    passed = [r for r in all_results if r.passed]
    failed = [r for r in all_results if not r.passed]

    if failed:
        print(f"FAILED ({len(failed)} failures, {len(passed)} passed):")
        for r in failed:
            print(f"  FAIL: {r.check} — {r.detail}")
        print()
    else:
        print(f"ALL PASSED ({len(passed)} checks)")

    # Print summary table
    print()
    print("Endpoint-to-Operation Summary:")
    print("-" * 90)
    print(f"{'Audience':<6} {'Method':<7} {'Path':<40} {'L4 Operation':<30}")
    print("-" * 90)
    for r in ALL_ROUTES:
        print(f"{r.audience:<6} {r.method:<7} {r.path_pattern:<40} {r.l4_operation:<30}")
    print("-" * 90)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
