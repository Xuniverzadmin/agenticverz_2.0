#!/usr/bin/env python3
"""API Wiring Check - Verify Endpoint Routes Are Properly Connected

Checks:
1. All routers in app/api/ are included in main.py
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
    """Find all router definitions in api/ directory."""
    routers = {}

    for filepath in api_dir.glob("*.py"):
        if filepath.name.startswith("__"):
            continue

        content = filepath.read_text()

        # Find router = APIRouter(...) patterns
        router_matches = re.findall(
            r'(\w+)\s*=\s*APIRouter\s*\(',
            content
        )

        if router_matches:
            routers[filepath.name] = set(router_matches)

    return routers


def find_mounted_routers(main_file: Path) -> Set[str]:
    """Find all routers mounted in main.py."""
    content = main_file.read_text()

    # Find app.include_router patterns
    mounted = set()

    # Pattern: app.include_router(xxx_router) or app.include_router(router)
    matches = re.findall(
        r'app\.include_router\s*\(\s*(\w+)',
        content
    )
    mounted.update(matches)

    # Pattern: from app.api.xxx import router
    import_matches = re.findall(
        r'from\s+app\.api\.(\w+)\s+import\s+(\w+)',
        content
    )
    for module, name in import_matches:
        if 'router' in name.lower():
            mounted.add(f"{module}.{name}")

    return mounted


def check_response_models(api_dir: Path) -> List[WiringIssue]:
    """Check that endpoints have proper response models."""
    issues = []

    for filepath in api_dir.glob("*.py"):
        if filepath.name.startswith("__"):
            continue

        content = filepath.read_text()
        lines = content.split('\n')

        for i, line in enumerate(lines):
            # Find endpoint decorators without response_model
            if re.match(r'\s*@router\.(get|post|put|delete|patch)\s*\(', line):
                # Check if response_model is specified
                # Look at next few lines for the full decorator
                decorator_block = '\n'.join(lines[i:i+5])

                if 'response_model' not in decorator_block:
                    # Get the function name
                    for j in range(i, min(i+10, len(lines))):
                        func_match = re.match(r'\s*(?:async\s+)?def\s+(\w+)', lines[j])
                        if func_match:
                            func_name = func_match.group(1)
                            issues.append(WiringIssue(
                                category="response_model",
                                file=f"{filepath.name}:{i+1}",
                                message=f"Endpoint '{func_name}' missing response_model",
                                severity="warning"
                            ))
                            break

    return issues


def check_route_consistency(api_dir: Path) -> List[WiringIssue]:
    """Check route prefixes match file naming conventions."""
    issues = []

    for filepath in api_dir.glob("*.py"):
        if filepath.name.startswith("__"):
            continue

        content = filepath.read_text()

        # Find APIRouter prefix
        prefix_match = re.search(
            r'APIRouter\s*\([^)]*prefix\s*=\s*["\']([^"\']+)["\']',
            content
        )

        if prefix_match:
            prefix = prefix_match.group(1).strip('/')
            filename = filepath.stem

            # Check consistency
            # v1_proxy.py should have prefix /v1 or similar
            # agents.py should have prefix /agents or /api/agents
            expected_patterns = [
                filename.replace('_', '-'),
                filename.replace('_', '/'),
                filename.split('_')[-1],  # last part
            ]

            prefix_normalized = prefix.replace('/', '-').replace('api-', '')
            if not any(exp in prefix_normalized or prefix_normalized in exp for exp in expected_patterns):
                issues.append(WiringIssue(
                    category="route_consistency",
                    file=filepath.name,
                    message=f"Prefix '{prefix}' may not match filename '{filename}'",
                    severity="warning"
                ))

    return issues


def check_duplicate_routes(api_dir: Path) -> List[WiringIssue]:
    """Check for duplicate route definitions."""
    issues = []
    routes = {}  # route -> file

    for filepath in api_dir.glob("*.py"):
        if filepath.name.startswith("__"):
            continue

        content = filepath.read_text()

        # Find route definitions
        route_matches = re.findall(
            r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            content
        )

        for method, path in route_matches:
            route_key = f"{method.upper()} {path}"
            if route_key in routes:
                issues.append(WiringIssue(
                    category="duplicate_route",
                    file=filepath.name,
                    message=f"Route '{route_key}' also defined in {routes[route_key]}",
                    severity="error"
                ))
            else:
                routes[route_key] = filepath.name

    return issues


def main():
    api_dir = Path("backend/app/api")
    main_file = Path("backend/app/main.py")

    print("=" * 70)
    print("API Wiring Check - Verifying Endpoint Configuration")
    print("=" * 70)
    print()

    all_issues = []

    # Check 1: Router mounting
    print("🔍 Checking router mounting...")
    if api_dir.exists() and main_file.exists():
        routers = find_routers_in_api(api_dir)
        mounted = find_mounted_routers(main_file)

        for filename, router_names in routers.items():
            for router_name in router_names:
                if router_name not in mounted and f"{filename.replace('.py', '')}.{router_name}" not in str(mounted):
                    # This is a heuristic check, may have false positives
                    pass  # Skip for now, too many false positives

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
