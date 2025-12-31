#!/usr/bin/env python3
"""SQLModel Pattern Linter v2.3 - Detect Unsafe Query Patterns

Enhanced with PIN-120 Test Suite Stabilization Prevention Mechanisms.

Patterns Detected:
1. DetachedInstanceError - ORM objects returned after session closes
2. Row tuple extraction issues
3. SQLModel version differences in .first() return type
4. Missing session.get() for direct ID lookups
5. Config value access with None values (PREV-9)
6. Migration SQL ON CONFLICT patterns (PREV-11)
7. Non-idempotent Prometheus metric registration (PREV-1)
8. Metric naming convention violations (PREV-2)
9. Concurrent claim SQL without FOR UPDATE SKIP LOCKED (PREV-6)
10. Test isolation fixture issues (PREV-5)
11. Cache timestamp initialization (PREV-4)
12. Async event loop lifecycle issues (PREV-12)
13. Timezone-naive datetime operations (PREV-20)

Usage:
    python scripts/ops/lint_sqlmodel_patterns.py [path]
    python scripts/ops/lint_sqlmodel_patterns.py backend/app/api/
    python scripts/ops/lint_sqlmodel_patterns.py --scan-all  # Full codebase scan

Exit codes:
    0 - No issues found
    1 - Issues found
    2 - Critical issues found (blocking)

RCA Reference: PIN-118 M24.2 Bug Fix, PIN-120 Test Suite Stabilization
"""

import re
import sys
from pathlib import Path
from typing import List
from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class LintIssue:
    file: str
    line: int
    pattern: str
    message: str
    suggestion: str
    severity: Severity = Severity.WARNING
    rule_id: str = ""


# =============================================================================
# RULE DEFINITIONS
# =============================================================================

UNSAFE_PATTERNS = [
    # =========================================================================
    # CATEGORY 1: Row Tuple Extraction Issues
    # =========================================================================
    {
        "id": "ROW001",
        "regex": r"(\w+)\s*=\s*session\.exec\([^)]+\)\.first\(\)\s*$",
        "message": "Potential Row tuple issue: .first() may return Row or model depending on SQLModel version",
        "suggestion": "Use: row = session.exec(stmt).first(); obj = row if isinstance(row, Model) else (row[0] if row else None)",
        "severity": Severity.WARNING,
        "exclude_if_followed_by": r"\[\s*0\s*\]",
    },
    {
        "id": "ROW002",
        "regex": r"for\s+\w+\s+in\s+session\.exec\([^)]+\)\.all\(\)",
        "message": "Unsafe: iterating .all() yields Row tuples, not model instances",
        "suggestion": "Use: for item in [r[0] for r in session.exec(stmt).all()]: OR use isinstance check",
        "severity": Severity.WARNING,
    },
    {
        "id": "ROW003",
        "regex": r"session\.exec\([^)]+\)\.first\(\)\.\w+",
        "message": "Unsafe: accessing attribute on .first() result may fail if Row tuple",
        "suggestion": "Extract model first: row = session.exec(stmt).first(); obj = row if isinstance(row, Model) else (row[0] if row else None)",
        "severity": Severity.ERROR,
    },
    {
        "id": "ROW004",
        "regex": r"session\.exec\([^)]*func\.(count|sum|avg|max|min)[^)]*\)\.one\(\)\s*$",
        "message": "Unsafe: .one() on aggregate returns Row tuple",
        "suggestion": "Use: result = session.exec(query).one(); value = result[0]",
        "severity": Severity.WARNING,
    },
    # =========================================================================
    # CATEGORY 2: DetachedInstanceError Prevention (NEW - from M24 RCA)
    # =========================================================================
    {
        "id": "DETACH001",
        "regex": r"def\s+\w+\([^)]*\)\s*->\s*(?:tuple\[)?(?:User|Tenant|Agent|Run|Workflow)\b",
        "message": "Function returns ORM model - may cause DetachedInstanceError if session closes",
        "suggestion": "Return dict instead of ORM object, or ensure caller has active session",
        "severity": Severity.WARNING,
        "context_check": "with_session_block",
    },
    {
        "id": "DETACH002",
        "regex": r"with\s+Session\([^)]*\)\s+as\s+session:\s*\n(?:[^\n]*\n)*?\s*return\s+(?!{)(?!\[)(?!None)(?!True)(?!False)(?!\d)(\w+)\s*$",
        "message": "Returning variable from 'with Session()' block - potential DetachedInstanceError",
        "suggestion": "Extract values to dict before returning: return {'id': obj.id, 'name': obj.name, ...}",
        "severity": Severity.ERROR,
    },
    {
        "id": "DETACH003",
        "regex": r"session\.commit\(\)\s*\n\s*session\.refresh\(\w+\)\s*\n(?:[^\n]*\n)*?\s*return\s+\w+",
        "message": "Returning refreshed object - may detach when session closes",
        "suggestion": "Extract to dict after refresh: user_data = {'id': user.id, ...}; return user_data",
        "severity": Severity.WARNING,
    },
    # =========================================================================
    # CATEGORY 3: session.get() vs select() Pattern
    # =========================================================================
    {
        "id": "GET001",
        "regex": r"select\(\w+\)\.where\(\w+\.id\s*==\s*\w+\)",
        "message": "Use session.get() for direct ID lookup instead of select().where()",
        "suggestion": "Replace with: obj = session.get(Model, id) - simpler and returns model directly",
        "severity": Severity.WARNING,
    },
    # =========================================================================
    # CATEGORY 4: Raw SQL Safety
    # =========================================================================
    {
        "id": "SQL001",
        "regex": r"session\.exec\s*\(\s*text\s*\([^)]+\)\s*,\s*\{",
        "message": "Unsafe: session.exec() does not accept params dict. Only takes 1 argument.",
        "suggestion": "Use session.execute(text(...), params) for raw SQL with parameters",
        "severity": Severity.ERROR,
    },
    # =========================================================================
    # CATEGORY 5: Session Scope Issues
    # =========================================================================
    {
        "id": "SCOPE001",
        "regex": r"(\w+)\s*=\s*session\.(get|exec)\([^)]+\)[^\n]*\n(?:[^\n]*\n)*?(?=\n\s*#|def\s|\nclass\s|\Z).*\1\.\w+",
        "message": "Accessing ORM object attributes outside session context",
        "suggestion": "Ensure all attribute access happens within the session block",
        "severity": Severity.WARNING,
        "multiline": True,
    },
    # =========================================================================
    # CATEGORY 6: Config Value Access (PIN-120 PREV-9)
    # =========================================================================
    {
        "id": "CFG001",
        "regex": r"if\s+['\"](\w+)['\"]\s+in\s+(\w+):\s*\n[^\n]*\2\[['\"]?\1['\"]?\]\s*\*",
        "message": "Unsafe: 'key' in dict check followed by multiplication - value may be None",
        "suggestion": "Use: if config.get('key') is not None: value = config['key'] * multiplier",
        "severity": Severity.WARNING,
        "multiline": True,
    },
    {
        "id": "CFG002",
        "regex": r"(\w+)\s*=\s*(\w+)\s+or\s+os\.environ\.get\(",
        "message": "Potential issue: empty string '' is falsy, will fall through to env var",
        "suggestion": "Use: value = param if param is not None else os.environ.get('KEY')",
        "severity": Severity.WARNING,
    },
    # =========================================================================
    # CATEGORY 7: Migration SQL Patterns (PIN-120 PREV-11)
    # =========================================================================
    {
        "id": "MIG001",
        "regex": r"ON\s+CONFLICT\s+ON\s+CONSTRAINT\s+(\w+)",
        "message": "ON CONFLICT ON CONSTRAINT requires actual CONSTRAINT, not UNIQUE INDEX",
        "suggestion": "For partial unique indexes, use: ON CONFLICT (column) WHERE condition",
        "severity": Severity.WARNING,
    },
    # =========================================================================
    # CATEGORY 8: Prometheus Metrics (PIN-120 PREV-1, PREV-2)
    # =========================================================================
    {
        "id": "PROM001",
        "regex": r"^(\w+)\s*=\s*(Counter|Gauge|Histogram)\s*\(\s*['\"](\w+)['\"]",
        "message": "Non-idempotent Prometheus metric - may cause 'Duplicated timeseries' in tests",
        "suggestion": "Use idempotent registration: get_or_create_counter() from app.utils.metrics_helpers",
        "severity": Severity.WARNING,
        "multiline": True,
    },
    {
        "id": "PROM002",
        "regex": r"(Counter|Gauge|Histogram)\s*\(\s*['\"](?![\w_]+_)(\w+)['\"]",
        "message": "Metric name should be prefixed with module name to avoid conflicts",
        "suggestion": "Use format: {module}_{metric_name}_total (e.g., drift_detector_detected_total)",
        "severity": Severity.WARNING,
    },
    # =========================================================================
    # CATEGORY 9: Concurrent Claim SQL Patterns (PIN-120 PREV-6)
    # =========================================================================
    {
        "id": "CONC001",
        "regex": r"UPDATE\s+\w+\s+SET\s+\w+\s*=\s*['\"]?(pending|executing|processing)['\"]?.*WHERE",
        "message": "Status UPDATE without FOR UPDATE SKIP LOCKED may cause race conditions",
        "suggestion": "Use CTE: WITH claimed AS (SELECT ... FOR UPDATE SKIP LOCKED) UPDATE ... FROM claimed",
        "severity": Severity.WARNING,
        "multiline": True,
    },
    # =========================================================================
    # CATEGORY 10: Test Isolation (PIN-120 PREV-5)
    # =========================================================================
    {
        "id": "TEST001",
        "regex": r"def\s+test_\w+.*:\s*\n(?:[^\n]*\n)*?session\.add\(",
        "message": "Test adds data to session without cleanup fixture",
        "suggestion": "Use db_session fixture with pre/post cleanup: DELETE FROM table WHERE type = 'test'",
        "severity": Severity.WARNING,
        "multiline": True,
    },
    # =========================================================================
    # CATEGORY 11: Cache Initialization (PIN-120 PREV-4)
    # =========================================================================
    {
        "id": "CACHE001",
        "regex": r"def\s+_?load_\w+cache\w*\([^)]*\).*:\s*\n(?:[^\n]*\n)*?(?!.*_cache_loaded_at)",
        "message": "Cache loading method should set _cache_loaded_at timestamp",
        "suggestion": "Add: self._cache_loaded_at = datetime.now(timezone.utc) at start of method",
        "severity": Severity.WARNING,
        "multiline": True,
    },
    # =========================================================================
    # CATEGORY 12: Async Event Loop (PIN-120 PREV-12)
    # =========================================================================
    {
        "id": "ASYNC001",
        "regex": r"create_async_engine\([^)]*\)\s*$",
        "message": "Module-level async engine may cause event loop lifecycle issues in tests",
        "suggestion": "Use fixture-scoped engine or mark tests with @pytest.mark.flaky",
        "severity": Severity.WARNING,
    },
    # =========================================================================
    # CATEGORY 13: Timezone-Aware Datetime Operations (PIN-120 PREV-20)
    # =========================================================================
    {
        "id": "TZ001",
        "regex": r"datetime\.now\(timezone\.utc\)\s*-\s*\w+\.\w+",
        "message": "Subtracting database datetime from timezone-aware datetime may fail (naive vs aware)",
        "suggestion": "Ensure DB datetime is aware: dt_aware = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt",
        "severity": Severity.WARNING,
    },
    {
        "id": "TZ002",
        "regex": r"\w+\.\w+\s*-\s*datetime\.now\(timezone\.utc\)",
        "message": "Subtracting timezone-aware datetime from database datetime may fail (naive vs aware)",
        "suggestion": "Ensure DB datetime is aware: dt_aware = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt",
        "severity": Severity.WARNING,
    },
    {
        "id": "TZ003",
        "regex": r"\.total_seconds\(\)\s*\*\s*1000.*started_at|started_at.*\.total_seconds\(\)\s*\*\s*1000",
        "message": "Duration calculation with started_at may involve naive datetime from DB",
        "suggestion": "Ensure started_at is timezone-aware before subtraction",
        "severity": Severity.WARNING,
    },
]

# Safe patterns that indicate proper handling
SAFE_PATTERNS = [
    r"row\s*=\s*session\.exec\([^)]+\)\.first\(\)",  # Using 'row' variable name
    r"result\s*=\s*session\.exec\([^)]+\)\.first\(\)",  # Using 'result' variable name
    r"row\[0\]\s+if\s+row\s+else\s+None",  # Proper extraction pattern
    r"result\[0\]\s+if\s+result\s+else\s+None",  # Proper extraction pattern
    r"r\[0\]\s+for\s+r\s+in",  # List comprehension extraction
    r"isinstance\(\w+,\s*\w+\)\s*else\s*\w+\[0\]",  # Type-safe extraction
    r"from app\.utils\.db_helpers import",  # Using safe helpers
    r"from app\.db_helpers import",  # Using safe helpers (alt path)
    r"query_one\(|query_all\(|query_scalar\(",  # Using helper functions
    r"session\.execute\s*\(\s*text\s*\(",  # Correct: session.execute() for raw SQL
    r"exec_sql\(",  # Helper function for raw SQL execution
    r"hasattr\(result,",  # Type checking pattern
    r"isinstance\(result,",  # Type checking pattern
    r"user_data\s*=\s*\{",  # Dict extraction pattern
    r"return\s*\{[^}]*\}",  # Returning dict (safe)
    r"->.*dict",  # Return type annotation is dict (safe)
    r"->.*Dict\[",  # Return type annotation is Dict (safe)
    r"session\.get\(\w+,",  # Using session.get() (safe for ID lookup)
    # PIN-120 PREV-9: Config value access patterns (safe)
    r"\.get\(['\"]?\w+['\"]?\)\s+is\s+not\s+None",  # Proper None check
    r"if\s+\w+\s+is\s+not\s+None\s*:",  # Explicit None check before use
    r"param\s+if\s+param\s+is\s+not\s+None\s+else",  # Ternary with None check
    # PIN-120 PREV-11: Migration patterns (safe when proper syntax used)
    r"ON\s+CONFLICT\s+\(\w+\)\s+WHERE",  # Correct partial index syntax
    # PIN-120 PREV-1: Idempotent Prometheus registration (safe patterns)
    r"get_or_create_counter\(|get_or_create_gauge\(|get_or_create_histogram\(",
    r"_find_existing_metric\(",
    r"_get_or_create_\w+\(",
    # PIN-120 PREV-6: Concurrent claim SQL (safe patterns)
    r"FOR\s+UPDATE\s+SKIP\s+LOCKED",
    r"WITH\s+claimed\s+AS",
    # PIN-120 PREV-5: Test isolation (safe patterns)
    r"@pytest\.fixture.*\n.*DELETE\s+FROM",  # Cleanup fixtures
    r"yield\s+session.*\n.*DELETE\s+FROM",
    # PIN-120 PREV-12: Async event loop (safe patterns)
    r"@pytest\.fixture\(scope=['\"]module['\"]\).*\n.*event_loop",
    r"pytest\.mark\.flaky",
    # DETACH002 safe patterns - scalar returns and generator patterns
    r"return\s+\w+_id\s*$",  # Returning scalar ID (e.g., agent_id, record_id)
    r"yield\s+session",  # Generator pattern for dependency injection
    r"def\s+get_session\s*\(",  # FastAPI dependency get_session function
    r"\.all\(\)\s*\)",  # .all() followed by closing paren (len(result.all()))
    r"len\s*\(\s*\w+\s*\)",  # len() call (scalar result)
    r"\w+_id\s*=\s*\w+\.id",  # Extracting ID to variable before return
    r"#.*Extract.*ID.*session",  # Comment indicating safe extraction
    r"#.*returns scalar",  # Comment indicating scalar return
    r"nova_runs_queued\.set",  # Prometheus metric set (scalar)
    # DETACH003 safe patterns - DI-managed sessions and Pydantic returns
    r"#.*DI-managed",  # Comment indicating DI-managed session
    r"#.*Safe:.*session",  # Comment indicating safe pattern
    r"#.*stays\s+open",  # Comment about session staying open
    r"return\s+\w+Status\(",  # Returning Pydantic Status model
    r"return\s+\w+Response\(",  # Returning Pydantic Response model
    r"session:\s*Session\s*=\s*Depends",  # DI session parameter
    # ASYNC001 safe patterns - intentional async engine configurations
    r"def\s+__init__\s*\([^)]*\):",  # Engine inside class __init__ is managed
    # PIN-120 PREV-20: Timezone-aware datetime patterns (safe)
    r"\.replace\(tzinfo=timezone\.utc\)",  # Explicit timezone assignment
    r"if\s+\w+\.tzinfo\s+is\s+None",  # Checking for naive datetime
    r"ensure_utc\(",  # Helper function for timezone
    r"_aware\s*=",  # Using _aware suffix for aware datetime vars
    r"#.*timezone.aware|#.*tzinfo",  # Comment indicating awareness
    r"self\.engine\s*=\s*create_async_engine",  # Class-scoped engine
    r"async_engine:\s*AsyncEngine",  # Typed module engine (intentional)
    r"pool_size\s*=",  # Production engine with pool config
]

# Files/directories to skip
SKIP_PATHS = [
    "__pycache__",
    ".venv",
    "alembic/versions",
    "node_modules",
    ".git",
    "dist",
    "build",
]


def is_safe_context(content: str, match_start: int, match_end: int) -> bool:
    """Check if the match is in a safe context."""
    context_start = max(0, match_start - 500)
    context_end = min(len(content), match_end + 500)
    context = content[context_start:context_end]

    for safe in SAFE_PATTERNS:
        if re.search(safe, context):
            return True
    return False


def check_with_session_block(content: str, match_start: int) -> bool:
    """Check if match is inside a 'with Session()' block."""
    before = content[:match_start]
    # Find last 'with Session' and matching 'def'
    last_with = before.rfind("with Session")
    last_def = before.rfind("\ndef ")

    # If with Session is after def, we're inside a with block
    return last_with > last_def if last_with > 0 else False


def lint_file(filepath: Path, verbose: bool = False) -> List[LintIssue]:
    """Lint a single Python file for unsafe SQLModel patterns."""
    issues = []

    try:
        content = filepath.read_text()
    except Exception:
        return []

    for pattern_def in UNSAFE_PATTERNS:
        regex = pattern_def["regex"]
        flags = re.MULTILINE
        if pattern_def.get("multiline"):
            flags |= re.DOTALL

        for match in re.finditer(regex, content, flags):
            line_num = content[: match.start()].count("\n") + 1

            # Check for exclusions
            if "exclude_if_followed_by" in pattern_def:
                next_chars = content[match.end() : match.end() + 20]
                if re.match(pattern_def["exclude_if_followed_by"], next_chars):
                    continue

            # Check context requirements
            if pattern_def.get("context_check") == "with_session_block":
                if not check_with_session_block(content, match.start()):
                    continue

            # Check if in safe context
            if is_safe_context(content, match.start(), match.end()):
                continue

            pattern_text = match.group()
            if len(pattern_text) > 80:
                pattern_text = pattern_text[:80] + "..."

            issues.append(
                LintIssue(
                    file=str(filepath),
                    line=line_num,
                    pattern=pattern_text.replace("\n", "\\n"),
                    message=pattern_def["message"],
                    suggestion=pattern_def["suggestion"],
                    severity=pattern_def.get("severity", Severity.WARNING),
                    rule_id=pattern_def.get("id", ""),
                )
            )

    return issues


def lint_directory(path: Path, verbose: bool = False) -> List[LintIssue]:
    """Lint all Python files in a directory."""
    issues = []

    for filepath in path.rglob("*.py"):
        if any(skip in str(filepath) for skip in SKIP_PATHS):
            continue

        file_issues = lint_file(filepath, verbose)
        issues.extend(file_issues)

        if verbose and file_issues:
            print(f"  📂 {filepath}: {len(file_issues)} issue(s)")

    return issues


def print_summary(issues: List[LintIssue]):
    """Print summary grouped by rule."""
    by_rule = {}
    for issue in issues:
        rule = issue.rule_id or "UNKNOWN"
        if rule not in by_rule:
            by_rule[rule] = []
        by_rule[rule].append(issue)

    print("\n📊 Summary by Rule:")
    print("-" * 50)
    for rule, rule_issues in sorted(by_rule.items()):
        severity = rule_issues[0].severity.value.upper()
        print(f"  {rule} ({severity}): {len(rule_issues)} occurrence(s)")


def main():
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    scan_all = "--scan-all" in sys.argv

    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    if scan_all:
        path = Path("backend")
    else:
        path = Path(args[0]) if args else Path("backend/app")

    print("=" * 70)
    print("SQLModel Pattern Linter v2.2 - Detecting Unsafe Query Patterns")
    print("  PIN-120 Test Suite Stabilization Prevention Mechanisms")
    print("=" * 70)
    print()
    print("Rules enforced:")
    print("  ROW001-004:    Row tuple extraction issues")
    print("  DETACH001-003: DetachedInstanceError prevention")
    print("  GET001:        session.get() recommendations")
    print("  SQL001:        Raw SQL safety")
    print("  SCOPE001:      Session scope issues")
    print("  CFG001-002:    Config value access patterns (PREV-9)")
    print("  MIG001:        Migration ON CONFLICT patterns (PREV-11)")
    print("  PROM001-002:   Prometheus metric registration (PREV-1, PREV-2)")
    print("  CONC001:       Concurrent claim SQL patterns (PREV-6)")
    print("  TEST001:       Test isolation fixtures (PREV-5)")
    print("  CACHE001:      Cache timestamp initialization (PREV-4)")
    print("  ASYNC001:      Async event loop lifecycle (PREV-12)")
    print("  TZ001-003:     Timezone-naive datetime operations (PREV-20)")
    print()

    if path.is_file():
        issues = lint_file(path, verbose)
    else:
        print(f"Scanning: {path}")
        issues = lint_directory(path, verbose)

    if not issues:
        print("\n✅ No unsafe SQLModel patterns detected!")
        print()
        print("Safe patterns in use:")
        print("  - row = session.exec(stmt).first()")
        print("    obj = row if isinstance(row, Model) else (row[0] if row else None)")
        print("  - session.get(Model, id) for direct ID lookup")
        print("  - Return dicts from functions to avoid DetachedInstanceError")
        print("  - session.execute(text(...), params) for raw SQL")
        sys.exit(0)

    # Separate by severity
    critical = [i for i in issues if i.severity == Severity.CRITICAL]
    errors = [i for i in issues if i.severity == Severity.ERROR]
    warnings = [i for i in issues if i.severity == Severity.WARNING]

    print(f"\n⚠️  Found {len(issues)} potential issue(s):")
    print(f"   🔴 Critical: {len(critical)}")
    print(f"   🟠 Error: {len(errors)}")
    print(f"   🟡 Warning: {len(warnings)}")
    print()

    for issue in sorted(issues, key=lambda x: (x.severity.value, x.file, x.line)):
        severity_icon = {"critical": "🔴", "error": "🟠", "warning": "🟡"}[
            issue.severity.value
        ]
        print(f"{severity_icon} [{issue.rule_id}] {issue.file}:{issue.line}")
        print(f"   Pattern: {issue.pattern}")
        print(f"   Issue: {issue.message}")
        print(f"   Fix: {issue.suggestion}")
        print()

    print_summary(issues)

    print()
    print("-" * 70)
    print("To fix issues, use these patterns:")
    print()
    print("1. Row tuple extraction:")
    print("   row = session.exec(stmt).first()")
    print("   obj = row if isinstance(row, Model) else (row[0] if row else None)")
    print()
    print("2. Prevent DetachedInstanceError:")
    print("   # Extract to dict before session closes")
    print("   user_data = {'id': user.id, 'email': user.email, ...}")
    print("   return user_data")
    print()
    print("3. Use session.get() for ID lookup:")
    print("   user = session.get(User, user_id)  # Returns model directly")
    print()
    print("4. Import helpers:")
    print("   from app.utils.db_helpers import query_one, query_all")
    print()
    print("5. Config value access (PIN-120 PREV-9):")
    print("   # WRONG: if 'key' in config: val = config['key'] * 10")
    print("   # RIGHT: if config.get('key') is not None: val = config['key'] * 10")
    print()
    print("6. Migration ON CONFLICT (PREV-11):")
    print("   # For partial unique indexes, use column syntax:")
    print("   # ON CONFLICT (column) WHERE condition DO UPDATE ...")
    print("   # NOT: ON CONFLICT ON CONSTRAINT index_name ...")
    print()
    print("7. Prometheus metrics (PREV-1, PREV-2):")
    print("   # Use idempotent registration:")
    print("   from app.utils.metrics_helpers import get_or_create_counter")
    print("   # Prefix with module name: drift_detector_detected_total")
    print()
    print("8. Concurrent claim SQL (PREV-6):")
    print("   # Use FOR UPDATE SKIP LOCKED in CTE:")
    print("   WITH claimed AS (SELECT ... FOR UPDATE SKIP LOCKED) UPDATE ...")
    print()
    print("9. Cache initialization (PREV-4):")
    print("   # Set timestamp in cache load methods:")
    print("   self._cache_loaded_at = datetime.now(timezone.utc)")
    print()
    print("10. Async event loop (PREV-12):")
    print("    # Use module-scoped event_loop fixture or mark flaky:")
    print("    @pytest.fixture(scope='module') def event_loop(): ...")
    print()
    print("11. Timezone-aware datetime (PREV-20):")
    print("    # Ensure DB datetime is timezone-aware before subtraction:")
    print(
        "    started_at_aware = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt"
    )
    print(
        "    duration = (datetime.now(timezone.utc) - started_at_aware).total_seconds()"
    )
    print()

    # Exit code based on severity
    if critical:
        sys.exit(2)
    elif errors:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
