#!/usr/bin/env python3
"""
Layer Validator - Detect Layer Violations in Codebase

Reference: PIN-240 (Seven-Layer Codebase Mental Model)

Layers (top to bottom):
  L1 — Product Experience (Frontend)
  L2 — Product APIs (Console / Public)
  L3 — Boundary Adapters (Translation)
  L4 — Domain Engines (System Truth)
  L5 — Execution & Workers
  L6 — Platform Substrate
  L7 — Fundamental Ops & Scripts

Violations detected:
  - L1 importing L4, L5, L6 (frontend calling domain/workers/platform)
  - L2 importing L1, L5 (API calling frontend or workers)
  - L3 importing L1, L2, L5 (adapter calling presentation or execution)
  - L4 importing L1, L2, L3 (domain knowing about products)
  - L5 importing L1, L2, L3 (workers knowing about products)

Usage:
  python scripts/ops/layer_validator.py                   # Scan all
  python scripts/ops/layer_validator.py --backend         # Backend only
  python scripts/ops/layer_validator.py --frontend        # Frontend only
  python scripts/ops/layer_validator.py --verbose         # Show all imports
  python scripts/ops/layer_validator.py --ci              # Exit 1 on violations
"""

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Layer definitions
LAYERS = {
    "L1": "Product Experience",
    "L2": "Product APIs",
    "L3": "Boundary Adapters",
    "L4": "Domain Engines",
    "L5": "Execution & Workers",
    "L6": "Platform Substrate",
    "L7": "Ops & Scripts",
}

# Layer classification rules (file path patterns)
LAYER_PATTERNS = {
    # Backend
    "backend/app/api/guard.py": "L2",
    "backend/app/api/customer_visibility.py": "L2",
    "backend/app/api/v1_killswitch.py": "L2",  # Actually L6 but labeled L2
    "backend/app/api/onboarding.py": "L2",
    "backend/app/api/predictions.py": "L2",
    "backend/app/api/": "L2",  # Default for API routes
    "backend/app/services/certificate.py": "L3",
    "backend/app/services/evidence_report.py": "L3",
    "backend/app/services/email_verification.py": "L3",
    "backend/app/services/prediction.py": "L3",
    "backend/app/services/policy_proposal.py": "L3",
    # Phase F-3: L3 Boundary Adapters (PIN-258)
    "backend/app/adapters/": "L3",
    "backend/app/adapters/runtime_adapter.py": "L3",
    "backend/app/adapters/workers_adapter.py": "L3",
    "backend/app/adapters/policy_adapter.py": "L3",
    "backend/app/services/pattern_detection.py": "L4",
    "backend/app/services/recovery_matcher.py": "L4",
    "backend/app/services/recovery_rule_engine.py": "L4",
    "backend/app/services/cost_anomaly_detector.py": "L4",
    # Phase E FIX-01: Reclassified from L5 to L4 (passed 10-point purity test)
    "backend/app/worker/simulate.py": "L4",
    # Phase E FIX-01: Extracted L4 domain engine from L5 failure_aggregation.py
    "backend/app/jobs/failure_classification_engine.py": "L4",
    # Phase E FIX-01: Graduation engine purity enforcement
    "backend/app/integrations/graduation_engine.py": "L4",
    # Phase E-4 Extraction #4: Claim decision domain engine
    "backend/app/services/claim_decision_engine.py": "L4",
    # Phase F-3: L4 Command Facades (PIN-258)
    "backend/app/commands/": "L4",
    "backend/app/commands/runtime_command.py": "L4",
    "backend/app/commands/worker_execution_command.py": "L4",
    "backend/app/commands/policy_command.py": "L4",
    "backend/app/worker/": "L5",
    "backend/app/workflow/": "L5",
    "backend/app/auth/": "L6",
    "backend/app/db/": "L6",
    "backend/app/models/": "L6",
    "backend/app/services/event_emitter.py": "L6",
    # Frontend
    "website/app-shell/src/products/ai-console/pages/": "L1",
    "website/app-shell/src/products/ai-console/app/": "L1",
    "website/app-shell/src/products/": "L1",
    "website/app-shell/src/components/": "L6",  # Shared UI = Platform
    "website/app-shell/src/lib/": "L6",
    "website/app-shell/src/api/": "L2",
    # Scripts
    "scripts/": "L7",
}

# Import patterns to detect
IMPORT_LAYER_HINTS = {
    # Backend imports
    "from app.api.guard": "L2",
    "from app.api.customer_visibility": "L2",
    "from app.api.v1_killswitch": "L2",
    "from app.api.": "L2",
    "from app.services.certificate": "L3",
    "from app.services.evidence_report": "L3",
    "from app.services.email_verification": "L3",
    "from app.services.prediction": "L3",
    "from app.services.policy_proposal": "L3",
    # Phase F-3: L3 Boundary Adapters (PIN-258)
    "from app.adapters": "L3",
    "from app.adapters.runtime_adapter": "L3",
    "from app.adapters.workers_adapter": "L3",
    "from app.adapters.policy_adapter": "L3",
    "from app.services.pattern_detection": "L4",
    "from app.services.recovery_matcher": "L4",
    "from app.services.recovery_rule_engine": "L4",
    "from app.services.cost_anomaly_detector": "L4",
    # Phase E FIX-01: Reclassified from L5 to L4 (passed 10-point purity test)
    "from app.worker.simulate": "L4",
    # Phase E FIX-01: Extracted L4 domain engine from L5 failure_aggregation.py
    "from app.jobs.failure_classification_engine": "L4",
    # Phase E FIX-01: Graduation engine purity enforcement
    "from app.integrations.graduation_engine": "L4",
    # Phase E-4 Extraction #4: Claim decision domain engine
    "from app.services.claim_decision_engine": "L4",
    # Phase F-3: L4 Command Facades (PIN-258)
    "from app.commands": "L4",
    "from app.commands.runtime_command": "L4",
    "from app.commands.worker_execution_command": "L4",
    "from app.commands.policy_command": "L4",
    "from app.worker": "L5",
    "from app.workflow": "L5",
    "from app.auth": "L6",
    "from app.db": "L6",
    "from app.models": "L6",
    "from app.services.event_emitter": "L6",
}

# Allowed imports (from -> to)
# Key = source layer, Value = set of allowed target layers
# Same-layer imports are always allowed (peers)
ALLOWED_IMPORTS = {
    "L1": {"L1", "L2", "L3"},  # Frontend can call APIs and adapters
    "L2": {"L2", "L3", "L4", "L6"},  # APIs can call adapters, domain, platform
    "L3": {"L3", "L4", "L6"},  # Adapters can call domain, platform
    "L4": {"L4", "L5", "L6"},  # Domain can call execution, platform
    # Phase R (PIN-263): L5→L4 FORBIDDEN — Workers execute, never decide
    # Enforcement: Step 5 Wave-1 (2026-01-01)
    # Escape: SIG-001 owner override via commit message
    "L5": {"L5", "L6"},  # Workers can ONLY call platform (L6) and peers (L5)
    "L6": {"L6"},  # Platform calls platform (peers)
    "L7": {"L1", "L2", "L3", "L4", "L5", "L6", "L7"},  # Ops can call anything
}


@dataclass
class Violation:
    """Represents a layer violation."""

    file: str
    line_number: int
    import_statement: str
    source_layer: str
    target_layer: str

    def __str__(self) -> str:
        return (
            f"{self.file}:{self.line_number}: "
            f"{self.source_layer} -> {self.target_layer} violation\n"
            f"  Import: {self.import_statement.strip()}"
        )


@dataclass
class ValidationResult:
    """Results from validation."""

    files_scanned: int = 0
    violations: List[Violation] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    imports_by_layer: Dict[str, List[str]] = field(default_factory=dict)


def get_file_layer(file_path: str) -> Optional[str]:
    """Determine which layer a file belongs to."""
    # Check specific patterns first (most specific to least)
    for pattern, layer in sorted(LAYER_PATTERNS.items(), key=lambda x: -len(x[0])):
        if pattern in file_path:
            return layer
    return None


def get_import_layer(import_line: str) -> Optional[str]:
    """Determine which layer an import targets."""
    for pattern, layer in IMPORT_LAYER_HINTS.items():
        if pattern in import_line:
            return layer
    return None


def extract_imports(file_path: Path) -> List[Tuple[int, str]]:
    """Extract import statements from a Python file."""
    imports = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(content.split("\n"), 1):
            stripped = line.strip()
            if stripped.startswith("from ") or stripped.startswith("import "):
                imports.append((i, stripped))
    except Exception:
        pass
    return imports


def check_violation(source_layer: str, target_layer: str) -> bool:
    """Check if importing from target_layer into source_layer is a violation."""
    if source_layer not in ALLOWED_IMPORTS:
        return False  # Unknown layer, can't validate
    return target_layer not in ALLOWED_IMPORTS[source_layer]


def validate_file(file_path: Path, verbose: bool = False) -> List[Violation]:
    """Validate a single file for layer violations."""
    violations = []
    rel_path = str(file_path)

    source_layer = get_file_layer(rel_path)
    if not source_layer:
        return []  # Can't classify file

    imports = extract_imports(file_path)

    for line_num, import_stmt in imports:
        target_layer = get_import_layer(import_stmt)
        if not target_layer:
            continue  # Can't classify import

        if check_violation(source_layer, target_layer):
            violations.append(
                Violation(
                    file=rel_path,
                    line_number=line_num,
                    import_statement=import_stmt,
                    source_layer=source_layer,
                    target_layer=target_layer,
                )
            )

    return violations


def validate_directory(
    root: Path,
    extensions: Set[str] = {".py"},
    exclude_patterns: Set[str] = {
        "__pycache__",
        ".git",
        "node_modules",
        "dist",
        ".venv",
        "venv",
    },
    verbose: bool = False,
) -> ValidationResult:
    """Validate all files in a directory."""
    result = ValidationResult()

    for file_path in root.rglob("*"):
        # Skip excluded directories
        if any(excl in str(file_path) for excl in exclude_patterns):
            continue

        # Only process matching extensions
        if file_path.suffix not in extensions:
            continue

        # Skip non-files
        if not file_path.is_file():
            continue

        result.files_scanned += 1

        violations = validate_file(file_path, verbose)
        result.violations.extend(violations)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Validate layer architecture in codebase",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Layers (PIN-240):
  L1 = Product Experience (pages, routes)
  L2 = Product APIs (console/public routes)
  L3 = Boundary Adapters (translation)
  L4 = Domain Engines (system truth)
  L5 = Execution & Workers
  L6 = Platform Substrate
  L7 = Ops & Scripts

Examples:
  %(prog)s                    # Validate all
  %(prog)s --backend          # Backend only
  %(prog)s --ci               # Exit 1 on violations
        """,
    )

    parser.add_argument("--backend", action="store_true", help="Validate backend only")
    parser.add_argument(
        "--frontend", action="store_true", help="Validate frontend only"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show all imports")
    parser.add_argument("--ci", action="store_true", help="Exit 1 if violations found")
    parser.add_argument("--path", type=str, default=".", help="Root path to scan")

    args = parser.parse_args()

    root = Path(args.path)

    # Determine what to scan
    if args.backend:
        scan_root = root / "backend"
        extensions = {".py"}
    elif args.frontend:
        scan_root = root / "website"
        extensions = {".tsx", ".ts"}
    else:
        scan_root = root
        extensions = {".py"}  # Start with Python only

    if not scan_root.exists():
        print(f"ERROR: Path not found: {scan_root}", file=sys.stderr)
        sys.exit(1)

    print("Layer Validator (PIN-240)")
    print(f"Scanning: {scan_root}")
    print("-" * 60)

    result = validate_directory(scan_root, extensions, verbose=args.verbose)

    print(f"Files scanned: {result.files_scanned}")
    print(f"Violations found: {len(result.violations)}")
    print()

    if result.violations:
        print("VIOLATIONS:")
        print("-" * 60)
        for v in result.violations:
            print(f"\n{v}")
        print()

        # Summary by type
        violation_types: Dict[str, int] = {}
        for v in result.violations:
            key = f"{v.source_layer} -> {v.target_layer}"
            violation_types[key] = violation_types.get(key, 0) + 1

        print("Summary by type:")
        for vtype, count in sorted(violation_types.items(), key=lambda x: -x[1]):
            src, tgt = vtype.split(" -> ")
            print(
                f"  {vtype}: {count} ({LAYERS.get(src, src)} imports {LAYERS.get(tgt, tgt)})"
            )

        if args.ci:
            sys.exit(1)
    else:
        print("No layer violations found!")
        print()
        print("Layer architecture is clean.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
