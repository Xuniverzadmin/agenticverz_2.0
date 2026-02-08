#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: API Wiring Check - Verify Endpoint Routes Are Properly Connected
# artifact_class: CODE
"""HOC API Wiring Check - Verify Endpoint Routes Are Properly Connected

Checks:
1. All L2 routers in app/hoc/api/** are imported by an L2.1 facade
2. All endpoint functions have proper response_model or return type
3. Detects orphaned routers (defined but not mounted)
4. Validates route prefixes match file names

Usage:
    python scripts/ops/check_api_wiring.py

Exit codes:
    0 - All checks passed
    1 - Issues found
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Set, NamedTuple


class WiringIssue(NamedTuple):
    category: str
    file: str
    message: str
    severity: str  # 'error', 'warning'


def find_routers_in_api(api_dir: Path) -> Dict[str, Set[str]]:
    """Find all router definitions in api/ directory (recursive)."""
    routers = {}

    for filepath in api_dir.rglob("*.py"):
        if filepath.name.startswith("__"):
            continue
        if "facades" in filepath.parts:
            continue

        content = filepath.read_text()

        # Find router = APIRouter(...) patterns
        router_matches = re.findall(r"(\w+)\s*=\s*APIRouter\s*\(", content)

        if router_matches:
            routers[str(filepath)] = set(router_matches)

    return routers


def find_mounted_routers(facades_dir: Path) -> Set[str]:
    """
    Find all L2 router modules mounted via L2.1 facades.

    HOC canonical wiring: `backend/app/hoc/app.py` imports facade router lists;
    facades import individual L2 routers via `from app.hoc.api.<...> import router ...`.
    """
    mounted: Set[str] = set()

    if not facades_dir.exists():
        return mounted

    for filepath in facades_dir.rglob("*.py"):
        if filepath.name.startswith("__"):
            continue

        content = filepath.read_text()
        import_matches = re.findall(
            r"from\s+app\.hoc\.api\.(?P<module>[\w\.]+)\s+import\s+router\b",
            content,
        )
        mounted.update(import_matches)

    return mounted


def check_response_models(api_dir: Path) -> List[WiringIssue]:
    """Check that endpoints have proper response models."""
    issues = []

    for filepath in api_dir.rglob("*.py"):
        if filepath.name.startswith("__"):
            continue
        if "facades" in filepath.parts:
            continue

        content = filepath.read_text()
        lines = content.split("\n")

        for i, line in enumerate(lines):
            # Find endpoint decorators without response_model
            if re.match(r"\s*@router\.(get|post|put|delete|patch)\s*\(", line):
                # Check if response_model is specified
                # Look at next few lines for the full decorator
                decorator_block = "\n".join(lines[i : i + 5])

                if "response_model" not in decorator_block:
                    # Get the function name
                    for j in range(i, min(i + 10, len(lines))):
                        func_match = re.match(r"\s*(?:async\s+)?def\s+(\w+)", lines[j])
                        if func_match:
                            func_name = func_match.group(1)
                            issues.append(
                                WiringIssue(
                                    category="response_model",
                                    file=f"{filepath.name}:{i + 1}",
                                    message=f"Endpoint '{func_name}' missing response_model",
                                    severity="warning",
                                )
                            )
                            break

    return issues


def check_route_consistency(api_dir: Path) -> List[WiringIssue]:
    """Check route prefixes match file naming conventions."""
    issues = []

    for filepath in api_dir.rglob("*.py"):
        if filepath.name.startswith("__"):
            continue
        if "facades" in filepath.parts:
            continue

        content = filepath.read_text()

        # Find APIRouter prefix
        prefix_match = re.search(
            r'APIRouter\s*\([^)]*prefix\s*=\s*["\']([^"\']+)["\']', content
        )

        if prefix_match:
            prefix = prefix_match.group(1).strip("/")
            filename = filepath.stem

            # Check consistency
            # v1_proxy.py should have prefix /v1 or similar
            # agents.py should have prefix /agents or /api/agents
            expected_patterns = [
                filename.replace("_", "-"),
                filename.replace("_", "/"),
                filename.split("_")[-1],  # last part
            ]

            prefix_normalized = prefix.replace("/", "-").replace("api-", "")
            if not any(
                exp in prefix_normalized or prefix_normalized in exp
                for exp in expected_patterns
            ):
                issues.append(
                    WiringIssue(
                        category="route_consistency",
                        file=filepath.name,
                        message=f"Prefix '{prefix}' may not match filename '{filename}'",
                        severity="warning",
                    )
                )

    return issues


def get_router_prefix(filepath: Path) -> str:
    """Extract the router prefix from a file."""
    content = filepath.read_text()

    # Find APIRouter prefix
    prefix_match = re.search(
        r'APIRouter\s*\([^)]*prefix\s*=\s*["\']([^"\']+)["\']', content, re.DOTALL
    )

    if prefix_match:
        return prefix_match.group(1).rstrip("/")

    # No prefix means root
    return ""


def check_duplicate_routes(api_dir: Path) -> List[WiringIssue]:
    """Check for duplicate route definitions (considering router prefixes)."""
    issues = []
    routes = {}  # full_path -> file

    for filepath in api_dir.rglob("*.py"):
        if filepath.name.startswith("__"):
            continue
        if "facades" in filepath.parts:
            continue

        content = filepath.read_text()
        prefix = get_router_prefix(filepath)

        # Find route definitions
        route_matches = re.findall(
            r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', content
        )

        for method, path in route_matches:
            # Construct full path with prefix
            if path.startswith("/"):
                full_path = f"{prefix}{path}"
            else:
                full_path = f"{prefix}/{path}"

            # Normalize path (remove double slashes)
            full_path = re.sub(r"/+", "/", full_path)
            if not full_path.startswith("/"):
                full_path = "/" + full_path

            route_key = f"{method.upper()} {full_path}"

            if route_key in routes:
                issues.append(
                    WiringIssue(
                        category="duplicate_route",
                        file=filepath.name,
                        message=f"Route '{route_key}' also defined in {routes[route_key]}",
                        severity="error",
                    )
                )
            else:
                routes[route_key] = filepath.name

    return issues


def main():
    api_dir = Path("backend/app/hoc/api")
    facades_dir = Path("backend/app/hoc/api/facades")
    hoc_entrypoint = Path("backend/app/hoc/app.py")

    print("=" * 70)
    print("HOC API Wiring Check - Verifying Endpoint Configuration")
    print("=" * 70)
    print()

    all_issues = []

    # Check 1: Router mounting via facades
    print("🔍 Checking L2 routers are mounted via facades...")
    if not api_dir.exists():
        all_issues.append(
            WiringIssue(
                category="missing_root",
                file=str(api_dir),
                message="HOC API root missing (expected backend/app/hoc/api)",
                severity="error",
            )
        )
    if not hoc_entrypoint.exists():
        all_issues.append(
            WiringIssue(
                category="missing_entrypoint",
                file=str(hoc_entrypoint),
                message="HOC entrypoint missing (expected backend/app/hoc/app.py)",
                severity="error",
            )
        )
    if api_dir.exists() and facades_dir.exists():
        routers = find_routers_in_api(api_dir)  # path -> {router var names}
        mounted_modules = find_mounted_routers(facades_dir)  # dotted module paths

        for filepath_str, router_names in routers.items():
            path = Path(filepath_str)
            try:
                rel = path.relative_to("backend/app")
            except ValueError:
                continue

            # Only enforce for L2 router modules under hoc/api/{cus,int,fdr}
            if rel.parts[:3] != ("hoc", "api", "cus") and rel.parts[:3] != ("hoc", "api", "int") and rel.parts[:3] != ("hoc", "api", "fdr"):
                continue

            # mounted_modules are captured as "cus.policies.monitors" etc (after app.hoc.api.)
            mounted_key = ".".join(rel.with_suffix("").parts[2:])  # cus....

            if not router_names:
                continue
            if mounted_key not in mounted_modules:
                all_issues.append(
                    WiringIssue(
                        category="orphan_router",
                        file=str(rel),
                        message="Defines APIRouter but is not imported by any facade (not mounted)",
                        severity="error",
                    )
                )

    # Check 2: Response models
    print("🔍 Checking response models...")
    response_issues = check_response_models(api_dir)
    all_issues.extend(response_issues)

    # Check 3: Route consistency
    print("🔍 Checking route consistency...")
    consistency_issues = check_route_consistency(api_dir)
    all_issues.extend(consistency_issues)

    # Check 4: Duplicate routes
    print("🔍 Checking for duplicate routes...")
    duplicate_issues = check_duplicate_routes(api_dir)
    all_issues.extend(duplicate_issues)

    print()

    # Report results
    errors = [i for i in all_issues if i.severity == "error"]
    warnings = [i for i in all_issues if i.severity == "warning"]

    if errors:
        print(f"❌ Found {len(errors)} error(s):")
        for issue in errors:
            print(f"   [{issue.category}] {issue.file}: {issue.message}")
        print()

    if warnings:
        print(f"⚠️  Found {len(warnings)} warning(s):")
        for issue in warnings[:10]:  # Limit to first 10
            print(f"   [{issue.category}] {issue.file}: {issue.message}")
        if len(warnings) > 10:
            print(f"   ... and {len(warnings) - 10} more warnings")
        print()

    if not all_issues:
        print("✅ All API wiring checks passed!")
        sys.exit(0)
    elif errors:
        print(f"Total: {len(errors)} error(s), {len(warnings)} warning(s)")
        sys.exit(1)
    else:
        print(f"Total: {len(warnings)} warning(s) (non-blocking)")
        sys.exit(0)


if __name__ == "__main__":
    main()
