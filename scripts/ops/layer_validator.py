#!/usr/bin/env python3
"""
BLCA — Bidirectional Layer Consistency Auditor

Reference: HOC_LAYER_TOPOLOGY_V1.md (v1.2.0)
Reference: PIN-240 (Seven-Layer Codebase Mental Model)

This tool enforces the HOC Layer Topology rules:

1. Layer import boundaries (L1-L8)
2. L4/L5 engines cannot import sqlalchemy/sqlmodel at runtime
3. File naming conventions (*_service.py is BANNED)
4. File header requirements (# Layer: declaration)
5. HOC-specific import rules:
   - L2.1 facades cannot import L3-L7
   - L5 engines cannot import ORM models directly
   - L5 workers cannot import L4 runtime
   - HOC files cannot import from legacy app.services
6. SEMANTIC LAYER VALIDATION (NEW - 2026-01-24):
   - HEADER_CLAIM_MISMATCH: Header claims don't match code behavior
     - L2 claims require HTTP route decorators
     - L6 claims require database operations
   - HEADER_LOCATION_MISMATCH: Header claims don't match file location
     - L2 files must be in api/, not engines/
     - L5 engines must be in engines/, not drivers/

Violation Types:
  MISSING_HEADER       - HOC file missing layer header (WARNING)
  BANNED_NAMING        - *_service.py naming (ERROR)
  SQLALCHEMY_RUNTIME   - L4/L5 with sqlalchemy outside TYPE_CHECKING (ERROR)
  LEGACY_IMPORT        - HOC importing from app.services (ERROR)
  LAYER_BOUNDARY       - Import violates layer rules (ERROR)
  HEADER_CLAIM_MISMATCH   - Code behavior doesn't match header claim (ERROR)
  HEADER_LOCATION_MISMATCH - File location doesn't match header claim (ERROR)

Usage:
  python scripts/ops/layer_validator.py                   # Scan all
  python scripts/ops/layer_validator.py --backend         # Backend only
  python scripts/ops/layer_validator.py --hoc             # HOC files only
  python scripts/ops/layer_validator.py --verbose         # Show details
  python scripts/ops/layer_validator.py --ci              # Exit 1 on violations
"""

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# =============================================================================
# HOC Layer Definitions (from HOC_LAYER_TOPOLOGY_V1.md)
# =============================================================================

LAYERS = {
    "L1": "Frontend",
    "L2.1": "API Facade",
    "L2": "Product APIs",
    "L3": "Boundary Adapters",
    "L4": "Governed Runtime / Domain Engines",
    "L5": "Engines / Workers / Schemas",
    "L6": "Database Drivers",
    "L7": "Models",
    "L8": "Database",
}

# =============================================================================
# HOC Path-based Layer Classification
# =============================================================================

HOC_LAYER_PATTERNS = {
    # L2.1 — API Facades
    "houseofcards/api/facades/": "L2.1",
    # L2 — APIs
    "houseofcards/api/customer/": "L2",
    "houseofcards/api/founder/": "L2",
    "houseofcards/api/internal/": "L2",
    # L3 — Adapters
    "/adapters/": "L3",
    # L4 — Runtime (in general/)
    "/general/runtime/": "L4",
    # L4 — Domain Facades (facades/ within domain, not api/facades)
    # These are L4 because they orchestrate but don't touch HTTP
    # L5 — Engines, Workers, Schemas
    "/engines/": "L5",
    "/workers/": "L5",
    "/schemas/": "L5",
    # L6 — Drivers
    "/drivers/": "L6",
    # L7 — Models
    "app/models/": "L7",
    "app/customer/models/": "L7",
    "app/founder/models/": "L7",
    "app/internal/models/": "L7",
}

# Legacy patterns (for backwards compatibility)
LEGACY_LAYER_PATTERNS = {
    "backend/app/api/": "L2",
    "backend/app/services/": "L4",  # Legacy services treated as L4
    "backend/app/adapters/": "L3",
    "backend/app/worker/": "L5",
    "backend/app/workflow/": "L5",
    "backend/app/auth/": "L6",
    "backend/app/db/": "L6",
    "backend/app/models/": "L7",
    "scripts/": "L7",
}

# =============================================================================
# Import Rules (HOC_LAYER_TOPOLOGY_V1.md Section 7)
# =============================================================================

# Allowed imports: source_layer -> set of allowed target layers
ALLOWED_IMPORTS = {
    "L1": {"L1", "L2.1"},
    "L2.1": {"L2.1", "L2"},  # Facades can ONLY import L2 APIs
    "L2": {"L2", "L3"},  # APIs import Adapters
    "L3": {"L3", "L4", "L5", "L6"},  # Adapters can cross-domain
    "L4": {"L4", "L5", "L6"},  # Runtime imports Engines, Drivers
    "L5": {"L5", "L6"},  # Engines/Workers import Drivers
    "L6": {"L6", "L7"},  # Drivers import Models
    "L7": {"L7"},  # Models are leaf
}

# =============================================================================
# Forbidden Import Patterns (Critical Rules)
# =============================================================================

# L4/L5 engines CANNOT import these at runtime
FORBIDDEN_RUNTIME_IMPORTS = {
    "sqlalchemy",
    "sqlmodel",
    "from sqlalchemy",
    "from sqlmodel",
}

# HOC files cannot import from legacy namespaces
FORBIDDEN_HOC_IMPORTS = {
    "from app.services.",
    "import app.services.",
}

# =============================================================================
# Naming Convention Rules
# =============================================================================

# BANNED filename patterns
BANNED_FILENAME_PATTERNS = [
    r".*_service\.py$",  # *_service.py is BANNED in HOC
]

# Required filename patterns per layer
REQUIRED_PATTERNS = {
    "L5": [r".*_engine\.py$", r".*_worker\.py$", r".*_schema\.py$", r".*\.py$"],
    "L6": [r".*_driver\.py$", r".*_store\.py$", r".*\.py$"],
}

# =============================================================================
# Violation Types
# =============================================================================


@dataclass
class Violation:
    """Represents a layer violation."""

    file: str
    line_number: int
    violation_type: str
    message: str
    severity: str = "ERROR"  # ERROR, WARNING

    def __str__(self) -> str:
        prefix = "⚠️ " if self.severity == "WARNING" else "❌ "
        return f"{prefix}[{self.violation_type}] {self.file}:{self.line_number}\n   {self.message}"


@dataclass
class ValidationResult:
    """Results from validation."""

    files_scanned: int = 0
    violations: List[Violation] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return len([v for v in self.violations if v.severity == "ERROR"])

    @property
    def warning_count(self) -> int:
        return len([v for v in self.violations if v.severity == "WARNING"])


# =============================================================================
# Layer Detection
# =============================================================================


def get_layer_from_header(file_path: Path) -> Optional[str]:
    """Extract layer from file header (# Layer: L{x})."""
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.split("\n")[:50]  # Check first 50 lines

        for line in lines:
            # Match patterns like "# Layer: L4", "# Layer: L6 — Platform Substrate"
            match = re.match(r"#\s*Layer:\s*(L\d(?:\.\d)?)", line, re.IGNORECASE)
            if match:
                return match.group(1).upper()
    except Exception:
        pass
    return None


def get_layer_from_path(file_path: str) -> Optional[str]:
    """Determine layer from file path patterns."""
    # Check HOC patterns first (more specific)
    for pattern, layer in sorted(HOC_LAYER_PATTERNS.items(), key=lambda x: -len(x[0])):
        if pattern in file_path:
            return layer

    # Check legacy patterns
    for pattern, layer in sorted(LEGACY_LAYER_PATTERNS.items(), key=lambda x: -len(x[0])):
        if pattern in file_path:
            return layer

    return None


def get_file_layer(file_path: Path) -> Tuple[Optional[str], str]:
    """
    Get layer for a file.

    Returns: (layer, source) where source is "header" or "path"
    """
    # Prefer header declaration
    header_layer = get_layer_from_header(file_path)
    if header_layer:
        return header_layer, "header"

    # Fall back to path-based detection
    path_layer = get_layer_from_path(str(file_path))
    return path_layer, "path"


# =============================================================================
# Semantic Layer Validation (Header Claim Verification)
# =============================================================================

# Patterns that indicate L2 (HTTP route handlers)
L2_INDICATORS = {
    "decorators": [
        r"@router\.",
        r"@app\.(get|post|put|delete|patch|options|head)",
        r"@api_router\.",
        r"from fastapi import.*Router",
        r"from starlette",
    ],
    "imports": [
        r"from fastapi import",
        r"from fastapi\.routing",
    ],
}

# Patterns that indicate L6 (Database drivers)
L6_INDICATORS = {
    "imports": [
        r"from sqlalchemy",
        r"from sqlmodel",
        r"import sqlalchemy",
        r"import sqlmodel",
    ],
    "code": [
        r"\.execute\(",
        r"select\(",
        r"insert\(",
        r"update\(",
        r"delete\(",
        r"AsyncSession",
        r"Session",
    ],
}

# Patterns that indicate business logic (L5 Engine behavior)
L5_ENGINE_INDICATORS = {
    "code": [
        r"def (process|handle|compute|calculate|validate|check|decide|evaluate)",
        r"if .+ (and|or) .+:",  # Complex conditionals
        r"for .+ in .+:",  # Iteration logic
    ],
}


def analyze_code_semantics(file_path: Path) -> Dict[str, List[str]]:
    """
    Analyze code to determine what layer behaviors are present.

    Returns dict with keys: 'l2_evidence', 'l5_evidence', 'l6_evidence'
    """
    evidence = {
        "l2_evidence": [],
        "l5_evidence": [],
        "l6_evidence": [],
    }

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Check L2 indicators (HTTP)
            for pattern in L2_INDICATORS["decorators"]:
                if re.search(pattern, stripped):
                    evidence["l2_evidence"].append(f"Line {i}: {stripped[:80]}")
            for pattern in L2_INDICATORS["imports"]:
                if re.search(pattern, stripped):
                    evidence["l2_evidence"].append(f"Line {i}: {stripped[:80]}")

            # Check L6 indicators (DB)
            for pattern in L6_INDICATORS["imports"]:
                if re.search(pattern, stripped):
                    evidence["l6_evidence"].append(f"Line {i}: {stripped[:80]}")
            for pattern in L6_INDICATORS["code"]:
                if re.search(pattern, stripped):
                    evidence["l6_evidence"].append(f"Line {i}: {stripped[:80]}")

            # Check L5 engine indicators (business logic)
            for pattern in L5_ENGINE_INDICATORS["code"]:
                if re.search(pattern, stripped):
                    evidence["l5_evidence"].append(f"Line {i}: {stripped[:80]}")

    except Exception:
        pass

    return evidence


def validate_header_claim(
    file_path: Path,
    declared_layer: str,
    evidence: Dict[str, List[str]]
) -> List[Violation]:
    """
    Validate that declared layer matches code behavior.

    NEW: This catches cases like knowledge_sdk.py claiming L2
    but having zero HTTP handling code.
    """
    violations = []
    rel_path = str(file_path)
    filename = file_path.name

    # Skip __init__.py files (they're structural)
    if filename == "__init__.py":
        return violations

    # L2 Claim Validation: Must have HTTP evidence
    if declared_layer == "L2":
        has_http = len(evidence["l2_evidence"]) > 0
        path_is_api = "/api/" in rel_path and "/facades/" not in rel_path

        if not has_http and not path_is_api:
            violations.append(Violation(
                file=rel_path,
                line_number=1,
                violation_type="HEADER_CLAIM_MISMATCH",
                message=(
                    f"File declares L2 (Product APIs) but has NO HTTP handling evidence.\n"
                    f"   L2 requires: HTTP route decorators (@router.*, @app.*)\n"
                    f"   Found: 0 HTTP indicators\n"
                    f"   Possible fix: Reclassify to correct layer (L3/L5) based on actual behavior"
                ),
                severity="ERROR",
            ))

    # L2.1 Claim Validation: Must be in facades path, no HTTP handlers
    if declared_layer == "L2.1":
        if len(evidence["l2_evidence"]) > 0:
            # L2.1 facades organize routers, they don't define routes
            has_route_defs = any("@router." in e or "@app." in e for e in evidence["l2_evidence"])
            if has_route_defs:
                violations.append(Violation(
                    file=rel_path,
                    line_number=1,
                    violation_type="HEADER_CLAIM_MISMATCH",
                    message=(
                        f"File declares L2.1 (API Facade) but defines HTTP routes.\n"
                        f"   L2.1 facades ORGANIZE routers, they don't DEFINE routes.\n"
                        f"   Found route definitions: {evidence['l2_evidence'][:2]}\n"
                        f"   Possible fix: Reclassify to L2 or split file"
                    ),
                    severity="ERROR",
                ))

    # L5 Engine in wrong location
    if declared_layer == "L5" and "/engines/" not in rel_path:
        if "/drivers/" in rel_path:
            violations.append(Violation(
                file=rel_path,
                line_number=1,
                violation_type="HEADER_LOCATION_MISMATCH",
                message=(
                    f"File declares L5 (Engine) but is located in drivers/.\n"
                    f"   L5 engines belong in engines/ directory.\n"
                    f"   Possible fix: Move file or reclassify header"
                ),
                severity="WARNING",
            ))

    # L6 Driver without DB evidence (may be misclassified)
    if declared_layer == "L6":
        has_db = len(evidence["l6_evidence"]) > 0
        if not has_db and "/drivers/" in rel_path:
            violations.append(Violation(
                file=rel_path,
                line_number=1,
                violation_type="HEADER_CLAIM_MISMATCH",
                message=(
                    f"File declares L6 (Driver) but has NO database operation evidence.\n"
                    f"   L6 drivers should contain: sqlalchemy/sqlmodel, queries, Session\n"
                    f"   Found: 0 DB indicators\n"
                    f"   Possible fix: Reclassify to L5 (if business logic) or add DB ops"
                ),
                severity="WARNING",  # Warning since some drivers are thin
            ))

    # L4/L5 claiming to be L2 (most common issue like knowledge_sdk.py)
    if declared_layer == "L2" and "/engines/" in rel_path:
        violations.append(Violation(
            file=rel_path,
            line_number=1,
            violation_type="HEADER_LOCATION_MISMATCH",
            message=(
                f"File declares L2 (Product APIs) but is located in engines/.\n"
                f"   L2 APIs belong in houseofcards/api/**\n"
                f"   engines/ directory is L5 territory.\n"
                f"   Possible fix: Change header to L5 or move to api/"
            ),
            severity="ERROR",
        ))

    return violations


# =============================================================================
# Import Analysis
# =============================================================================


def extract_imports(file_path: Path) -> List[Tuple[int, str, bool]]:
    """Extract import statements from a Python file.

    Returns: List of (line_number, import_statement, in_type_checking_block)
    """
    imports = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        in_type_checking = False

        for i, line in enumerate(content.split("\n"), 1):
            stripped = line.strip()

            # Track TYPE_CHECKING blocks
            if "TYPE_CHECKING" in stripped and "if" in stripped:
                in_type_checking = True
            elif in_type_checking and stripped and not stripped.startswith("#"):
                # Check for end of TYPE_CHECKING block (dedent or else)
                if not line.startswith(" ") and not line.startswith("\t"):
                    in_type_checking = False

            if stripped.startswith("from ") or stripped.startswith("import "):
                imports.append((i, stripped, in_type_checking))
    except Exception:
        pass
    return imports


def get_import_target_layer(import_line: str) -> Optional[str]:
    """Determine target layer of an import."""
    # HOC import patterns
    if "houseofcards/api/facades/" in import_line or "houseofcards.api.facades" in import_line:
        return "L2.1"
    if "houseofcards/api/" in import_line or "houseofcards.api." in import_line:
        return "L2"
    if "/adapters/" in import_line or ".adapters." in import_line:
        return "L3"
    if "/general/runtime/" in import_line or ".general.runtime." in import_line:
        return "L4"
    if "/engines/" in import_line or ".engines." in import_line:
        return "L5"
    if "/workers/" in import_line or ".workers." in import_line:
        return "L5"
    if "/drivers/" in import_line or ".drivers." in import_line:
        return "L6"
    if "app.models" in import_line or "app/models" in import_line:
        return "L7"
    if "app.customer.models" in import_line or "app.founder.models" in import_line:
        return "L7"

    # Legacy patterns
    if "from app.api." in import_line:
        return "L2"
    if "from app.services." in import_line:
        return "L4"
    if "from app.adapters." in import_line:
        return "L3"
    if "from app.worker." in import_line or "from app.workflow." in import_line:
        return "L5"
    if "from app.auth." in import_line or "from app.db." in import_line:
        return "L6"

    return None


def is_sqlalchemy_import(import_line: str) -> bool:
    """Check if import is sqlalchemy/sqlmodel."""
    return any(pattern in import_line for pattern in FORBIDDEN_RUNTIME_IMPORTS)


def is_forbidden_hoc_import(import_line: str) -> bool:
    """Check if import is from forbidden legacy namespace."""
    return any(pattern in import_line for pattern in FORBIDDEN_HOC_IMPORTS)


# =============================================================================
# Validation Functions
# =============================================================================


def check_layer_import_violation(
    source_layer: str, target_layer: str
) -> bool:
    """Check if importing target_layer from source_layer is a violation."""
    if source_layer not in ALLOWED_IMPORTS:
        return False
    return target_layer not in ALLOWED_IMPORTS[source_layer]


def validate_file(file_path: Path, verbose: bool = False) -> List[Violation]:
    """Validate a single file for all HOC violations."""
    violations = []
    rel_path = str(file_path)
    is_hoc_file = "houseofcards" in rel_path

    # 1. Check layer declaration in header
    layer, source = get_file_layer(file_path)

    if is_hoc_file and source != "header":
        violations.append(Violation(
            file=rel_path,
            line_number=1,
            violation_type="MISSING_HEADER",
            message="HOC file missing '# Layer: L{x}' header declaration",
            severity="WARNING",
        ))

    if not layer:
        return violations  # Can't validate without knowing layer

    # 1b. NEW: Semantic validation - verify header claim matches code behavior
    if is_hoc_file and source == "header":
        evidence = analyze_code_semantics(file_path)
        claim_violations = validate_header_claim(file_path, layer, evidence)
        violations.extend(claim_violations)

    # 2. Check naming convention (only for HOC files)
    if is_hoc_file:
        filename = file_path.name
        for pattern in BANNED_FILENAME_PATTERNS:
            if re.match(pattern, filename):
                violations.append(Violation(
                    file=rel_path,
                    line_number=1,
                    violation_type="BANNED_NAMING",
                    message=f"Filename '{filename}' matches banned pattern. Use *_engine.py or *_driver.py instead of *_service.py",
                    severity="ERROR",
                ))

    # 3. Check imports
    imports = extract_imports(file_path)

    for line_num, import_stmt, in_type_checking in imports:
        # 3a. Check L4/L5 sqlalchemy runtime import (CRITICAL)
        if layer in ("L4", "L5") and is_sqlalchemy_import(import_stmt):
            if not in_type_checking:
                violations.append(Violation(
                    file=rel_path,
                    line_number=line_num,
                    violation_type="SQLALCHEMY_RUNTIME",
                    message=f"L{layer[-1]} cannot import sqlalchemy/sqlmodel at runtime. Use TYPE_CHECKING block.\n   Import: {import_stmt}",
                    severity="ERROR",
                ))

        # 3b. Check HOC importing from legacy app.services
        if is_hoc_file and is_forbidden_hoc_import(import_stmt):
            violations.append(Violation(
                file=rel_path,
                line_number=line_num,
                violation_type="LEGACY_IMPORT",
                message=f"HOC file cannot import from legacy app.services namespace.\n   Import: {import_stmt}",
                severity="ERROR",
            ))

        # 3c. Check layer boundary violations
        target_layer = get_import_target_layer(import_stmt)
        if target_layer and check_layer_import_violation(layer, target_layer):
            violations.append(Violation(
                file=rel_path,
                line_number=line_num,
                violation_type="LAYER_BOUNDARY",
                message=f"{layer} cannot import {target_layer}. Allowed: {ALLOWED_IMPORTS.get(layer, set())}\n   Import: {import_stmt}",
                severity="ERROR",
            ))

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
        "alembic/versions",
    },
    hoc_only: bool = False,
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

        # HOC-only filter
        if hoc_only and "houseofcards" not in str(file_path):
            continue

        result.files_scanned += 1

        violations = validate_file(file_path, verbose)
        result.violations.extend(violations)

    return result


# =============================================================================
# Main
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="BLCA — Bidirectional Layer Consistency Auditor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
HOC Layer Topology V1.2.0:
  L1    = Frontend
  L2.1  = API Facade (organizers)
  L2    = Product APIs
  L3    = Boundary Adapters (cross-domain allowed)
  L4    = Governed Runtime / Domain Engines
  L5    = Engines / Workers / Schemas
  L6    = Database Drivers
  L7    = Models
  L8    = Database

Critical Rules:
  - L4/L5 engines CANNOT import sqlalchemy at runtime (use TYPE_CHECKING)
  - *_service.py naming is BANNED (use *_engine.py or *_driver.py)
  - HOC files cannot import from legacy app.services

Examples:
  %(prog)s                    # Validate all
  %(prog)s --backend          # Backend only
  %(prog)s --hoc              # HOC files only
  %(prog)s --ci               # Exit 1 on violations
        """,
    )

    parser.add_argument("--backend", action="store_true", help="Validate backend only")
    parser.add_argument("--hoc", action="store_true", help="Validate HOC files only")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show details")
    parser.add_argument("--ci", action="store_true", help="Exit 1 if violations found")
    parser.add_argument("--path", type=str, default=".", help="Root path to scan")

    args = parser.parse_args()

    root = Path(args.path)

    # Determine what to scan
    if args.backend:
        scan_root = root / "backend"
    else:
        scan_root = root

    if not scan_root.exists():
        print(f"ERROR: Path not found: {scan_root}", file=sys.stderr)
        sys.exit(1)

    print("Layer Validator (PIN-240)")
    print(f"Scanning: {scan_root}")
    print("-" * 60)

    result = validate_directory(
        scan_root,
        hoc_only=args.hoc,
        verbose=args.verbose,
    )

    print(f"Files scanned: {result.files_scanned}")
    print(f"Violations found: {len(result.violations)}")
    print()

    if result.violations:
        # Group by type
        by_type: Dict[str, List[Violation]] = {}
        for v in result.violations:
            by_type.setdefault(v.violation_type, []).append(v)

        for vtype, violations in sorted(by_type.items()):
            errors = [v for v in violations if v.severity == "ERROR"]
            warnings = [v for v in violations if v.severity == "WARNING"]

            print(f"\n{vtype}: {len(errors)} errors, {len(warnings)} warnings")
            print("-" * 40)

            for v in violations[:10]:  # Show first 10
                print(f"\n{v}")

            if len(violations) > 10:
                print(f"\n   ... and {len(violations) - 10} more")

        print()
        print(f"SUMMARY: {result.error_count} errors, {result.warning_count} warnings")

        if args.ci and result.error_count > 0:
            sys.exit(1)
    else:
        print("No layer violations found!")
        print()
        print("Layer architecture is clean.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
