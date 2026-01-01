#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: manual | CI
#   Execution: sync
# Role: Signal Registry Auditor (Observe-Only Mode)
# Authority: READ-ONLY (no mutations)
# Reference: PIN-252, auditor_rules.yaml

"""
Signal Registry Auditor

Compares the frozen signal registry against codebase reality.
Operates in OBSERVE-ONLY mode - reports findings but does not block.

Usage:
    python signal_auditor.py                    # Full audit
    python signal_auditor.py --mode observe     # Observe-only (default)
    python signal_auditor.py --mode enforce     # CI blocking mode (future)
    python signal_auditor.py --check orphans    # Check orphaned signals only
    python signal_auditor.py --check unregistered  # Check unregistered writes only
    python signal_auditor.py --json             # JSON output
"""

import argparse
import json
import logging
import pathlib
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Set

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("signal_auditor")

# Paths
REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
REGISTRY_PATH = REPO_ROOT / "docs" / "architecture" / "SIGNAL_REGISTRY_COMPLETE.md"
PYTHON_BASELINE = (
    REPO_ROOT / "docs" / "architecture" / "SIGNAL_REGISTRY_PYTHON_BASELINE.md"
)
RULES_PATH = pathlib.Path(__file__).parent / "auditor_rules.yaml"
BACKEND_APP = REPO_ROOT / "backend" / "app"

# Patterns for detecting DB writes (strict - must be actual code, not comments)
WRITE_PATTERNS = [
    re.compile(r"^\s*session\.add\s*\("),
    re.compile(r"^\s*session\.execute\s*\("),
    re.compile(r"^\s*await\s+session\.execute\s*\("),
    re.compile(r"^\s*session\.commit\s*\("),
    re.compile(r"^\s*await\s+session\.commit\s*\("),
]

# Patterns to EXCLUDE (comments, docstrings, model definitions)
EXCLUDE_LINE_PATTERNS = [
    re.compile(r"^\s*#"),  # Comments
    re.compile(r"^\s*\"\"\""),  # Docstrings
    re.compile(r"^\s*'''"),  # Docstrings
    re.compile(r"Field\s*\("),  # SQLModel field definitions
    re.compile(r"description\s*="),  # Field descriptions
    re.compile(r"^\s*def\s+"),  # Function definitions
]

# Files to exclude from analysis
EXCLUDED_PATTERNS = [
    "__pycache__",
    ".pytest_cache",
    "tests/",
    "alembic/",
]


@dataclass
class Signal:
    """Parsed signal from registry."""

    uid: str
    name: str
    signal_class: str = "UNKNOWN"
    trigger: str = "UNKNOWN"
    producer: str = "UNKNOWN"
    p_layer: str = "UNKNOWN"
    consumer: str = "UNKNOWN"
    c_layer: str = "UNKNOWN"
    persistence: str = "UNKNOWN"
    l2_api: str = "—"
    verified_path: str = "NO"


@dataclass
class WriteLocation:
    """Location of a DB write in codebase."""

    file: str
    line: int
    pattern: str
    context: str = ""


@dataclass
class AuditResult:
    """Complete audit result."""

    mode: str = "observe"
    registry_signals: int = 0
    codebase_writes: int = 0
    orphaned_signals: List[str] = field(default_factory=list)
    unregistered_writes: List[WriteLocation] = field(default_factory=list)
    unknown_fields: Dict[str, List[str]] = field(default_factory=dict)
    l7_flow_gaps: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    passed: bool = True


def parse_registry(registry_path: pathlib.Path) -> List[Signal]:
    """Parse signals from registry markdown."""
    signals = []

    if not registry_path.exists():
        logger.error(f"Registry not found: {registry_path}")
        return signals

    text = registry_path.read_text()

    # Find signal tables - look for rows starting with | SIG-
    # Pattern matches: | SIG-XXX | SignalName | ... |
    sig_pattern = re.compile(r"^\|\s*(SIG-\d+)\s*\|\s*([^|]+)\s*\|", re.MULTILINE)

    # Track UIDs to avoid duplicates
    seen_uids = set()

    for match in sig_pattern.finditer(text):
        uid = match.group(1).strip()
        name = match.group(2).strip()

        # Skip if we've seen this UID (e.g., in "Files Removed" section)
        if uid in seen_uids:
            continue

        # Skip removed signals (SIG-201 to SIG-205)
        if uid in ("SIG-201", "SIG-202", "SIG-203", "SIG-204", "SIG-205"):
            continue

        seen_uids.add(uid)
        signals.append(Signal(uid=uid, name=name))

    # Also parse Python baseline for full signal list
    python_baseline = registry_path.parent / "SIGNAL_REGISTRY_PYTHON_BASELINE.md"
    if python_baseline.exists():
        baseline_text = python_baseline.read_text()
        for match in sig_pattern.finditer(baseline_text):
            uid = match.group(1).strip()
            name = match.group(2).strip()

            if uid not in seen_uids:
                seen_uids.add(uid)
                signals.append(Signal(uid=uid, name=name))

    logger.info(f"Parsed {len(signals)} signals from registry")
    return signals


def find_write_locations(app_root: pathlib.Path) -> List[WriteLocation]:
    """Find all DB write locations in codebase."""
    writes = []

    for py_file in app_root.rglob("*.py"):
        # Skip excluded paths
        rel_path = str(py_file.relative_to(app_root.parent))
        if any(excl in rel_path for excl in EXCLUDED_PATTERNS):
            continue

        try:
            content = py_file.read_text(errors="ignore")
            lines = content.split("\n")

            for i, line in enumerate(lines, 1):
                # Skip lines that match exclusion patterns
                if any(excl.search(line) for excl in EXCLUDE_LINE_PATTERNS):
                    continue

                for pattern in WRITE_PATTERNS:
                    if pattern.search(line):
                        writes.append(
                            WriteLocation(
                                file=rel_path,
                                line=i,
                                pattern=pattern.pattern[:30],
                                context=line.strip()[:80],
                            )
                        )
                        break  # Don't double-count same line

        except Exception as e:
            logger.warning(f"Error reading {py_file}: {e}")

    logger.info(f"Found {len(writes)} write locations in codebase")
    return writes


def find_registered_producers(signals: List[Signal]) -> Set[str]:
    """Extract producer files from signals (if available)."""
    producers = set()

    # This is a simplified extraction - in practice, we'd parse the full registry
    # For now, return known producers from Python baseline
    known_producers = {
        "guard_write_service.py",
        "cost_write_service.py",
        "runner.py",
        "recovery_matcher.py",
        "llm_failure_service.py",
        "tenant_service.py",
        "user_write_service.py",
        "worker_registry_service.py",
        "memory_service.py",
        "registry_service.py",
        "job_service.py",
        "message_service.py",
        "prediction.py",
        "policy_violation_service.py",
        "founder_action_write_service.py",
        "graduation_engine.py",
        "dispatcher.py",
        "checkpoint.py",
        "circuit_breaker.py",
        "cost_anomaly_detector.py",
        "incident_aggregator.py",
    }

    return known_producers


def check_orphaned_signals(signals: List[Signal]) -> List[str]:
    """Check for signals with no consumer."""
    orphaned = []

    for sig in signals:
        # If consumer is explicitly NONE or missing, flag it
        if sig.consumer in ("NONE", "—", "UNKNOWN"):
            # But skip internal-only signals (L7 ops)
            if sig.p_layer == "L7" and sig.c_layer == "L7":
                continue
            orphaned.append(f"{sig.uid} ({sig.name}): No consumer")

    return orphaned


def check_unregistered_writes(
    writes: List[WriteLocation],
    registered_producers: Set[str],
) -> List[WriteLocation]:
    """Find writes not covered by registry."""
    unregistered = []

    for write in writes:
        # Extract filename from path
        filename = pathlib.Path(write.file).name

        # Skip if it's a known producer
        if filename in registered_producers:
            continue

        # Skip test files
        if "test" in write.file.lower():
            continue

        # Skip migrations
        if "alembic" in write.file:
            continue

        unregistered.append(write)

    return unregistered


def check_unknown_fields(signals: List[Signal]) -> Dict[str, List[str]]:
    """Find signals with UNKNOWN fields."""
    unknowns: Dict[str, List[str]] = {}

    for sig in signals:
        unknown_fields = []

        if sig.trigger == "UNKNOWN":
            unknown_fields.append("trigger")
        if sig.producer == "UNKNOWN":
            unknown_fields.append("producer")
        if sig.consumer == "UNKNOWN":
            unknown_fields.append("consumer")
        if sig.persistence == "UNKNOWN":
            unknown_fields.append("persistence")

        if unknown_fields:
            unknowns[sig.uid] = unknown_fields

    return unknowns


def run_audit(mode: str = "observe") -> AuditResult:
    """Run the full audit."""
    result = AuditResult(mode=mode)

    # Parse registry
    signals = parse_registry(REGISTRY_PATH)
    result.registry_signals = len(signals)

    if not signals:
        # Try Python baseline
        signals = parse_registry(PYTHON_BASELINE)
        result.registry_signals = len(signals)

    # Find write locations
    writes = find_write_locations(BACKEND_APP)
    result.codebase_writes = len(writes)

    # Get registered producers
    registered_producers = find_registered_producers(signals)

    # Check orphaned signals
    result.orphaned_signals = check_orphaned_signals(signals)
    if result.orphaned_signals:
        result.warnings.append(f"Found {len(result.orphaned_signals)} orphaned signals")

    # Check unregistered writes
    result.unregistered_writes = check_unregistered_writes(writes, registered_producers)
    if result.unregistered_writes:
        result.warnings.append(
            f"Found {len(result.unregistered_writes)} unregistered write locations"
        )

    # Check unknown fields
    result.unknown_fields = check_unknown_fields(signals)
    if result.unknown_fields:
        unknown_count = len(result.unknown_fields)
        unknown_pct = (
            (unknown_count / result.registry_signals * 100)
            if result.registry_signals
            else 0
        )
        result.warnings.append(
            f"Found {unknown_count} signals ({unknown_pct:.1f}%) with UNKNOWN fields"
        )

    # Determine pass/fail based on mode
    if mode == "enforce":
        if result.errors:
            result.passed = False
    # In observe mode, always pass but report findings

    return result


def print_report(result: AuditResult, json_output: bool = False) -> None:
    """Print audit report."""
    if json_output:
        # Convert to JSON-serializable format
        output = {
            "mode": result.mode,
            "registry_signals": result.registry_signals,
            "codebase_writes": result.codebase_writes,
            "orphaned_signals": result.orphaned_signals,
            "unregistered_writes": [
                {
                    "file": w.file,
                    "line": w.line,
                    "pattern": w.pattern,
                    "context": w.context,
                }
                for w in result.unregistered_writes[:20]  # Limit output
            ],
            "unknown_fields": result.unknown_fields,
            "warnings": result.warnings,
            "errors": result.errors,
            "passed": result.passed,
        }
        print(json.dumps(output, indent=2))
        return

    # Human-readable report
    print("\n" + "=" * 60)
    print("SIGNAL REGISTRY AUDIT REPORT")
    print(f"Mode: {result.mode.upper()}")
    print("=" * 60)

    print("\n📊 Summary:")
    print(f"   Registry signals: {result.registry_signals}")
    print(f"   Codebase writes:  {result.codebase_writes}")
    print(f"   Orphaned signals: {len(result.orphaned_signals)}")
    print(f"   Unregistered writes: {len(result.unregistered_writes)}")
    print(f"   Signals with UNKNOWNs: {len(result.unknown_fields)}")

    if result.orphaned_signals:
        print(f"\n⚠️  Orphaned Signals ({len(result.orphaned_signals)}):")
        for sig in result.orphaned_signals[:10]:
            print(f"   - {sig}")
        if len(result.orphaned_signals) > 10:
            print(f"   ... and {len(result.orphaned_signals) - 10} more")

    if result.unregistered_writes:
        print(f"\n⚠️  Unregistered Write Locations ({len(result.unregistered_writes)}):")
        for write in result.unregistered_writes[:10]:
            print(f"   - {write.file}:{write.line}")
            print(f"     {write.context[:60]}...")
        if len(result.unregistered_writes) > 10:
            print(f"   ... and {len(result.unregistered_writes) - 10} more")

    if result.unknown_fields:
        print(f"\n📝 Signals with UNKNOWN fields ({len(result.unknown_fields)}):")
        for uid, fields in list(result.unknown_fields.items())[:10]:
            print(f"   - {uid}: {', '.join(fields)}")
        if len(result.unknown_fields) > 10:
            print(f"   ... and {len(result.unknown_fields) - 10} more")

    if result.warnings:
        print("\n⚠️  Warnings:")
        for warning in result.warnings:
            print(f"   - {warning}")

    if result.errors:
        print("\n❌ Errors:")
        for error in result.errors:
            print(f"   - {error}")

    print("\n" + "-" * 60)
    if result.passed:
        print("✅ AUDIT PASSED (observe-only mode)")
    else:
        print("❌ AUDIT FAILED")
    print("-" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Signal Registry Auditor")
    parser.add_argument(
        "--mode",
        choices=["observe", "enforce"],
        default="observe",
        help="Audit mode (default: observe)",
    )
    parser.add_argument(
        "--check",
        choices=["all", "orphans", "unregistered", "unknown"],
        default="all",
        help="Specific check to run",
    )
    parser.add_argument("--json", action="store_true", help="JSON output")

    args = parser.parse_args()

    try:
        result = run_audit(mode=args.mode)
        print_report(result, json_output=args.json)

        # Exit code based on mode
        if args.mode == "enforce" and not result.passed:
            sys.exit(2)
        elif result.warnings and args.mode == "enforce":
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        logger.exception(f"Audit failed: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
