# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: scheduler
#   Execution: sync
# Role: Validate artifact intent declarations for completeness and correctness
# Callers: CI pipeline, pre-commit hooks, Claude
# Allowed Imports: L6 (filesystem)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-245 (Integration Integrity System)

"""
Intent Validator — Machine-Readable Intent Detection

This script validates that all code artifacts have proper intent declarations.
It enforces PRE-BUILD-001, PRE-BUILD-002, PRE-BUILD-003, and RUNTIME-003.

Usage:
    python scripts/ops/intent_validator.py --check <file_path>
    python scripts/ops/intent_validator.py --scan <directory>
    python scripts/ops/intent_validator.py --diff  # Check only changed files
    python scripts/ops/intent_validator.py --report  # Full compliance report

Exit codes:
    0 = All validations passed
    1 = Validation failures detected
    2 = Configuration error
"""

import os
import sys
import re
import yaml
import argparse
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Set
from enum import Enum

# Import incident logger
try:
    from architecture_incident_logger import log_incident
    INCIDENT_LOGGING_ENABLED = True
except ImportError:
    INCIDENT_LOGGING_ENABLED = False
    def log_incident(*args, **kwargs):
        pass  # Fallback if logger not available


class ValidationSeverity(Enum):
    BLOCKING = "BLOCKING"
    WARNING = "WARNING"
    INFO = "INFO"


class ViolationType(Enum):
    MISSING_INTENT = "MISSING_INTENT"
    INCOMPLETE_INTENT = "INCOMPLETE_INTENT"
    MISSING_LAYER = "MISSING_LAYER"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    MISSING_TEMPORAL = "MISSING_TEMPORAL"
    MISSING_HEADER = "MISSING_HEADER"
    INVALID_LAYER = "INVALID_LAYER"
    LAYER_IMPORT_VIOLATION = "LAYER_IMPORT_VIOLATION"


@dataclass
class ValidationResult:
    file_path: str
    valid: bool
    violations: List[Dict] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_violation(self, violation_type: ViolationType, message: str,
                      severity: ValidationSeverity = ValidationSeverity.BLOCKING):
        self.violations.append({
            "type": violation_type.value,
            "message": message,
            "severity": severity.value
        })
        if severity == ValidationSeverity.BLOCKING:
            self.valid = False


@dataclass
class IntentDeclaration:
    """Parsed intent declaration from ARTIFACT_INTENT.yaml or file header."""
    artifact_id: Optional[str] = None
    file_path: Optional[str] = None
    layer_declared: Optional[str] = None
    layer_confidence: Optional[str] = None
    layer_justification: Optional[str] = None
    temporal_trigger: Optional[str] = None
    temporal_execution: Optional[str] = None
    temporal_lifecycle: Optional[str] = None
    product_owner: Optional[str] = None
    product_slice: Optional[str] = None
    responsibility_role: Optional[str] = None
    allowed_layers: List[str] = field(default_factory=list)
    forbidden_layers: List[str] = field(default_factory=list)


# Valid values for each field
VALID_LAYERS = {"L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8"}
VALID_CONFIDENCE = {"high", "medium"}  # LOW is blocking
VALID_TRIGGERS = {"user", "api", "worker", "scheduler", "external"}
VALID_EXECUTION = {"sync", "async", "deferred"}
VALID_LIFECYCLE = {"request", "job", "long-running", "batch"}
VALID_PRODUCTS = {"ai-console", "system-wide", "product-builder", "ops-console"}
VALID_SLICES = {"surface", "adapter", "platform", "catalyst"}

# Layer import rules (what each layer CAN import)
LAYER_IMPORT_RULES = {
    "L1": {"L2"},
    "L2": {"L3", "L4", "L6"},
    "L3": {"L4", "L6"},
    "L4": {"L5", "L6"},
    "L5": {"L6"},
    "L6": set(),
    "L7": {"L6"},
    "L8": set(),  # Tests can import anything
}

# File extensions to validate
VALIDATED_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".yaml", ".yml", ".sh"}

# Directories to skip
SKIP_DIRECTORIES = {
    "__pycache__", "node_modules", ".git", ".venv", "venv",
    "dist", "build", ".pytest_cache", ".mypy_cache"
}

# Files to skip
SKIP_FILES = {"__init__.py", "conftest.py"}


class IntentValidator:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.intent_registry: Dict[str, IntentDeclaration] = {}
        self._load_intent_registry()

    def _load_intent_registry(self):
        """Load all ARTIFACT_INTENT declarations from the registry."""
        intent_dir = self.repo_root / "docs" / "artifact-intents"
        if intent_dir.exists():
            for intent_file in intent_dir.glob("*.yaml"):
                try:
                    with open(intent_file) as f:
                        data = yaml.safe_load(f)
                        if data and "file_path" in data:
                            intent = self._parse_intent_yaml(data)
                            self.intent_registry[data["file_path"]] = intent
                except Exception as e:
                    print(f"Warning: Could not load {intent_file}: {e}", file=sys.stderr)

    def _parse_intent_yaml(self, data: Dict) -> IntentDeclaration:
        """Parse ARTIFACT_INTENT.yaml format into IntentDeclaration."""
        intent = IntentDeclaration()
        intent.artifact_id = data.get("artifact_id")
        intent.file_path = data.get("file_path")

        layer = data.get("layer", {})
        intent.layer_declared = layer.get("declared")
        intent.layer_confidence = layer.get("confidence")
        intent.layer_justification = layer.get("justification")

        temporal = data.get("temporal", {})
        intent.temporal_trigger = temporal.get("trigger")
        intent.temporal_execution = temporal.get("execution")
        intent.temporal_lifecycle = temporal.get("lifecycle")

        product = data.get("product", {})
        intent.product_owner = product.get("owner")
        intent.product_slice = product.get("slice")

        responsibility = data.get("responsibility", {})
        intent.responsibility_role = responsibility.get("role")

        deps = data.get("dependencies", {})
        intent.allowed_layers = deps.get("allowed_layers", [])
        intent.forbidden_layers = deps.get("forbidden_layers", [])

        return intent

    def _parse_file_header(self, file_path: Path) -> Optional[IntentDeclaration]:
        """Extract intent declaration from file header comments."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(4096)  # Read first 4KB for header
        except Exception:
            return None

        intent = IntentDeclaration()
        intent.file_path = str(file_path.relative_to(self.repo_root))

        # Python/Shell header pattern
        if file_path.suffix in {".py", ".sh", ".yaml", ".yml"}:
            # Layer: L{x} — {name}
            layer_match = re.search(r"#\s*Layer:\s*(L\d)\s*[—-]\s*(.+)", content)
            if layer_match:
                intent.layer_declared = layer_match.group(1)

            # Product: {product}
            product_match = re.search(r"#\s*Product:\s*(\S+)", content)
            if product_match:
                intent.product_owner = product_match.group(1)

            # Temporal trigger and execution
            trigger_match = re.search(r"#\s*Trigger:\s*(\S+)", content)
            if trigger_match:
                intent.temporal_trigger = trigger_match.group(1)

            exec_match = re.search(r"#\s*Execution:\s*(\S+)", content)
            if exec_match:
                intent.temporal_execution = exec_match.group(1)

            # Role
            role_match = re.search(r"#\s*Role:\s*(.+)", content)
            if role_match:
                intent.responsibility_role = role_match.group(1).strip()

            # Allowed/Forbidden imports
            allowed_match = re.search(r"#\s*Allowed Imports:\s*(.+)", content)
            if allowed_match:
                intent.allowed_layers = [l.strip() for l in allowed_match.group(1).split(",")]

            forbidden_match = re.search(r"#\s*Forbidden Imports:\s*(.+)", content)
            if forbidden_match:
                intent.forbidden_layers = [l.strip() for l in forbidden_match.group(1).split(",")]

        # TypeScript/JavaScript header pattern
        elif file_path.suffix in {".ts", ".tsx", ".js", ".jsx"}:
            # JSDoc style: * Layer: L{x} — {name}
            layer_match = re.search(r"\*\s*Layer:\s*(L\d)\s*[—-]\s*(.+)", content)
            if layer_match:
                intent.layer_declared = layer_match.group(1)

            product_match = re.search(r"\*\s*Product:\s*(\S+)", content)
            if product_match:
                intent.product_owner = product_match.group(1)

            trigger_match = re.search(r"\*\s*Trigger:\s*(\S+)", content)
            if trigger_match:
                intent.temporal_trigger = trigger_match.group(1)

            exec_match = re.search(r"\*\s*Execution:\s*(\S+)", content)
            if exec_match:
                intent.temporal_execution = exec_match.group(1)

            role_match = re.search(r"\*\s*Role:\s*(.+)", content)
            if role_match:
                intent.responsibility_role = role_match.group(1).strip()

        # Check if we found anything meaningful
        if intent.layer_declared or intent.temporal_trigger:
            return intent
        return None

    def validate_file(self, file_path: Path) -> ValidationResult:
        """Validate a single file for intent compliance."""
        result = ValidationResult(
            file_path=str(file_path.relative_to(self.repo_root)),
            valid=True
        )

        # Skip non-validated extensions
        if file_path.suffix not in VALIDATED_EXTENSIONS:
            return result

        # Skip special files
        if file_path.name in SKIP_FILES:
            return result

        # Get intent from registry or file header
        rel_path = str(file_path.relative_to(self.repo_root))
        intent = self.intent_registry.get(rel_path) or self._parse_file_header(file_path)

        if intent is None:
            result.add_violation(
                ViolationType.MISSING_INTENT,
                f"No intent declaration found. Use ARTIFACT_INTENT.yaml or add file header.",
                ValidationSeverity.BLOCKING
            )
            return result

        # Validate layer declaration (PRE-BUILD-003)
        if not intent.layer_declared:
            result.add_violation(
                ViolationType.MISSING_LAYER,
                "Layer declaration missing. Must be L1-L8.",
                ValidationSeverity.BLOCKING
            )
        elif intent.layer_declared not in VALID_LAYERS:
            result.add_violation(
                ViolationType.INVALID_LAYER,
                f"Invalid layer '{intent.layer_declared}'. Must be one of: {VALID_LAYERS}",
                ValidationSeverity.BLOCKING
            )

        # Validate confidence (PRE-BUILD-003)
        if intent.layer_confidence and intent.layer_confidence.lower() not in VALID_CONFIDENCE:
            if intent.layer_confidence.lower() == "low":
                result.add_violation(
                    ViolationType.LOW_CONFIDENCE,
                    "Layer confidence is LOW. Cannot proceed without clarification.",
                    ValidationSeverity.BLOCKING
                )

        # Validate temporal declaration (PRE-BUILD-002)
        if not intent.temporal_trigger:
            result.add_violation(
                ViolationType.MISSING_TEMPORAL,
                "Temporal trigger missing. Must be: user|api|worker|scheduler|external",
                ValidationSeverity.BLOCKING
            )
        elif intent.temporal_trigger not in VALID_TRIGGERS:
            result.add_violation(
                ViolationType.MISSING_TEMPORAL,
                f"Invalid trigger '{intent.temporal_trigger}'. Must be one of: {VALID_TRIGGERS}",
                ValidationSeverity.BLOCKING
            )

        if not intent.temporal_execution:
            result.add_violation(
                ViolationType.MISSING_TEMPORAL,
                "Temporal execution mode missing. Must be: sync|async|deferred",
                ValidationSeverity.BLOCKING
            )
        elif intent.temporal_execution not in VALID_EXECUTION:
            result.add_violation(
                ViolationType.MISSING_TEMPORAL,
                f"Invalid execution mode '{intent.temporal_execution}'. Must be one of: {VALID_EXECUTION}",
                ValidationSeverity.BLOCKING
            )

        # Validate product owner (RUNTIME-003)
        if not intent.product_owner:
            result.add_violation(
                ViolationType.INCOMPLETE_INTENT,
                "Product owner missing. Must be: ai-console|system-wide|product-builder",
                ValidationSeverity.BLOCKING
            )

        # Validate role
        if not intent.responsibility_role or intent.responsibility_role.upper() == "TODO":
            result.add_violation(
                ViolationType.INCOMPLETE_INTENT,
                "Responsibility role missing or set to TODO.",
                ValidationSeverity.BLOCKING
            )

        return result

    def scan_directory(self, directory: Path) -> List[ValidationResult]:
        """Scan a directory recursively for intent violations."""
        results = []

        for root, dirs, files in os.walk(directory):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in SKIP_DIRECTORIES]

            for file in files:
                file_path = Path(root) / file
                if file_path.suffix in VALIDATED_EXTENSIONS:
                    result = self.validate_file(file_path)
                    if result.violations:  # Only include files with issues
                        results.append(result)

        return results

    def check_changed_files(self) -> List[ValidationResult]:
        """Check only files that have changed (git diff)."""
        try:
            # Get list of changed files
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.repo_root
            )
            changed_files = result.stdout.strip().split("\n")

            # Also check staged files
            result = subprocess.run(
                ["git", "diff", "--name-only", "--cached"],
                capture_output=True,
                text=True,
                cwd=self.repo_root
            )
            staged_files = result.stdout.strip().split("\n")

            all_changed = set(changed_files + staged_files)
            all_changed.discard("")

        except Exception as e:
            print(f"Warning: Could not get git diff: {e}", file=sys.stderr)
            return []

        results = []
        for file_path in all_changed:
            full_path = self.repo_root / file_path
            if full_path.exists() and full_path.suffix in VALIDATED_EXTENSIONS:
                result = self.validate_file(full_path)
                if result.violations:
                    results.append(result)

        return results

    def generate_report(self, results: List[ValidationResult]) -> str:
        """Generate a compliance report."""
        total_files = len(results)
        blocking_violations = sum(
            1 for r in results
            for v in r.violations
            if v["severity"] == "BLOCKING"
        )

        report = []
        report.append("=" * 70)
        report.append("INTENT VALIDATION REPORT")
        report.append("=" * 70)
        report.append(f"Files with violations: {total_files}")
        report.append(f"Blocking violations: {blocking_violations}")
        report.append("")

        if not results:
            report.append("All validated files have proper intent declarations.")
            return "\n".join(report)

        # Group by violation type
        by_type: Dict[str, List[str]] = {}
        for result in results:
            for violation in result.violations:
                vtype = violation["type"]
                if vtype not in by_type:
                    by_type[vtype] = []
                by_type[vtype].append(f"  {result.file_path}: {violation['message']}")

        for vtype, files in by_type.items():
            report.append(f"\n{vtype} ({len(files)} files)")
            report.append("-" * 40)
            for f in files[:10]:  # Limit to first 10
                report.append(f)
            if len(files) > 10:
                report.append(f"  ... and {len(files) - 10} more")

        report.append("")
        report.append("=" * 70)

        if blocking_violations > 0:
            report.append("RESULT: BLOCKED")
            report.append(f"{blocking_violations} blocking violations must be resolved.")
        else:
            report.append("RESULT: PASSED (with warnings)")

        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(
        description="Validate artifact intent declarations"
    )
    parser.add_argument(
        "--check",
        type=Path,
        help="Check a single file"
    )
    parser.add_argument(
        "--scan",
        type=Path,
        help="Scan a directory recursively"
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Check only changed files (git diff)"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate full compliance report"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("/root/agenticverz2.0"),
        help="Repository root directory"
    )

    args = parser.parse_args()

    validator = IntentValidator(args.repo_root)
    results = []

    if args.check:
        file_path = args.check if args.check.is_absolute() else args.repo_root / args.check
        result = validator.validate_file(file_path)
        results = [result] if result.violations else []

    elif args.scan:
        scan_path = args.scan if args.scan.is_absolute() else args.repo_root / args.scan
        results = validator.scan_directory(scan_path)

    elif args.diff:
        results = validator.check_changed_files()

    elif args.report:
        results = validator.scan_directory(args.repo_root / "backend" / "app")
        results += validator.scan_directory(args.repo_root / "website")

    else:
        parser.print_help()
        return 2

    # Output results
    if args.json:
        import json
        output = {
            "total_violations": len(results),
            "blocking": sum(1 for r in results for v in r.violations if v["severity"] == "BLOCKING"),
            "results": [
                {
                    "file": r.file_path,
                    "valid": r.valid,
                    "violations": r.violations
                }
                for r in results
            ]
        }
        print(json.dumps(output, indent=2))
    else:
        report = validator.generate_report(results)
        print(report)

    # Exit code and incident logging
    blocking = any(
        v["severity"] == "BLOCKING"
        for r in results
        for v in r.violations
    )

    # Log incidents for blocking violations
    if blocking and INCIDENT_LOGGING_ENABLED:
        for r in results:
            for v in r.violations:
                if v["severity"] == "BLOCKING":
                    # Map violation type to incident code
                    code_map = {
                        "MISSING_INTENT": "INTENT-001",
                        "INCOMPLETE_INTENT": "INTENT-002",
                        "MISSING_LAYER": "LAYER-001",
                        "LOW_CONFIDENCE": "LAYER-002",
                        "MISSING_TEMPORAL": "INTENT-003",
                        "MISSING_HEADER": "INTENT-001",
                        "INVALID_LAYER": "LAYER-003",
                        "LAYER_IMPORT_VIOLATION": "LAYER-004",
                    }
                    incident_code = code_map.get(v["type"], "INTENT-001")
                    log_incident(
                        code=incident_code,
                        file=r.file_path,
                        layer="unknown",  # Will be detected by validator
                        summary=v["message"],
                        source="intent_validator"
                    )

    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
