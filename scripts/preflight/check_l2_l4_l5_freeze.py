#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Role: L2-L4-L5 freeze enforcement preflight check (Phase C — PIN-491)
# artifact_class: CODE

"""
L2-L4-L5 Freeze Enforcement (Phase C — PIN-491)

Preflight check that ensures no new L2→L5 direct imports have been introduced.
Runs as part of the 30-minute preflight cron and in run_all_checks.sh.

Checks:
  1. FREEZE-001: No new L2→L5 direct gaps (gap detector --check)
  2. FREEZE-003: No new cross-domain L2 imports

Exit codes:
  0 = All checks pass
  1 = Regression detected
  2 = Infrastructure error (missing baseline, etc.)
"""

import ast
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HOC_ROOT = PROJECT_ROOT / "backend" / "app" / "hoc"
L2_API_ROOT = HOC_ROOT / "api" / "cus"

DOMAINS = [
    "account", "activity", "analytics", "api_keys", "controls",
    "incidents", "integrations", "logs", "overview", "policies",
    "general", "ops", "recovery",
]

# Known cross-domain imports that are acceptable (wired through L4 or pre-existing baseline)
KNOWN_CROSS_DOMAIN = {
    # (l2_domain, l5_domain) pairs
    ("integrations", "activity"),  # cus_telemetry.py → activity.telemetry via L4
    ("incidents", "logs"),         # incidents.py → logs.pdf via L4
    ("recovery", "incidents"),     # recovery.py → incidents L5 (excluded from A-phase)
    # Pre-existing cross-domain (frozen at Phase C baseline — do not add new entries)
    ("policies", "analytics"),     # analytics.py in policies L2 → analytics L5 (inline imports)
    ("policies", "account"),       # aos_accounts.py in policies L2 → account L5 (inline imports)
    ("policies", "logs"),          # guard.py in policies L2 → logs L5 (inline imports)
}


def check_cross_domain_imports() -> list[str]:
    """FREEZE-003: Detect cross-domain L2→L5 imports."""
    violations: list[str] = []

    for domain in DOMAINS:
        api_dir = L2_API_ROOT / domain
        if not api_dir.exists():
            continue

        for filepath in sorted(api_dir.rglob("*.py")):
            if filepath.name == "__init__.py":
                continue
            try:
                source = filepath.read_text()
                tree = ast.parse(source, filename=str(filepath))
            except (SyntaxError, UnicodeDecodeError):
                continue

            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom) or node.module is None:
                    continue
                m = re.match(
                    r"app\.hoc\.cus\.(\w+)\.L5_(?:engines|support|controls)",
                    node.module,
                )
                if m:
                    l5_domain = m.group(1)
                    if l5_domain != domain and (domain, l5_domain) not in KNOWN_CROSS_DOMAIN:
                        rel_path = filepath.relative_to(PROJECT_ROOT)
                        violations.append(
                            f"{rel_path}:{node.lineno} — "
                            f"L2 domain '{domain}' imports L5 from '{l5_domain}'"
                        )

    return violations


def main() -> int:
    failed = False

    # Check 1: FREEZE-001 — Gap detector baseline check
    print("FREEZE-001: L2→L5 gap regression check")
    # Import and run gap detector check inline
    sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "ops"))
    try:
        from l5_spine_pairing_gap_detector import (
            DOMAINS as GAP_DOMAINS,
            _discover_l5_engines,
            check_against_baseline,
            compute_domain_report,
            scan_l2_imports,
            scan_l4_imports,
        )

        all_engines = {}
        for domain in GAP_DOMAINS:
            engines = _discover_l5_engines(domain)
            if engines:
                all_engines[domain] = engines

        l2_refs = scan_l2_imports()
        l4_refs = scan_l4_imports()

        reports = []
        for domain in GAP_DOMAINS:
            engines = all_engines.get(domain, [])
            if not engines:
                continue
            reports.append(compute_domain_report(domain, engines, l2_refs, l4_refs))

        exit_code = check_against_baseline(reports)
        if exit_code != 0:
            failed = True
            if exit_code == 2:
                print("  WARNING: No baseline found — run --freeze-baseline first")
    except ImportError as e:
        print(f"  ERROR: Could not import gap detector: {e}")
        return 2

    # Check 2: FREEZE-003 — Cross-domain imports
    print("")
    print("FREEZE-003: Cross-domain L2→L5 import check")
    violations = check_cross_domain_imports()
    if violations:
        print(f"  FAIL: {len(violations)} cross-domain violations found:")
        for v in violations:
            print(f"    - {v}")
        failed = True
    else:
        print("  PASS: No unauthorized cross-domain imports")

    print("")
    if failed:
        print("L2-L4-L5 FREEZE: FAILED")
        return 1
    else:
        print("L2-L4-L5 FREEZE: PASSED")
        return 0


if __name__ == "__main__":
    sys.exit(main())
