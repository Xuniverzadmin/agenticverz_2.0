#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: HOC Authority Analyzer v1.0
# artifact_class: CODE
"""
HOC Authority Analyzer v1.0

A mechanical enforcer of authority contracts.
Does NOT infer intent. Does NOT use heuristics.

Rule = Layer × Forbidden Operation × Call-Site

References:
- AUTHORITY_VIOLATION_SPEC_V1.md
- RUNTIME_CONTEXT_MODEL.md
- L4_L5_CONTRACTS_V1.md
"""

import argparse
import ast
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import yaml
from datetime import datetime, timezone


# =============================================================================
# I. Core Data Model
# =============================================================================

class Layer(Enum):
    """Layer classification derived from file path."""
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"
    L5 = "L5"
    L5_WORKFLOW = "L5_workflow"
    L6 = "L6"
    UNKNOWN = "UNKNOWN"


class Severity(Enum):
    """Violation severity from AUTHORITY_VIOLATION_SPEC_V1.md."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ViolationType(Enum):
    """Violation types from AUTHORITY_VIOLATION_SPEC_V1.md."""
    TIME_LEAK = "TIME_LEAK"
    STATE_MACHINE_DUPLICATION = "STATE_MACHINE_DUPLICATION"
    TRANSACTION_BYPASS = "TRANSACTION_BYPASS"
    ORCHESTRATION_LEAK = "ORCHESTRATION_LEAK"
    AUTHORITY_LEAK = "AUTHORITY_LEAK"
    DECISION_VS_EXECUTION = "DECISION_VS_EXECUTION"


@dataclass
class Violation:
    """A detected authority violation."""
    file: str
    layer: str
    line: int
    call: str
    violation_type: ViolationType
    severity: Severity
    reason: str
    required_harness: Optional[str] = None
    confidence: str = "HIGH"

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "layer": self.layer,
            "line": self.line,
            "call": self.call,
            "violation": self.violation_type.value,
            "severity": self.severity.value,
            "reason": self.reason,
            "required_harness": self.required_harness,
            "confidence": self.confidence,
        }


@dataclass
class ScanResult:
    """Result of scanning a single file."""
    file: str
    layer: Layer
    violations: List[Violation] = field(default_factory=list)
    imports: Set[str] = field(default_factory=set)
    calls: List[Tuple[str, int]] = field(default_factory=list)


# =============================================================================
# II. Operation Registry (Authoritative - From Contracts)
# =============================================================================

# Forbidden operations per layer
# Derived directly from L4_L5_CONTRACTS_V1.md
FORBIDDEN_OPERATIONS: Dict[Layer, Dict[str, Tuple[ViolationType, Severity, str]]] = {
    Layer.L5: {
        # Transaction authority violations
        "session.commit": (
            ViolationType.TRANSACTION_BYPASS,
            Severity.CRITICAL,
            "L5 cannot commit transactions - L4 owns commit authority"
        ),
        ".commit()": (
            ViolationType.TRANSACTION_BYPASS,
            Severity.CRITICAL,
            "L5 cannot commit transactions - L4 owns commit authority"
        ),
        "session.rollback": (
            ViolationType.TRANSACTION_BYPASS,
            Severity.CRITICAL,
            "L5 cannot rollback transactions - L4 owns rollback authority"
        ),
        # Orchestration authority violations
        "asyncio.sleep": (
            ViolationType.ORCHESTRATION_LEAK,
            Severity.HIGH,
            "L5 cannot implement retry/backoff - L4 owns orchestration"
        ),
        "time.sleep": (
            ViolationType.ORCHESTRATION_LEAK,
            Severity.HIGH,
            "L5 cannot implement retry/backoff - L4 owns orchestration"
        ),
        # Time authority violations
        "datetime.now": (
            ViolationType.TIME_LEAK,
            Severity.HIGH,
            "L5 must use TimeContext.now() - direct datetime breaks replay"
        ),
        "datetime.utcnow": (
            ViolationType.TIME_LEAK,
            Severity.HIGH,
            "L5 must use TimeContext.now() - direct datetime breaks replay"
        ),
        "datetime.today": (
            ViolationType.TIME_LEAK,
            Severity.HIGH,
            "L5 must use TimeContext.now() - direct datetime breaks replay"
        ),
        # Authority leak violations
        "uuid.uuid4": (
            ViolationType.AUTHORITY_LEAK,
            Severity.HIGH,
            "L5 cannot generate IDs - IDs must come from context or L4"
        ),
        "uuid.uuid1": (
            ViolationType.AUTHORITY_LEAK,
            Severity.HIGH,
            "L5 cannot generate IDs - IDs must come from context or L4"
        ),
        "uuid4()": (
            ViolationType.AUTHORITY_LEAK,
            Severity.HIGH,
            "L5 cannot generate IDs - IDs must come from context or L4"
        ),
    },
    Layer.L6: {
        # Transaction authority violations
        "session.commit": (
            ViolationType.TRANSACTION_BYPASS,
            Severity.CRITICAL,
            "L6 cannot commit transactions - L4 owns commit authority"
        ),
        ".commit()": (
            ViolationType.TRANSACTION_BYPASS,
            Severity.CRITICAL,
            "L6 cannot commit transactions - L4 owns commit authority"
        ),
        "session.rollback": (
            ViolationType.TRANSACTION_BYPASS,
            Severity.CRITICAL,
            "L6 cannot rollback transactions - L4 owns rollback authority"
        ),
        # Time authority violations
        "datetime.now": (
            ViolationType.TIME_LEAK,
            Severity.HIGH,
            "L6 must use TimeContext.now() - direct datetime breaks replay"
        ),
        "datetime.utcnow": (
            ViolationType.TIME_LEAK,
            Severity.HIGH,
            "L6 must use TimeContext.now() - direct datetime breaks replay"
        ),
        "datetime.today": (
            ViolationType.TIME_LEAK,
            Severity.HIGH,
            "L6 must use TimeContext.now() - direct datetime breaks replay"
        ),
        # Authority leak violations
        "uuid.uuid4": (
            ViolationType.AUTHORITY_LEAK,
            Severity.CRITICAL,
            "L6 cannot generate IDs - IDs must come from context"
        ),
        "uuid.uuid1": (
            ViolationType.AUTHORITY_LEAK,
            Severity.CRITICAL,
            "L6 cannot generate IDs - IDs must come from context"
        ),
        "uuid4()": (
            ViolationType.AUTHORITY_LEAK,
            Severity.CRITICAL,
            "L6 cannot generate IDs - IDs must come from context"
        ),
    },
}

# Required context for operations
REQUIRES_CONTEXT: Dict[str, Tuple[str, str]] = {
    "datetime.now": ("TimeContext", "from app.hoc.cus.general.L5_utils.time import utc_now"),
    "datetime.utcnow": ("TimeContext", "from app.hoc.cus.general.L5_utils.time import utc_now"),
    "session.add": ("TransactionContext", "TransactionContext from L4"),
    "session.commit": ("RuntimeCoordinatorContract", "Only L4 may commit"),
}

# Severity mapping for violation types
SEVERITY_MAP: Dict[ViolationType, Severity] = {
    ViolationType.TIME_LEAK: Severity.HIGH,
    ViolationType.STATE_MACHINE_DUPLICATION: Severity.CRITICAL,
    ViolationType.TRANSACTION_BYPASS: Severity.CRITICAL,
    ViolationType.ORCHESTRATION_LEAK: Severity.CRITICAL,
    ViolationType.AUTHORITY_LEAK: Severity.HIGH,
    ViolationType.DECISION_VS_EXECUTION: Severity.MEDIUM,
}

# Required harness for each violation type
REQUIRED_HARNESS: Dict[ViolationType, str] = {
    ViolationType.TIME_LEAK: "from app.hoc.cus.general.L5_utils.time import utc_now",
    ViolationType.TRANSACTION_BYPASS: "from app.hoc.cus.general.L4_runtime.drivers.transaction_coordinator import RunCompletionTransaction",
    ViolationType.ORCHESTRATION_LEAK: "from app.hoc.cus.general.L4_runtime.engines.governance_orchestrator import GovernanceOrchestrator",
    ViolationType.STATE_MACHINE_DUPLICATION: "from app.hoc.cus.general.L5_workflow.contracts.engines.contract_engine import ContractStateMachine",
    ViolationType.AUTHORITY_LEAK: "ID/timestamp must come from RuntimeContext",
}


# =============================================================================
# III. Layer Detection (Header-First, Path-Fallback)
# =============================================================================

def _detect_layer_from_header(file_path: str) -> Optional[Layer]:
    """
    Detect layer from file header declaration.

    Looks for: # Layer: L{N} — ...

    Header declarations take precedence over folder path.
    This allows files to be architecturally reclassified without moving them.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            # Read first 30 lines (header section)
            for i, line in enumerate(f):
                if i > 30:
                    break
                line = line.strip()
                if line.startswith("# Layer:"):
                    # Parse "# Layer: L4 — ..." or "# Layer: L6 — ..."
                    if " L4 " in line or line.endswith(" L4"):
                        return Layer.L4
                    if " L5_workflow" in line.lower():
                        return Layer.L5_WORKFLOW
                    if " L5 " in line or line.endswith(" L5"):
                        return Layer.L5
                    if " L6 " in line or line.endswith(" L6"):
                        return Layer.L6
                    if " L3 " in line or line.endswith(" L3"):
                        return Layer.L3
                    if " L2 " in line or line.endswith(" L2"):
                        return Layer.L2
    except Exception:
        pass
    return None


def _detect_layer_from_path(file_path: str) -> Layer:
    """
    Detect layer from file path (fallback).
    Used when header doesn't declare layer.
    """
    path_str = str(file_path)

    # Check for specific layer folders
    if "/L4_runtime/" in path_str or "/L4_" in path_str:
        return Layer.L4
    if "/L5_workflow/" in path_str:
        return Layer.L5_WORKFLOW
    if "/L5_" in path_str:
        return Layer.L5
    if "/L6_" in path_str or "/L6_drivers/" in path_str:
        return Layer.L6
    if "/L3_" in path_str or "/L3_adapters/" in path_str:
        return Layer.L3
    if "/api/" in path_str:
        return Layer.L2

    return Layer.UNKNOWN


def detect_layer(file_path: str) -> Layer:
    """
    Detect layer from file.

    Priority:
    1. Header declaration (# Layer: L{N} — ...)
    2. Folder path pattern (/L{N}_/)

    Header-first allows architectural reclassification without file moves.
    """
    # First, check header declaration
    header_layer = _detect_layer_from_header(file_path)
    if header_layer is not None:
        return header_layer

    # Fall back to path-based detection
    return _detect_layer_from_path(file_path)


def get_domain(file_path: str) -> str:
    """Extract domain from file path."""
    path_str = str(file_path)

    domains = [
        "policies", "incidents", "analytics", "account",
        "activity", "logs", "integrations", "overview",
        "api_keys", "general"
    ]

    for domain in domains:
        # Check both absolute and relative paths
        if f"/{domain}/" in path_str or path_str.startswith(f"{domain}/"):
            return domain

    return "unknown"


# =============================================================================
# IV. AST Analysis (Mechanical)
# =============================================================================

def extract_imports(tree: ast.AST) -> Set[str]:
    """Extract all imported names from AST."""
    imports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
                if alias.asname:
                    imports.add(alias.asname)

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports.add(module)
            for alias in node.names:
                imports.add(alias.name)
                if alias.asname:
                    imports.add(alias.asname)
                # Full import path
                if module:
                    imports.add(f"{module}.{alias.name}")

    return imports


def extract_calls(tree: ast.AST) -> List[Tuple[str, int, str]]:
    """
    Extract all function calls from AST.
    Returns: [(call_string, line_number, enclosing_function), ...]
    """
    calls = []
    current_function = "<module>"

    class CallVisitor(ast.NodeVisitor):
        def __init__(self):
            self.current_function = "<module>"

        def visit_FunctionDef(self, node):
            old_func = self.current_function
            self.current_function = node.name
            self.generic_visit(node)
            self.current_function = old_func

        def visit_AsyncFunctionDef(self, node):
            old_func = self.current_function
            self.current_function = node.name
            self.generic_visit(node)
            self.current_function = old_func

        def visit_Call(self, node):
            try:
                call_str = ast.unparse(node.func)
                calls.append((call_str, node.lineno, self.current_function))
            except Exception:
                pass
            self.generic_visit(node)

    visitor = CallVisitor()
    visitor.visit(tree)

    return calls


def has_exception_handling_with_retry(tree: ast.AST) -> List[Tuple[int, str]]:
    """
    Detect try/except blocks that suggest orchestration patterns.
    Returns: [(line, pattern_description), ...]
    """
    patterns = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            # Check for retry patterns in except handlers
            for handler in node.handlers:
                handler_code = ast.unparse(handler) if handler.body else ""
                if any(keyword in handler_code.lower() for keyword in ["retry", "sleep", "backoff", "attempt"]):
                    patterns.append((node.lineno, "try/except with retry pattern"))

    return patterns


def detect_state_machine_patterns(tree: ast.AST) -> List[Tuple[int, str, str]]:
    """
    Detect state machine implementation patterns.
    Returns: [(line, class_name, pattern_type), ...]
    """
    patterns = []
    state_keywords = {
        "PENDING", "ACTIVE", "COMPLETED", "DRAFT", "APPROVED",
        "FAILED", "CANCELLED", "EXPIRED", "RUNNING", "QUEUED",
        "REJECTED", "ARCHIVED", "INACTIVE"
    }
    transition_methods = {
        "can_transition", "validate_transition", "is_valid_transition",
        "check_transition", "allowed_transitions", "transition_to",
        "change_state", "set_status", "update_status", "move_to_state"
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            has_state_enum = False
            has_transition_method = False

            for item in node.body:
                # Check for state-like enum values
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name) and target.id.upper() in state_keywords:
                            has_state_enum = True

                # Check for transition methods
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if item.name in transition_methods:
                        has_transition_method = True
                        patterns.append((
                            item.lineno,
                            node.name,
                            f"transition_method:{item.name}"
                        ))

            if has_state_enum and has_transition_method:
                patterns.append((
                    node.lineno,
                    node.name,
                    "state_machine_implementation"
                ))

    return patterns


# =============================================================================
# V. Violation Detection (Contract-Based)
# =============================================================================

def detect_violations(
    file_path: str,
    layer: Layer,
    calls: List[Tuple[str, int, str]],
    imports: Set[str],
    tree: ast.AST,
) -> List[Violation]:
    """
    Detect authority violations based on layer contracts.
    Rule = Layer × Forbidden Operation × Call-Site
    """
    violations = []
    relative_path = get_relative_path(file_path)

    # Skip L4 and L2 - they have authority
    if layer in (Layer.L4, Layer.L2, Layer.UNKNOWN):
        return violations

    # Get forbidden operations for this layer
    forbidden = FORBIDDEN_OPERATIONS.get(layer, {})

    # Also check L5 rules for L5_WORKFLOW
    if layer == Layer.L5_WORKFLOW:
        forbidden = {**FORBIDDEN_OPERATIONS.get(Layer.L5, {})}

    # Check each call against forbidden operations
    for call_str, line, func_name in calls:
        for forbidden_pattern, (violation_type, severity, reason) in forbidden.items():
            if forbidden_pattern in call_str:
                # Check if utc_now is imported (allows TIME_LEAK exceptions)
                if violation_type == ViolationType.TIME_LEAK:
                    if "utc_now" in imports or "TimeContext" in imports:
                        continue  # Already using authority

                violations.append(Violation(
                    file=relative_path,
                    layer=layer.value,
                    line=line,
                    call=call_str,
                    violation_type=violation_type,
                    severity=severity,
                    reason=reason,
                    required_harness=REQUIRED_HARNESS.get(violation_type),
                    confidence="HIGH",
                ))

    # Detect state machine duplication (L5 only, not L5_workflow)
    if layer == Layer.L5:
        state_patterns = detect_state_machine_patterns(tree)
        for line, class_name, pattern_type in state_patterns:
            if "state_machine_implementation" in pattern_type:
                # Check if importing from general state authority
                if not any("contract_engine" in imp or "ContractStateMachine" in imp for imp in imports):
                    violations.append(Violation(
                        file=relative_path,
                        layer=layer.value,
                        line=line,
                        call=f"class {class_name}",
                        violation_type=ViolationType.STATE_MACHINE_DUPLICATION,
                        severity=Severity.CRITICAL,
                        reason=f"State machine in L5 must use general/L5_workflow authority",
                        required_harness=REQUIRED_HARNESS.get(ViolationType.STATE_MACHINE_DUPLICATION),
                        confidence="MEDIUM",
                    ))

    # Detect orchestration leaks (try/except with retry)
    if layer in (Layer.L5, Layer.L6):
        retry_patterns = has_exception_handling_with_retry(tree)
        for line, pattern in retry_patterns:
            violations.append(Violation(
                file=relative_path,
                layer=layer.value,
                line=line,
                call=pattern,
                violation_type=ViolationType.ORCHESTRATION_LEAK,
                severity=Severity.CRITICAL,
                reason="Retry/backoff logic belongs in L4 orchestrator",
                required_harness=REQUIRED_HARNESS.get(ViolationType.ORCHESTRATION_LEAK),
                confidence="MEDIUM",
            ))

    return violations


def get_relative_path(file_path: str) -> str:
    """Convert absolute path to relative path from hoc/cus/."""
    path_str = str(file_path)
    if "/hoc/cus/" in path_str:
        return path_str.split("/hoc/cus/")[1]
    if "/hoc/" in path_str:
        return path_str.split("/hoc/")[1]
    return path_str


# =============================================================================
# VI. Scanner
# =============================================================================

def scan_file(file_path: Path) -> Optional[ScanResult]:
    """Scan a single Python file for authority violations."""
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"  Warning: Could not parse {file_path}: {e}", file=sys.stderr)
        return None

    layer = detect_layer(str(file_path))
    imports = extract_imports(tree)
    calls = extract_calls(tree)
    violations = detect_violations(str(file_path), layer, calls, imports, tree)

    return ScanResult(
        file=str(file_path),
        layer=layer,
        violations=violations,
        imports=imports,
        calls=[(c[0], c[1]) for c in calls],
    )


def scan_directory(
    root_path: Path,
    domain: Optional[str] = None,
    verbose: bool = False,
) -> List[ScanResult]:
    """Scan all Python files in directory."""
    results = []

    # Find all Python files in hoc/cus/
    hoc_path = root_path / "backend" / "app" / "hoc" / "cus"
    if not hoc_path.exists():
        print(f"Error: HOC path not found: {hoc_path}", file=sys.stderr)
        return results

    # Filter by domain if specified
    if domain:
        search_path = hoc_path / domain
        if not search_path.exists():
            print(f"Error: Domain not found: {search_path}", file=sys.stderr)
            return results
    else:
        search_path = hoc_path

    python_files = list(search_path.rglob("*.py"))

    if verbose:
        print(f"Scanning {len(python_files)} files in {search_path}")

    for file_path in python_files:
        # Skip __pycache__ and test files
        if "__pycache__" in str(file_path):
            continue
        if "/tests/" in str(file_path):
            continue

        result = scan_file(file_path)
        if result:
            results.append(result)

            if verbose and result.violations:
                print(f"  {get_relative_path(str(file_path))}: {len(result.violations)} violations")

    return results


# =============================================================================
# VII. Output Generation
# =============================================================================

def generate_report(
    results: List[ScanResult],
    output_format: str = "yaml",
) -> dict:
    """Generate violation report."""
    all_violations = []
    for result in results:
        all_violations.extend(result.violations)

    # Group by severity
    by_severity = {s.value: [] for s in Severity}
    for v in all_violations:
        by_severity[v.severity.value].append(v.to_dict())

    # Group by domain
    by_domain = {}
    for v in all_violations:
        domain = get_domain(v.file)
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append(v.to_dict())

    # Group by violation type
    by_type = {t.value: [] for t in ViolationType}
    for v in all_violations:
        by_type[v.violation_type.value].append(v.to_dict())

    # Count by layer
    by_layer = {}
    for result in results:
        layer = result.layer.value
        if layer not in by_layer:
            by_layer[layer] = {"files": 0, "violations": 0}
        by_layer[layer]["files"] += 1
        by_layer[layer]["violations"] += len(result.violations)

    report = {
        "scan_metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "script_version": "1.0.0",
            "files_scanned": len(results),
            "total_violations": len(all_violations),
            "spec_reference": "AUTHORITY_VIOLATION_SPEC_V1.md",
            "context_reference": "RUNTIME_CONTEXT_MODEL.md",
            "contracts_reference": "L4_L5_CONTRACTS_V1.md",
        },
        "summary": {
            "by_severity": {k: len(v) for k, v in by_severity.items() if v},
            "by_type": {k: len(v) for k, v in by_type.items() if v},
            "by_domain": {k: len(v) for k, v in by_domain.items()},
            "by_layer": by_layer,
        },
        "violations": {
            "critical": by_severity.get("CRITICAL", []),
            "high": by_severity.get("HIGH", []),
            "medium": by_severity.get("MEDIUM", []),
            "low": by_severity.get("LOW", []),
        },
        "by_domain": by_domain,
        "by_type": {k: v for k, v in by_type.items() if v},
    }

    return report


def write_report(report: dict, output_path: Path) -> None:
    """Write report to file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        yaml.dump(report, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"Report written to: {output_path}")


def print_summary(report: dict) -> None:
    """Print summary to console."""
    meta = report["scan_metadata"]
    summary = report["summary"]

    print("\n" + "=" * 60)
    print("HOC AUTHORITY ANALYZER - SCAN COMPLETE")
    print("=" * 60)
    print(f"Files scanned: {meta['files_scanned']}")
    print(f"Total violations: {meta['total_violations']}")
    print()

    if summary["by_severity"]:
        print("By Severity:")
        for severity, count in summary["by_severity"].items():
            print(f"  {severity}: {count}")
        print()

    if summary["by_type"]:
        print("By Violation Type:")
        for vtype, count in summary["by_type"].items():
            print(f"  {vtype}: {count}")
        print()

    if summary["by_domain"]:
        print("By Domain:")
        for domain, count in sorted(summary["by_domain"].items(), key=lambda x: -x[1]):
            if count > 0:
                print(f"  {domain}: {count}")
        print()

    # Print critical violations
    critical = report["violations"].get("critical", [])
    if critical:
        print("CRITICAL VIOLATIONS:")
        for v in critical[:10]:  # Show first 10
            print(f"  {v['file']}:{v['line']} - {v['violation']} - {v['call']}")
        if len(critical) > 10:
            print(f"  ... and {len(critical) - 10} more")
        print()


# =============================================================================
# VIII. CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="HOC Authority Analyzer - Contract Enforcer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full scan
  python hoc_authority_analyzer.py --mode full

  # Single domain
  python hoc_authority_analyzer.py --mode full --domain policies

  # CI mode (fail on CRITICAL)
  python hoc_authority_analyzer.py --mode full --check --fail-on CRITICAL

  # Verbose output
  python hoc_authority_analyzer.py --mode full --verbose
        """
    )

    parser.add_argument(
        "--mode",
        choices=["full", "datetime", "transaction", "orchestration", "state"],
        default="full",
        help="Scan mode (default: full)"
    )
    parser.add_argument(
        "--domain",
        help="Scan specific domain only"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="CI mode - exit 1 if violations found at fail-on level"
    )
    parser.add_argument(
        "--fail-on",
        choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        default="CRITICAL",
        help="Severity level to fail on in CI mode (default: CRITICAL)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/architecture/hoc"),
        help="Output directory for report"
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        help="Output file path (overrides output-dir)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Repository root path"
    )

    args = parser.parse_args()

    # Determine root path
    root_path = args.root.resolve()
    if not (root_path / "backend").exists():
        # Try parent directories
        for parent in [root_path.parent, root_path.parent.parent]:
            if (parent / "backend").exists():
                root_path = parent
                break

    print(f"Repository root: {root_path}")

    # Scan
    results = scan_directory(
        root_path,
        domain=args.domain,
        verbose=args.verbose,
    )

    # Generate report
    report = generate_report(results)

    # Write report
    if args.output_file:
        output_path = args.output_file
    else:
        output_path = root_path / args.output_dir / "HOC_AUTHORITY_VIOLATIONS.yaml"

    write_report(report, output_path)

    # Print summary
    print_summary(report)

    # CI mode check
    if args.check:
        severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        fail_index = severity_order.index(args.fail_on)

        for i, severity in enumerate(severity_order):
            if i <= fail_index:
                count = report["summary"]["by_severity"].get(severity, 0)
                if count > 0:
                    print(f"\nCI FAILURE: {count} {severity} violations found")
                    sys.exit(1)

        print("\nCI PASSED: No violations at or above threshold")
        sys.exit(0)


if __name__ == "__main__":
    main()
