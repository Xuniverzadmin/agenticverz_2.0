#!/usr/bin/env python3
"""
UC-001 / UC-002 validation script.

Validates the current code/doc invariants for:
- UC-001 (LLM Run Monitoring) expected status GREEN
- UC-002 (Customer Onboarding) expected status GREEN
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_status_docs() -> list[CheckResult]:
    results: list[CheckResult] = []
    idx = REPO_ROOT / "backend/app/hoc/docs/architecture/usecases/INDEX.md"
    linkage = REPO_ROOT / "backend/app/hoc/docs/architecture/usecases/HOC_USECASE_CODE_LINKAGE.md"
    idx_text = read_text(idx)
    link_text = read_text(linkage)

    uc001_idx = "UC-001 | LLM Run Monitoring" in idx_text and "| `GREEN` |" in idx_text
    uc002_idx = "UC-002 | Customer Onboarding" in idx_text and "| `GREEN` |" in idx_text
    uc001_link = "## UC-001: LLM Run Monitoring" in link_text and "Status: `GREEN`" in link_text
    uc002_link = "## UC-002: Customer Onboarding" in link_text and "Status: `GREEN`" in link_text

    results.append(CheckResult("docs.uc001.index_status", uc001_idx, f"{idx} UC-001 GREEN"))
    results.append(CheckResult("docs.uc002.index_status", uc002_idx, f"{idx} UC-002 GREEN"))
    results.append(CheckResult("docs.uc001.linkage_status", uc001_link, f"{linkage} UC-001 GREEN"))
    results.append(CheckResult("docs.uc002.linkage_status", uc002_link, f"{linkage} UC-002 GREEN"))
    return results


def check_tombstones_removed() -> list[CheckResult]:
    results: list[CheckResult] = []
    old_files = [
        REPO_ROOT / "backend/app/hoc/api/cus/policies/aos_accounts.py",
        REPO_ROOT / "backend/app/hoc/api/cus/policies/aos_cus_integrations.py",
        REPO_ROOT / "backend/app/hoc/api/cus/policies/aos_api_key.py",
    ]
    for path in old_files:
        results.append(CheckResult(f"code.no_tombstone.{path.name}", not path.exists(), f"{path} removed"))

    app_root = REPO_ROOT / "backend/app"
    pattern = re.compile(r"from app\.hoc\.api\.cus\.policies\.(aos_accounts|aos_cus_integrations|aos_api_key)")
    offenders: list[str] = []
    for py in app_root.rglob("*.py"):
        txt = read_text(py)
        if pattern.search(txt):
            offenders.append(str(py.relative_to(REPO_ROOT)))
    results.append(
        CheckResult(
            "code.no_old_imports",
            len(offenders) == 0,
            "old policy-path imports absent" if not offenders else f"offenders={offenders}",
        )
    )
    return results


def check_integrations_write_session() -> list[CheckResult]:
    results: list[CheckResult] = []
    path = REPO_ROOT / "backend/app/hoc/api/cus/integrations/aos_cus_integrations.py"
    txt = read_text(path)
    required_pairs = [
        ("create_integration", "sync_session"),
        ("update_integration", "sync_session"),
        ("delete_integration", "sync_session"),
        ("enable_integration", "sync_session"),
        ("disable_integration", "sync_session"),
        ("test_integration_credentials", "sync_session"),
    ]
    has_dep = "get_sync_session_dep" in txt and "Depends(get_sync_session_dep)" in txt
    results.append(CheckResult("code.integrations.sync_dep", has_dep, f"{path} uses get_sync_session_dep"))

    for fn, token in required_pairs:
        # Simple function-local heuristic
        ok = bool(re.search(rf"async def {fn}\(.*?params=\{{.*?\"{token}\": session", txt, re.S))
        results.append(CheckResult(f"code.integrations.{fn}.sync_session", ok, f"{fn} passes {token}"))
    return results


def check_onboarding_authority_boundary() -> list[CheckResult]:
    results: list[CheckResult] = []
    path = REPO_ROOT / "backend/app/hoc/cus/hoc_spine/orchestrator/handlers/onboarding_handler.py"
    txt = read_text(path)

    has_queries = all(
        q in txt
        for q in [
            "FROM api_keys",
            "FROM cus_integrations",
            "FROM sdk_attestations",
            "activation_predicate_evaluated",
        ]
    )
    # Match CI check 35 behavior: scan activation section non-comment lines only.
    no_cache_import = True
    in_activation = False
    forbidden = ["connector_registry_driver", "connector_registry", "get_connector_registry", "ConnectorRegistry"]
    for line in txt.splitlines():
        stripped = line.strip()
        if "ACTIVATION PREDICATE HELPERS" in stripped:
            in_activation = True
            continue
        if not in_activation or stripped.startswith("#"):
            continue
        if any(tok in stripped for tok in forbidden):
            no_cache_import = False
            break
    results.append(CheckResult("code.onboarding.db_evidence_queries", has_queries, "api_keys/cus_integrations/sdk_attestations checks"))
    results.append(CheckResult("code.onboarding.no_cache_import", no_cache_import, "no connector cache import in activation path"))
    return results


def check_ci_guardrail_and_migration() -> list[CheckResult]:
    results: list[CheckResult] = []
    ci = REPO_ROOT / "backend/scripts/ci/check_init_hygiene.py"
    ci_txt = read_text(ci)
    has_check35 = "check_activation_no_cache_import" in ci_txt and "ACTIVATION_CACHE_BOUNDARY" in ci_txt
    results.append(CheckResult("ci.check35.activation_cache_boundary", has_check35, f"{ci} has check 35"))

    mig = REPO_ROOT / "backend/alembic/versions/127_create_sdk_attestations.py"
    mig_ok = mig.exists() and "sdk_attestations" in read_text(mig)
    results.append(CheckResult("db.migration.sdk_attestations", mig_ok, f"{mig} exists"))
    return results


def run_cmd(name: str, cmd: list[str], cwd: Path) -> CheckResult:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    ok = proc.returncode == 0
    detail = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else (proc.stderr.strip() or f"exit={proc.returncode}")
    return CheckResult(name, ok, detail)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate UC-001/UC-002 technical/codebase invariants.")
    parser.add_argument("--run-ci", action="store_true", help="Also run check_init_hygiene.py --ci")
    parser.add_argument("--run-tests", action="store_true", help="Also run activation predicate authority tests")
    args = parser.parse_args()

    checks: list[CheckResult] = []
    checks.extend(check_status_docs())
    checks.extend(check_tombstones_removed())
    checks.extend(check_integrations_write_session())
    checks.extend(check_onboarding_authority_boundary())
    checks.extend(check_ci_guardrail_and_migration())

    if args.run_ci:
        checks.append(
            run_cmd(
                "ci.check_init_hygiene",
                ["python3", "scripts/ci/check_init_hygiene.py", "--ci"],
                REPO_ROOT / "backend",
            )
        )
    if args.run_tests:
        checks.append(
            run_cmd(
                "tests.activation_predicate_authority",
                ["pytest", "-q", "tests/governance/t4/test_activation_predicate_authority.py"],
                REPO_ROOT / "backend",
            )
        )

    passed = sum(1 for c in checks if c.ok)
    failed = len(checks) - passed
    print("UC-001/UC-002 Validation Report")
    print("=" * 40)
    for c in checks:
        mark = "PASS" if c.ok else "FAIL"
        print(f"[{mark}] {c.name} :: {c.detail}")
    print("-" * 40)
    print(f"Total: {len(checks)} | Passed: {passed} | Failed: {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
