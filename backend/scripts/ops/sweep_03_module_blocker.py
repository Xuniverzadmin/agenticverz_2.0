#!/usr/bin/env python3
# Layer: L8 — Ops Script
# AUDIENCE: INTERNAL
# Role: Sweep-03 tracking - count blocking app.services imports in HOC
# Reference: PIN-470, Sweep-03 Legacy Module Migration

"""
Sweep-03 Module Blocker Tracker

Counts blocking `app.services.*` imports in HOC files.
Excludes model imports (L6 drivers may import models).

Usage:
    python scripts/ops/sweep_03_module_blocker.py --count
    python scripts/ops/sweep_03_module_blocker.py --domains
    python scripts/ops/sweep_03_module_blocker.py --domain policies --verbose
    python scripts/ops/sweep_03_module_blocker.py --priority
"""

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

# HOC root
HOC_ROOT = Path(__file__).parent.parent.parent / "app" / "hoc" / "cus"

# Excluded patterns - these are ALLOWED imports
EXCLUDED_PATTERNS = [
    r"app\.services\.\w+\.models",       # app.services.*.models
    r"app\.services\.audit\.models",     # explicit audit models
    r"app\.models\.",                    # app/models/*
]

# Excluded file patterns - not code files
EXCLUDED_FILE_PATTERNS = [
    r"\.md$",          # markdown
    r"\.deprecated$",  # deprecated files
    r"__pycache__",    # cache
]


def is_excluded_import(import_line: str) -> bool:
    """Check if import is excluded (models allowed)."""
    for pattern in EXCLUDED_PATTERNS:
        if re.search(pattern, import_line):
            return True
    return False


def is_excluded_file(file_path: Path) -> bool:
    """Check if file should be excluded from scan."""
    path_str = str(file_path)
    for pattern in EXCLUDED_FILE_PATTERNS:
        if re.search(pattern, path_str):
            return True
    return False


def find_blocking_imports(verbose: bool = False) -> dict:
    """Find all blocking app.services imports in HOC."""
    results = defaultdict(list)

    # Pattern for app.services imports (excluding models)
    import_pattern = re.compile(r"from app\.services\.")

    for py_file in HOC_ROOT.rglob("*.py"):
        if is_excluded_file(py_file):
            continue

        try:
            content = py_file.read_text()
        except Exception:
            continue

        # Skip files in docstrings
        in_docstring = False

        for line_no, line in enumerate(content.split("\n"), 1):
            # Simple docstring detection
            if '"""' in line or "'''" in line:
                in_docstring = not in_docstring
                continue
            if in_docstring:
                continue

            if import_pattern.search(line):
                if not is_excluded_import(line):
                    # Get domain from path
                    try:
                        rel_path = py_file.relative_to(HOC_ROOT)
                        domain = rel_path.parts[0] if rel_path.parts else "unknown"
                    except ValueError:
                        domain = "unknown"

                    results[domain].append({
                        "file": str(py_file.relative_to(HOC_ROOT.parent.parent)),
                        "line": line_no,
                        "import": line.strip(),
                    })

    return dict(results)


def extract_module(import_line: str) -> str:
    """Extract module name from import line."""
    match = re.search(r"from (app\.services\.[a-z_\.]+)", import_line)
    if match:
        return match.group(1)
    return "unknown"


def count_by_module(results: dict) -> dict:
    """Count imports by module."""
    module_counts = defaultdict(int)
    for domain, imports in results.items():
        for imp in imports:
            module = extract_module(imp["import"])
            module_counts[module] += 1
    return dict(sorted(module_counts.items(), key=lambda x: -x[1]))


def main():
    parser = argparse.ArgumentParser(description="Sweep-03 Module Blocker Tracker")
    parser.add_argument("--count", action="store_true", help="Show total count only")
    parser.add_argument("--domains", action="store_true", help="Show per-domain counts")
    parser.add_argument("--domain", type=str, help="Show specific domain details")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--priority", action="store_true", help="Show priority modules")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--ci", action="store_true", help="CI mode - exit 1 if > 0")

    args = parser.parse_args()

    results = find_blocking_imports(args.verbose)

    # Calculate totals
    total = sum(len(imports) for imports in results.values())

    if args.json:
        import json
        print(json.dumps({
            "total": total,
            "by_domain": {d: len(i) for d, i in results.items()},
            "by_module": count_by_module(results),
        }, indent=2))
        sys.exit(1 if args.ci and total > 0 else 0)

    if args.count:
        print(f"Blocking imports: {total}")
        sys.exit(1 if args.ci and total > 0 else 0)

    if args.domains:
        print("Blocking imports by domain:")
        for domain, imports in sorted(results.items(), key=lambda x: -len(x[1])):
            print(f"  {domain}: {len(imports)}")
        print(f"\nTotal: {total}")
        sys.exit(1 if args.ci and total > 0 else 0)

    if args.domain:
        domain_results = results.get(args.domain, [])
        print(f"Domain: {args.domain}")
        print(f"Count: {len(domain_results)}")
        if args.verbose:
            for imp in domain_results:
                print(f"  {imp['file']}:{imp['line']}")
                print(f"    {imp['import']}")
        sys.exit(1 if args.ci and len(domain_results) > 0 else 0)

    if args.priority:
        module_counts = count_by_module(results)
        print("Priority modules (by import count):")
        for module, count in list(module_counts.items())[:15]:
            print(f"  {module}: {count}")
        print(f"\nTotal unique modules: {len(module_counts)}")
        print(f"Total blocking imports: {total}")
        sys.exit(1 if args.ci and total > 0 else 0)

    # Default: show summary
    print(f"Sweep-03 Legacy Module Migration Status")
    print(f"=" * 50)
    print(f"\nBlocking imports: {total}")
    print(f"\nBy domain:")
    for domain, imports in sorted(results.items(), key=lambda x: -len(x[1])):
        status = "CLEAN" if len(imports) == 0 else "BLOCKED"
        print(f"  {domain}: {len(imports)} ({status})")

    print(f"\nTop modules to migrate:")
    module_counts = count_by_module(results)
    for module, count in list(module_counts.items())[:10]:
        print(f"  {module}: {count}")


if __name__ == "__main__":
    main()
