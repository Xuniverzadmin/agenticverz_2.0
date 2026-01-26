#!/usr/bin/env python3
"""
Sweep-03: Legacy Module Migration Tracker

Tracks HOC engine imports to legacy modules that need migration.
EXCLUDES model imports (L6 drivers legitimately access models).

Usage:
    python scripts/ops/sweep_03_module_blocker.py [OPTIONS]

Options:
    --count           Show total blocker count
    --domains         Show domain-by-domain status
    --domain DOMAIN   Show specific domain details
    --verbose, -v     Show file-level details
    --json            Output as JSON
    --ci              Exit 1 if blockers remain (for CI)
    --priority        Show migration priority list
"""

import argparse
import json
import re
import sys
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Set


HOC_ROOT = Path("app/hoc/cus")

# Modules that are EXCLUDED from migration (models/data structures)
# L6 drivers legitimately access these
EXCLUDED_PATTERNS = [
    r"app\.services\.\w+\.models",      # app.services.*.models
    r"app\.services\.audit\.models",    # explicit
    r"app\.models\.",                   # app/models/*
]

# Modules already in L4_runtime (already resolved in Sweep-02A)
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

SCAN_PATTERNS = ["L5_engines/*.py", "L5_controls/*.py"]


@dataclass
class ImportInfo:
    file_path: str
    line_num: int
    module: str
    statement: str


@dataclass
class DomainStats:
    name: str
    files_scanned: int = 0
    files_clean: int = 0
    blocker_count: int = 0
    excluded_count: int = 0  # Model imports (OK)
    imports: List[ImportInfo] = field(default_factory=list)
    modules: Dict[str, int] = field(default_factory=lambda: defaultdict(int))


def is_excluded(module: str) -> bool:
    """Check if module is excluded from migration (models/data structures)."""
    for pattern in EXCLUDED_PATTERNS:
        if re.match(pattern, module):
            return True
    return False


def is_l4_covered(line: str) -> bool:
    """Check if import is already covered by L4_runtime."""
    return any(covered in line for covered in L4_RUNTIME_COVERED)


def extract_module(stmt: str) -> str:
    """Extract module path from import statement."""
    if "from app.services." in stmt:
        parts = stmt.split("from app.services.")[1].split()[0]
        return "app.services." + parts.rstrip(")")
    elif "import app.services." in stmt:
        parts = stmt.split("import app.services.")[1].split()[0]
        return "app.services." + parts.rstrip(")")
    return ""


def find_docstring_regions(content: str) -> List[tuple]:
    """Find line ranges that are inside docstrings."""
    regions = []
    for match in re.finditer(r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')', content):
        start_line = content[:match.start()].count('\n') + 1
        end_line = content[:match.end()].count('\n') + 1
        regions.append((start_line, end_line))
    return regions


def in_docstring(line_num: int, regions: List[tuple]) -> bool:
    """Check if line is inside a docstring."""
    return any(start <= line_num <= end for start, end in regions)


def analyze_file(file_path: Path) -> Dict:
    """Analyze a file for legacy module imports."""
    result = {
        "blockers": [],
        "excluded": [],
    }

    try:
        content = file_path.read_text()
        lines = content.split('\n')
        docstring_regions = find_docstring_regions(content)

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Only look at app.services imports
            if not (stripped.startswith('from app.services') or
                    stripped.startswith('import app.services')):
                continue

            # Skip docstrings
            if in_docstring(i, docstring_regions):
                continue

            # Skip L4_runtime covered
            if is_l4_covered(stripped):
                continue

            module = extract_module(stripped)
            if not module:
                continue

            info = ImportInfo(
                file_path=str(file_path),
                line_num=i,
                module=module,
                statement=stripped
            )

            if is_excluded(module):
                result["excluded"].append(info)
            else:
                result["blockers"].append(info)

    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)

    return result


def scan_domain(domain_path: Path) -> DomainStats:
    """Scan a domain and return stats."""
    stats = DomainStats(name=domain_path.name)

    for pattern in SCAN_PATTERNS:
        for file_path in domain_path.glob(pattern):
            if file_path.name.startswith('__'):
                continue

            stats.files_scanned += 1
            result = analyze_file(file_path)

            if not result["blockers"] and not result["excluded"]:
                stats.files_clean += 1

            for info in result["blockers"]:
                stats.blocker_count += 1
                stats.imports.append(info)
                stats.modules[info.module] += 1

            stats.excluded_count += len(result["excluded"])

    return stats


def scan_all_domains(hoc_path: Path) -> Dict[str, DomainStats]:
    """Scan all domains."""
    results = {}

    for domain_path in sorted(hoc_path.iterdir()):
        if not domain_path.is_dir() or domain_path.name.startswith('_'):
            continue

        stats = scan_domain(domain_path)
        results[domain_path.name] = stats

    return results


def get_status(stats: DomainStats) -> str:
    """Get domain status string."""
    if stats.blocker_count == 0 and stats.excluded_count == 0:
        return "CLEAN"
    elif stats.blocker_count == 0:
        return "CLEAN (models OK)"
    else:
        return "BLOCKED"


def print_domains_table(all_stats: Dict[str, DomainStats], verbose: bool = False):
    """Print domain status table."""
    print("=" * 90)
    print("SWEEP-03: Legacy Module Migration — Domain Status")
    print("=" * 90)
    print()
    print(f"{'Domain':<15} {'Files':<8} {'Clean':<8} {'Blocked':<10} {'Models':<10} {'Status'}")
    print("-" * 90)

    total_files = 0
    total_clean = 0
    total_blocked = 0
    total_excluded = 0

    for domain in sorted(all_stats.keys()):
        stats = all_stats[domain]
        status = get_status(stats)

        total_files += stats.files_scanned
        total_clean += stats.files_clean
        total_blocked += stats.blocker_count
        total_excluded += stats.excluded_count

        print(f"{domain:<15} {stats.files_scanned:<8} {stats.files_clean:<8} "
              f"{stats.blocker_count:<10} {stats.excluded_count:<10} {status}")

        if verbose and stats.blocker_count > 0:
            for module, count in sorted(stats.modules.items(), key=lambda x: -x[1]):
                print(f"    └─ {module}: {count} imports")

    print("-" * 90)
    print(f"{'TOTAL':<15} {total_files:<8} {total_clean:<8} "
          f"{total_blocked:<10} {total_excluded:<10}")
    print()


def print_priority_list(all_stats: Dict[str, DomainStats]):
    """Print migration priority list."""
    # Aggregate modules across all domains
    all_modules = defaultdict(lambda: {"count": 0, "domains": set()})

    for domain, stats in all_stats.items():
        for module, count in stats.modules.items():
            all_modules[module]["count"] += count
            all_modules[module]["domains"].add(domain)

    print("=" * 90)
    print("SWEEP-03: Migration Priority (by import count)")
    print("=" * 90)
    print()
    print(f"{'Priority':<10} {'Module':<45} {'Imports':<10} {'Domains'}")
    print("-" * 90)

    sorted_modules = sorted(all_modules.items(), key=lambda x: -x[1]["count"])

    for i, (module, info) in enumerate(sorted_modules, 1):
        priority = "HIGH" if info["count"] >= 4 else "MEDIUM" if info["count"] >= 2 else "LOW"
        domains = ", ".join(sorted(info["domains"]))
        print(f"{priority:<10} {module:<45} {info['count']:<10} {domains}")

    print()
    print(f"Total modules to migrate: {len(all_modules)}")
    print(f"Total blocking imports: {sum(m['count'] for m in all_modules.values())}")


def print_domain_detail(stats: DomainStats):
    """Print detailed info for a single domain."""
    print("=" * 90)
    print(f"SWEEP-03: Domain Detail — {stats.name.upper()}")
    print("=" * 90)
    print()
    print(f"Files scanned: {stats.files_scanned}")
    print(f"Files clean: {stats.files_clean}")
    print(f"Blocking imports: {stats.blocker_count}")
    print(f"Model imports (OK): {stats.excluded_count}")
    print(f"Status: {get_status(stats)}")
    print()

    if stats.blocker_count > 0:
        print("Blocking Modules:")
        print("-" * 60)
        for module, count in sorted(stats.modules.items(), key=lambda x: -x[1]):
            print(f"  {module}: {count} imports")

        print()
        print("Blocking Imports (file:line):")
        print("-" * 60)
        for info in sorted(stats.imports, key=lambda x: (x.module, x.file_path)):
            short_path = info.file_path.replace("app/hoc/cus/", "")
            print(f"  {short_path}:{info.line_num}")
            print(f"    {info.statement[:70]}...")


def main():
    parser = argparse.ArgumentParser(description="Sweep-03 Legacy Module Migration Tracker")
    parser.add_argument("--count", action="store_true", help="Show total blocker count")
    parser.add_argument("--domains", action="store_true", help="Show domain status table")
    parser.add_argument("--domain", help="Show specific domain details")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--ci", action="store_true", help="Exit 1 if blockers remain")
    parser.add_argument("--priority", action="store_true", help="Show migration priority list")
    args = parser.parse_args()

    # Find HOC root
    if HOC_ROOT.exists():
        hoc_path = HOC_ROOT
    else:
        # Try from repo root
        hoc_path = Path("backend") / HOC_ROOT
        if not hoc_path.exists():
            print("ERROR: Cannot find hoc/cus directory", file=sys.stderr)
            sys.exit(1)

    # Scan all domains
    all_stats = scan_all_domains(hoc_path)

    # Calculate totals
    total_blocked = sum(s.blocker_count for s in all_stats.values())
    total_excluded = sum(s.excluded_count for s in all_stats.values())

    # Handle output mode
    if args.json:
        output = {
            "total_blocked": total_blocked,
            "total_excluded": total_excluded,
            "domains": {
                name: {
                    "files_scanned": s.files_scanned,
                    "files_clean": s.files_clean,
                    "blocker_count": s.blocker_count,
                    "excluded_count": s.excluded_count,
                    "status": get_status(s),
                    "modules": dict(s.modules) if args.verbose else None
                }
                for name, s in all_stats.items()
            }
        }
        print(json.dumps(output, indent=2))

    elif args.count:
        print(f"LEGACY_MODULE_BLOCKER: {total_blocked}")
        print(f"(Model imports excluded: {total_excluded})")

    elif args.domain:
        if args.domain in all_stats:
            print_domain_detail(all_stats[args.domain])
        else:
            print(f"ERROR: Domain '{args.domain}' not found", file=sys.stderr)
            sys.exit(1)

    elif args.priority:
        print_priority_list(all_stats)

    else:
        # Default: show domains table
        print_domains_table(all_stats, verbose=args.verbose)

        print("Legend:")
        print("  Files    = L5 engine/control files scanned")
        print("  Clean    = Files with no legacy imports")
        print("  Blocked  = Imports needing module migration")
        print("  Models   = Model imports (excluded, L6 access OK)")
        print()
        print("Status:")
        print("  CLEAN           = No legacy imports")
        print("  CLEAN (models)  = Only model imports (L6 access OK)")
        print("  BLOCKED         = Has imports needing migration")

    # CI mode
    if args.ci:
        if total_blocked > 0:
            print(f"\nCI FAILURE: {total_blocked} blocking imports remain", file=sys.stderr)
            sys.exit(1)
        else:
            print("\nCI PASS: No blocking imports", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
