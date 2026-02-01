#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: preflight.py - Pre-Implementation Evaluation System v2.0
# artifact_class: CODE
"""
preflight.py - Pre-Implementation Evaluation System v2.0

PURPOSE: Evaluate code changes BEFORE implementation to catch issues early.
         Uses AST parsing for reliability, semantic collision detection for accuracy.

IMPROVEMENTS over v1:
- AST-based route extraction (not regex)
- Semantic path collision detection (not just ordering)
- Type constraint awareness ({id:int} vs {id:uuid})
- Runtime validation hook generator

Usage:
    # Check for route conflicts in FastAPI
    ./scripts/ops/preflight.py --routes

    # Check with verbose output
    ./scripts/ops/preflight.py --routes --verbose

    # Generate runtime validation hook
    ./scripts/ops/preflight.py --generate-hook

    # Full pre-flight check (includes SDK build freshness)
    ./scripts/ops/preflight.py --full

Checks:
    - Route collisions (semantic collision detection)
    - Untyped path parameters
    - Import analysis
    - SDK build freshness (PIN-125 PREV-18)
"""

import ast
import re
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class RouteInfo:
    """Parsed route information."""

    path: str
    method: str
    file: str
    line: int
    function_name: str
    # Path segments with type info
    segments: List[dict] = field(default_factory=list)
    # Original decorator node for context
    has_type_constraint: bool = False


@dataclass
class Issue:
    severity: str  # 'error', 'warning', 'suggestion'
    category: str
    message: str
    file: str
    line: Optional[int] = None
    suggestion: Optional[str] = None


class RouteSegment:
    """Represents a single path segment with type awareness."""

    def __init__(self, raw: str):
        self.raw = raw
        self.is_param = raw.startswith("{") and raw.endswith("}")
        self.name = None
        self.type_constraint = None

        if self.is_param:
            inner = raw[1:-1]
            if ":" in inner:
                self.name, self.type_constraint = inner.split(":", 1)
            else:
                self.name = inner

    def can_match(self, value: str) -> bool:
        """Check if this segment can match a given value."""
        if not self.is_param:
            return self.raw == value

        # Parameter with type constraint
        if self.type_constraint:
            if self.type_constraint == "int":
                return value.isdigit()
            elif self.type_constraint == "uuid":
                # UUID pattern
                uuid_pattern = (
                    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
                )
                return bool(re.match(uuid_pattern, value, re.I))
            elif self.type_constraint == "path":
                return True  # Matches anything including slashes

        # Unconstrained parameter matches anything
        return True

    def conflicts_with(self, other: "RouteSegment") -> Optional[str]:
        """
        Check if this segment conflicts with another.
        Returns conflict description or None.
        """
        # Both static - conflict only if different
        if not self.is_param and not other.is_param:
            return None if self.raw == other.raw else None

        # Both are params - no conflict (both would match same things)
        if self.is_param and other.is_param:
            return None

        # One param, one static
        param_seg = self if self.is_param else other
        static_seg = other if self.is_param else self

        # Check if the param could match the static value
        if param_seg.can_match(static_seg.raw):
            # Conflict exists
            if param_seg.type_constraint:
                return f"'{param_seg.raw}' (typed param) may match '{static_seg.raw}'"
            else:
                return (
                    f"'{param_seg.raw}' (untyped param) WILL match '{static_seg.raw}'"
                )

        return None


class ASTRouteExtractor(ast.NodeVisitor):
    """Extract routes using AST parsing for reliability."""

    HTTP_METHODS = {"get", "post", "put", "delete", "patch", "head", "options"}

    def __init__(self, file_path: str, source: str):
        self.file_path = file_path
        self.source = source
        self.lines = source.split("\n")
        self.routes: List[RouteInfo] = []
        self.current_class = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._check_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._check_function(node)
        self.generic_visit(node)

    def _check_function(self, node):
        """Check if function has route decorators."""
        for decorator in node.decorator_list:
            route_info = self._parse_decorator(decorator, node)
            if route_info:
                self.routes.append(route_info)

    def _parse_decorator(self, decorator, func_node) -> Optional[RouteInfo]:
        """Parse a decorator to extract route info."""
        # Handle @router.get("/path") or @app.get("/path")
        if not isinstance(decorator, ast.Call):
            return None

        if not isinstance(decorator.func, ast.Attribute):
            return None

        method = decorator.func.attr.lower()
        if method not in self.HTTP_METHODS:
            return None

        # Extract path from first argument
        if not decorator.args:
            return None

        path_arg = decorator.args[0]
        if isinstance(path_arg, ast.Constant) and isinstance(path_arg.value, str):
            path = path_arg.value
        elif isinstance(path_arg, ast.Str):  # Python 3.7 compat
            path = path_arg.s
        else:
            return None

        # Parse segments
        segments = self._parse_path_segments(path)
        has_type = any(seg.type_constraint for seg in segments)

        return RouteInfo(
            path=path,
            method=method.upper(),
            file=self.file_path,
            line=decorator.lineno,
            function_name=func_node.name,
            segments=[
                {"raw": s.raw, "is_param": s.is_param, "type": s.type_constraint}
                for s in segments
            ],
            has_type_constraint=has_type,
        )

    def _parse_path_segments(self, path: str) -> List[RouteSegment]:
        """Parse path into segments with type info."""
        parts = path.strip("/").split("/")
        return [RouteSegment(p) for p in parts if p]


class SemanticCollisionDetector:
    """Detect actual route collisions based on matching semantics."""

    def __init__(self):
        self.issues: List[Issue] = []

    def analyze(self, routes: List[RouteInfo]) -> List[Issue]:
        """Analyze routes for semantic collisions."""
        self.issues = []

        # Group by file (each file has its own router)
        by_file = defaultdict(list)
        for r in routes:
            by_file[r.file].append(r)

        for file_path, file_routes in by_file.items():
            self._analyze_file_routes(file_path, file_routes)

        return self.issues

    def _analyze_file_routes(self, file_path: str, routes: List[RouteInfo]):
        """Analyze routes within a single file."""
        # Group by method
        by_method = defaultdict(list)
        for r in routes:
            by_method[r.method].append(r)

        for method, method_routes in by_method.items():
            # Sort by line number to establish declaration order
            sorted_routes = sorted(method_routes, key=lambda r: r.line)

            # Check all pairs
            for i, r1 in enumerate(sorted_routes):
                for r2 in sorted_routes[i + 1 :]:
                    self._check_pair(r1, r2, method)

    def _check_pair(self, earlier: RouteInfo, later: RouteInfo, method: str):
        """Check if two routes can collide semantically.

        The key insight is: we only flag a collision as PROBLEMATIC if, at the
        FIRST segment where one route is more specific than the other, the EARLIER
        route has the parameter (less specific) and the LATER has static (more specific).

        If the earlier route has a static segment first, it's correctly more specific
        and should take priority - no issue.
        """
        seg1 = [RouteSegment(s["raw"]) for s in earlier.segments]
        seg2 = [RouteSegment(s["raw"]) for s in later.segments]

        # Different length = no collision
        if len(seg1) != len(seg2):
            return

        # Find the first position where one route is more specific than the other
        first_differentiator = None  # (position, earlier_is_more_specific, s1, s2)

        for i, (s1, s2) in enumerate(zip(seg1, seg2)):
            if not s1.is_param and not s2.is_param:
                # Both static
                if s1.raw != s2.raw:
                    return  # Paths definitively diverge, no overlap
                continue  # Same static segment

            # At least one is a param
            if s1.is_param and s2.is_param:
                # Both params - could potentially still collide
                # Check if they have distinguishing type constraints
                if s1.type_constraint and s2.type_constraint:
                    if s1.type_constraint != s2.type_constraint:
                        return  # Type constraints disambiguate, no collision
                continue  # Both params with same/no constraints - no clear winner yet

            # One is static, one is param - this is our differentiator
            if not s1.is_param and s2.is_param:
                # Earlier has static (more specific), later has param
                first_differentiator = (i, True, s1, s2)  # Earlier is more specific
            else:  # s1.is_param and not s2.is_param
                # Earlier has param, later has static (later is more specific)
                first_differentiator = (i, False, s1, s2)  # Earlier is LESS specific
            break

        if first_differentiator:
            pos, earlier_is_more_specific, s1, s2 = first_differentiator

            if not earlier_is_more_specific:
                # This is the bad case: param route is shadowing static route
                # The earlier route has a param where the later has a static value
                self.issues.append(
                    Issue(
                        severity="error",
                        category="route_collision",
                        message=f"Route collision: {method} {earlier.path} shadows {later.path}",
                        file=earlier.file,
                        line=earlier.line,
                        suggestion=f"Move '{later.path}' (line {later.line}) BEFORE '{earlier.path}' (line {earlier.line}). "
                        f"Or add type constraint: {{{s1.name}:uuid}} to disambiguate.",
                    )
                )
            # If earlier_is_more_specific, order is correct - don't log (too noisy)


class PreflightChecker:
    def __init__(self, project_root: str = "."):
        self.root = Path(project_root)
        self.issues: List[Issue] = []
        self.routes: List[RouteInfo] = []

    # =========================================================================
    # GOVERNANCE QUALIFIER CHECK (PIN-281 - System Gate)
    # =========================================================================

    def check_governance_qualifiers(
        self, capabilities: List[str] = None
    ) -> List[Issue]:
        """
        Evaluate governance qualifiers for L2 contract readiness.

        This is a SYSTEM GATE, not advice. If any capability referenced in
        L2 tests or product claims is not QUALIFIED, this check BLOCKS.

        Reference: GOVERNANCE_QUALIFIERS.yaml, SESSION_PLAYBOOK.yaml governance_qualifiers
        """
        issues = []

        # Import the qualifier evaluator
        try:
            sys.path.insert(0, str(self.root / "scripts" / "ops"))
            from evaluate_qualifiers import (
                evaluate_all_capabilities,
                QualifierState,
            )
        except ImportError as e:
            issues.append(
                Issue(
                    severity="error",
                    category="qualifier",
                    message=f"Cannot import evaluate_qualifiers: {e}",
                    file="scripts/ops/evaluate_qualifiers.py",
                    suggestion="Ensure evaluate_qualifiers.py exists and is valid",
                )
            )
            return issues

        try:
            results = evaluate_all_capabilities(self.root)
        except FileNotFoundError as e:
            issues.append(
                Issue(
                    severity="error",
                    category="qualifier",
                    message=f"CAPABILITY_LIFECYCLE.yaml not found: {e}",
                    file="docs/governance/CAPABILITY_LIFECYCLE.yaml",
                    suggestion="Run: python scripts/ops/evaluate_qualifiers.py --generate",
                )
            )
            return issues

        # If specific capabilities provided, check only those
        if capabilities:
            for cap in capabilities:
                if cap not in results:
                    issues.append(
                        Issue(
                            severity="error",
                            category="qualifier",
                            message=f"Unknown capability: {cap}",
                            file="docs/governance/CAPABILITY_LIFECYCLE.yaml",
                        )
                    )
                elif results[cap].state != QualifierState.QUALIFIED:
                    issues.append(
                        Issue(
                            severity="error",
                            category="qualifier",
                            message=f"GQ-L2-CONTRACT-READY FAILED: {cap} is {results[cap].state.value}",
                            file="docs/governance/QUALIFIER_EVALUATION.yaml",
                            suggestion=f"Cannot proceed with L2 testing. Fix gates: {', '.join(results[cap].failed_gates + results[cap].pending_gates)}",
                        )
                    )
        else:
            # Report summary of all qualifiers
            qualified = sum(
                1 for r in results.values() if r.state == QualifierState.QUALIFIED
            )
            disqualified = [
                r for r in results.values() if r.state == QualifierState.DISQUALIFIED
            ]

            if disqualified:
                for r in disqualified:
                    issues.append(
                        Issue(
                            severity="warning",
                            category="qualifier",
                            message=f"DISQUALIFIED: {r.capability} - {', '.join(r.disqualification_reasons[:2])}",
                            file="docs/governance/QUALIFIER_EVALUATION.yaml",
                        )
                    )

        return issues

    # =========================================================================
    # ROUTE ANALYSIS - AST-based extraction + semantic collision detection
    # =========================================================================

    def analyze_routes(
        self, api_dir: str = "backend/app/api"
    ) -> Tuple[List[RouteInfo], List[Issue]]:
        """Analyze FastAPI routes for potential collisions."""
        api_path = self.root / api_dir

        if not api_path.exists():
            return [], []

        all_routes = []
        parse_issues = []

        for py_file in api_path.glob("*.py"):
            try:
                source = py_file.read_text()
                extractor = ASTRouteExtractor(str(py_file), source)
                tree = ast.parse(source)
                extractor.visit(tree)
                all_routes.extend(extractor.routes)
            except SyntaxError as e:
                parse_issues.append(
                    Issue(
                        severity="error",
                        category="syntax",
                        message=f"Syntax error in {py_file}: {e}",
                        file=str(py_file),
                        line=e.lineno,
                    )
                )
            except Exception as e:
                parse_issues.append(
                    Issue(
                        severity="warning",
                        category="parse",
                        message=f"Could not parse {py_file}: {e}",
                        file=str(py_file),
                    )
                )

        # Semantic collision detection
        detector = SemanticCollisionDetector()
        collision_issues = detector.analyze(all_routes)

        self.routes = all_routes
        return all_routes, parse_issues + collision_issues

    # =========================================================================
    # UNTYPED PARAM WARNING - Suggest adding type constraints
    # =========================================================================

    def check_untyped_params(self, routes: List[RouteInfo]) -> List[Issue]:
        """Warn about untyped path parameters that should have constraints."""
        issues = []

        # Common param names that should be typed
        should_be_typed = {
            "id": "uuid or int",
            "tenant_id": "uuid",
            "agent_id": "uuid",
            "run_id": "uuid",
            "call_id": "uuid",
            "trace_id": "uuid",
            "user_id": "uuid",
        }

        for route in routes:
            for seg in route.segments:
                if seg.get("is_param") and not seg.get("type"):
                    # Extract param name
                    raw = seg["raw"]
                    name = raw[1:-1] if raw.startswith("{") else raw

                    if name in should_be_typed:
                        issues.append(
                            Issue(
                                severity="warning",
                                category="untyped_param",
                                message=f"Untyped param '{name}' in {route.path}",
                                file=route.file,
                                line=route.line,
                                suggestion=f"Consider adding type: {{{name}:{should_be_typed[name]}}}",
                            )
                        )

        return issues

    # =========================================================================
    # RUNTIME HOOK GENERATOR - Create startup validation
    # =========================================================================

    def generate_runtime_hook(self) -> str:
        """Generate a runtime validation hook for FastAPI startup."""
        return '''
# Add this to backend/app/main.py

from fastapi import FastAPI
from typing import Dict, List, Set
import re

def validate_route_order(app: FastAPI) -> List[str]:
    """
    Runtime validation of route ordering.
    Call during startup to catch route conflicts early.
    """
    issues = []

    # Group routes by path pattern length and method
    routes_by_method: Dict[str, List[tuple]] = {}

    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            for method in route.methods:
                if method not in routes_by_method:
                    routes_by_method[method] = []
                routes_by_method[method].append((route.path, route.endpoint.__name__))

    # Check for potential shadows
    for method, routes in routes_by_method.items():
        for i, (path1, name1) in enumerate(routes):
            for path2, name2 in routes[i+1:]:
                if _paths_can_collide(path1, path2):
                    # Check if first path has param where second has static
                    parts1 = path1.strip('/').split('/')
                    parts2 = path2.strip('/').split('/')

                    if len(parts1) == len(parts2):
                        for p1, p2 in zip(parts1, parts2):
                            is_param1 = '{' in p1
                            is_param2 = '{' in p2

                            if is_param1 and not is_param2:
                                issues.append(
                                    f"ROUTE SHADOW: {method} {path1} ({name1}) "
                                    f"may shadow {path2} ({name2})"
                                )
                                break

    return issues


def _paths_can_collide(path1: str, path2: str) -> bool:
    """Check if two paths could match the same request."""
    parts1 = path1.strip('/').split('/')
    parts2 = path2.strip('/').split('/')

    if len(parts1) != len(parts2):
        return False

    for p1, p2 in zip(parts1, parts2):
        is_param1 = '{' in p1
        is_param2 = '{' in p2

        # Both static and different = no collision
        if not is_param1 and not is_param2 and p1 != p2:
            return False

    return True


# Usage in main.py:
#
# @app.on_event("startup")
# async def startup_route_validation():
#     issues = validate_route_order(app)
#     if issues:
#         import logging
#         logger = logging.getLogger(__name__)
#         for issue in issues:
#             logger.warning(issue)
'''

    # =========================================================================
    # IMPORT ANALYSIS
    # =========================================================================

    def analyze_imports(self, file_path: str) -> List[Issue]:
        """Analyze imports for potential issues."""
        path = self.root / file_path
        if not path.exists():
            return []

        issues = []
        try:
            content = path.read_text()
            tree = ast.parse(content)

            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)

            # Check for potentially problematic imports
            if "typing" not in str(imports) and "Optional" in content:
                issues.append(
                    Issue(
                        severity="warning",
                        category="import",
                        message="Using Optional but typing not imported",
                        file=file_path,
                        suggestion="Add: from typing import Optional",
                    )
                )

        except Exception as e:
            issues.append(
                Issue(
                    severity="warning",
                    category="parse",
                    message=f"Could not analyze imports: {e}",
                    file=file_path,
                )
            )

        return issues

    # =========================================================================
    # SDK BUILD VERIFICATION (PIN-125 PREV-18)
    # =========================================================================

    def check_sdk_build_freshness(self) -> List[Issue]:
        """
        Verify JS SDK dist is up to date with source.

        PIN-125 Prevention Mechanism:
        - PREV-18: SDK Build Freshness

        Checks if any source file in sdk/js/aos-sdk/src/ is newer than dist/.
        """
        issues = []

        src_dir = self.root / "sdk/js/aos-sdk/src"
        dist_dir = self.root / "sdk/js/aos-sdk/dist"

        if not src_dir.exists():
            return issues  # No JS SDK source

        if not dist_dir.exists():
            issues.append(
                Issue(
                    severity="error",
                    category="sdk_build",
                    message="JS SDK dist/ not found - must run 'npm run build'",
                    file=str(dist_dir),
                    suggestion="cd sdk/js/aos-sdk && npm run build",
                )
            )
            return issues

        # Get latest source modification time
        src_files = list(src_dir.rglob("*.ts"))
        if not src_files:
            return issues

        latest_src_mtime = max(f.stat().st_mtime for f in src_files)
        latest_src_file = max(src_files, key=lambda f: f.stat().st_mtime)

        # Get earliest dist modification time (conservative check)
        dist_files = list(dist_dir.glob("index.*"))
        if not dist_files:
            issues.append(
                Issue(
                    severity="error",
                    category="sdk_build",
                    message="JS SDK dist/ is empty - must run 'npm run build'",
                    file=str(dist_dir),
                    suggestion="cd sdk/js/aos-sdk && npm run build",
                )
            )
            return issues

        earliest_dist_mtime = min(f.stat().st_mtime for f in dist_files)

        # If any source is newer than dist, warn
        if latest_src_mtime > earliest_dist_mtime:
            issues.append(
                Issue(
                    severity="warning",
                    category="sdk_build",
                    message=f"JS SDK source ({latest_src_file.name}) modified after dist/",
                    file=str(latest_src_file),
                    suggestion="cd sdk/js/aos-sdk && npm run build",
                )
            )

        return issues

    # =========================================================================
    # FULL PREFLIGHT
    # =========================================================================

    def full_preflight(self, check_qualifiers: bool = True) -> Dict:
        """Run full preflight check on the project."""
        results = {
            "routes": [],
            "route_issues": [],
            "untyped_issues": [],
            "import_issues": [],
            "sdk_issues": [],
            "qualifier_issues": [],
            "summary": {},
        }

        # Route analysis
        routes, route_issues = self.analyze_routes()
        results["routes"] = [
            {"path": r.path, "method": r.method, "file": r.file, "line": r.line}
            for r in routes
        ]
        results["route_issues"] = route_issues

        # Untyped param warnings
        results["untyped_issues"] = self.check_untyped_params(routes)

        # Check all API files for imports
        api_path = self.root / "backend/app/api"
        if api_path.exists():
            for py_file in api_path.glob("*.py"):
                rel_path = str(py_file.relative_to(self.root))
                results["import_issues"].extend(self.analyze_imports(rel_path))

        # SDK build freshness check (PIN-125 PREV-18)
        results["sdk_issues"] = self.check_sdk_build_freshness()

        # Governance qualifier check (PIN-281 - System Gate)
        if check_qualifiers:
            results["qualifier_issues"] = self.check_governance_qualifiers()

        # Summary
        all_issues = route_issues + results["sdk_issues"]
        qualifier_errors = [
            i for i in results.get("qualifier_issues", []) if i.severity == "error"
        ]
        errors = [i for i in all_issues if i.severity == "error"] + qualifier_errors
        warnings = [i for i in all_issues if i.severity == "warning"]
        qualifier_warnings = [
            i for i in results.get("qualifier_issues", []) if i.severity == "warning"
        ]

        results["summary"] = {
            "total_routes": len(routes),
            "errors": len(errors),
            "warnings": len(warnings)
            + len(results["untyped_issues"])
            + len(qualifier_warnings),
            "sdk_issues": len(results["sdk_issues"]),
            "qualifier_errors": len(qualifier_errors),
            "qualifier_warnings": len(qualifier_warnings),
            "pass": len(errors) == 0,
        }

        return results

    # =========================================================================
    # REPORT
    # =========================================================================

    def print_report(self, results: Dict, verbose: bool = False):
        """Print a formatted report."""
        print("\n" + "=" * 60)
        print("  PREFLIGHT CHECK REPORT v2.0")
        print("=" * 60)

        route_issues = results.get("route_issues", [])
        errors = [i for i in route_issues if i.severity == "error"]
        fixed = [i for i in route_issues if i.severity == "suggestion"]

        # Route collisions (errors)
        if errors:
            print("\n🚨 ROUTE COLLISIONS:")
            for issue in errors:
                print(f"  [{issue.severity.upper()}] {issue.message}")
                if issue.suggestion:
                    print(f"           → {issue.suggestion}")
                print(f"           @ {issue.file}:{issue.line}")
        else:
            print("\n✅ No route collisions detected")

        # Correctly ordered routes
        if fixed:
            if verbose:
                print(f"\n✅ {len(fixed)} route pairs correctly ordered:")
                for issue in fixed:
                    print(f"  {issue.message}")
            else:
                print(
                    f"\n(+{len(fixed)} route pairs correctly ordered - use --verbose to see)"
                )

        # Untyped param warnings
        untyped = results.get("untyped_issues", [])
        if untyped and verbose:
            print(f"\n⚠️  UNTYPED PARAMETERS ({len(untyped)}):")
            for issue in untyped:
                print(f"  {issue.message}")
                if issue.suggestion:
                    print(f"    → {issue.suggestion}")

        # SDK build issues (PIN-125 PREV-18)
        sdk_issues = results.get("sdk_issues", [])
        if sdk_issues:
            sdk_errors = [i for i in sdk_issues if i.severity == "error"]
            sdk_warnings = [i for i in sdk_issues if i.severity == "warning"]
            if sdk_errors:
                print(f"\n🔴 SDK BUILD ERRORS ({len(sdk_errors)}):")
                for issue in sdk_errors:
                    print(f"  [{issue.category}] {issue.message}")
                    if issue.suggestion:
                        print(f"    → {issue.suggestion}")
            if sdk_warnings and verbose:
                print(f"\n⚠️  SDK BUILD WARNINGS ({len(sdk_warnings)}):")
                for issue in sdk_warnings:
                    print(f"  [{issue.category}] {issue.message}")
                    if issue.suggestion:
                        print(f"    → {issue.suggestion}")

        # Governance Qualifier issues (PIN-281 - System Gate)
        qualifier_issues = results.get("qualifier_issues", [])
        if qualifier_issues:
            qual_errors = [i for i in qualifier_issues if i.severity == "error"]
            qual_warnings = [i for i in qualifier_issues if i.severity == "warning"]
            if qual_errors:
                print(f"\n🚫 GOVERNANCE QUALIFIER GATE FAILED ({len(qual_errors)}):")
                for issue in qual_errors:
                    print(f"  [{issue.category}] {issue.message}")
                    if issue.suggestion:
                        print(f"    → {issue.suggestion}")
            if qual_warnings:
                print(f"\n⚠️  GOVERNANCE QUALIFIER WARNINGS ({len(qual_warnings)}):")
                for issue in qual_warnings:
                    print(f"  {issue.message}")
        else:
            print("\n✅ Governance qualifiers: No errors")

        # Summary
        summary = results.get("summary", {})
        print("\n" + "-" * 60)
        print(f"  Routes analyzed: {summary.get('total_routes', 0)}")
        print(f"  Errors: {summary.get('errors', 0)}")
        print(f"  Warnings: {summary.get('warnings', 0)}")
        if (
            summary.get("qualifier_errors", 0) > 0
            or summary.get("qualifier_warnings", 0) > 0
        ):
            print(
                f"  Qualifier issues: {summary.get('qualifier_errors', 0)} errors, {summary.get('qualifier_warnings', 0)} warnings"
            )
        print(f"  Status: {'✅ PASS' if summary.get('pass') else '❌ FAIL'}")
        print("=" * 60 + "\n")

        return summary.get("pass", True)


# =============================================================================
# CLI
# =============================================================================


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Pre-implementation evaluation v2.0")
    parser.add_argument("file", nargs="?", help="File or directory to analyze")
    parser.add_argument("--routes", action="store_true", help="Analyze routes only")
    parser.add_argument("--full", action="store_true", help="Full preflight check")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show all details")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--generate-hook", action="store_true", help="Generate runtime validation hook"
    )
    parser.add_argument("--root", default=".", help="Project root directory")
    parser.add_argument(
        "--qualifiers",
        "-q",
        nargs="*",
        metavar="CAP",
        help="Check governance qualifiers (GQ-L2-CONTRACT-READY). "
        "No args = check all, with args = check specific capabilities",
    )
    parser.add_argument(
        "--no-qualifiers",
        action="store_true",
        help="Skip governance qualifier checks in --full mode",
    )

    args = parser.parse_args()

    checker = PreflightChecker(args.root)

    if args.generate_hook:
        print(checker.generate_runtime_hook())
        return

    # Handle --qualifiers mode (standalone qualifier check)
    if args.qualifiers is not None:
        capabilities = args.qualifiers if args.qualifiers else None
        issues = checker.check_governance_qualifiers(capabilities)

        print("\n" + "=" * 60)
        print("  GOVERNANCE QUALIFIER CHECK (GQ-L2-CONTRACT-READY)")
        print("=" * 60)

        errors = [i for i in issues if i.severity == "error"]
        warnings = [i for i in issues if i.severity == "warning"]

        if errors:
            print(f"\n🚫 BLOCKED ({len(errors)} errors):")
            for issue in errors:
                print(f"  ✗ {issue.message}")
                if issue.suggestion:
                    print(f"    → {issue.suggestion}")
        elif warnings:
            print(f"\n⚠️  WARNINGS ({len(warnings)}):")
            for issue in warnings:
                print(f"  {issue.message}")
        else:
            print("\n✅ All specified capabilities are QUALIFIED")
            print("   L2 testing and product claims are PERMITTED")

        print("\n" + "=" * 60)
        print(f"  Status: {'❌ FAIL' if errors else '✅ PASS'}")
        print("=" * 60 + "\n")

        sys.exit(1 if errors else 0)

    if args.full:
        results = checker.full_preflight(check_qualifiers=not args.no_qualifiers)
        if args.json:
            # Convert Issue objects to dicts for JSON
            for key in [
                "route_issues",
                "untyped_issues",
                "import_issues",
                "qualifier_issues",
                "sdk_issues",
            ]:
                if key in results:
                    results[key] = [
                        {
                            "severity": i.severity,
                            "category": i.category,
                            "message": i.message,
                            "file": i.file,
                            "line": i.line,
                            "suggestion": i.suggestion,
                        }
                        for i in results[key]
                    ]
            print(json.dumps(results, indent=2))
        else:
            success = checker.print_report(results, verbose=args.verbose)
            sys.exit(0 if success else 1)

    elif args.routes:
        api_dir = args.file or "backend/app/api"
        routes, issues = checker.analyze_routes(api_dir)

        results = {
            "routes": [
                {"path": r.path, "method": r.method, "file": r.file, "line": r.line}
                for r in routes
            ],
            "route_issues": issues,
            "untyped_issues": checker.check_untyped_params(routes),
            "summary": {
                "total_routes": len(routes),
                "errors": len([i for i in issues if i.severity == "error"]),
                "warnings": len([i for i in issues if i.severity == "warning"]),
                "pass": len([i for i in issues if i.severity == "error"]) == 0,
            },
        }

        if args.json:
            for key in ["route_issues", "untyped_issues"]:
                results[key] = [
                    {
                        "severity": i.severity,
                        "category": i.category,
                        "message": i.message,
                        "file": i.file,
                        "line": i.line,
                        "suggestion": i.suggestion,
                    }
                    for i in results[key]
                ]
            print(json.dumps(results, indent=2))
        else:
            success = checker.print_report(results, verbose=args.verbose)
            sys.exit(0 if success else 1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
