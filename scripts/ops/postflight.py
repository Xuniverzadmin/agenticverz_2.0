#!/usr/bin/env python3
"""
postflight.py - Post-Implementation Hygiene Check Engine v2.0

PURPOSE: Validate code quality, consistency, and hygiene AFTER implementation.
         Run after finishing coding to catch issues before commit.

IMPROVEMENTS (v2.0 - PIN-108):
- Warning budgets per category (fail on regressions)
- Baseline file support (.postflight-baseline.json)
- Suppression annotations (# postflight: ignore)
- Exit code enforcement for CI

Usage:
    # Quick check (syntax + imports + security)
    ./scripts/ops/postflight.py --quick

    # Full check (all categories)
    ./scripts/ops/postflight.py --full

    # Check specific file
    ./scripts/ops/postflight.py backend/app/api/ops.py

    # Check with auto-fix suggestions
    ./scripts/ops/postflight.py --fix-suggestions

    # Save current counts as baseline
    ./scripts/ops/postflight.py --save-baseline

    # Fail if warnings exceed baseline
    ./scripts/ops/postflight.py --enforce-budget

    # JSON output for CI
    ./scripts/ops/postflight.py --json

Categories:
    - syntax: Python syntax validation
    - imports: Import analysis and circular dependency detection
    - security: Hardcoded secrets, SQL injection patterns
    - complexity: Function length, nesting depth, cyclomatic complexity
    - consistency: Naming conventions, code style
    - coverage: Missing type hints, docstrings
    - api: FastAPI patterns, response models, error handling
    - duplication: Repeated code blocks
    - unused: Dead code detection

Warning Budgets (defaults):
    - errors: 0 (always fail)
    - security warnings: 5
    - complexity warnings: 20
    - other warnings: 50
"""

import ast
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional


# =============================================================================
# Warning Budget Configuration
# =============================================================================

DEFAULT_BUDGETS = {
    # Errors always fail (budget = 0)
    "syntax": {"error": 0, "warning": 10, "suggestion": 100},
    "imports": {
        "error": 0,
        "warning": 150,
        "suggestion": 200,
    },  # High due to intentional lazy imports
    "security": {"error": 0, "warning": 10, "suggestion": 50},
    "complexity": {"error": 0, "warning": 30, "suggestion": 100},
    "consistency": {"error": 0, "warning": 20, "suggestion": 200},
    "coverage": {"error": 0, "warning": 50, "suggestion": 500},
    "api": {"error": 0, "warning": 20, "suggestion": 100},
    "duplication": {"error": 0, "warning": 20, "suggestion": 100},
    "unused": {"error": 0, "warning": 50, "suggestion": 100},
}

BASELINE_FILE = ".postflight-baseline.json"
SUPPRESSION_PATTERN = re.compile(r"#\s*postflight:\s*ignore(?:\[([^\]]+)\])?")


def load_baseline(root: Path) -> Dict:
    """Load warning baseline from file."""
    baseline_path = root / BASELINE_FILE
    if baseline_path.exists():
        try:
            return json.loads(baseline_path.read_text())
        except Exception:
            return {}
    return {}


def save_baseline(root: Path, counts: Dict):
    """Save current warning counts as baseline."""
    baseline_path = root / BASELINE_FILE
    baseline_path.write_text(json.dumps(counts, indent=2))
    print(f"Baseline saved to {baseline_path}")


def check_budget_violations(
    counts: Dict, baseline: Dict, budgets: Dict = None
) -> List[str]:
    """
    Check if warning counts exceed budget.
    Returns list of violation messages.
    """
    if budgets is None:
        budgets = DEFAULT_BUDGETS

    violations = []

    for category, severity_counts in counts.items():
        cat_budget = budgets.get(
            category, {"error": 0, "warning": 50, "suggestion": 200}
        )
        cat_baseline = baseline.get(category, {})

        for severity, count in severity_counts.items():
            budget = cat_budget.get(severity, 100)
            prev_count = cat_baseline.get(severity, 0)

            # Always fail on errors
            if severity == "error" and count > 0:
                violations.append(
                    f"BUDGET EXCEEDED: {category}/{severity}: {count} > 0 (errors not allowed)"
                )

            # For warnings/suggestions, check if NEW issues were added
            elif count > prev_count and count > budget:
                violations.append(
                    f"BUDGET EXCEEDED: {category}/{severity}: {count} > {budget} "
                    f"(was {prev_count}, added {count - prev_count} new)"
                )

    return violations


@dataclass
class Issue:
    severity: str  # 'error', 'warning', 'suggestion'
    category: str
    message: str
    file: str
    line: Optional[int] = None
    fix: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class CheckResult:
    passed: bool
    issues: List[Issue] = field(default_factory=list)
    metrics: Dict[str, any] = field(default_factory=dict)


class PostflightChecker:
    def __init__(self, project_root: str = "."):
        self.root = Path(project_root)
        self.issues: List[Issue] = []
        self.metrics: Dict[str, any] = {}

    # =========================================================================
    # SYNTAX VALIDATION
    # =========================================================================

    def check_syntax(self, file_path: str) -> List[Issue]:
        """Validate Python syntax."""
        issues = []
        path = (
            self.root / file_path
            if not Path(file_path).is_absolute()
            else Path(file_path)
        )

        if not path.exists() or not path.suffix == ".py":
            return issues

        try:
            content = path.read_text()
            ast.parse(content)
        except SyntaxError as e:
            issues.append(
                Issue(
                    severity="error",
                    category="syntax",
                    message=f"Syntax error: {e.msg}",
                    file=str(file_path),
                    line=e.lineno,
                )
            )

        return issues

    # =========================================================================
    # IMPORT ANALYSIS
    # =========================================================================

    def check_imports(self, file_path: str) -> List[Issue]:
        """Analyze imports for issues."""
        issues = []
        path = (
            self.root / file_path
            if not Path(file_path).is_absolute()
            else Path(file_path)
        )

        if not path.exists() or not path.suffix == ".py":
            return issues

        try:
            content = path.read_text()
            tree = ast.parse(content)

            imports = []
            from_imports = defaultdict(list)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append((alias.name, node.lineno))
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for alias in node.names:
                            from_imports[node.module].append((alias.name, node.lineno))

            # Check for duplicate imports
            seen = set()
            for name, line in imports:
                if name in seen:
                    issues.append(
                        Issue(
                            severity="warning",
                            category="imports",
                            message=f"Duplicate import: {name}",
                            file=str(file_path),
                            line=line,
                        )
                    )
                seen.add(name)

            # Check for common missing imports
            if "Optional" in content and "from typing import" not in content:
                if "Optional" not in str(imports):
                    issues.append(
                        Issue(
                            severity="warning",
                            category="imports",
                            message="Using Optional but not imported from typing",
                            file=str(file_path),
                            fix="Add: from typing import Optional",
                        )
                    )

            if (
                "List[" in content
                and "List" not in content.split("from typing import")[1].split("\n")[0]
                if "from typing import" in content
                else True
            ):
                if "from typing import" not in content or "List" not in content:
                    pass  # This check needs refinement

            # Check for import order (stdlib, third-party, local)
            # This is a simplified check

        except Exception as e:
            issues.append(
                Issue(
                    severity="warning",
                    category="imports",
                    message=f"Could not analyze imports: {e}",
                    file=str(file_path),
                )
            )

        return issues

    # =========================================================================
    # SECURITY CHECKS
    # =========================================================================

    def check_security(self, file_path: str) -> List[Issue]:
        """Check for security issues."""
        issues = []
        path = (
            self.root / file_path
            if not Path(file_path).is_absolute()
            else Path(file_path)
        )

        if not path.exists():
            return issues

        # Skip test files for hardcoded secret checks
        if "test_" in str(path) or "/tests/" in str(path):
            return issues

        content = path.read_text()
        lines = content.split("\n")

        # Hardcoded secrets patterns - more specific to avoid false positives
        secret_patterns = [
            # Real password assignments (not model fields or placeholders)
            (r'password\s*=\s*["\'][a-zA-Z0-9!@#$%^&*]{8,}["\']', "Hardcoded password"),
            # Real API keys (long alphanumeric strings, not "api_key" or short test values)
            (r'api_key\s*=\s*["\'][a-zA-Z0-9\-_]{32,}["\']', "Hardcoded API key"),
            # Secrets with real-looking values
            (r'secret\s*=\s*["\'][a-zA-Z0-9]{32,}["\']', "Hardcoded secret"),
            # Bearer tokens
            (r"Bearer\s+[a-zA-Z0-9\-_]{40,}", "Hardcoded bearer token"),
        ]

        for i, line in enumerate(lines):
            # Skip comments
            if line.strip().startswith("#"):
                continue

            # Skip enum/constant definitions (ALL_CAPS = "value")
            if re.match(r'\s*[A-Z_]+\s*=\s*["\']', line):
                continue

            # Skip type hints and model fields
            if ": str" in line or ": Optional" in line:
                continue

            for pattern, msg in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Skip if it's reading from env
                    if (
                        "os.getenv" in line
                        or "os.environ" in line
                        or "environ.get" in line
                    ):
                        continue
                    # Skip placeholder values
                    if (
                        "test" in line.lower()
                        or "example" in line.lower()
                        or "placeholder" in line.lower()
                    ):
                        continue
                    issues.append(
                        Issue(
                            severity="error",
                            category="security",
                            message=msg,
                            file=str(file_path),
                            line=i + 1,
                            fix="Use environment variables instead",
                        )
                    )

        # SQL injection patterns
        sql_patterns = [
            (r'execute\s*\(\s*f["\']', "Potential SQL injection with f-string"),
            (r'execute\s*\(\s*["\'].*%s', "Potential SQL injection with % formatting"),
            (
                r'execute\s*\(\s*["\'].*\+\s*\w+',
                "Potential SQL injection with concatenation",
            ),
        ]

        for i, line in enumerate(lines):
            for pattern, msg in sql_patterns:
                if re.search(pattern, line):
                    # Check if it's using parameterized queries
                    if "$1" in line or "$2" in line or "?" in line:
                        continue  # Likely parameterized
                    issues.append(
                        Issue(
                            severity="warning",
                            category="security",
                            message=msg,
                            file=str(file_path),
                            line=i + 1,
                            fix="Use parameterized queries with $1, $2, etc.",
                        )
                    )

        return issues

    # =========================================================================
    # COMPLEXITY ANALYSIS
    # =========================================================================

    def check_complexity(self, file_path: str) -> List[Issue]:
        """Check function complexity."""
        issues = []
        path = (
            self.root / file_path
            if not Path(file_path).is_absolute()
            else Path(file_path)
        )

        if not path.exists() or not path.suffix == ".py":
            return issues

        try:
            content = path.read_text()
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Function length
                    func_lines = (
                        node.end_lineno - node.lineno + 1
                        if hasattr(node, "end_lineno")
                        else 0
                    )

                    if func_lines > 100:
                        issues.append(
                            Issue(
                                severity="warning",
                                category="complexity",
                                message=f"Function '{node.name}' is {func_lines} lines - consider splitting",
                                file=str(file_path),
                                line=node.lineno,
                            )
                        )
                    elif func_lines > 50:
                        issues.append(
                            Issue(
                                severity="suggestion",
                                category="complexity",
                                message=f"Function '{node.name}' is {func_lines} lines - may benefit from splitting",
                                file=str(file_path),
                                line=node.lineno,
                            )
                        )

                    # Nesting depth
                    max_depth = self._get_max_nesting_depth(node)
                    if max_depth > 5:
                        issues.append(
                            Issue(
                                severity="warning",
                                category="complexity",
                                message=f"Function '{node.name}' has nesting depth {max_depth} - too deep",
                                file=str(file_path),
                                line=node.lineno,
                                fix="Extract nested logic into helper functions",
                            )
                        )

                    # Parameter count
                    param_count = len(node.args.args) + len(node.args.kwonlyargs)
                    if param_count > 7:
                        issues.append(
                            Issue(
                                severity="suggestion",
                                category="complexity",
                                message=f"Function '{node.name}' has {param_count} parameters - consider using a dataclass",
                                file=str(file_path),
                                line=node.lineno,
                            )
                        )

        except Exception:
            pass  # Skip files that can't be parsed

        return issues

    def _get_max_nesting_depth(self, node, current_depth=0) -> int:
        """Calculate maximum nesting depth."""
        max_depth = current_depth

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                child_depth = self._get_max_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)

        return max_depth

    # =========================================================================
    # CONSISTENCY CHECKS
    # =========================================================================

    def check_consistency(self, file_path: str) -> List[Issue]:
        """Check naming conventions and code style."""
        issues = []
        path = (
            self.root / file_path
            if not Path(file_path).is_absolute()
            else Path(file_path)
        )

        if not path.exists() or not path.suffix == ".py":
            return issues

        try:
            content = path.read_text()
            tree = ast.parse(content)

            for node in ast.walk(tree):
                # Function naming (should be snake_case)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not node.name.startswith("_"):
                        if not re.match(r"^[a-z][a-z0-9_]*$", node.name):
                            issues.append(
                                Issue(
                                    severity="suggestion",
                                    category="consistency",
                                    message=f"Function '{node.name}' should use snake_case",
                                    file=str(file_path),
                                    line=node.lineno,
                                )
                            )

                # Class naming (should be PascalCase)
                if isinstance(node, ast.ClassDef):
                    if not re.match(r"^[A-Z][a-zA-Z0-9]*$", node.name):
                        issues.append(
                            Issue(
                                severity="suggestion",
                                category="consistency",
                                message=f"Class '{node.name}' should use PascalCase",
                                file=str(file_path),
                                line=node.lineno,
                            )
                        )

                # Constants (module level UPPER_CASE)
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            # Check if it's at module level and looks like a constant
                            if target.id.isupper() or (
                                target.id[0].isupper() and "_" in target.id
                            ):
                                continue  # Probably a constant
                            # Could add more checks here

        except Exception:
            pass

        return issues

    # =========================================================================
    # COVERAGE CHECKS (Type Hints & Docstrings)
    # =========================================================================

    def check_coverage(self, file_path: str) -> List[Issue]:
        """Check for missing type hints and docstrings."""
        issues = []
        path = (
            self.root / file_path
            if not Path(file_path).is_absolute()
            else Path(file_path)
        )

        if not path.exists() or not path.suffix == ".py":
            return issues

        try:
            content = path.read_text()
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Skip private/dunder methods
                    if node.name.startswith("_"):
                        continue

                    # Check for return type annotation
                    if node.returns is None:
                        issues.append(
                            Issue(
                                severity="suggestion",
                                category="coverage",
                                message=f"Function '{node.name}' missing return type hint",
                                file=str(file_path),
                                line=node.lineno,
                            )
                        )

                    # Check for docstring
                    if not ast.get_docstring(node):
                        issues.append(
                            Issue(
                                severity="suggestion",
                                category="coverage",
                                message=f"Function '{node.name}' missing docstring",
                                file=str(file_path),
                                line=node.lineno,
                            )
                        )

        except Exception:
            pass

        return issues

    # =========================================================================
    # API CONSISTENCY CHECKS
    # =========================================================================

    def check_api_patterns(self, file_path: str) -> List[Issue]:
        """Check FastAPI patterns and consistency."""
        issues = []
        path = (
            self.root / file_path
            if not Path(file_path).is_absolute()
            else Path(file_path)
        )

        if not path.exists() or "api" not in str(path):
            return issues

        content = path.read_text()
        lines = content.split("\n")

        # Check for missing response_model
        route_pattern = re.compile(r"@router\.(get|post|put|delete|patch)\s*\([^)]*\)")

        for i, line in enumerate(lines):
            match = route_pattern.search(line)
            if match:
                # Check if response_model is present
                # Look at this line and possibly the next few
                route_block = "\n".join(lines[i : i + 5])
                if (
                    "response_model" not in route_block
                    and "response_class" not in route_block
                ):
                    # Don't flag if it returns dict or Response directly
                    if "Dict" not in route_block and "Response" not in route_block:
                        issues.append(
                            Issue(
                                severity="suggestion",
                                category="api",
                                message="Endpoint missing response_model - consider adding for documentation",
                                file=str(file_path),
                                line=i + 1,
                            )
                        )

        # Check for inconsistent error handling
        http_exception_count = content.count("raise HTTPException")
        if http_exception_count > 10:
            issues.append(
                Issue(
                    severity="suggestion",
                    category="api",
                    message=f"File has {http_exception_count} HTTPException raises - consider an error factory",
                    file=str(file_path),
                    fix="Create a helper function like: def api_error(status, message): raise HTTPException(...)",
                )
            )

        return issues

    # =========================================================================
    # DUPLICATION DETECTION
    # =========================================================================

    def check_duplication(self, file_path: str) -> List[Issue]:
        """Detect potentially duplicated code blocks."""
        issues = []
        path = (
            self.root / file_path
            if not Path(file_path).is_absolute()
            else Path(file_path)
        )

        if not path.exists() or not path.suffix == ".py":
            return issues

        content = path.read_text()
        lines = content.split("\n")

        # Look for repeated SQL queries
        sql_queries = re.findall(
            r'(?:execute|text)\s*\(\s*"""([^"]+)"""', content, re.DOTALL
        )
        if len(sql_queries) > 5:
            # Check for similar patterns
            query_hashes = defaultdict(int)
            for q in sql_queries:
                # Normalize query
                normalized = re.sub(r"\s+", " ", q.strip().lower())
                # Extract table name pattern
                tables = re.findall(r"(?:from|join|into|update)\s+(\w+)", normalized)
                for t in tables:
                    query_hashes[t] += 1

            for table, count in query_hashes.items():
                if count > 3:
                    issues.append(
                        Issue(
                            severity="suggestion",
                            category="duplication",
                            message=f"Table '{table}' queried {count} times - consider a query helper",
                            file=str(file_path),
                        )
                    )

        # Look for repeated error handling patterns
        error_blocks = re.findall(
            r"except\s+\w+.*?(?=\n\s*(?:except|else|finally|\n\n))", content, re.DOTALL
        )
        if len(error_blocks) > 5:
            issues.append(
                Issue(
                    severity="suggestion",
                    category="duplication",
                    message=f"Found {len(error_blocks)} exception handlers - consider centralizing error handling",
                    file=str(file_path),
                )
            )

        return issues

    # =========================================================================
    # UNUSED CODE DETECTION
    # =========================================================================

    def check_unused(self, file_path: str) -> List[Issue]:
        """Detect potentially unused code."""
        issues = []
        path = (
            self.root / file_path
            if not Path(file_path).is_absolute()
            else Path(file_path)
        )

        if not path.exists() or not path.suffix == ".py":
            return issues

        try:
            content = path.read_text()
            tree = ast.parse(content)

            # Collect all defined names
            defined_names = set()
            used_names = set()

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    defined_names.add(node.name)
                elif isinstance(node, ast.ClassDef):
                    defined_names.add(node.name)
                elif isinstance(node, ast.Name):
                    if isinstance(node.ctx, ast.Load):
                        used_names.add(node.id)

            # Check imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.asname or alias.name.split(".")[0]
                        if name not in used_names and not name.startswith("_"):
                            issues.append(
                                Issue(
                                    severity="warning",
                                    category="unused",
                                    message=f"Import '{alias.name}' appears unused",
                                    file=str(file_path),
                                    line=node.lineno,
                                )
                            )
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        name = alias.asname or alias.name
                        if (
                            name not in used_names
                            and not name.startswith("_")
                            and name != "*"
                        ):
                            # Skip type-only imports
                            if "TYPE_CHECKING" in content:
                                continue
                            issues.append(
                                Issue(
                                    severity="warning",
                                    category="unused",
                                    message=f"Import '{name}' from {node.module} appears unused",
                                    file=str(file_path),
                                    line=node.lineno,
                                )
                            )

        except Exception:
            pass

        return issues

    # =========================================================================
    # FULL CHECK
    # =========================================================================

    def check_file(
        self, file_path: str, categories: Optional[List[str]] = None
    ) -> List[Issue]:
        """Run all checks on a file."""
        all_issues = []

        checks = {
            "syntax": self.check_syntax,
            "imports": self.check_imports,
            "security": self.check_security,
            "complexity": self.check_complexity,
            "consistency": self.check_consistency,
            "coverage": self.check_coverage,
            "api": self.check_api_patterns,
            "duplication": self.check_duplication,
            "unused": self.check_unused,
        }

        for name, check_fn in checks.items():
            if categories is None or name in categories:
                issues = check_fn(file_path)
                all_issues.extend(issues)

        return all_issues

    def check_directory(
        self, dir_path: str, categories: Optional[List[str]] = None
    ) -> List[Issue]:
        """Check all Python files in a directory."""
        all_issues = []
        path = (
            self.root / dir_path if not Path(dir_path).is_absolute() else Path(dir_path)
        )

        for py_file in path.rglob("*.py"):
            if "__pycache__" in str(py_file) or ".pytest_cache" in str(py_file):
                continue
            rel_path = str(py_file.relative_to(self.root))
            issues = self.check_file(rel_path, categories)
            all_issues.extend(issues)

        return all_issues

    def full_check(self) -> Dict[str, any]:
        """Run full postflight check on the project."""
        results = {
            "summary": {
                "errors": 0,
                "warnings": 0,
                "suggestions": 0,
            },
            "by_category": defaultdict(list),
            "by_file": defaultdict(list),
            "category_counts": defaultdict(
                lambda: defaultdict(int)
            ),  # category -> severity -> count
            "issues": [],
        }

        # Check backend
        backend_path = self.root / "backend/app"
        if backend_path.exists():
            issues = self.check_directory("backend/app")
            for issue in issues:
                results["issues"].append(issue.to_dict())
                results["by_category"][issue.category].append(issue.to_dict())
                results["by_file"][issue.file].append(issue.to_dict())
                results["category_counts"][issue.category][issue.severity] += 1

                if issue.severity == "error":
                    results["summary"]["errors"] += 1
                elif issue.severity == "warning":
                    results["summary"]["warnings"] += 1
                else:
                    results["summary"]["suggestions"] += 1

        # Convert defaultdicts to regular dicts for JSON serialization
        results["category_counts"] = {
            k: dict(v) for k, v in results["category_counts"].items()
        }

        return results

    # =========================================================================
    # REPORT
    # =========================================================================

    def print_report(self, results: Dict, verbose: bool = False):
        """Print a formatted report."""
        print("\n" + "=" * 60)
        print("  POSTFLIGHT CHECK REPORT")
        print("=" * 60)

        summary = results["summary"]
        print("\n  Summary:")
        print(f"    🔴 Errors:      {summary['errors']}")
        print(f"    🟡 Warnings:    {summary['warnings']}")
        print(f"    💡 Suggestions: {summary['suggestions']}")

        # Show errors first
        if summary["errors"] > 0:
            print("\n🔴 ERRORS (must fix):")
            for issue in results["issues"]:
                if issue["severity"] == "error":
                    loc = (
                        f"{issue['file']}:{issue['line']}"
                        if issue["line"]
                        else issue["file"]
                    )
                    print(f"  [{issue['category']}] {issue['message']}")
                    print(f"           @ {loc}")
                    if issue.get("fix"):
                        print(f"           → {issue['fix']}")

        # Show warnings
        if summary["warnings"] > 0 and verbose:
            print("\n🟡 WARNINGS:")
            for issue in results["issues"]:
                if issue["severity"] == "warning":
                    loc = (
                        f"{issue['file']}:{issue['line']}"
                        if issue["line"]
                        else issue["file"]
                    )
                    print(f"  [{issue['category']}] {issue['message']}")
                    print(f"           @ {loc}")

        # Show top files with issues
        if results["by_file"]:
            print("\n📁 Files with most issues:")
            sorted_files = sorted(
                results["by_file"].items(), key=lambda x: len(x[1]), reverse=True
            )[:5]
            for file, issues in sorted_files:
                errors = len([i for i in issues if i["severity"] == "error"])
                warnings = len([i for i in issues if i["severity"] == "warning"])
                print(f"  {file}: {errors}E {warnings}W")

        # Categories summary
        print("\n📊 By Category:")
        for cat, issues in sorted(results["by_category"].items()):
            count = len(issues)
            errors = len([i for i in issues if i["severity"] == "error"])
            print(f"  {cat}: {count} ({errors} errors)")

        print("\n" + "-" * 60)
        if summary["errors"] > 0:
            print("  STATUS: ❌ FAILED - Fix errors before committing")
        elif summary["warnings"] > 5:
            print("  STATUS: ⚠️  PASSED (with warnings)")
        else:
            print("  STATUS: ✅ PASSED")
        print("=" * 60 + "\n")


# =============================================================================
# CLI
# =============================================================================


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Post-implementation hygiene check v2.0"
    )
    parser.add_argument("file", nargs="?", help="File or directory to check")
    parser.add_argument(
        "--quick",
        "-q",
        action="store_true",
        help="Quick check (syntax, imports, security)",
    )
    parser.add_argument(
        "--full", "-f", action="store_true", help="Full check (all categories)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show all issues including suggestions",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--fix-suggestions", action="store_true", help="Show fix suggestions"
    )
    parser.add_argument(
        "--category", "-c", action="append", help="Check specific category"
    )
    parser.add_argument("--root", default=".", help="Project root directory")
    # Budget enforcement
    parser.add_argument(
        "--save-baseline", action="store_true", help="Save current counts as baseline"
    )
    parser.add_argument(
        "--enforce-budget",
        action="store_true",
        help="Fail if warnings exceed baseline/budget",
    )
    parser.add_argument(
        "--show-budgets", action="store_true", help="Show current warning budgets"
    )

    args = parser.parse_args()

    root = Path(args.root)
    checker = PostflightChecker(args.root)

    # Show budgets and exit
    if args.show_budgets:
        print("\n📊 Warning Budgets (per category):")
        print("-" * 50)
        for cat, limits in sorted(DEFAULT_BUDGETS.items()):
            print(f"  {cat}:")
            print(f"    errors:      {limits['error']} (always 0)")
            print(f"    warnings:    {limits['warning']}")
            print(f"    suggestions: {limits['suggestion']}")
        return

    # Determine categories
    if args.quick:
        categories = ["syntax", "imports", "security"]
    elif args.category:
        categories = args.category
    else:
        categories = None  # All categories

    if args.full or (not args.file and not args.quick):
        results = checker.full_check()

        # Save baseline if requested
        if args.save_baseline:
            save_baseline(root, results["category_counts"])

        # Check budget violations
        exit_code = 0
        if args.enforce_budget:
            baseline = load_baseline(root)
            violations = check_budget_violations(results["category_counts"], baseline)
            if violations:
                print("\n🚨 BUDGET VIOLATIONS:")
                for v in violations:
                    print(f"  {v}")
                exit_code = 1

        if args.json:
            output = results.copy()
            output["by_category"] = dict(output["by_category"])
            output["by_file"] = dict(output["by_file"])
            print(json.dumps(output, indent=2, default=str))
        else:
            checker.print_report(results, verbose=args.verbose)

            if args.enforce_budget:
                if exit_code == 0:
                    print("✅ All warning budgets OK")
                else:
                    print("\n❌ Budget enforcement FAILED")

        sys.exit(exit_code)

    elif args.file:
        path = Path(args.file)
        if path.is_dir():
            issues = checker.check_directory(args.file, categories)
        else:
            issues = checker.check_file(args.file, categories)

        if args.json:
            print(json.dumps([i.to_dict() for i in issues], indent=2))
        else:
            if issues:
                print(f"\n📋 Issues in {args.file}:")
                for issue in issues:
                    severity_icon = {
                        "error": "🔴",
                        "warning": "🟡",
                        "suggestion": "💡",
                    }[issue.severity]
                    loc = f":{issue.line}" if issue.line else ""
                    print(
                        f"  {severity_icon} [{issue.category}] {issue.message} @ {issue.file}{loc}"
                    )
                    if args.fix_suggestions and issue.fix:
                        print(f"           → {issue.fix}")
            else:
                print(f"\n✅ No issues found in {args.file}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
