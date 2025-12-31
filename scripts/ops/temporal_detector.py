# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: scheduler
#   Execution: sync
# Role: Detect temporal violations through import pattern analysis
# Callers: CI pipeline, pre-commit hooks, Claude
# Allowed Imports: L6 (filesystem)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-245 (Integration Integrity System)

"""
Temporal Detector — Heuristic Detection of Temporal Violations

This script detects sync-async boundary violations by analyzing:
1. Import patterns (L1-L3 importing from L5)
2. Async function usage in sync contexts
3. Worker patterns leaking into API handlers
4. Background task creation in wrong layers

Enforces:
- RUNTIME-001: Sync-Async Boundary Guard
- RUNTIME-002: Async Leak Detection Guard

Usage:
    python scripts/ops/temporal_detector.py --check <file_path>
    python scripts/ops/temporal_detector.py --scan <directory>
    python scripts/ops/temporal_detector.py --diff
    python scripts/ops/temporal_detector.py --report

Exit codes:
    0 = No temporal violations
    1 = Temporal violations detected
    2 = Configuration error
"""

import os
import sys
import re
import ast
import argparse
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from enum import Enum

# Import incident logger
try:
    from architecture_incident_logger import log_incident
    INCIDENT_LOGGING_ENABLED = True
except ImportError:
    INCIDENT_LOGGING_ENABLED = False
    def log_incident(*args, **kwargs):
        pass  # Fallback if logger not available


class TemporalViolationType(Enum):
    SYNC_IMPORTING_ASYNC = "TV-001"  # Sync layer importing from L5
    API_AWAITING_WORKER = "TV-002"   # API handler awaiting worker
    HIDDEN_DEFERRED = "TV-003"       # Deferred execution hidden behind sync API
    BACKGROUND_IN_L1L2 = "TV-004"    # Background task creation in L1-L2
    UNDECLARED_TEMPORAL = "TV-005"   # Undeclared temporal behavior
    ASYNC_LEAK_UPWARD = "TV-006"     # Async semantics leaking upward


@dataclass
class TemporalViolation:
    file_path: str
    line_number: int
    violation_type: TemporalViolationType
    message: str
    severity: str = "BLOCKING"
    context: str = ""


@dataclass
class FileAnalysis:
    file_path: str
    layer: Optional[str] = None
    temporal_execution: Optional[str] = None
    imports: List[str] = field(default_factory=list)
    async_functions: List[str] = field(default_factory=list)
    await_calls: List[Tuple[int, str]] = field(default_factory=list)
    background_patterns: List[Tuple[int, str]] = field(default_factory=list)
    violations: List[TemporalViolation] = field(default_factory=list)


# Layer classification by directory path
LAYER_PATH_PATTERNS = {
    # L1: Frontend/UI
    "website/aos-console/console/src/products": "L1",
    "website/aos-console/console/src/pages": "L1",
    "website/aos-console/console/src/components": "L1",

    # L2: API routes
    "backend/app/api": "L2",
    "backend/app/routes": "L2",

    # L3: Adapters
    "backend/app/adapters": "L3",

    # L4: Domain engines
    "backend/app/domain": "L4",
    "backend/app/engines": "L4",
    "backend/app/policy": "L4",

    # L5: Workers/Execution
    "backend/app/worker": "L5",
    "backend/app/execution": "L5",
    "backend/app/jobs": "L5",

    # L6: Platform
    "backend/app/db": "L6",
    "backend/app/services": "L6",
    "backend/app/core": "L6",

    # L7: Ops
    "scripts/ops": "L7",
    "monitoring": "L7",

    # L8: Tests/CI
    "backend/tests": "L8",
    "scripts/ci": "L8",
}

# Import patterns that indicate L5 (worker/execution) code
L5_IMPORT_PATTERNS = [
    r"from\s+app\.worker",
    r"from\s+app\.execution",
    r"from\s+app\.jobs",
    r"import\s+.*worker",
    r"import\s+.*executor",
    r"from\s+celery",
    r"from\s+rq\s+import",
    r"from\s+dramatiq",
    r"from\s+huey",
]

# Patterns that indicate async execution in wrong contexts
ASYNC_LEAK_PATTERNS = [
    # Background task creation
    (r"BackgroundTasks?\s*\(", "BackgroundTasks instantiation"),
    (r"\.add_task\s*\(", "add_task() call"),
    (r"asyncio\.create_task\s*\(", "asyncio.create_task()"),
    (r"asyncio\.ensure_future\s*\(", "asyncio.ensure_future()"),
    (r"threading\.Thread\s*\(", "Thread creation"),
    (r"concurrent\.futures", "concurrent.futures usage"),
    (r"ProcessPoolExecutor", "ProcessPoolExecutor"),
    (r"ThreadPoolExecutor", "ThreadPoolExecutor"),

    # Worker dispatch patterns
    (r"\.delay\s*\(", "Celery delay()"),
    (r"\.apply_async\s*\(", "Celery apply_async()"),
    (r"\.enqueue\s*\(", "Task queue enqueue()"),
    (r"\.send\s*\(", "Message send()"),

    # Deferred execution
    (r"schedule\s*\(", "Scheduler usage"),
    (r"run_in_executor\s*\(", "run_in_executor()"),
]

# Patterns indicating sync context where async shouldn't be
SYNC_CONTEXT_PATTERNS = [
    (r"def\s+\w+\s*\([^)]*\)\s*:", "sync function definition"),
    (r"@app\.get", "sync GET endpoint"),
    (r"@app\.post", "sync POST endpoint"),
    (r"@router\.get", "sync GET route"),
    (r"@router\.post", "sync POST route"),
]


class TemporalDetector:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    def _detect_layer(self, file_path: Path) -> Optional[str]:
        """Detect layer from file path and header."""
        rel_path = str(file_path.relative_to(self.repo_root))

        # Check path patterns
        for pattern, layer in LAYER_PATH_PATTERNS.items():
            if rel_path.startswith(pattern):
                return layer

        # Try to read from file header
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(2048)

            # Python header
            match = re.search(r"#\s*Layer:\s*(L\d)", content)
            if match:
                return match.group(1)

            # TypeScript header
            match = re.search(r"\*\s*Layer:\s*(L\d)", content)
            if match:
                return match.group(1)

        except Exception:
            pass

        return None

    def _detect_temporal(self, file_path: Path) -> Optional[str]:
        """Detect temporal execution mode from file header."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(2048)

            match = re.search(r"#\s*Execution:\s*(\w+)", content)
            if match:
                return match.group(1).lower()

            match = re.search(r"\*\s*Execution:\s*(\w+)", content)
            if match:
                return match.group(1).lower()

        except Exception:
            pass

        return None

    def _extract_imports(self, content: str) -> List[str]:
        """Extract all import statements."""
        imports = []

        # Python imports
        for match in re.finditer(r"^(?:from\s+(\S+)\s+import|import\s+(\S+))", content, re.MULTILINE):
            module = match.group(1) or match.group(2)
            imports.append(module)

        # TypeScript imports
        for match in re.finditer(r"import\s+.*\s+from\s+['\"]([^'\"]+)['\"]", content):
            imports.append(match.group(1))

        return imports

    def _check_l5_imports(self, imports: List[str], layer: str) -> List[str]:
        """Check if any imports are from L5 (worker) modules."""
        l5_imports = []

        for imp in imports:
            for pattern in L5_IMPORT_PATTERNS:
                # Convert import to pattern-checkable format
                import_str = f"from {imp}" if not imp.startswith("import") else imp
                if re.search(pattern, import_str):
                    l5_imports.append(imp)
                    break

        return l5_imports

    def _find_async_patterns(self, content: str) -> List[Tuple[int, str, str]]:
        """Find async execution patterns with line numbers."""
        findings = []
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            for pattern, description in ASYNC_LEAK_PATTERNS:
                if re.search(pattern, line):
                    findings.append((line_num, description, line.strip()))

        return findings

    def _find_await_in_sync(self, content: str) -> List[Tuple[int, str]]:
        """Find await calls that might be in sync context."""
        findings = []
        lines = content.split('\n')
        in_sync_function = False
        current_indent = 0

        for line_num, line in enumerate(lines, 1):
            stripped = line.lstrip()

            # Check for sync function definition
            if re.match(r"def\s+\w+\s*\(", stripped) and "async" not in line:
                in_sync_function = True
                current_indent = len(line) - len(stripped)

            # Check for async function (resets sync context)
            if re.match(r"async\s+def", stripped):
                in_sync_function = False

            # Check for class definition (resets context)
            if re.match(r"class\s+", stripped):
                in_sync_function = False

            # Check indent to see if we're still in the function
            if stripped and len(line) - len(stripped) <= current_indent and not stripped.startswith('#'):
                if not re.match(r"def\s+", stripped):
                    in_sync_function = False

            # Look for await in sync context
            if in_sync_function and "await " in line:
                findings.append((line_num, line.strip()))

        return findings

    def analyze_file(self, file_path: Path) -> FileAnalysis:
        """Analyze a single file for temporal violations."""
        analysis = FileAnalysis(
            file_path=str(file_path.relative_to(self.repo_root))
        )

        # Skip non-Python files for detailed analysis
        if file_path.suffix not in {'.py', '.ts', '.tsx'}:
            return analysis

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return analysis

        # Detect layer and temporal mode
        analysis.layer = self._detect_layer(file_path)
        analysis.temporal_execution = self._detect_temporal(file_path)

        # Extract imports
        analysis.imports = self._extract_imports(content)

        # Check for L5 imports from sync layers (TV-001)
        if analysis.layer in {"L1", "L2", "L3"}:
            l5_imports = self._check_l5_imports(analysis.imports, analysis.layer)
            for imp in l5_imports:
                analysis.violations.append(TemporalViolation(
                    file_path=analysis.file_path,
                    line_number=0,
                    violation_type=TemporalViolationType.SYNC_IMPORTING_ASYNC,
                    message=f"Sync layer {analysis.layer} imports from L5 module: {imp}",
                    context=f"Import: {imp}"
                ))

        # Check for async patterns in wrong layers (TV-004)
        if analysis.layer in {"L1", "L2"}:
            async_patterns = self._find_async_patterns(content)
            for line_num, description, context in async_patterns:
                analysis.violations.append(TemporalViolation(
                    file_path=analysis.file_path,
                    line_number=line_num,
                    violation_type=TemporalViolationType.BACKGROUND_IN_L1L2,
                    message=f"Background task pattern in {analysis.layer}: {description}",
                    context=context
                ))

        # Check for await in sync functions (TV-002)
        await_in_sync = self._find_await_in_sync(content)
        for line_num, context in await_in_sync:
            analysis.violations.append(TemporalViolation(
                file_path=analysis.file_path,
                line_number=line_num,
                violation_type=TemporalViolationType.API_AWAITING_WORKER,
                message="await found in sync function context",
                context=context
            ))

        # Check for undeclared temporal (TV-005)
        if analysis.layer and analysis.layer in {"L1", "L2", "L3", "L4", "L5"}:
            if not analysis.temporal_execution:
                analysis.violations.append(TemporalViolation(
                    file_path=analysis.file_path,
                    line_number=0,
                    violation_type=TemporalViolationType.UNDECLARED_TEMPORAL,
                    message=f"Layer {analysis.layer} file has no temporal execution declaration",
                    severity="WARNING"
                ))

        return analysis

    def scan_directory(self, directory: Path) -> List[FileAnalysis]:
        """Scan a directory for temporal violations."""
        results = []
        skip_dirs = {"__pycache__", "node_modules", ".git", ".venv", "dist", "build"}

        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in skip_dirs]

            for file in files:
                if file.endswith(('.py', '.ts', '.tsx')):
                    file_path = Path(root) / file
                    analysis = self.analyze_file(file_path)
                    if analysis.violations:
                        results.append(analysis)

        return results

    def check_changed_files(self) -> List[FileAnalysis]:
        """Check only changed files."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.repo_root
            )
            changed = set(result.stdout.strip().split("\n"))

            result = subprocess.run(
                ["git", "diff", "--name-only", "--cached"],
                capture_output=True,
                text=True,
                cwd=self.repo_root
            )
            changed.update(result.stdout.strip().split("\n"))
            changed.discard("")

        except Exception:
            return []

        results = []
        for file_path in changed:
            full_path = self.repo_root / file_path
            if full_path.exists() and full_path.suffix in {'.py', '.ts', '.tsx'}:
                analysis = self.analyze_file(full_path)
                if analysis.violations:
                    results.append(analysis)

        return results

    def generate_report(self, results: List[FileAnalysis]) -> str:
        """Generate temporal violation report."""
        total_violations = sum(len(a.violations) for a in results)
        blocking = sum(
            1 for a in results
            for v in a.violations
            if v.severity == "BLOCKING"
        )

        report = []
        report.append("=" * 70)
        report.append("TEMPORAL VIOLATION REPORT")
        report.append("=" * 70)
        report.append(f"Files with violations: {len(results)}")
        report.append(f"Total violations: {total_violations}")
        report.append(f"Blocking violations: {blocking}")
        report.append("")

        if not results:
            report.append("No temporal violations detected.")
            return "\n".join(report)

        # Group by violation type
        by_type: Dict[str, List[TemporalViolation]] = {}
        for analysis in results:
            for v in analysis.violations:
                vtype = v.violation_type.value
                if vtype not in by_type:
                    by_type[vtype] = []
                by_type[vtype].append(v)

        for vtype, violations in sorted(by_type.items()):
            report.append(f"\n{vtype}: {TemporalViolationType(vtype).name} ({len(violations)} violations)")
            report.append("-" * 50)
            for v in violations[:5]:
                loc = f"{v.file_path}:{v.line_number}" if v.line_number else v.file_path
                report.append(f"  [{v.severity}] {loc}")
                report.append(f"    {v.message}")
                if v.context:
                    report.append(f"    Context: {v.context[:60]}...")
            if len(violations) > 5:
                report.append(f"  ... and {len(violations) - 5} more")

        report.append("")
        report.append("=" * 70)

        if blocking > 0:
            report.append("RESULT: BLOCKED")
            report.append(f"{blocking} temporal violations must be resolved.")
            report.append("")
            report.append("Resolution patterns:")
            report.append("  1. Add adapter layer between sync and async")
            report.append("  2. Change execution model (return job_id, poll for result)")
            report.append("  3. Restructure call hierarchy through domain layer")
        else:
            report.append("RESULT: PASSED (with warnings)")

        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(
        description="Detect temporal violations through import pattern analysis"
    )
    parser.add_argument("--check", type=Path, help="Check a single file")
    parser.add_argument("--scan", type=Path, help="Scan a directory")
    parser.add_argument("--diff", action="store_true", help="Check changed files only")
    parser.add_argument("--report", action="store_true", help="Full scan report")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("/root/agenticverz2.0"),
        help="Repository root"
    )

    args = parser.parse_args()

    detector = TemporalDetector(args.repo_root)
    results = []

    if args.check:
        file_path = args.check if args.check.is_absolute() else args.repo_root / args.check
        analysis = detector.analyze_file(file_path)
        results = [analysis] if analysis.violations else []

    elif args.scan:
        scan_path = args.scan if args.scan.is_absolute() else args.repo_root / args.scan
        results = detector.scan_directory(scan_path)

    elif args.diff:
        results = detector.check_changed_files()

    elif args.report:
        results = detector.scan_directory(args.repo_root / "backend" / "app")

    else:
        parser.print_help()
        return 2

    if args.json:
        import json
        output = {
            "total_violations": sum(len(a.violations) for a in results),
            "results": [
                {
                    "file": a.file_path,
                    "layer": a.layer,
                    "temporal": a.temporal_execution,
                    "violations": [
                        {
                            "type": v.violation_type.value,
                            "line": v.line_number,
                            "message": v.message,
                            "severity": v.severity
                        }
                        for v in a.violations
                    ]
                }
                for a in results
            ]
        }
        print(json.dumps(output, indent=2))
    else:
        report = detector.generate_report(results)
        print(report)

    # Exit code and incident logging
    blocking = any(
        v.severity == "BLOCKING"
        for a in results
        for v in a.violations
    )

    # Log incidents for blocking violations
    if blocking and INCIDENT_LOGGING_ENABLED:
        for a in results:
            for v in a.violations:
                if v.severity == "BLOCKING":
                    log_incident(
                        code=v.violation_type.value,  # e.g., TV-001
                        file=v.file_path,
                        layer=a.layer or "unknown",
                        summary=v.message,
                        source="temporal_detector"
                    )

    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
