#!/usr/bin/env python3
"""
Mypy Autofix Engine - Automatically applies type fixes.

This engine:
1. Runs mypy and captures errors
2. Parses error codes and locations
3. Applies appropriate fixes from macros.py
4. Ensures required imports exist
5. Reports what was changed

Supported fix categories:
- union-attr: Optional guards (assert x is not None)
- no-any-return: Return type wrappers (bool, int, float, cast)
- attr-defined: SQLAlchemy/Pydantic casts
- misc: Prometheus/callable fixes

Usage:
    python tools/mypy_autofix/apply.py              # Auto-fix all
    python tools/mypy_autofix/apply.py --zone-a    # Zone A only
    python tools/mypy_autofix/apply.py --dry-run   # Preview changes
    python tools/mypy_autofix/apply.py --report    # Show fix report
"""

import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Set

# Zone A critical paths
ZONE_A_PATHS = [
    "app/policy/ir/",
    "app/policy/ast/",
    "app/policy/runtime/deterministic_engine.py",
    "app/workflow/engine.py",
    "app/workflow/canonicalize.py",
    "app/services/certificate.py",
    "app/services/evidence_report.py",
    "app/traces/pg_store.py",
    "app/utils/deterministic.py",
    "app/utils/canonical_json.py",
]

ZONE_B_PATHS = [
    "app/api/",
    "app/skills/",
    "app/agents/",
    "app/services/",
    "app/planner/",
    "app/integrations/",
    "app/memory/",
    "app/auth/",
    "app/policy/validators/",
    "app/policy/optimizer/",
]

# SQLAlchemy method patterns (false positives)
# These appear in mypy error messages as: "X" has no attribute "METHOD"
SQLALCHEMY_ATTR_PATTERNS = [
    '"desc"',
    '"asc"',
    '"ilike"',
    '"like"',
    '"in_"',
    '"notin_"',
    '"between"',
    '"is_"',
    '"isnot"',
    '"contains"',
    '"startswith"',
    '"endswith"',
    '"label"',
    '"op"',
    '"nullsfirst"',
    '"nullslast"',
]

# Prometheus metric patterns
PROMETHEUS_PATTERNS = ["Counter", "Histogram", "Gauge", "Summary"]

# Pydantic boundary patterns
PYDANTIC_PATTERNS = [".dict(", ".parse_obj(", ".model_dump("]

# Error parsing regex
ERROR_RE = re.compile(r"(?P<file>.+?):(?P<line>\d+)(?::(?P<col>\d+))?: error: (?P<msg>.+?) \[(?P<code>.+?)\]")


@dataclass
class MypyError:
    """Parsed mypy error."""

    file: str
    line: int
    col: Optional[int]
    msg: str
    code: str

    @property
    def zone(self) -> str:
        """Determine which zone this file belongs to."""
        for path in ZONE_A_PATHS:
            if self.file.startswith(path):
                return "A"
        for path in ZONE_B_PATHS:
            if self.file.startswith(path):
                return "B"
        return "C"

    def matches_pattern(self, patterns: list[str]) -> bool:
        """Check if error message matches any pattern."""
        return any(p in self.msg for p in patterns)


@dataclass
class FixResult:
    """Result of applying a fix."""

    file: str
    line: int
    code: str
    fix_applied: str
    success: bool
    message: str = ""
    category: str = ""


@dataclass
class FixReport:
    """Summary of all fixes applied."""

    total_errors: int = 0
    fixes_applied: int = 0
    fixes_skipped: int = 0
    fixes_failed: int = 0
    results: list[FixResult] = field(default_factory=list)
    files_modified: Set[str] = field(default_factory=set)

    def print_summary(self) -> None:
        """Print fix summary."""
        print("\n" + "=" * 70)
        print("  MYPY AUTOFIX REPORT")
        print("=" * 70)
        print(f"  Total errors:     {self.total_errors}")
        print(f"  Fixes applied:    {self.fixes_applied}")
        print(f"  Fixes skipped:    {self.fixes_skipped}")
        print(f"  Fixes failed:     {self.fixes_failed}")
        print(f"  Files modified:   {len(self.files_modified)}")
        print("=" * 70)

        if self.results:
            # Group by category
            by_category: dict[str, list[FixResult]] = {}
            for r in self.results:
                cat = r.category or r.code
                by_category.setdefault(cat, []).append(r)

            print("\n  Applied fixes by category:")
            for cat, results in sorted(by_category.items()):
                print(f"\n    [{cat}] ({len(results)} fixes)")
                for r in results[:5]:
                    status = "+" if r.success else "x"
                    print(f"      [{status}] {r.file}:{r.line} -> {r.fix_applied[:50]}")
                if len(results) > 5:
                    print(f"      ... and {len(results) - 5} more")


def run_mypy(zone_a_only: bool = False) -> list[str]:
    """Run mypy and capture output."""
    cmd = ["mypy", "app/", "--ignore-missing-imports", "--show-error-codes"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip().split("\n") if result.stdout else []


def parse_errors(lines: list[str], zone_a_only: bool = False) -> list[MypyError]:
    """Parse mypy output into structured errors."""
    errors = []
    for line in lines:
        match = ERROR_RE.match(line)
        if not match:
            continue

        error = MypyError(
            file=match.group("file"),
            line=int(match.group("line")),
            col=int(match.group("col")) if match.group("col") else None,
            msg=match.group("msg"),
            code=match.group("code"),
        )

        if zone_a_only and error.zone != "A":
            continue

        errors.append(error)

    return errors


# =============================================================================
# VARIABLE EXTRACTION
# =============================================================================


def extract_variable_from_line(path: Path, line_no: int) -> Optional[str]:
    """Extract variable being accessed from the source line."""
    try:
        lines = path.read_text().splitlines()
        idx = line_no - 1
        if idx < 0 or idx >= len(lines):
            return None

        line = lines[idx].strip()

        # Pattern: var.method() or var.attr
        match = re.match(r".*?(\w+)\.\w+", line)
        if match:
            var = match.group(1)
            if var not in ("self", "cls", "return", "if", "else", "and", "or", "not"):
                return var

        # Pattern: if var is not None
        match = re.search(r"(\w+)\s+is\s+not\s+None", line)
        if match:
            return match.group(1)

        return None

    except Exception:
        return None


def extract_variable_from_msg(msg: str) -> Optional[str]:
    """Extract variable name from error message (fallback)."""
    if 'Item "None"' in msg:
        return None

    match = re.search(r'Item "([^"]+)"', msg)
    if match and match.group(1) != "None":
        return match.group(1)

    return None


# =============================================================================
# IMPORT GUARD
# =============================================================================


def ensure_typing_imports(path: Path, needs_cast: bool = False, needs_any: bool = False) -> bool:
    """Ensure file has required typing imports. Returns True if modified."""
    try:
        content = path.read_text()
        lines = content.splitlines()

        # Check what's already imported
        has_any = bool(re.search(r"from typing import.*\bAny\b", content))
        has_cast = bool(re.search(r"from typing import.*\bcast\b", content))

        needs_modification = False
        if needs_any and not has_any:
            needs_modification = True
        if needs_cast and not has_cast:
            needs_modification = True

        if not needs_modification:
            return False

        # Find existing typing import
        for i, line in enumerate(lines):
            if line.startswith("from typing import"):
                imports = re.search(r"from typing import (.+)", line)
                if imports:
                    current = [x.strip() for x in imports.group(1).split(",")]
                    if needs_any and "Any" not in current:
                        current.append("Any")
                    if needs_cast and "cast" not in current:
                        current.append("cast")
                    current.sort()
                    lines[i] = f"from typing import {', '.join(current)}"
                    path.write_text("\n".join(lines) + "\n")
                    return True

        # No existing typing import - add one after other imports
        import_line = "from typing import "
        needed = []
        if needs_any:
            needed.append("Any")
        if needs_cast:
            needed.append("cast")
        import_line += ", ".join(sorted(needed))

        # Find where to insert
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                insert_idx = i + 1
            elif line.strip() and not line.startswith("#") and insert_idx > 0:
                break

        lines.insert(insert_idx, import_line)
        path.write_text("\n".join(lines) + "\n")
        return True

    except Exception:
        return False


# =============================================================================
# FIX HANDLERS
# =============================================================================


def is_inside_multiline_expr(lines: list[str], idx: int) -> bool:
    """Check if line is inside a multi-line expression (can't insert statement)."""
    # Count open parens/brackets from start of file to this line
    open_parens = 0
    open_brackets = 0
    open_braces = 0

    for i in range(idx):
        line = lines[i]
        # Skip strings (rough heuristic)
        in_string = False
        for j, ch in enumerate(line):
            if ch in "\"'":
                in_string = not in_string
            if not in_string:
                if ch == "(":
                    open_parens += 1
                elif ch == ")":
                    open_parens -= 1
                elif ch == "[":
                    open_brackets += 1
                elif ch == "]":
                    open_brackets -= 1
                elif ch == "{":
                    open_braces += 1
                elif ch == "}":
                    open_braces -= 1

    return open_parens > 0 or open_brackets > 0 or open_braces > 0


def is_continuation_line(lines: list[str], idx: int) -> bool:
    """Check if line is a continuation (elif/else/except/finally) - can't insert before."""
    if idx >= len(lines):
        return False
    stripped = lines[idx].lstrip()
    return stripped.startswith(("elif ", "else:", "except ", "except:", "finally:"))


def apply_guard(path: Path, line_no: int, var: str, dry_run: bool = False) -> FixResult:
    """Apply an assert guard before the problematic line."""
    try:
        lines = path.read_text().splitlines()
        idx = line_no - 1

        if idx < 0 or idx >= len(lines):
            return FixResult(
                file=str(path),
                line=line_no,
                code="union-attr",
                fix_applied="guard",
                success=False,
                message="Line out of range",
            )

        # Don't insert inside multi-line expressions (would cause syntax error)
        if is_inside_multiline_expr(lines, idx):
            return FixResult(
                file=str(path),
                line=line_no,
                code="union-attr",
                fix_applied="guard",
                success=False,
                message="Inside multi-line expression",
                category="guard",
            )

        # Don't insert before elif/else/except/finally (breaks control flow)
        if is_continuation_line(lines, idx):
            return FixResult(
                file=str(path),
                line=line_no,
                code="union-attr",
                fix_applied="guard",
                success=False,
                message="Before continuation line",
                category="guard",
            )

        indent_match = re.match(r"(\s*)", lines[idx])
        indent = indent_match.group(1) if indent_match else ""
        guard = f"{indent}assert {var} is not None"

        # Check if guard already exists
        if idx > 0 and f"assert {var} is not None" in lines[idx - 1]:
            return FixResult(
                file=str(path),
                line=line_no,
                code="union-attr",
                fix_applied="guard (exists)",
                success=True,
                category="guard",
            )

        if not dry_run:
            lines.insert(idx, guard)
            path.write_text("\n".join(lines) + "\n")

        return FixResult(
            file=str(path),
            line=line_no,
            code="union-attr",
            fix_applied=f"assert {var} is not None",
            success=True,
            category="guard",
        )

    except Exception as e:
        return FixResult(
            file=str(path),
            line=line_no,
            code="union-attr",
            fix_applied="guard",
            success=False,
            message=str(e),
        )


def apply_bool_wrap(path: Path, line_no: int, dry_run: bool = False) -> FixResult:
    """Wrap return expression in bool()."""
    try:
        lines = path.read_text().splitlines()
        idx = line_no - 1

        if idx < 0 or idx >= len(lines):
            return FixResult(
                file=str(path),
                line=line_no,
                code="no-any-return",
                fix_applied="bool_wrap",
                success=False,
                message="Line out of range",
            )

        line = lines[idx]
        match = re.match(r"(\s*)return\s+(.+)", line)
        if not match:
            return FixResult(
                file=str(path),
                line=line_no,
                code="no-any-return",
                fix_applied="bool_wrap",
                success=False,
                message="Not a return statement",
            )

        indent = match.group(1)
        expr = match.group(2)

        if expr.startswith("bool("):
            return FixResult(
                file=str(path),
                line=line_no,
                code="no-any-return",
                fix_applied="bool_wrap (exists)",
                success=True,
                category="bool_wrap",
            )

        if not dry_run:
            lines[idx] = f"{indent}return bool({expr})"
            path.write_text("\n".join(lines) + "\n")

        return FixResult(
            file=str(path),
            line=line_no,
            code="no-any-return",
            fix_applied=f"bool({expr[:30]}...)" if len(expr) > 30 else f"bool({expr})",
            success=True,
            category="bool_wrap",
        )

    except Exception as e:
        return FixResult(
            file=str(path),
            line=line_no,
            code="no-any-return",
            fix_applied="bool_wrap",
            success=False,
            message=str(e),
        )


def apply_int_wrap(path: Path, line_no: int, dry_run: bool = False) -> FixResult:
    """Wrap return expression in int()."""
    try:
        lines = path.read_text().splitlines()
        idx = line_no - 1
        line = lines[idx]

        match = re.match(r"(\s*)return\s+(.+)", line)
        if not match:
            return FixResult(
                file=str(path),
                line=line_no,
                code="no-any-return",
                fix_applied="int_wrap",
                success=False,
                message="Not a return statement",
            )

        indent = match.group(1)
        expr = match.group(2)

        if expr.startswith("int("):
            return FixResult(
                file=str(path),
                line=line_no,
                code="no-any-return",
                fix_applied="int_wrap (exists)",
                success=True,
                category="int_wrap",
            )

        if not dry_run:
            lines[idx] = f"{indent}return int({expr})"
            path.write_text("\n".join(lines) + "\n")

        return FixResult(
            file=str(path),
            line=line_no,
            code="no-any-return",
            fix_applied=f"int({expr[:30]})",
            success=True,
            category="int_wrap",
        )

    except Exception as e:
        return FixResult(
            file=str(path),
            line=line_no,
            code="no-any-return",
            fix_applied="int_wrap",
            success=False,
            message=str(e),
        )


def apply_sqlalchemy_cast(path: Path, line_no: int, dry_run: bool = False) -> FixResult:
    """Cast SQLAlchemy expression to Any.

    Transforms patterns like:
        .order_by(Model.col.desc())  ->  .order_by(cast(Any, Model.col).desc())
        x = y.ilike(...)  ->  x = cast(Any, y).ilike(...)
    """
    try:
        lines = path.read_text().splitlines()
        idx = line_no - 1
        line = lines[idx]

        # Skip if already has cast
        if "cast(Any," in line:
            return FixResult(
                file=str(path),
                line=line_no,
                code="attr-defined",
                fix_applied="sa_cast (exists)",
                success=True,
                category="sqlalchemy",
            )

        # Find pattern: something.method() where method is SQLAlchemy
        # Look for: VAR.method( or VAR.attr
        sa_methods = [
            "desc",
            "asc",
            "ilike",
            "like",
            "in_",
            "notin_",
            "between",
            "is_",
            "isnot",
            "contains",
            "startswith",
            "endswith",
            "label",
            "op",
            "nullsfirst",
            "nullslast",
        ]

        modified = False
        new_line = line
        for method in sa_methods:
            # Pattern: word.method( -> cast(Any, word).method(
            pattern = rf"(\b\w+(?:\.\w+)*)\.({method})\("
            replacement = r"cast(Any, \1).\2("
            new_line_candidate = re.sub(pattern, replacement, new_line)
            if new_line_candidate != new_line:
                new_line = new_line_candidate
                modified = True
                break

        if modified:
            if not dry_run:
                lines[idx] = new_line
                path.write_text("\n".join(lines) + "\n")
                ensure_typing_imports(path, needs_cast=True, needs_any=True)

            return FixResult(
                file=str(path),
                line=line_no,
                code="attr-defined",
                fix_applied=f"cast(Any, expr).{method}()",
                success=True,
                category="sqlalchemy",
            )

        # Could not auto-fix - add # type: ignore as fallback
        if "# type: ignore" not in line:
            if not dry_run:
                lines[idx] = line.rstrip() + "  # type: ignore[attr-defined]"
                path.write_text("\n".join(lines) + "\n")
            return FixResult(
                file=str(path),
                line=line_no,
                code="attr-defined",
                fix_applied="# type: ignore[attr-defined]",
                success=True,
                category="sqlalchemy",
            )

        return FixResult(
            file=str(path),
            line=line_no,
            code="attr-defined",
            fix_applied="already ignored",
            success=True,
            category="sqlalchemy",
        )

    except Exception as e:
        return FixResult(
            file=str(path),
            line=line_no,
            code="attr-defined",
            fix_applied="sa_cast",
            success=False,
            message=str(e),
        )


def apply_prometheus_any(path: Path, line_no: int, dry_run: bool = False) -> FixResult:
    """Add Any annotation to Prometheus metric."""
    try:
        lines = path.read_text().splitlines()
        idx = line_no - 1
        line = lines[idx]

        # Check if already annotated
        if ": Any =" in line or ": Any=" in line:
            return FixResult(
                file=str(path),
                line=line_no,
                code="misc",
                fix_applied="prom_any (exists)",
                success=True,
                category="prometheus",
            )

        # Parse: NAME = Counter/Histogram/...
        match = re.match(r"(\s*)(\w+)\s*=\s*(.+)", line)
        if not match:
            return FixResult(
                file=str(path),
                line=line_no,
                code="misc",
                fix_applied="prom_any",
                success=False,
                message="Not an assignment",
            )

        indent = match.group(1)
        name = match.group(2)
        value = match.group(3)

        if not dry_run:
            lines[idx] = f"{indent}{name}: Any = {value}"
            path.write_text("\n".join(lines) + "\n")
            ensure_typing_imports(path, needs_any=True)

        return FixResult(
            file=str(path),
            line=line_no,
            code="misc",
            fix_applied=f"{name}: Any = ...",
            success=True,
            category="prometheus",
        )

    except Exception as e:
        return FixResult(
            file=str(path),
            line=line_no,
            code="misc",
            fix_applied="prom_any",
            success=False,
            message=str(e),
        )


def apply_callable_fix(path: Path, line_no: int, dry_run: bool = False) -> FixResult:
    """Fix callable type annotation."""
    try:
        lines = path.read_text().splitlines()
        idx = line_no - 1
        line = lines[idx]

        # Replace 'callable' with 'Callable[..., Any]'
        if "callable" in line.lower():
            new_line = re.sub(r"\bcallable\b", "Callable[..., Any]", line, flags=re.IGNORECASE)
            if new_line != line and not dry_run:
                lines[idx] = new_line
                path.write_text("\n".join(lines) + "\n")
                ensure_typing_imports(path, needs_any=True)
                # Also need to import Callable
                content = path.read_text()
                if "Callable" not in content:
                    # Add Callable to imports
                    lines = content.splitlines()
                    for i, ln in enumerate(lines):
                        if "from typing import" in ln:
                            if "Callable" not in ln:
                                lines[i] = ln.rstrip() + ", Callable"
                            break
                    path.write_text("\n".join(lines) + "\n")

            return FixResult(
                file=str(path),
                line=line_no,
                code="misc",
                fix_applied="Callable[..., Any]",
                success=True,
                category="callable",
            )

        return FixResult(
            file=str(path),
            line=line_no,
            code="misc",
            fix_applied="callable_fix",
            success=False,
            message="No callable found",
        )

    except Exception as e:
        return FixResult(
            file=str(path),
            line=line_no,
            code="misc",
            fix_applied="callable_fix",
            success=False,
            message=str(e),
        )


# =============================================================================
# MAIN FIX DISPATCHER
# =============================================================================


def apply_fix(error: MypyError, dry_run: bool = False) -> Optional[FixResult]:
    """Apply appropriate fix for an error."""
    path = Path(error.file)

    if not path.exists():
        return None

    # union-attr: Apply guard
    if error.code == "union-attr":
        var = extract_variable_from_line(path, error.line)
        if not var:
            var = extract_variable_from_msg(error.msg)
        if var:
            return apply_guard(path, error.line, var, dry_run)

    # no-any-return: Apply appropriate wrapper
    if error.code == "no-any-return":
        if "bool" in error.msg.lower():
            return apply_bool_wrap(path, error.line, dry_run)
        if "int" in error.msg.lower():
            return apply_int_wrap(path, error.line, dry_run)

    # attr-defined: Check for SQLAlchemy/Pydantic patterns
    if error.code == "attr-defined":
        if error.matches_pattern(SQLALCHEMY_ATTR_PATTERNS):
            return apply_sqlalchemy_cast(path, error.line, dry_run)
        if error.matches_pattern(PYDANTIC_PATTERNS):
            return apply_sqlalchemy_cast(path, error.line, dry_run)  # Same cast logic

    # misc: Check for Prometheus/callable patterns
    if error.code == "misc":
        if error.matches_pattern(PROMETHEUS_PATTERNS):
            return apply_prometheus_any(path, error.line, dry_run)
        if "callable" in error.msg.lower():
            return apply_callable_fix(path, error.line, dry_run)

    # valid-type: callable as type
    if error.code == "valid-type" and "callable" in error.msg.lower():
        return apply_callable_fix(path, error.line, dry_run)

    return None


def main() -> int:
    """Main entry point."""
    args = sys.argv[1:]
    zone_a_only = "--zone-a" in args
    dry_run = "--dry-run" in args
    show_report = "--report" in args or dry_run

    print("Running mypy...")
    lines = run_mypy(zone_a_only)
    errors = parse_errors(lines, zone_a_only)

    report = FixReport(total_errors=len(errors))

    print(f"Found {len(errors)} errors" + (" (Zone A only)" if zone_a_only else ""))

    if dry_run:
        print("\n[DRY RUN] No changes will be made.\n")

    for error in errors:
        result = apply_fix(error, dry_run)

        if result is None:
            report.fixes_skipped += 1
        elif result.success:
            report.fixes_applied += 1
            report.results.append(result)
            report.files_modified.add(result.file)
        else:
            report.fixes_failed += 1
            report.results.append(result)

    if show_report:
        report.print_summary()

    # Return non-zero if any fixes were applied (for CI)
    if report.fixes_applied > 0 and not dry_run:
        print(f"\n{report.fixes_applied} fix(es) applied to {len(report.files_modified)} file(s).")
        print("Run `git diff` to review changes.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
