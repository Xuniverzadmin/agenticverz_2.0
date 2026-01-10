#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: weekly cron or manual
#   Execution: sync
# Role: DB-AUTH-001 Governance Drift Detector
# Reference: DB-AUTH-001

"""
DB Authority Governance Drift Detector

Scans the codebase for governance drift indicators:
1. New scripts without _db_guard.py imports
2. New env files without DB_AUTHORITY
3. New docs mentioning DB usage without authority declaration

Output: Log → Pin → Review. No auto-fix.

Usage:
    python db_authority_drift_detector.py [--output json|text] [--pin]
    python db_authority_drift_detector.py --trend  # Show trend over time

Exit Codes:
    0 - No drift detected (or improving)
    1 - Drift detected (findings logged)
    2 - Error during scan
    3 - REGRESSION: Drift count INCREASED (hard fail)

Trend Tracking:
    Stores history in .db_authority_drift_history.json
    Shows: Previous drift → Current drift (Δ)
    Goal: Monotonic decrease
"""

# History file location
DRIFT_HISTORY_FILE = ".db_authority_drift_history.json"

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, NamedTuple


class Finding(NamedTuple):
    """A governance drift finding."""
    category: str
    severity: str  # HIGH, MEDIUM, LOW
    file: str
    issue: str
    recommendation: str


# Patterns that indicate DB usage
DB_USAGE_PATTERNS = [
    r"psycopg",
    r"DATABASE_URL",
    r"sqlalchemy",
    r"session\.execute",
    r"conn\.execute",
    r"cursor\.execute",
    r"\.query\(",
    r"create_engine",
    r"sessionmaker",
    r"AsyncSession",
]

# Patterns that indicate _db_guard is used
DB_GUARD_PATTERNS = [
    r"from.*_db_guard",
    r"import.*_db_guard",
    r"assert_db_authority",
    r"require_neon",
    r"require_local",
    r"register_connection",
]

# Patterns in docs that mention DB usage
DOC_DB_PATTERNS = [
    r"database",
    r"DATABASE_URL",
    r"postgres",
    r"neon",
    r"local.*db",
    r"db.*connection",
]


def find_python_scripts(root: Path) -> List[Path]:
    """Find all Python scripts that might touch DB."""
    scripts = []

    for pattern in ["backend/scripts/**/*.py", "scripts/**/*.py"]:
        scripts.extend(root.glob(pattern))

    # Exclude __pycache__, .venv, tests
    scripts = [
        s for s in scripts
        if "__pycache__" not in str(s)
        and ".venv" not in str(s)
        and "_db_guard.py" not in str(s)  # Exclude the guard itself
    ]

    return scripts


def find_env_files(root: Path) -> List[Path]:
    """Find all env files."""
    env_files = []

    for pattern in [".env*", "**/.env*"]:
        env_files.extend(root.glob(pattern))

    # Exclude .venv
    env_files = [e for e in env_files if ".venv" not in str(e)]

    return env_files


def find_doc_files(root: Path) -> List[Path]:
    """Find markdown documentation files."""
    return list(root.glob("docs/**/*.md"))


def check_script_for_db_guard(script: Path) -> Finding | None:
    """Check if a script that touches DB uses _db_guard."""
    try:
        content = script.read_text()
    except Exception:
        return None

    # Check if script touches DB
    touches_db = any(re.search(p, content) for p in DB_USAGE_PATTERNS)

    if not touches_db:
        return None

    # Check if it uses _db_guard
    uses_guard = any(re.search(p, content) for p in DB_GUARD_PATTERNS)

    if uses_guard:
        return None

    return Finding(
        category="SCRIPT_WITHOUT_GUARD",
        severity="HIGH",
        file=str(script),
        issue="Script touches database but doesn't use _db_guard",
        recommendation="Add: from scripts._db_guard import assert_db_authority"
    )


def check_env_for_authority(env_file: Path) -> Finding | None:
    """Check if an env file declares DB_AUTHORITY."""
    try:
        content = env_file.read_text()
    except Exception:
        return None

    # Skip if file doesn't mention database at all
    if "DATABASE" not in content.upper() and "POSTGRES" not in content.upper():
        return None

    # Check for DB_AUTHORITY
    if "DB_AUTHORITY=" in content:
        return None

    return Finding(
        category="ENV_WITHOUT_AUTHORITY",
        severity="HIGH",
        file=str(env_file),
        issue="Env file has database config but no DB_AUTHORITY",
        recommendation="Add: DB_AUTHORITY=neon (or local)"
    )


def check_doc_for_authority(doc: Path) -> Finding | None:
    """Check if a doc mentioning DB usage declares authority context."""
    try:
        content = doc.read_text().lower()
    except Exception:
        return None

    # Check if doc mentions DB
    mentions_db = any(re.search(p, content) for p in DOC_DB_PATTERNS)

    if not mentions_db:
        return None

    # Check if it mentions authority
    mentions_authority = (
        "db_authority" in content
        or "db-auth-001" in content
        or "authoritative" in content
        or "canonical" in content
    )

    if mentions_authority:
        return None

    # Only flag docs that seem to be about DB operations
    if "how to" in content or "guide" in content or "setup" in content:
        return Finding(
            category="DOC_WITHOUT_AUTHORITY",
            severity="MEDIUM",
            file=str(doc),
            issue="Doc discusses DB usage without mentioning authority",
            recommendation="Add section on DB_AUTHORITY declaration"
        )

    return None


def scan_for_drift(root: Path) -> List[Finding]:
    """Scan the codebase for governance drift."""
    findings = []

    # Check scripts
    for script in find_python_scripts(root):
        finding = check_script_for_db_guard(script)
        if finding:
            findings.append(finding)

    # Check env files
    for env_file in find_env_files(root):
        finding = check_env_for_authority(env_file)
        if finding:
            findings.append(finding)

    # Check docs
    for doc in find_doc_files(root):
        finding = check_doc_for_authority(doc)
        if finding:
            findings.append(finding)

    return findings


def output_text(findings: List[Finding]) -> None:
    """Output findings as text."""
    if not findings:
        print("=== DB-AUTH-001 Drift Detector ===")
        print("Status: CLEAN")
        print("No governance drift detected.")
        return

    print("=== DB-AUTH-001 Drift Detector ===")
    print(f"Status: DRIFT DETECTED")
    print(f"Findings: {len(findings)}")
    print()

    by_severity = {"HIGH": [], "MEDIUM": [], "LOW": []}
    for f in findings:
        by_severity[f.severity].append(f)

    for severity in ["HIGH", "MEDIUM", "LOW"]:
        if by_severity[severity]:
            print(f"=== {severity} Severity ===")
            for f in by_severity[severity]:
                print(f"\n[{f.category}] {f.file}")
                print(f"  Issue: {f.issue}")
                print(f"  Fix: {f.recommendation}")
            print()


def output_json(findings: List[Finding]) -> None:
    """Output findings as JSON."""
    data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "invariant": "DB-AUTH-001",
        "status": "CLEAN" if not findings else "DRIFT",
        "finding_count": len(findings),
        "findings": [
            {
                "category": f.category,
                "severity": f.severity,
                "file": f.file,
                "issue": f.issue,
                "recommendation": f.recommendation
            }
            for f in findings
        ]
    }
    print(json.dumps(data, indent=2))


def generate_pin_content(findings: List[Finding]) -> str:
    """Generate memory PIN content for drift findings."""
    now = datetime.now(timezone.utc)
    pin_date = now.strftime("%Y-%m-%d")

    content = f"""# PIN-XXX: DB-AUTH-001 Drift Detection - {pin_date}

**Status:** REVIEW_REQUIRED
**Created:** {pin_date}
**Category:** Governance / Drift Detection
**Invariant:** DB-AUTH-001

---

## Summary

Automated drift detection found {len(findings)} governance compliance issue(s).

---

## Findings

"""

    by_severity = {"HIGH": [], "MEDIUM": [], "LOW": []}
    for f in findings:
        by_severity[f.severity].append(f)

    for severity in ["HIGH", "MEDIUM", "LOW"]:
        if by_severity[severity]:
            content += f"### {severity} Severity\n\n"
            for f in by_severity[severity]:
                content += f"**{f.category}**\n"
                content += f"- File: `{f.file}`\n"
                content += f"- Issue: {f.issue}\n"
                content += f"- Fix: {f.recommendation}\n\n"

    content += """---

## Action Required

1. Review each finding
2. Apply fixes or document exceptions
3. Re-run drift detector to verify
4. Update this PIN status to RESOLVED

---

## Related

- `docs/governance/DB_AUTH_001_INVARIANT.md`
- `backend/scripts/_db_guard.py`
"""

    return content


# =============================================================================
# TREND TRACKING
# =============================================================================

def load_history(root: Path) -> List[dict]:
    """Load drift history from file."""
    history_file = root / DRIFT_HISTORY_FILE
    if not history_file.exists():
        return []
    try:
        return json.loads(history_file.read_text())
    except Exception:
        return []


def save_history(root: Path, history: List[dict]) -> None:
    """Save drift history to file."""
    history_file = root / DRIFT_HISTORY_FILE
    # Keep last 100 entries
    history = history[-100:]
    history_file.write_text(json.dumps(history, indent=2))


def record_drift(root: Path, count: int) -> dict:
    """Record current drift count and return trend info."""
    history = load_history(root)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "count": count
    }
    history.append(entry)
    save_history(root, history)

    # Calculate trend
    if len(history) < 2:
        return {
            "previous": None,
            "current": count,
            "delta": None,
            "trend": "BASELINE"
        }

    previous = history[-2]["count"]
    delta = count - previous

    if delta < 0:
        trend = "IMPROVING"
    elif delta > 0:
        trend = "REGRESSING"
    else:
        trend = "STABLE"

    return {
        "previous": previous,
        "current": count,
        "delta": delta,
        "trend": trend
    }


def show_trend(root: Path) -> None:
    """Display trend over time."""
    history = load_history(root)

    if not history:
        print("No drift history recorded yet.")
        print("Run the detector first to establish baseline.")
        return

    print("=== DB-AUTH-001 Drift Trend ===")
    print()

    # Show last 10 entries
    recent = history[-10:]
    for i, entry in enumerate(recent):
        ts = entry["timestamp"][:10]  # Just date
        count = entry["count"]

        if i == 0:
            print(f"  {ts}: {count} (baseline)")
        else:
            prev = recent[i-1]["count"]
            delta = count - prev
            arrow = "↓" if delta < 0 else "↑" if delta > 0 else "→"
            print(f"  {ts}: {count} ({arrow} {abs(delta)})")

    print()

    # Summary
    if len(history) >= 2:
        first = history[0]["count"]
        last = history[-1]["count"]
        total_delta = last - first
        print(f"Total change: {first} → {last} (Δ {total_delta:+d})")

        if total_delta < 0:
            print("Trend: IMPROVING ✓")
        elif total_delta > 0:
            print("Trend: REGRESSING ✗")
        else:
            print("Trend: STABLE")
    else:
        print("Need more data points for trend analysis.")


def main():
    parser = argparse.ArgumentParser(
        description="DB-AUTH-001 Governance Drift Detector"
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format"
    )
    parser.add_argument(
        "--pin",
        action="store_true",
        help="Generate memory PIN content for findings"
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Root directory to scan"
    )
    parser.add_argument(
        "--trend",
        action="store_true",
        help="Show drift trend over time (no scan)"
    )
    parser.add_argument(
        "--record",
        action="store_true",
        help="Record current drift count to history"
    )

    args = parser.parse_args()

    root = Path(args.root).resolve()

    # Trend-only mode
    if args.trend:
        show_trend(root)
        sys.exit(0)

    try:
        findings = scan_for_drift(root)
    except Exception as e:
        print(f"Error during scan: {e}", file=sys.stderr)
        sys.exit(2)

    # Count HIGH severity findings (scripts without guard)
    high_count = len([f for f in findings if f.severity == "HIGH"])

    # Track trend (will be used for regression detection)
    trend = None

    # Record drift if requested (do this before output so we have trend data)
    if args.record:
        trend = record_drift(root, high_count)

    if args.output == "json":
        output_json(findings)
    else:
        output_text(findings)

        # Show trend if we have history
        history = load_history(root)
        if history:
            print()
            print("=== Trend ===")
            if trend:
                if trend["previous"] is not None:
                    print(f"Previous: {trend['previous']}")
                    print(f"Current:  {trend['current']}")
                    print(f"Delta:    {trend['delta']:+d}")
                    print(f"Status:   {trend['trend']}")
                else:
                    print(f"Baseline established: {trend['current']}")
            else:
                last = history[-1]
                print(f"Last recorded: {last['count']} ({last['timestamp'][:10]})")
                print(f"Current scan:  {high_count}")
                print(f"(Use --record to save this count)")

    if args.pin and findings:
        print("\n" + "=" * 60)
        print("MEMORY PIN CONTENT (copy to docs/memory-pins/)")
        print("=" * 60 + "\n")
        print(generate_pin_content(findings))

    # Check for regression (HARD FAIL)
    if args.record and trend and trend["delta"] is not None and trend["delta"] > 0:
        print()
        print("=" * 60)
        print("REGRESSION DETECTED — HARD FAIL")
        print("=" * 60)
        print()
        print(f"Previous count: {trend['previous']}")
        print(f"Current count:  {trend['current']}")
        print(f"Increase:       +{trend['delta']}")
        print()
        print("DB-AUTH-001 requires monotonic decrease.")
        print("Drift count must NEVER increase.")
        print()
        print("This means someone added a DB-touching script")
        print("without understanding DB-AUTH-001.")
        print()
        print("ACTION REQUIRED:")
        print("  1. Identify the new script(s)")
        print("  2. Add proper _db_guard.py usage")
        print("  3. Re-run this detector")
        print()
        print("Reference: docs/governance/DB_AUTH_001_INVARIANT.md")
        sys.exit(3)

    # Exit with 1 if drift detected, 0 if clean or improving
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
