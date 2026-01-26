#!/usr/bin/env python3
"""
Sweep-02A: Actionable Subset Identifier

Identifies which app.services.* imports can be rewired to L4_runtime TODAY
vs which require module migration first.

The L4_runtime currently re-exports from:
- app.services.governance.* (CAN BE REWIRED)

Other service modules require migration first (OUT OF SCOPE for this sweep):
- app.services.activity.*
- app.services.incidents.*
- app.services.policy.*
- app.services.audit.*
- etc.
"""

import sys
from pathlib import Path
from collections import defaultdict


HOC_ROOT = Path("app/hoc/cus")

# Services that have L4_runtime equivalents (CAN BE REWIRED)
L4_RUNTIME_COVERED = [
    "app.services.governance.audit_service",
    "app.services.governance.contract_service",
    "app.services.governance.eligibility_engine",
    "app.services.governance.governance_orchestrator",
    "app.services.governance.job_executor",
    "app.services.governance.rollout_projection",
    "app.services.governance.validator_service",
    "app.services.governance.cross_domain",
    "app.services.governance.run_governance_facade",
    "app.services.governance.transaction_coordinator",
]

# Patterns to scan
SCAN_PATTERNS = [
    "*/L5_engines/*.py",
    "*/L5_controls/*.py",
]


def categorize_imports(file_path: Path) -> dict:
    """Categorize imports as actionable or deferred."""
    result = {
        "actionable": [],       # Can be rewired to L4_runtime
        "deferred": [],         # Requires module migration first
        "docstring_examples": [],  # Inside docstrings, not actual imports
    }

    try:
        content = file_path.read_text()
        lines = content.split('\n')

        # Track if we're inside a docstring
        in_docstring = False
        docstring_delim = None

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Track docstring boundaries
            # Check for triple quotes that start/end docstrings
            if not in_docstring:
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    docstring_delim = stripped[:3]
                    # Check if it ends on same line
                    if stripped.count(docstring_delim) == 1:
                        in_docstring = True
                    # else: single-line docstring, no state change
            else:
                # We're in a docstring, check for closing
                if docstring_delim in stripped:
                    in_docstring = False
                    docstring_delim = None

            if not (stripped.startswith('from app.services') or
                    stripped.startswith('import app.services')):
                continue

            # Check if this import is covered by L4_runtime
            is_actionable = False
            for covered in L4_RUNTIME_COVERED:
                if covered in line:
                    is_actionable = True
                    break

            # If inside a docstring, it's an example, not an actual import
            if in_docstring or (i > 1 and lines[i-2].strip().startswith('Usage:')):
                result["docstring_examples"].append((i, stripped))
            elif is_actionable:
                result["actionable"].append((i, stripped))
            else:
                result["deferred"].append((i, stripped))

    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)

    return result


def scan_hoc(backend_root: Path) -> dict:
    """Scan HOC and categorize all violations."""
    hoc_path = backend_root / HOC_ROOT

    results = {
        "actionable_total": 0,
        "deferred_total": 0,
        "docstring_total": 0,
        "actionable_files": [],
        "deferred_files": [],
        "docstring_files": [],
        "deferred_modules": defaultdict(int),
    }

    for pattern in SCAN_PATTERNS:
        for file_path in hoc_path.glob(pattern):
            if file_path.name.startswith('__'):
                continue

            cats = categorize_imports(file_path)
            rel_path = str(file_path.relative_to(backend_root))

            if cats["actionable"]:
                results["actionable_files"].append((rel_path, cats["actionable"]))
                results["actionable_total"] += len(cats["actionable"])

            if cats["docstring_examples"]:
                results["docstring_files"].append((rel_path, cats["docstring_examples"]))
                results["docstring_total"] += len(cats["docstring_examples"])

            if cats["deferred"]:
                results["deferred_files"].append((rel_path, cats["deferred"]))
                results["deferred_total"] += len(cats["deferred"])

                # Track which modules are deferred
                for _, stmt in cats["deferred"]:
                    # Extract module path
                    if "from app.services." in stmt:
                        parts = stmt.split("from app.services.")[1].split()[0]
                        module = parts.split(".")[0]
                        results["deferred_modules"][module] += 1

    return results


def print_report(results: dict):
    """Print categorized report."""

    print("=" * 70)
    print("SWEEP-02A: Actionable Subset Analysis")
    print("=" * 70)
    print()

    print("-" * 70)
    print("SUMMARY")
    print("-" * 70)
    print(f"  ACTIONABLE (can rewire to L4_runtime): {results['actionable_total']}")
    print(f"  DOCSTRINGS (examples, not imports):    {results['docstring_total']}")
    print(f"  DEFERRED (needs module migration):     {results['deferred_total']}")
    print(f"  TOTAL violations:                      {results['actionable_total'] + results['deferred_total']}")
    print()

    if results['actionable_files']:
        print("-" * 70)
        print("ACTIONABLE FILES (governance.* -> L4_runtime)")
        print("-" * 70)
        for file_path, violations in sorted(results['actionable_files']):
            print(f"\n  {file_path} ({len(violations)} imports)")
            for line_num, stmt in violations:
                print(f"    Line {line_num}: {stmt[:55]}...")
        print()

    if results['docstring_files']:
        print("-" * 70)
        print("DOCSTRING EXAMPLES (not actual imports)")
        print("-" * 70)
        for file_path, examples in sorted(results['docstring_files']):
            print(f"\n  {file_path} ({len(examples)} examples)")
            for line_num, stmt in examples:
                print(f"    Line {line_num}: {stmt[:55]}...")
        print()

    if results['deferred_modules']:
        print("-" * 70)
        print("DEFERRED MODULES (require migration first)")
        print("-" * 70)
        for module, count in sorted(results['deferred_modules'].items(), key=lambda x: -x[1]):
            print(f"  app.services.{module}: {count} imports")
        print()

    print("-" * 70)
    print("EXECUTION RECOMMENDATION")
    print("-" * 70)
    if results['actionable_total'] > 0:
        print(f"  Phase 1: Rewire {results['actionable_total']} actionable imports to L4_runtime")
        print(f"  Phase 2: (Separate sweep) Migrate {len(results['deferred_modules'])} modules to HOC")
    elif results['docstring_total'] > 0:
        print("  ACTIONABLE SCOPE COMPLETE")
        print(f"  Remaining {results['docstring_total']} items are docstring examples (not actual imports)")
        print(f"  {results['deferred_total']} imports require module migration (Sweep-03)")
    else:
        print("  No actionable items. All violations require module migration first.")
    print("=" * 70)

    return results['actionable_total']


def main():
    script_path = Path(__file__).resolve()
    backend_root = script_path.parent.parent.parent / "backend"

    if not backend_root.exists():
        backend_root = Path.cwd()
        if not (backend_root / "app" / "hoc").exists():
            print("ERROR: Must run from backend/ or repository root", file=sys.stderr)
            sys.exit(1)

    results = scan_hoc(backend_root)
    actionable_count = print_report(results)

    sys.exit(min(actionable_count, 255))


if __name__ == "__main__":
    main()
