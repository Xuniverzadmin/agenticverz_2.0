#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Analyze signal consumption from L8 to L2 layer
# Authority: READ-ONLY (audit script)
# Reference: L1_L2_L8 Binding Audit

"""
L8 → L2 Binding Analysis
Searches for signal names referenced inside L2 APIs.
Identifies orphaned signals (emitted but not consumed).
"""

import ast
import pathlib
import re
import sys

# Signal concept hints (what L8 might emit)
SIGNAL_CONCEPTS = [
    "incident",
    "anomaly",
    "violation",
    "recovery",
    "prediction",
    "alert",
    "metric",
    "health",
    "canary",
    "rollback",
    "budget",
    "cost",
    "policy",
    "guard",
    "trace",
    "replay",
    "mismatch",
    "failure",
    "timeout",
    "throttle",
    "killswitch",
]

# L8 source directories
L8_ROOTS = [
    "scripts",
    "monitoring",
    "observability",
    ".github/workflows",
]

# L2 API directory
L2_API_ROOT = pathlib.Path("backend/app/api")


def find_signal_sources(repo_root: pathlib.Path):
    """Find where each signal concept is emitted in L8."""
    sources = {}  # concept -> list of files

    for root in L8_ROOTS:
        root_path = repo_root / root
        if not root_path.exists():
            continue

        for ext in ["*.py", "*.yaml", "*.yml", "*.sh"]:
            for path in root_path.rglob(ext):
                try:
                    text = path.read_text(errors="ignore").lower()
                except Exception:
                    continue

                for concept in SIGNAL_CONCEPTS:
                    if concept in text:
                        rel_path = str(path.relative_to(repo_root))
                        sources.setdefault(concept, set()).add(rel_path)

    return sources


def find_signal_consumers(repo_root: pathlib.Path):
    """Find where each signal concept is consumed in L2."""
    consumers = {}  # concept -> list of files

    api_root = repo_root / "backend" / "app" / "api"
    if not api_root.exists():
        return consumers

    for path in api_root.glob("*.py"):
        try:
            text = path.read_text(errors="ignore").lower()
        except Exception:
            continue

        for concept in SIGNAL_CONCEPTS:
            if concept in text:
                consumers.setdefault(concept, set()).add(path.name)

    return consumers


def find_l2_to_store_bindings(repo_root: pathlib.Path):
    """Find which L2 APIs write to persistent stores (L6)."""
    bindings = {}  # api file -> what it writes

    api_root = repo_root / "backend" / "app" / "api"
    if not api_root.exists():
        return bindings

    # Patterns indicating DB writes
    write_patterns = [
        re.compile(r'session\.add\('),
        re.compile(r'session\.execute\('),
        re.compile(r'\.create\('),
        re.compile(r'\.update\('),
        re.compile(r'\.delete\('),
        re.compile(r'INSERT\s+INTO', re.I),
        re.compile(r'UPDATE\s+', re.I),
        re.compile(r'DELETE\s+FROM', re.I),
    ]

    for path in api_root.glob("*.py"):
        try:
            text = path.read_text(errors="ignore")
        except Exception:
            continue

        writes = []
        for pattern in write_patterns:
            if pattern.search(text):
                writes.append(pattern.pattern[:20])

        if writes:
            bindings[path.name] = writes

    return bindings


def main():
    repo_root = pathlib.Path(__file__).parent.parent.parent

    sources = find_signal_sources(repo_root)
    consumers = find_signal_consumers(repo_root)
    l2_writes = find_l2_to_store_bindings(repo_root)

    # Output markdown
    print("# L8 → L2 Binding Analysis")
    print()
    print(f"**Signal Concepts Tracked:** {len(SIGNAL_CONCEPTS)}")
    print()

    print("## Signal Binding Matrix")
    print()
    print("| Signal Concept | L8 Sources | L2 Consumers | Binding Status |")
    print("|----------------|------------|--------------|----------------|")

    orphaned = []
    bound = []

    for concept in sorted(SIGNAL_CONCEPTS):
        src_count = len(sources.get(concept, set()))
        consumer_count = len(consumers.get(concept, set()))

        if src_count > 0 and consumer_count == 0:
            status = "ORPHANED"
            orphaned.append(concept)
        elif src_count > 0 and consumer_count > 0:
            status = "BOUND"
            bound.append(concept)
        elif src_count == 0 and consumer_count > 0:
            status = "L2-ONLY"
        else:
            status = "UNUSED"

        src_files = ", ".join(sorted(sources.get(concept, set()))[:2])
        if len(sources.get(concept, set())) > 2:
            src_files += "..."

        consumer_files = ", ".join(sorted(consumers.get(concept, set())))

        print(f"| {concept} | {src_count} ({src_files or '-'}) | {consumer_count} ({consumer_files or '-'}) | {status} |")

    print()
    print("## Binding Summary")
    print()
    print(f"- **Bound Signals:** {len(bound)} (L8 → L2 connected)")
    print(f"- **Orphaned Signals:** {len(orphaned)} (L8 emits, no L2 consumer)")
    print()

    if orphaned:
        print("### Orphaned Signals (Action Required)")
        print()
        print("These signals are emitted in L8 but have no L2 API consumer:")
        print()
        for concept in orphaned:
            src_files = sorted(sources.get(concept, set()))[:3]
            print(f"- **{concept}**: emitted in {', '.join(src_files)}")

    print()
    print("## L2 → L6 Write Bindings")
    print()
    print("API files that write directly to persistent storage:")
    print()
    print("| API File | Write Patterns |")
    print("|----------|----------------|")

    for api_file, patterns in sorted(l2_writes.items()):
        patterns_str = ", ".join(set(patterns))[:50]
        print(f"| `{api_file}` | {patterns_str} |")

    print()
    print("---")
    print()
    print("## Recommendations")
    print()
    print("1. **Orphaned signals** should either:")
    print("   - Be surfaced via L2 API (if product-relevant)")
    print("   - Be documented as system-only (intentional)")
    print()
    print("2. **L2 → L6 writes** should be:")
    print("   - Documented in semantic Authority header")
    print("   - Reviewed for product-safety before L1 exposure")


if __name__ == "__main__":
    main()
