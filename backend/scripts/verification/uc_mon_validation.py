#!/usr/bin/env python3
"""
UC-MON local-first validation aggregator.

Default mode is advisory (exit 0 even with WARN findings).
Use --strict to make WARN findings fail with non-zero exit code.

Aggregates checks from:
1. Plan/methods/route-map doc existence
2. Event schema contract base + CI anchor
3. Scaffold verifier scripts existence
4. Migration existence (128-132)
5. as_of deterministic read surface
6. Sub-verifier invocation (route map, event, storage, determinism)
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = REPO_ROOT / "backend"


@dataclass
class CheckResult:
    name: str
    status: str  # PASS | WARN | FAIL
    detail: str


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def exists_check(name: str, path: Path, advisory: bool = False) -> CheckResult:
    if path.exists():
        return CheckResult(name, "PASS", f"{path.name} exists")
    if advisory:
        return CheckResult(name, "WARN", f"{path.name} missing (advisory)")
    return CheckResult(name, "FAIL", f"{path.name} missing")


# =============================================================================
# SECTION 1: DOC CHECKS
# =============================================================================

def check_plan_and_methods_docs() -> list[CheckResult]:
    results: list[CheckResult] = []
    base = BACKEND_ROOT / "app/hoc/docs/architecture/usecases"
    results.append(exists_check("docs.uc_mon_plan", base / "UC_MONITORING_USECASE_PLAN.md"))
    results.append(exists_check("docs.uc_mon_methods", base / "UC_MONITORING_IMPLEMENTATION_METHODS.md"))
    results.append(exists_check("docs.uc_mon_route_map", base / "UC_MONITORING_ROUTE_OPERATION_MAP.md"))
    results.append(exists_check("docs.uc_mon_handover", base / "HANDOVER_UC_MONITORING_TO_CLAUDE.md"))
    return results


# =============================================================================
# SECTION 2: EVENT CONTRACT BASE
# =============================================================================

def check_event_contract_base() -> list[CheckResult]:
    results: list[CheckResult] = []
    contract = BACKEND_ROOT / "app/hoc/cus/hoc_spine/authority/event_schema_contract.py"
    results.append(exists_check("event.base_contract_file", contract))
    if not contract.exists():
        return results

    txt = read_text(contract)
    required_tokens = [
        "REQUIRED_EVENT_FIELDS",
        "EventSchemaViolation",
        "validate_event_payload",
    ]
    for token in required_tokens:
        ok = token in txt
        results.append(CheckResult(
            f"event.base_contract.{token}",
            "PASS" if ok else "FAIL",
            f"{token} {'present' if ok else 'missing'}",
        ))
    return results


def check_event_contract_usage_anchor() -> list[CheckResult]:
    ci = BACKEND_ROOT / "scripts/ci/check_init_hygiene.py"
    if not ci.exists():
        return [CheckResult("ci.check_event_contract_usage", "FAIL", "check_init_hygiene.py missing")]
    txt = read_text(ci)
    ok = "check_event_schema_contract_usage" in txt
    return [CheckResult(
        "ci.check_event_contract_usage",
        "PASS" if ok else "WARN",
        f"check_event_schema_contract_usage {'found' if ok else 'missing (advisory)'}",
    )]


# =============================================================================
# SECTION 3: SCAFFOLD SCRIPTS
# =============================================================================

def check_scaffold_scripts() -> list[CheckResult]:
    results: list[CheckResult] = []
    scripts = [
        BACKEND_ROOT / "scripts/verification/uc_mon_route_operation_map_check.py",
        BACKEND_ROOT / "scripts/verification/uc_mon_event_contract_check.py",
        BACKEND_ROOT / "scripts/verification/uc_mon_storage_contract_check.py",
        BACKEND_ROOT / "scripts/verification/uc_mon_deterministic_read_check.py",
    ]
    for path in scripts:
        results.append(exists_check(f"scripts.{path.name}", path))
    return results


# =============================================================================
# SECTION 4: MIGRATIONS
# =============================================================================

def check_migrations() -> list[CheckResult]:
    results: list[CheckResult] = []
    expected = [
        "128_monitoring_activity_feedback_contracts.py",
        "129_monitoring_incident_resolution_recurrence.py",
        "130_monitoring_controls_binding_fields.py",
        "131_monitoring_analytics_reproducibility_fields.py",
        "132_monitoring_logs_replay_mode_fields.py",
    ]
    base = BACKEND_ROOT / "alembic/versions"
    for name in expected:
        results.append(exists_check(f"migrations.{name}", base / name))
    return results


# =============================================================================
# SECTION 5: AS_OF CONTRACT SURFACE
# =============================================================================

def check_as_of_contract_surface() -> list[CheckResult]:
    results: list[CheckResult] = []
    api_targets = [
        BACKEND_ROOT / "app/hoc/api/cus/activity/activity.py",
        BACKEND_ROOT / "app/hoc/api/cus/incidents/incidents.py",
        BACKEND_ROOT / "app/hoc/api/cus/logs/traces.py",
    ]
    analytics_root = BACKEND_ROOT / "app/hoc/api/cus/analytics"

    pattern = re.compile(r"\bas_of\b")
    for path in api_targets:
        if not path.exists():
            results.append(CheckResult(f"determinism.as_of.{path.name}", "WARN", f"{path.name} missing (advisory)"))
            continue
        txt = read_text(path)
        has = bool(pattern.search(txt))
        results.append(CheckResult(
            f"determinism.as_of.{path.name}",
            "PASS" if has else "WARN",
            f"{'contains' if has else 'missing'} as_of token (advisory — rollout pending)",
        ))

    analytics_files = sorted(analytics_root.glob("*.py")) if analytics_root.exists() else []
    if not analytics_files:
        results.append(CheckResult("determinism.as_of.analytics", "WARN", "no analytics API files found (advisory)"))
        return results
    any_as_of = any(pattern.search(read_text(f)) for f in analytics_files)
    results.append(CheckResult(
        "determinism.as_of.analytics",
        "PASS" if any_as_of else "WARN",
        f"{'at least one analytics file has as_of' if any_as_of else 'no analytics file has as_of (advisory)'}",
    ))
    return results


# =============================================================================
# SECTION 6: DOMAIN AUTHORITY BOUNDARY CHECKS
# =============================================================================

# Operation keys that indicate enforcement/activation — must NOT appear in proposal files
ENFORCEMENT_OP_PATTERNS = [
    "policies.activate",
    "policies.enforce",
    "policies.compile",
    "policies.publish",
    "controls.enforce",
    "controls.activate",
]

# Proposal files must only use these operation prefixes
PROPOSAL_ALLOWED_OPS: dict[str, list[str]] = {
    "policy_proposals.py": ["policies.proposals_query", "policies.approval"],
}

# L2 write paths must stay within their canonical domain
CANONICAL_WRITE_ISOLATION: list[tuple[str, str, list[str]]] = [
    # (domain_label, L2 file relative path, allowed L4 operation prefixes)
    ("policies", "app/hoc/api/cus/policies/policies.py", ["policies."]),
    ("controls", "app/hoc/api/cus/controls/controls.py", ["controls."]),
    ("incidents", "app/hoc/api/cus/incidents/incidents.py", ["incidents."]),
]


def check_authority_boundaries() -> list[CheckResult]:
    """Check domain authority isolation: proposals cannot mutate enforcement."""
    results: list[CheckResult] = []
    op_pattern = re.compile(r'registry\.execute\(\s*"([^"]+)"')

    # Check 1: Policy proposals do not call enforcement operations
    proposals_file = BACKEND_ROOT / "app" / "hoc" / "api" / "cus" / "policies" / "policy_proposals.py"
    if proposals_file.exists():
        txt = read_text(proposals_file)
        ops_found = op_pattern.findall(txt)
        enforcement_calls = [op for op in ops_found if any(e in op for e in ENFORCEMENT_OP_PATTERNS)]
        results.append(CheckResult(
            "authority.proposals_no_enforcement",
            "PASS" if not enforcement_calls else "FAIL",
            f"policy_proposals.py: {'no enforcement ops' if not enforcement_calls else f'VIOLATION: {enforcement_calls}'}",
        ))
        # Verify only allowed ops used
        allowed = PROPOSAL_ALLOWED_OPS.get("policy_proposals.py", [])
        if allowed:
            violations = [op for op in ops_found if not any(op.startswith(a) for a in allowed)]
            results.append(CheckResult(
                "authority.proposals_allowed_ops_only",
                "PASS" if not violations else "WARN",
                f"{'only allowed ops' if not violations else f'unexpected ops: {violations}'}",
            ))
    else:
        results.append(CheckResult(
            "authority.proposals_no_enforcement",
            "WARN",
            "policy_proposals.py not found (advisory)",
        ))

    # Check 2: Controls mutations stay in controls domain
    controls_file = BACKEND_ROOT / "app" / "hoc" / "api" / "cus" / "controls" / "controls.py"
    if controls_file.exists():
        txt = read_text(controls_file)
        ops_found = op_pattern.findall(txt)
        non_controls = [op for op in ops_found if not op.startswith("controls.")]
        results.append(CheckResult(
            "authority.controls_canonical_only",
            "PASS" if not non_controls else "WARN",
            f"controls.py: {'all ops in controls domain' if not non_controls else f'cross-domain ops: {non_controls}'}",
        ))

    # Check 3: Incident writes stay in incidents domain
    # Allowlist: logs.pdf is a shared PDF renderer used by export endpoints (legitimate)
    INCIDENTS_CROSS_DOMAIN_ALLOWLIST = {"logs.pdf"}
    incidents_file = BACKEND_ROOT / "app" / "hoc" / "api" / "cus" / "incidents" / "incidents.py"
    if incidents_file.exists():
        txt = read_text(incidents_file)
        ops_found = op_pattern.findall(txt)
        non_incidents = [op for op in ops_found if not op.startswith("incidents.") and op not in INCIDENTS_CROSS_DOMAIN_ALLOWLIST]
        results.append(CheckResult(
            "authority.incidents_canonical_only",
            "PASS" if not non_incidents else "WARN",
            f"incidents.py: {'all ops in incidents domain (logs.pdf allowed for exports)' if not non_incidents else f'cross-domain ops: {non_incidents}'}",
        ))

    # Check 4: No L2 proposal file directly imports L5 enforcement engines
    for proposal_domain, proposal_name in [
        ("policies", "policy_proposals.py"),
        ("controls", "controls.py"),
    ]:
        f = BACKEND_ROOT / "app" / "hoc" / "api" / "cus" / proposal_domain / proposal_name
        if f.exists():
            txt = read_text(f)
            has_l5 = "L5_engines" in txt
            has_l6 = "L6_drivers" in txt
            results.append(CheckResult(
                f"authority.{proposal_domain}_no_direct_l5l6",
                "PASS" if not (has_l5 or has_l6) else "FAIL",
                f"{proposal_name}: {'clean L4-only' if not (has_l5 or has_l6) else 'DIRECT L5/L6 import detected'}",
            ))

    return results


# =============================================================================
# SECTION 7: SUB-VERIFIER INVOCATION
# =============================================================================

def run_sub_verifier(name: str, script_path: Path) -> CheckResult:
    """Run a sub-verifier script and report its exit code."""
    if not script_path.exists():
        return CheckResult(f"sub_verifier.{name}", "WARN", f"{script_path.name} missing (advisory)")
    try:
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(BACKEND_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
            env={"PYTHONPATH": str(BACKEND_ROOT), "PATH": "/usr/bin:/usr/local/bin"},
        )
        ok = proc.returncode == 0
        # Get last meaningful line of output
        lines = [l for l in proc.stdout.strip().splitlines() if l.strip()]
        summary = lines[-1] if lines else f"exit={proc.returncode}"
        return CheckResult(
            f"sub_verifier.{name}",
            "PASS" if ok else "WARN",
            summary,
        )
    except subprocess.TimeoutExpired:
        return CheckResult(f"sub_verifier.{name}", "WARN", "timeout (30s)")
    except Exception as e:
        return CheckResult(f"sub_verifier.{name}", "WARN", f"error: {e}")


def check_sub_verifiers() -> list[CheckResult]:
    results: list[CheckResult] = []
    verifiers = [
        ("route_map", BACKEND_ROOT / "scripts/verification/uc_mon_route_operation_map_check.py"),
        ("event_contract", BACKEND_ROOT / "scripts/verification/uc_mon_event_contract_check.py"),
        ("storage_contract", BACKEND_ROOT / "scripts/verification/uc_mon_storage_contract_check.py"),
        ("deterministic_read", BACKEND_ROOT / "scripts/verification/uc_mon_deterministic_read_check.py"),
    ]
    for name, path in verifiers:
        results.append(run_sub_verifier(name, path))
    return results


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(description="UC-MON local-first validation aggregator.")
    parser.add_argument("--strict", action="store_true", help="Treat WARN as FAIL (for future CI adoption).")
    args = parser.parse_args()

    checks: list[CheckResult] = []
    checks.extend(check_plan_and_methods_docs())
    checks.extend(check_event_contract_base())
    checks.extend(check_event_contract_usage_anchor())
    checks.extend(check_scaffold_scripts())
    checks.extend(check_migrations())
    checks.extend(check_as_of_contract_surface())
    checks.extend(check_authority_boundaries())
    checks.extend(check_sub_verifiers())

    pass_count = sum(1 for c in checks if c.status == "PASS")
    warn_count = sum(1 for c in checks if c.status == "WARN")
    fail_count = sum(1 for c in checks if c.status == "FAIL")

    print("UC-MON Validation Report")
    print("=" * 50)
    for c in checks:
        print(f"[{c.status}] {c.name} :: {c.detail}")
    print("-" * 50)
    print(f"Total: {len(checks)} | PASS: {pass_count} | WARN: {warn_count} | FAIL: {fail_count}")

    if fail_count > 0:
        return 1
    if args.strict and warn_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
